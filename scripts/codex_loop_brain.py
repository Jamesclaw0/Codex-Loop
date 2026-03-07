#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 導入拆分後的核心模組
from core.git_manager import GitManager
from core.llm_client import LLMClient
from core.linter import Linter
from core.patcher import SafePatcher
from core.reporter import Reporter

# 配置
KB_DIR = os.getenv("MUSE_CORE_KB_DIR", "/Users/jameschen/Downloads/obsidian/知識庫")
PROMPT_TEMPLATE = Path(KB_DIR) / "01_Operations/Templates/developer_prompt_v2.md"

class CodexLoopV2:
    """
    🧬 Codex-Loop v2.0: Modular Intelligence Orchestrator
    符合 Clean Code SRP 原則，將職責委派給專業模組。
    """
    
    def __init__(self, mode="developer", scope="staged", apply_patch=False, base_ref="HEAD"):
        self.mode = mode
        self.scope = scope
        self.apply_patch = apply_patch
        self.base_ref = base_ref
        
        # 1. 初始化 Git 管理員
        self.git = GitManager()
        
        # 2. 初始化 LLM 客戶端 (傳遞鎖定檔路徑)
        self.llm = LLMClient(lock_file=Path(self.git.git_dir) / "codex_loop_v2.lock" if self.git.git_dir else None)
        
        # 3. 初始化其餘組件
        self.linter = Linter()
        self.patcher = SafePatcher(lock_dir=self.git.git_dir or "/tmp")
        self.reporter = Reporter()
        
        # 報告路徑
        self.report_path = Path(self.git.git_dir) / "codex_loop_report.md" if self.git.git_dir else Path("/tmp/codex_loop_report.md")

    def _get_lessons(self):
        """獲取跨專案與全域教訓。"""
        lessons = []
        sub_file = Path(KB_DIR) / "00_System_Knowledge/01_Operations/04_Subconscious_Memory.md"
        if sub_file.exists():
            content = sub_file.read_text(encoding="utf-8")
            if "<muse_subconscious>" in content:
                extracted = content.split("<muse_subconscious>")[1].split("</muse_subconscious>")[0]
                lessons.append(f"--- Global Subconscious ---\n{extracted.strip()}")
        
        local_lessons = Path(self.git.project_root) / ".codex_lessons.md"
        if local_lessons.exists():
            lessons.append(f"--- Project Lessons ---\n{local_lessons.read_text(encoding='utf-8')}")
        
        return "\n\n".join(lessons)

    def run_review(self, manual_files=None):
        print(f"🔍 [v2.0] Mode: {self.mode} | Scope: {self.scope}")
        
        # Step 1: 獲取變更
        if manual_files:
            code_files = [f for f in manual_files if Path(f).is_file()]
            diff_text = ""
            for f in code_files:
                try:
                    lines = Path(f).read_text(encoding="utf-8").splitlines()
                    diff_text += f"\ndiff --git a/{f} b/{f}\nnew file mode 100644\n--- /dev/null\n+++ b/{f}\n@@ -0,0 +1,{len(lines)} @@\n"
                    diff_text += "\n".join([f"+{line}" for line in lines]) + "\n"
                except: pass
        else:
            files, diff_text = self.git.get_changes(self.scope, self.base_ref)
            code_files = [f for f in files if f.endswith(".py")]
        
        if not code_files and not diff_text.strip():
            print("✅ [SKIPPED] No significant changes detected.")
            return True

        # Step 2: 靜態分析
        linter_json = self.linter.scan(code_files)
        
        # Step 3: LLM 深度審查 (注入教訓)
        prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8") if PROMPT_TEMPLATE.exists() else "Review this diff:"
        lessons = self._get_lessons()
        
        full_prompt = f"{prompt}\n\nMANDATORY LESSONS:\n{lessons}\n\nLINTER_HINTS:\n{linter_json}\n"
        
        print("🧠 Calling LLM for Cognitive Review...")
        data, raw_output = self.llm.ask(full_prompt, diff_text)
        
        # Step 4: 結果呈現與報告
        if data.get("status") == "FAIL":
            print(self.reporter.render_ansi_table(data.get("violations", [])))
            self.reporter.write_markdown_report(self.report_path, data)
            
            # Step 5: 自動套用補丁 (若開啟)
            if self.apply_patch:
                self.patcher.apply(data.get("violations", []))
            
            return False
        
        print("🎉 [PASSED] Cognitive security check cleared.")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="Files to review")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--base", default="HEAD")
    args = parser.parse_args()
    
    # 優先級：指定檔案 > all > base > staged
    if args.files:
        scope = "manual"
    elif args.all:
        scope = "all"
    elif args.base != "HEAD":
        scope = "base"
    else:
        scope = "staged"
        
    engine = CodexLoopV2(scope=scope, apply_patch=args.apply, base_ref=args.base)
    # 若為 manual 模式，手動傳入檔案清單 (需調整 engine.run_review)
    sys.exit(0 if engine.run_review(args.files) else 1)
