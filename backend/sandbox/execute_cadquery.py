#!/usr/bin/env python3
"""Isolated CadQuery execution wrapper.

Receives a CadQuery script via stdin or file argument, executes it in an
isolated subprocess with a 30s timeout, and writes a JSON result file
containing file paths or error traceback.
"""

import argparse
import json
import os
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="CadQuery sandbox executor")
    parser.add_argument("--script", help="Path to the CadQuery script file")
    parser.add_argument("--output-dir", default="/sandbox/outputs", help="Directory for generated artifacts")
    parser.add_argument("--result-file", default="/sandbox/outputs/result.json", help="Path to write JSON result")
    args = parser.parse_args()

    if args.script:
        with open(args.script, "r") as fh:
            script_content = fh.read()
    else:
        script_content = sys.stdin.read()

    os.makedirs(args.output_dir, exist_ok=True)

    run_id = os.getpid()
    work_dir = os.path.join(args.output_dir, f"run_{run_id}")
    os.makedirs(work_dir, exist_ok=True)

    script_path = os.path.join(work_dir, "script.py")

    with open(script_path, "w") as fh:
        fh.write(script_content)

    wrapper_code = f"""\
import sys, os, traceback, json
sys.path.insert(0, "/usr/local/lib/python3.11/site-packages")

work_dir = {json.dumps(work_dir)}
result = {{"status": "success", "files": {{}}, "logs": ""}}

os.chdir(work_dir)

try:
    exec(open({json.dumps(script_path)}, "r").read(), {{"__name__": "__main__", "__file__": {json.dumps(script_path)}})
    for fmt in ("step", "stl", "gltf"):
        path = os.path.join(work_dir, f"output.{{fmt}}")
        if os.path.exists(path):
            result["files"][fmt] = path
except Exception:
    result["status"] = "error"
    result["error"] = traceback.format_exc()

print(json.dumps(result))
"""

    wrapper_path = os.path.join(work_dir, "wrapper.py")
    with open(wrapper_path, "w") as fh:
        fh.write(wrapper_code)

    try:
        proc = subprocess.run(
            [sys.executable, wrapper_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=work_dir,
        )
    except subprocess.TimeoutExpired:
        result = {
            "status": "error",
            "error": "Execution timed out after 30 seconds",
            "files": {},
            "logs": "",
        }
        _write_result(args.result_file, result)
        return
    except Exception as exc:
        result = {
            "status": "error",
            "error": str(exc),
            "files": {},
            "logs": "",
        }
        _write_result(args.result_file, result)
        return

    combined_output = proc.stdout + proc.stderr

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
        result["logs"] = combined_output.strip()
    except (json.JSONDecodeError, IndexError):
        result = {
            "status": "error",
            "error": proc.stderr.strip() or proc.stdout.strip() or "Unknown execution error",
            "files": {},
            "logs": combined_output.strip(),
        }

    _write_result(args.result_file, result)


def _write_result(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
    print(json.dumps(data))


if __name__ == "__main__":
    main()
