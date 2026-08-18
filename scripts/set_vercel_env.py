import subprocess
import time
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
SCOPE = "mohommadhuafnan756-1743s-projects"
TARGETS = ["production", "preview", "development"]

def set_all_env():
    if not ENV_PATH.exists():
        print(f"Error: {ENV_PATH} not found.")
        return

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    env_vars = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and v:
                env_vars[k] = v

    print(f"=== Loaded {len(env_vars)} environment variables from .env ===")

    for k, v in env_vars.items():
        print(f"\nSetting {k} on Vercel...")
        for target in TARGETS:
            cmd = f"npx vercel env add {k} {target} --scope {SCOPE}"
            p = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = p.communicate(input=f"{v}\n")
            status = "OK" if p.returncode == 0 else f"ERR: {err.strip()}"
            print(f"  [{target.upper()}]: {status}")

    print("\n=== Listing all configured environment variables on Vercel ===")
    subprocess.run(f"npx vercel env ls --scope {SCOPE}", shell=True)

    print("\n=== Deploying Production Build with New Environment Variables ===")
    p_deploy = subprocess.run(
        f"npx vercel deploy --prod --yes --scope {SCOPE}",
        shell=True,
        capture_output=True,
        text=True
    )
    print(p_deploy.stdout)
    print(p_deploy.stderr)
    print("\n=== DEPLOYMENT COMPLETE ===")

if __name__ == "__main__":
    set_all_env()
