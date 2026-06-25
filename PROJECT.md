# 智能法务合同修改与润色智能体

## 项目简介

一个基于大语言模型（LLM）的智能法务合同处理系统，能够自动识别 Word 合同文档中的风险条款，并在保持原有排版格式的前提下进行智能润色修改。

## 核心功能

| 功能 | 说明 |
|------|------|
| 合同感知 | 自动解析 Word 文档，将合同按段落和表格切片，生成结构化文本块 |
| 法务审查 | 利用 LLM 对条款进行风险识别，自动区分标题、当事人信息与实质性条款 |
| 安全审计 | 使用 AST 静态检查防止提示词注入攻击，确保返回内容安全 |
| 无损回填 | 采用 Run 级替换算法，保持文档原有字体、字号、加粗等格式，修改内容标红显示 |
| Web 界面 | 提供友好的文件上传界面，支持拖拽上传，实时展示修改结果 |

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Web 服务                       │
│                    (app.py)                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   合同感知    │───▶│   法务审查    │───▶│  安全审计   │ │
│  │ ContractPerception│ LegalBrain │   │ SecurityGuard│ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │        │
│         ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────┐│
│  │              无损回填执行模块                         ││
│  │              ContractExecutor                       ││
│  └─────────────────────────────────────────────────────┘│
│                          │                              │
│                          ▼                              │
│                   outputs/modified_xxx.docx             │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
office_agent/
├── app.py                    # FastAPI Web 应用主入口
├── config.yaml               # 配置文件（API密钥、服务器、存储）
├── config_loader.py          # 配置加载模块
├── contract_perception.py    # 合同感知模块 - 文档解析与切片
├── legal_brain.py            # 法务大模型决策模块 - LLM调用与解析
├── security_guard.py         # 安全审计模块 - AST防注入检查
├── contract_executor.py      # 无损回填模块 - Run级格式保持替换
├── main.py                   # 命令行测试入口
├── requirements.txt          # Python 依赖
├── templates/                # HTML 模板
│   ├── index.html            # 上传页面
│   └── result.html           # 结果展示页面
├── uploads/                  # 上传文件存储目录
├── outputs/                  # 修改后文件存储目录
├── venv/                     # Python 虚拟环境
└── prompt.txt                # 项目需求文档
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`，填入你的 LLM API 配置：

```yaml
llm:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
```

### 3. 启动服务

```bash
python app.py
```

访问 http://localhost:5000 使用 Web 界面。

## 使用流程

1. **上传合同**：在 Web 界面选择或拖拽 Word 合同文件
2. **输入指令**：描述希望对合同进行的修改（如"修改不平等违约金条款"）
3. **AI 审查**：系统自动调用 LLM 对每个条款进行风险审查
4. **查看结果**：展示发现的风险条款和修改建议
5. **下载文件**：下载修改后的 Word 文档（修改内容标红显示）

## 模块说明

### ContractPerception（合同感知）
- 扫描 Word 文档，提取所有段落和表格内容
- 为每个文本块生成唯一 block_id，便于定位回填
- 支持段落和表格单元格两种内容类型

### LegalBrain（法务审查）
- 调用 OpenAI 兼容 API 进行条款审查
- 智能区分标题、当事人信息与实质性条款
- 强制输出 JSON 格式，支持重试纠错
- 明确限制不修改标题、编号、当事人信息

### SecurityGuard（安全审计）
- 使用 ast.parse() 进行静态代码检查
- 正则表达式匹配可疑模式（exec、eval、import 等）
- 双重检查防止提示词注入攻击

### ContractExecutor（无损回填）
- Run 级替换算法，保持原有字体、字号、加粗、颜色等格式
- 修改内容自动标红（RGB: 255,0,0）
- 段落格式完整保留（对齐、缩进、行距等）
- 输出文件强制 .docx 格式

## 配置说明

```yaml
# LLM API 配置
llm:
  api_key: "your-api-key"      # API 密钥
  base_url: "https://api.openai.com/v1"  # API 地址
  model: "gpt-4"               # 模型名称
  temperature: 0.3             # 生成温度
  max_retries: 3               # 最大重试次数

# 服务器配置
server:
  host: "0.0.0.0"              # 监听地址
  port: 5000                   # 监听端口
  debug: true                  # 调试模式

# 文件存储配置
storage:
  upload_dir: "uploads"        # 上传目录
  output_dir: "outputs"        # 输出目录
  max_file_size_mb: 20         # 最大文件大小
  allowed_extensions:          # 允许的文件类型
    - ".docx"
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页（上传界面） |
| POST | `/` | 上传文件并处理 |
| GET | `/download/{filename}` | 下载文件 |
| GET | `/api/health` | 健康检查 |

## 依赖说明

- `python-docx`: Word 文档处理
- `openai`: LLM API 调用（兼容 OpenAI 接口）
- `fastapi`: Web 框架
- `uvicorn`: ASGI 服务器
- `pyyaml`: 配置文件解析
- `python-multipart`: 文件上传支持
