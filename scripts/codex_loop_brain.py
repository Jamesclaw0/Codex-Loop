#!/usr/bin/env python3
"""
功能: Codex-Loop 跨模型邏輯腦核心決策與審查模組
🧠 Muse-Core Cognitive Loop Brain (Lvl 16)
負責處理 codex-loop 的核心邏輯、跨嘗試記憶與品質決策。
支援 Inner Loop，將審核報告輸出至 /tmp/codex_loop_report.md 供 parallel_fix.py 驅動自動修復迴圈。
"""
import os
import sys
import subprocess
import fcntl
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime

# --- 配置 ---
KB_DIR = os.getenv("MUSE_CORE_KB_DIR", "/Users/jameschen/Downloads/obsidian/知識庫")

class CodexLoopBrain:
    def __init__(self, scope=".", use_global=False, base_commit="staged"):
        self.scope = scope if not use_global else ""
        self.base_commit = base_commit
        self.git_dir = self._get_git_dir()
        self.transcripts_dir = Path.home() / ".muse_transcripts"
        self.transcripts_dir.mkdir(exist_ok=True)
        
        if self.git_dir:
            abs_git_dir = os.path.abspath(self.git_dir)
            repo_hash = hashlib.md5(abs_git_dir.encode()).hexdigest()[:8]
            self.count_file = os.path.join(self.git_dir, "codex_loop_count.txt")
            self.lock_file = f"/tmp/codex_loop_{repo_hash}.lock"
            self.report_file = f"/tmp/codex_loop_report_{repo_hash}.md"
        else:
            self.count_file = "/tmp/codex_loop_count.txt"
            self.lock_file = "/tmp/codex_loop_global.lock"
            self.report_file = "/tmp/codex_loop_report.md"

    def _get_subconscious_lessons(self):
        """讀取大腦潛意識與專案教訓。"""
        lessons = []
        # 1. 讀取全域潛意識
        sub_file = Path(KB_DIR) / "00_System_Knowledge/01_Operations/04_Subconscious_Memory.md"
        if sub_file.exists():
            try:
                content = sub_file.read_text(encoding="utf-8")
                if "<muse_subconscious>" in content:
                    extracted = content.split("<muse_subconscious>")[1].split("</muse_subconscious>")[0]
                    lessons.append(f"--- Global Subconscious Lessons ---\n{extracted.strip()}")
            except Exception: pass

        # 2. 讀取專案局部教訓
        if self.git_dir:
            local_lessons = Path(self.git_dir).parent / ".codex_lessons.md"
            if local_lessons.exists():
                try:
                    lessons.append(f"--- Project Specific Lessons ---\n{local_lessons.read_text(encoding='utf-8')}")
                except Exception: pass
        
        return "\n\n".join(lessons) if lessons else "No specific lessons found."

    def _record_transcript(self, status, diff, report):
        """紀錄審查碎片供大腦潛意識消化。"""
        transcript = {
            "timestamp": datetime.now().isoformat(),
            "repo": self.git_dir or "global",
            "scope": self.scope,
            "status": status,
            "diff": diff[:5000],  # 截斷以保護 JSONL 大小
            "report": report
        }
        ts_file = self.transcripts_dir / f"loop_{int(time.time())}.jsonl"
        try:
            with open(ts_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(transcript, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ [BRAIN] Warning: Could not record transcript: {e}")

    def _get_git_dir(self):
        try:
            return subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_fail_count(self):
        if os.path.exists(self.count_file):
            try:
                with open(self.count_file, "r") as f:
                    return int(f.read().strip())
            except (ValueError, OSError) as e:
                print(f"⚠️ [BRAIN] Warning: Could not read fail count: {e}")
                return 0
        return 0

    def set_fail_count(self, count):
        try:
            with open(self.count_file, "w") as f:
                f.write(str(count))
        except OSError as e:
            print(f"⚠️ [BRAIN] Warning: Could not write fail count: {e}")

    def _write_fallback_report(self, msg):
        """發生系統性錯誤時，寫入 Fallback 報告，保護 Inner Loop。"""
        try:
            with open(self.report_file, "w") as f:
                f.write(f"# Codex Loop System Error\n\n{msg}\n\n[P1] System Execution Failure.")
        except IOError:
            pass

    def run_review(self):
        fail_count = self.get_fail_count()
        diff_cmd = ["git", "-c", "core.quotepath=false", "diff", "--relative", "--name-only"]
        if self.base_commit == "staged":
            diff_cmd.append("--cached")
        else:
            diff_cmd.append(f"{self.base_commit}...HEAD")
        
        if self.scope:
            diff_cmd.extend(["--", self.scope])
            
        try:
            files = subprocess.check_output(diff_cmd).decode().splitlines()
        except subprocess.CalledProcessError as e:
            err_msg = "❌ git diff error. Not in a git repo?"
            print(err_msg)
            self._write_fallback_report(err_msg)
            return False
            
        code_files = [f for f in files if f.endswith(('.py', '.js', '.ts', '.sh', '.md', '.json'))]
        if not code_files:
            print("✅ [SKIPPED] 無程式碼變更。")
            self.set_fail_count(0)
            return True

        diff_content_cmd = ["git", "diff", "--relative"]
        if self.base_commit == "staged":
            diff_content_cmd.append("--cached")
        else:
            diff_content_cmd.append(f"{self.base_commit}...HEAD")
        if self.scope:
            diff_content_cmd.extend(["--", self.scope])
            
        try:
            diff_text = subprocess.check_output(diff_content_cmd).decode()
        except subprocess.CalledProcessError as e:
            err_msg = "❌ git diff content error."
            print(err_msg)
            self._write_fallback_report(err_msg)
            return False

        lessons = self._get_subconscious_lessons()
        prompt = f"Instruction: Review the code for bugs, logic errors, and anti-patterns. Use the subconscious lessons below as mandatory quality criteria.\n\nLESSONS:\n{lessons}\n\nFILES: {', '.join(code_files)}\n\nDIFF:\n"
        
        print("🔍 正在呼叫 Codex 進行輔助決策 (已注入大腦教訓)...")
        try:
            with open(self.lock_file, "w") as lock_f:
                fcntl.flock(lock_f, fcntl.LOCK_EX)
                res = subprocess.run(["codex", "exec", "-"], input=prompt + diff_text, capture_output=True, text=True, timeout=180)
            report = res.stdout + res.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            err_msg = f"❌ [BRAIN] Codex CLI 執行失敗或超時: {e}"
            print(err_msg)
            self._write_fallback_report(err_msg)
            return False
            
        is_pass = (res.returncode == 0) and ("STATUS: PASS" in res.stdout)
        
        # 經驗紀錄 (Lvl 16 閉環關鍵)
        self._record_transcript("PASS" if is_pass else "FAIL", diff_text, report)
        
        try:
            with open(self.report_file, "w") as f:
                f.write(report)
        except OSError as e:
            print(f"⚠️ [BRAIN] Warning: Could not write report: {e}")
        
        if is_pass:
            print("🎉 [PASSED] 認知閉環驗證通過！")
            self.set_fail_count(0)
            return True
        else:
            new_count = fail_count + 1
            print(f"⚠️ [REJECTED] 偵測到品質缺陷。嘗試次數: {new_count}/3")
            
            if new_count >= 3:
                print("\n" + "!" * 60)
                print("🚨 [FATAL] 已達到最大重試次數 (3次)。")
                print("阻止理由: 持續偵測到代碼品質缺陷，Codex 報告指出硬性缺陷。")
                print("操作建議: 請 Sir 手動檢查 /tmp/codex_loop_report_*.md 並修正 root cause。")
                print("!" * 60 + "\n")
                self.set_fail_count(0)  # 達到上限後歸零，讓 Sir 手動修復後可重新啟動三輪
                sys.exit(1) # 強制中斷
            
            self.set_fail_count(new_count)
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--global", dest="is_global", action="store_true")
    parser.add_argument("--base", default="staged", help="Git base commit")
    args = parser.parse_args()
    brain = CodexLoopBrain(use_global=args.is_global, base_commit=args.base)
    if brain.run_review():
        sys.exit(0)
    else:
        sys.exit(1)
