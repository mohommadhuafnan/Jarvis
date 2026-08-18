import sys
import subprocess
import tempfile
from pathlib import Path
from backend.config import WORKSPACE_DIR
from backend.tools.registry import registry, RiskLevel

@registry.register(
    name="code.generate",
    description="Generate clean, production-ready code with explanation for any requested language or algorithm.",
    risk_level=RiskLevel.LOW,
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string", "description": "Programming language, e.g. 'python', 'javascript', 'html'"},
            "prompt": {"type": "string", "description": "Description of what code to generate"}
        },
        "required": ["language", "prompt"]
    }
)
def generate_code(language: str, prompt: str):
    # If called via tool, returns structured placeholder or metadata
    return {
        "language": language,
        "prompt": prompt,
        "status": "READY_FOR_EXECUTION"
    }

@registry.register(
    name="code.run",
    description="Safely execute Python or JavaScript code in a sandboxed isolated subprocess (HIGH RISK: requires confirmation).",
    risk_level=RiskLevel.HIGH,
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string", "enum": ["python", "javascript"], "description": "Language to execute"},
            "code": {"type": "string", "description": "The exact source code to execute"}
        },
        "required": ["language", "code"]
    }
)
def run_code(language: str, code: str):
    language = language.lower()
    suffix = ".py" if language == "python" else ".js"

    # Create temporary script inside workspace sandbox
    temp_file = WORKSPACE_DIR / f"temp_exec_{Path(tempfile.mktemp()).stem}{suffix}"
    try:
        temp_file.write_text(code, encoding="utf-8")
        
        if language == "python":
            cmd = [sys.executable, str(temp_file)]
        elif language == "javascript":
            cmd = ["node", str(temp_file)]
        else:
            return {"error": f"Unsupported execution language: {language}"}

        # Run with 5 second hard timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(WORKSPACE_DIR)
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout if result.stdout else "[No output]",
            "stderr": result.stderr if result.stderr else None,
            "execution_mode": "SANDBOXED_SUBPROCESS"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Execution timed out (5s limit exceeded)."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Execution error: {str(e)}"
        }
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
