from pathlib import Path
import tempfile
from .config import Config
from .generator import generate, export, checksums

def compare():
    with tempfile.TemporaryDirectory() as tmp:
        a=Path(tmp)/"run_a"; b=Path(tmp)/"run_b"
        for dest in (a,b): export(generate(Config(output_dir=str(dest))),dest)
        ca,cb=checksums(a),checksums(b)
        return {"identical":ca==cb,"run_a":ca,"run_b":cb}
if __name__=="__main__":
    result=compare(); print("REPRODUCIBLE:",result["identical"])
    if not result["identical"]: raise SystemExit(1)
