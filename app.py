"""
智能法务合同修改与润色智能体 - FastAPI Web 应用
"""
import os
import sys
import io
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from config_loader import load_config
from contract_perception import ContractPerception
from legal_brain import LegalBrain
from security_guard import SecurityGuard
from contract_executor import ContractExecutor

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI(title="智能法务合同修改与润色智能体")
config = load_config()

storage_config = config.get_storage_config()
UPLOAD_DIR = Path(storage_config.get('upload_dir', 'uploads'))
OUTPUT_DIR = Path(storage_config.get('output_dir', 'outputs'))
ALLOWED_EXTENSIONS = storage_config.get('allowed_extensions', ['.docx'])

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory="templates")


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    ext = Path(original_filename).suffix
    return f"{timestamp}_{unique_id}{ext}"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    instruction: str = Form(...)
):
    if not file.filename:
        return templates.TemplateResponse(request, "index.html", {"error": "未选择文件"})

    if not allowed_file(file.filename):
        return templates.TemplateResponse(request, "index.html", {
            "error": f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        })

    if not instruction.strip():
        return templates.TemplateResponse(request, "index.html", {"error": "请输入修改指令"})

    original_filename = file.filename
    unique_filename = generate_unique_filename(original_filename)
    upload_path = UPLOAD_DIR / unique_filename

    try:
        content = await file.read()
        upload_path.write_bytes(content)
    except Exception as e:
        return templates.TemplateResponse(request, "index.html", {"error": f"文件上传失败: {str(e)}"})

    try:
        result = process_contract(str(upload_path), instruction.strip(), unique_filename)
        return templates.TemplateResponse(request, "result.html", {
            "result": result,
            "original_file": unique_filename,
            "output_file": result['output_filename']
        })
    except Exception as e:
        return templates.TemplateResponse(request, "index.html", {"error": f"处理失败: {str(e)}"})


def process_contract(file_path: str, user_instruction: str, original_filename: str) -> dict:
    llm_config = config.get_llm_config()
    perception = ContractPerception()
    brain = LegalBrain(
        api_key=llm_config.get('api_key'),
        base_url=llm_config.get('base_url'),
        model=llm_config.get('model', 'gpt-4')
    )
    security = SecurityGuard()
    executor = ContractExecutor()

    blocks = perception.scan_contract(file_path)
    modification_map = {}
    risk_blocks = []

    for block in blocks:
        result = brain.review_and_rewrite(user_instruction, block.text)
        if result is None:
            continue

        audit_result, audit_msg = security.audit_json_response({
            'revised_text': result.revised_text,
            'risk_analysis': result.risk_analysis
        })

        if not audit_result:
            continue

        if result.has_risk and result.revised_text != block.text:
            modification_map[block.block_id] = result.revised_text
            risk_blocks.append({
                'block_id': block.block_id,
                'original': block.text[:100] + '...' if len(block.text) > 100 else block.text,
                'revised': result.revised_text[:100] + '...' if len(result.revised_text) > 100 else result.revised_text,
                'analysis': result.risk_analysis
            })

    output_filename = f"modified_{original_filename}"
    if not output_filename.endswith('.docx'):
        output_filename = output_filename.rsplit('.', 1)[0] + '.docx'
    output_path = OUTPUT_DIR / output_filename

    if modification_map:
        executor.execute_modification(file_path, str(output_path), modification_map)

    return {
        'total_blocks': len(blocks),
        'risk_count': len(modification_map),
        'risk_blocks': risk_blocks,
        'output_filename': output_filename,
        'has_modifications': len(modification_map) > 0
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    output_path = OUTPUT_DIR / filename
    if output_path.exists():
        return FileResponse(
            str(output_path),
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=filename
        )
    upload_path = UPLOAD_DIR / filename
    if upload_path.exists():
        return FileResponse(
            str(upload_path),
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=filename
        )
    return JSONResponse(status_code=404, content={"error": "文件不存在"})


@app.get("/api/health")
async def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}


if __name__ == '__main__':
    import uvicorn
    server_config = config.get_server_config()
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 5000)
    
    print(f"启动服务: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
