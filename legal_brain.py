"""
法务大模型决策模块 - LegalBrain
负责调用 LLM API 对合同条款进行风险审查和重写
"""
from dataclasses import dataclass
from typing import Optional
import json
import re

from openai import OpenAI


@dataclass
class ReviewResult:
    """审查结果数据结构"""
    has_risk: bool
    risk_analysis: str
    revised_text: str


class LegalBrain:
    """法务大模型决策模块 - 负责合同条款的风险审查和润色"""

    SYSTEM_PROMPT = """你是一位拥有15年经验的资深法务总监，精通中国合同法和商业合同实务。

你的职责：
1. 识别合同中不平等、显失公平的条款
2. 分析条款中的法律风险
3. 提供符合《民法典》合同编的修改建议
4. 确保修改后的条款对双方公平对等

【重要限制】你必须遵守以下规则：
- 只修改合同的实质性条款（如违约金、付款条件、责任划分等）
- 绝对不要修改以下内容：
  * 合同标题（如"房屋租赁合同"、"技术服务合同"等）
  * 条款编号（如"第一条"、"第二条"等）
  * 当事人信息（甲方、乙方名称等）
  * 空白填写处（下划线部分）
  * 格式性描述（如"以下简称甲方"等）
- 如果输入的文本是标题或格式性内容，has_risk 必须设为 false，revised_text 返回原文

你必须严格按照指定的 JSON 格式输出结果。"""

    USER_PROMPT_TEMPLATE = """请对以下合同条款进行法务审查和修改：

用户指令：{instruction}

合同条款：{text}

请先判断该文本是否属于以下类型：
1. 合同标题 -> 不修改，has_risk=false
2. 条款编号（如"第一条 XXX"）-> 不修改，has_risk=false
3. 当事人信息 -> 不修改，has_risk=false
4. 空白填写处 -> 不修改，has_risk=false
5. 实质性合同条款 -> 根据用户指令审查并修改

如果是实质性条款且存在风险，请按以下 JSON 格式输出：
{{
    "has_risk": true,
    "risk_analysis": "对该条款的风险分析说明",
    "revised_text": "修改后的条款文本"
}}

如果不需要修改，请输出：
{{
    "has_risk": false,
    "risk_analysis": "该内容无需修改",
    "revised_text": "原文保持不变"
}}

注意：
1. 只输出 JSON，不要输出其他内容
2. 对于标题、编号、当事人信息等，revised_text 必须与原文完全一致
3. 只有实质性条款才进行修改"""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4"):
        """
        初始化法务大模型模块
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = 3

    def review_and_rewrite(self, user_instruction: str, block_text: str) -> Optional[ReviewResult]:
        """
        对合同条款进行风险审查和重写
        
        Args:
            user_instruction: 用户修改指令
            block_text: 合同条款文本
            
        Returns:
            审查结果，失败返回 None
        """
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            instruction=user_instruction,
            text=block_text
        )

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content
                result = self._parse_json_response(content)
                if result:
                    return result

            except Exception as e:
                print(f"[LegalBrain] 调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return None

        return None

    def _parse_json_response(self, content: str) -> Optional[ReviewResult]:
        """
        解析 LLM 返回的 JSON 响应
        
        Args:
            content: LLM 响应内容
            
        Returns:
            解析后的 ReviewResult，失败返回 None
        """
        try:
            # 尝试直接解析
            data = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return None
            else:
                return None

        # 验证必要字段
        required_fields = ['has_risk', 'risk_analysis', 'revised_text']
        if not all(field in data for field in required_fields):
            return None

        # 清理文本，移除可能导致格式问题的字符
        revised_text = self._sanitize_text(str(data['revised_text']))
        risk_analysis = self._sanitize_text(str(data['risk_analysis']))

        return ReviewResult(
            has_risk=bool(data['has_risk']),
            risk_analysis=risk_analysis,
            revised_text=revised_text
        )

    def _sanitize_text(self, text: str) -> str:
        """
        清理文本，移除可能导致格式问题的字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除可能导致 Word 文档格式问题的字符
        # 保留中文标点和正常换行
        text = text.replace('\r\n', '\n')  # 统一换行符
        text = text.replace('\r', '\n')    # 统一换行符
        
        # 移除连续的换行符，只保留单个换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除开头和结尾的空白
        text = text.strip()
        
        return text
