"""
AST安全与合规审计模块 - SecurityGuard
负责使用 AST 静态检查防止提示词注入攻击
"""
import ast
import re
from typing import Tuple


class SecurityGuard:
    """AST安全与合规审计模块 - 负责防止恶意代码注入"""

    # 可疑的 Python 关键字和模式
    SUSPICIOUS_PATTERNS = [
        r'\bexec\s*\(',
        r'\beval\s*\(',
        r'\bcompile\s*\(',
        r'\b__import__\s*\(',
        r'\bos\.\s*system\s*\(',
        r'\bos\.\s*popen\s*\(',
        r'\bsubprocess\.',
        r'\bimport\s+os\b',
        r'\bfrom\s+os\s+import\b',
        r'\bimport\s+subprocess\b',
        r'\bfrom\s+subprocess\s+import\b',
        r'\bopen\s*\(.*["\']w',
        r'\brm\s+-rf\b',
        r'\bprint\s*\(\s*["\'].*exec',
    ]

    def audit_json_response(self, llm_json: dict) -> Tuple[bool, str]:
        """
        审计 LLM 返回的 JSON 响应，防止提示词注入
        
        Args:
            llm_json: LLM 返回的字典
            
        Returns:
            (是否安全, 审计信息)
        """
        if not isinstance(llm_json, dict):
            return False, "输入不是有效的字典类型"

        # 检查 revised_text 字段
        revised_text = llm_json.get('revised_text', '')
        if not isinstance(revised_text, str):
            return False, "revised_text 不是字符串类型"

        # AST 静态检查
        is_safe, message = self._ast_check(revised_text)
        if not is_safe:
            return False, f"AST 检查失败: {message}"

        # 正则模式检查
        is_safe, message = self._pattern_check(revised_text)
        if not is_safe:
            return False, f"模式检查失败: {message}"

        # 检查其他可能包含代码的字段
        for field in ['risk_analysis']:
            field_value = llm_json.get(field, '')
            if isinstance(field_value, str):
                is_safe, message = self._pattern_check(field_value)
                if not is_safe:
                    return False, f"字段 {field} 模式检查失败: {message}"

        return True, "审计通过"

    def _ast_check(self, text: str) -> Tuple[bool, str]:
        """
        使用 AST 检查文本是否包含可执行代码
        
        Args:
            text: 待检查的文本
            
        Returns:
            (是否安全, 信息)
        """
        # 尝试将文本作为 Python 代码解析
        try:
            tree = ast.parse(text, mode='eval')
            # 如果能成功解析为表达式，检查是否包含危险操作
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_func_name(node)
                    if func_name in ['exec', 'eval', 'compile', '__import__']:
                        return False, f"检测到危险函数调用: {func_name}"
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    return False, "检测到 import 语句"
        except SyntaxError:
            # 语法错误说明不是有效的 Python 代码，这是好事
            pass
        except Exception as e:
            return False, f"AST 解析异常: {str(e)}"

        return True, "AST 检查通过"

    def _get_func_name(self, node: ast.Call) -> str:
        """获取函数调用的名称"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _pattern_check(self, text: str) -> Tuple[bool, str]:
        """
        使用正则表达式检查可疑模式
        
        Args:
            text: 待检查的文本
            
        Returns:
            (是否安全, 信息)
        """
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"检测到可疑模式: {pattern}"

        return True, "模式检查通过"

    def sanitize_text(self, text: str) -> str:
        """
        清理文本中的潜在危险内容
        
        Args:
            text: 待清理的文本
            
        Returns:
            清理后的文本
        """
        # 移除可能的代码块标记
        text = re.sub(r'```python.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        # 移除可能的系统命令
        text = re.sub(r'!\s*\(.*?\)', '', text)
        text = re.sub(r'!\s*\[.*?\]\(.*?\)', '', text)

        return text.strip()
