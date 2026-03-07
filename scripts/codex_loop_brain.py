#!/usr/bin/env python3
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 導入拆分後的核心模組
from core.git_manager import GitManager
from core.llm_client import LLMClient
from core.linter import Linter
from core.patcher import SafePatcher
from core.reporter import Reporter

# 配置
# 優先使用環境變數，否則自動判斷 Repo 根目錄 (scripts/.. 為 repo root)
REPO_ROOT = Path(__file__).resolve().parents[1]
KB_DIR = os.getenv("MUSE_CORE_KB_DIR", str(REPO_ROOT))

# 優先尋找 Repo 內的模板，其次尋找 KB 目錄下的模板
PROMPT_TEMPLATE = REPO_ROOT / "scripts/Templates/developer_prompt_v2.md"
if not PROMPT_TEMPLATE.exists():
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
        
        # 🔗 基於絕對路徑的雜湊防衝突 (P16 Lesson 118: Use absolute-git-dir)
        repo_path = str(self.git.git_dir).encode("utf-8")
        repo_id = hashlib.md5(repo_path).hexdigest()[:8]
        
        # 2. 初始化組件 (使用隔離路徑)
        self.llm = LLMClient(lock_file=Path(f"/tmp/codex_loop_{repo_id}.lock"))
        self.linter = Linter()
        self.patcher = SafePatcher(lock_dir=self.git.git_dir or "/tmp")
        self.reporter = Reporter()
        
        # 🔗 重複偵測器 (Repetition Guard)
        self.history_hashes = set()
        
        # 3. 根據 Persona Profile 進行配置調整
        self._apply_persona_profile(mode)
        
        # 報告與補丁路徑 (符合 P16 Sandbox 定義)
        self.report_file = Path(f"/tmp/codex_loop_report_{repo_id}.md")
        self.patch_file = Path(f"/tmp/codex_auto_{repo_id}.patch")
        self.transcripts_dir = Path(f"/tmp/codex_transcripts_{repo_id}")
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def _apply_persona_profile(self, mode):
        """實作 README 中承諾的三種進階玩家模式。"""
        if mode == "safe-commit":
            # 本機平安模式：標準審查，不強迫自癒，除非指定
            self.max_strikes = 2
            self.persona_hint = "👤 MODE: SAFE-COMMIT (Maintain focus on stability and clean commit hygiene)."
        elif mode == "agent-shield":
            # 多 Agent 保護框：高次數限制，強勢自癒，防止 Agent 擺爛
            self.max_strikes = 3
            self.apply_patch = True
            self.persona_hint = "👤 MODE: AGENT-SHIELD (Enforce strict self-healing to prevent agent regressions)."
        elif mode == "audit":
            # 執政大審：單次深度審核，不進行自癒循環，產出高質量報告
            self.max_strikes = 1
            self.persona_hint = "👤 MODE: FINAL-AUDIT (Generate high-fidelity architectural oversight report)."
        else:
            # 預設模式 (Developer)
            self.max_strikes = 3
            self.persona_hint = "👤 MODE: DEVELOPER (Balanced cognitive-loop audit)."
        
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

    def _export_report(self, data):
        """導出雜湊隔離的報告。"""
        try:
            self.reporter.write_markdown_report(self.report_file, data)
            # 同步全域報告 (供 UI)
            Path("/tmp/codex_loop_report.md").write_text(self.report_file.read_text(), encoding="utf-8")
        except: pass

    def run_review(self, manual_files=None):
        print(f"🔍 [v2.0] Mode: {self.mode} | Scope: {self.scope}")
        
        # 🛡️ 修復子目錄執行問題：切換至專案根目錄
        original_cwd = os.getcwd()
        os.chdir(self.git.project_root)
        
        strike = 0
        try:
            while strike < self.max_strikes:
                strike += 1
                print(f"🚀 [Round {strike}/{self.max_strikes}] Initiating Audit...")
                
                if manual_files:
                    code_files = [str(Path(f).absolute()) for f in manual_files if Path(f).is_file()]
                    diff_text = "Manual Review Mode"
                else:
                    files, diff_text = self.git.get_changes(self.scope, self.base_ref)
                    code_files = [f for f in files if f.endswith(".py")]
                
                if not code_files and not diff_text.strip():
                    print("✅ [SKIPPED] No significant changes.")
                    return True

                linter_json = self.linter.scan(code_files)
                prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8") if PROMPT_TEMPLATE.exists() else "Review:"
                lessons = self._get_lessons()
                
                # 注入 Persona Hint
                full_prompt = f"{self.persona_hint}\n\n{prompt}\n\nLESSONS:\n{lessons}\n\nLINTER:\n{linter_json}\n"
                
                # 🛡️ Final Strike 模式：強制要求解決方案 (P16 Request: 3次沒過就要提供正確的code)
                if strike == self.max_strikes and self.max_strikes > 1:
                    full_prompt += "\n⚠️ [CRITICAL] FINAL STRIKE: This is your last chance. You MUST provide a definitive, compile-ready patch (Unified Diff) for all remaining violations. No more advice. Fix everything NOW.\n"
                
                print(f"🧠 Calling LLM for Cognitive Review (Strike {strike})...")
                data, raw_output = self.llm.ask(full_prompt, diff_text)
                
                # 📜 存檔原始轉錄 (協助後續自省)
                ts_file = self.transcripts_dir / f"round_{strike}_{datetime.now().strftime('%H%M%S')}.log"
                ts_file.write_text(raw_output, encoding="utf-8")
                
                # 🛡️ Repetition Guard (偵測是否原地打轉)
                # 雜湊 violations 內容比雜湊原始輸出更能偵測「換句話說但建議相同」的情況
                suggestions_hash = hashlib.md5(json.dumps(data.get("violations", []), sort_keys=True).encode()).hexdigest()
                if suggestions_hash in self.history_hashes:
                    print(f"⚠️ [STUCK] Detected repeated suggestions at Strike {strike}. Breaking to prevent dead-loop.")
                    self._export_report(data)
                    return False
                self.history_hashes.add(suggestions_hash)
                
                if data.get("status") == "FAIL":
                    print(self.reporter.render_ansi_table(data.get("violations", [])))
                    self._export_report(data)
                    
                    if self.apply_patch:
                        print("🛠️ Applying auto-patches...")
                        self.patcher.apply(data.get("violations", []))
                        # 繼續下一輪循環
                        continue
                    else:
                        return False
                
                print("🎉 [PASSED] Cognitive security check cleared.")
                return True
            
            print("🎉 [PASSED] Cognitive security check cleared.")
            return True
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="Files to review")
    parser.add_argument("--mode", default="developer", choices=["developer", "safe-commit", "agent-shield", "audit"], help="Persona mode")
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
        
    engine = CodexLoopV2(mode=args.mode, scope=scope, apply_patch=args.apply, base_ref=args.base)
    sys.exit(0 if engine.run_review(args.files) else 1)
