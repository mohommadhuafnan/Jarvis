import os
from pathlib import Path
from backend.config import WORKSPACE_DIR
from backend.tools.registry import registry, RiskLevel

def _resolve_safe_path(filepath: str) -> Path:
    # Resolve against WORKSPACE_DIR and prevent directory traversal
    clean_path = Path(filepath).name if "/" not in filepath and "\\" not in filepath else Path(filepath)
    if clean_path.is_absolute():
        target = clean_path
    else:
        target = (WORKSPACE_DIR / clean_path).resolve()
    
    # Ensure it is within WORKSPACE_DIR
    if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
        target = WORKSPACE_DIR / target.name
    return target

@registry.register(
    name="files.list",
    description="List all files in the sandboxed workspace directory.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_files():
    files = []
    for item in WORKSPACE_DIR.glob("**/*"):
        if item.is_file():
            rel = item.relative_to(WORKSPACE_DIR)
            files.append({
                "name": item.name,
                "path": str(rel),
                "size_bytes": item.stat().st_size,
                "modified": item.stat().st_mtime
            })
    return {
        "workspace": str(WORKSPACE_DIR),
        "total_files": len(files),
        "files": files
    }

@registry.register(
    name="files.read",
    description="Read the text content of a file inside the sandboxed workspace.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Filename or relative path inside workspace"}
        },
        "required": ["filename"]
    }
)
def read_file(filename: str):
    target = _resolve_safe_path(filename)
    if not target.exists():
        return {"error": f"File '{filename}' does not exist in workspace."}
    try:
        content = target.read_text(encoding="utf-8")
        return {
            "filename": target.name,
            "size": len(content),
            "content": content
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

@registry.register(
    name="files.create",
    description="Create or write content to a file inside the sandboxed workspace.",
    risk_level=RiskLevel.MEDIUM,
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Filename to create, e.g. 'report.txt', 'analysis.py'"},
            "content": {"type": "string", "description": "Text or code content to write"}
        },
        "required": ["filename", "content"]
    }
)
def create_file(filename: str, content: str):
    target = _resolve_safe_path(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {
        "success": True,
        "filename": target.name,
        "path": str(target),
        "bytes_written": len(content.encode("utf-8")),
        "message": f"File '{target.name}' written successfully in workspace."
    }

@registry.register(
    name="files.delete",
    description="Delete a file from the sandboxed workspace (HIGH RISK: requires confirmation).",
    risk_level=RiskLevel.HIGH,
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Filename to delete"}
        },
        "required": ["filename"]
    }
)
def delete_file(filename: str):
    target = _resolve_safe_path(filename)
    if not target.exists():
        return {"error": f"File '{filename}' not found."}
    target.unlink()
    return {
        "success": True,
        "filename": filename,
        "message": f"File '{filename}' has been deleted."
    }
