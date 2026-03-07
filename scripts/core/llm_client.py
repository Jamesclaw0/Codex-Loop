import subprocess
import json
import fcntl
import shutil
import hashlib
import time
from pathlib import Path

class LLMClient:
    """負責與 LLM (Codex) 的通訊與結果解析。"""

    def __init__(self, bin_path=None, lock_file=None):
        # 優先使用傳入路徑，否則動態偵測絕對路徑
        self.llm_bin = bin_path or shutil.which("codex") or "/Users/jameschen/.npm-global/bin/codex"
        self.lock_file = lock_file or "/tmp/codex_loop_v2.lock"

    def ask(self, prompt, payload):
        """執行 LLM 請求並返回解析後的 JSON 結果。"""
        full_prompt = prompt + payload
        try:
            with open(self.lock_file, "w") as lock_f:
                fcntl.flock(lock_f, fcntl.LOCK_EX)
                res = subprocess.run(
                    [self.llm_bin, "exec", "-"], 
                    input=full_prompt, 
                    capture_output=True, 
                    text=True, 
                    timeout=180
                )
            
            # 使用更穩裝的 JSON 區塊選取模式
            output = res.stdout + res.stderr
            try:
                if "```json" in output:
                    json_str = output.split("```json")[1].split("```")[0].strip()
                elif "{" in output:
                    json_str = "{" + output.split("{", 1)[1].rsplit("}", 1)[0] + "}"
                else:
                    json_str = output.strip()
                
                return json.loads(json_str), output
            except (json.JSONDecodeError, IndexError):
                # 備援：若非 JSON，則包裝為失敗狀態
                return {"status": "FAIL", "summary": "LLM output was not valid JSON.", "violations": []}, output
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"status": "FAIL", "summary": f"LLM client error: {e}", "violations": []}, str(e)
