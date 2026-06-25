# 智能法务合同修改与润色智能体

一个基于大语言模型（LLM）的智能法务合同处理系统，能够自动识别 Word 合同文档中的风险条款，并在保持原有排版格式的前提下进行智能润色修改。

## 功能特点

- **合同感知** - 自动解析 Word 文档，将合同按段落和表格切片
- **法务审查** - 利用 LLM 对条款进行风险识别，智能区分标题与实质性条款
- **安全审计** - 使用 AST 静态检查防止提示词注入攻击
- **无损回填** - 采用 Run 级替换算法，保持原有格式，修改内容标红显示
- **Web 界面** - 支持文件拖拽上传，实时展示修改结果

## 快速开始

### 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`，填入 LLM API 配置：

```yaml
llm:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
```

### 启动服务

```bash
python app.py
```

访问 http://localhost:5000 使用 Web 界面。

## 项目结构

```
office_agent/
├── app.py                    # FastAPI Web 应用主入口
├── config.yaml               # 配置文件（API密钥、服务器、存储）
├── config_loader.py          # 配置加载模块
├── contract_perception.py    # 合同感知模块
├── legal_brain.py            # 法务大模型决策模块
├── security_guard.py         # 安全审计模块
├── contract_executor.py      # 无损回填模块
├── main.py                   # 命令行测试入口
├── requirements.txt          # Python 依赖
├── templates/                # HTML 模板
│   ├── index.html            # 上传页面
│   └── result.html           # 结果展示页面
├── uploads/                  # 上传文件存储
├── outputs/                  # 修改后文件存储
└── venv/                     # Python 虚拟环境
```

## 使用流程

1. 上传 Word 合同文件
2. 输入修改指令（如"修改不平等违约金条款"）
3. AI 自动审查每个条款的风险
4. 查看发现的风险条款和修改建议
5. 下载修改后的文档（修改内容标红显示）

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 文档处理 | python-docx |
| LLM 调用 | OpenAI SDK（兼容接口） |
| 安全审计 | ast（Python 内置） |
| 配置管理 | PyYAML |

## 核心模块

- **ContractPerception** - 扫描 Word 文档，生成结构化文本块
- **LegalBrain** - 调用 LLM 进行条款审查，区分标题与实质性条款
- **SecurityGuard** - AST 静态检查 + 正则匹配，双重防注入
- **ContractExecutor** - Run 级替换，保持字体/字号/加粗等格式，修改内容标红

## 配置说明

```yaml
llm:
  api_key: "your-api-key"          # API 密钥
  base_url: "https://api.openai.com/v1"  # API 地址
  model: "gpt-4"                   # 模型名称
  temperature: 0.3                 # 生成温度

server:
  host: "0.0.0.0"                  # 监听地址
  port: 5000                       # 监听端口

storage:
  upload_dir: "uploads"            # 上传目录
  output_dir: "outputs"            # 输出目录
  max_file_size_mb: 20             # 最大文件大小
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页（上传界面） |
| POST | `/` | 上传文件并处理 |
| GET | `/download/{filename}` | 下载文件 |
| GET | `/api/health` | 健康检查 |

## License

MIT
