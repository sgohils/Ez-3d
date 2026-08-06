from __future__ import annotations

import os
import re
import shutil
import time


def inject_stl_tolerance(code: str, tolerance: float) -> str:
    pattern = r'cq\.exporters\.export\(result,\s*["\']output\.stl["\'](?:,\s*tolerance\s*=\s*[\d.]+)?\)'
    replacement = f'cq.exporters.export(result, "output.stl", tolerance={tolerance})'
    return re.sub(pattern, replacement, code)


def cleanup_old_sessions(outputs_dir: str, max_age_seconds: int = 3600) -> None:
    if not os.path.isdir(outputs_dir):
        return
    cutoff = time.time() - max_age_seconds
    for entry in os.listdir(outputs_dir):
        session_dir = os.path.join(outputs_dir, entry)
        if os.path.isdir(session_dir):
            mtime = os.path.getmtime(session_dir)
            if mtime < cutoff:
                shutil.rmtree(session_dir, ignore_errors=True)
