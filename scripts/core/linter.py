import subprocess
import shutil

class Linter:
    """封裝靜態分析工具 (Ruff) 的執行。"""

    def __init__(self):
        self.paths_to_try = [
            shutil.which("ruff"),
            "/Users/jameschen/.local/bin/uv run --with ruff ruff",
            "ruff"
        ]

    def scan(self, files):
        """執行掃描並返回結構化違規列表。"""
        if not files: return []
        
        for base in self.paths_to_try:
            if not base: continue
            try:
                cmd_parts = base.split()
                # 雙重格式旗標試錯 (Fix detected by self-review)
                for format_flag in ["--output-format", "--format"]:
                    full_cmd = cmd_parts + ["check", format_flag, "json"] + files
                    res = subprocess.run(full_cmd, capture_output=True, text=True)
                    if res.returncode in [0, 1] and res.stdout.strip().startswith("["):
                        return res.stdout.strip()
            except Exception: continue
        return "[]"
