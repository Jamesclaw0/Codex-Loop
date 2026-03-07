#!/usr/bin/env python3
import sys
import os
import json
import hashlib
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 配置
BRAIN_SEARCH_BIN = "/Users/jameschen/.openclaw/skills/memory-sync/scripts/brain_search.py"
DRIFT_DETECTOR_BIN = "/Users/jameschen/Downloads/obsidian/知識庫/01_Operations/scripts/drift_detector.py"
UI_TASTE_MD = "/Users/jameschen/Downloads/obsidian/知識庫/00_System_Knowledge/02_Arsenal/Skills_Library/ui_taste.md"
UV_BIN = "/Users/jameschen/.local/bin/uv"

# 導入拆分後的核心模組
from core.git_manager import GitManager
from core.llm_client import LLMClient
from core.linter import Linter
from core.patcher import SafePatcher
from core.reporter import Reporter
from core.workspace_manager import WorkspaceManager

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
    
    def __init__(self, mode="developer", scope="staged", apply_patch=False, base_ref="HEAD", profile=None, isolated=False):
        self.mode = mode
        self.scope = scope
        self.apply_patch = apply_patch
        self.base_ref = base_ref
        self.isolated = isolated
        
        # 0. 套用 Profile 預設 (DX Polish Lvl 16.5)
        if profile == "solo-dev":
            self.mode = "safe-commit"
            self.apply_patch = True
            print("👤 [PROFILE] solo-dev active (Safe-Commit + Auto-Apply + 180s Timeout)")
        
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
        self.workspace_manager = WorkspaceManager(self.git.project_root)
        
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
        
    def _get_lessons(self, query=None):
        """獲取跨專案與全域教訓，並加入動態經驗回查 (Phase 1)。"""
        lessons = []
        
        # 1. 全域潛意識教訓 (靜態)
        sub_file = Path(KB_DIR) / "00_System_Knowledge/01_Operations/04_Subconscious_Memory.md"
        if sub_file.exists():
            content = sub_file.read_text(encoding="utf-8")
            if "<muse_subconscious>" in content:
                extracted = content.split("<muse_subconscious>")[1].split("</muse_subconscious>")[0]
                lessons.append(f"--- Global Subconscious ---\n{extracted.strip()}")
        
        # 2. 專案教訓 (靜態)
        local_lessons = Path(self.git.project_root) / ".codex_lessons.md"
        if local_lessons.exists():
            lessons.append(f"--- Project Lessons ---\n{local_lessons.read_text(encoding='utf-8')}")
            
        # 3. 🛡️ Lvl 18 Dynamic Experience Recall (動態)
        if query and os.path.exists(BRAIN_SEARCH_BIN):
            dynamic = self._get_dynamic_lessons(query)
            if dynamic:
                lessons.append(dynamic)
        
        return "\n\n".join(lessons)

    def _get_dynamic_lessons(self, query):
        """透過 uv run 呼叫 brain_search.py 進行向量檢索 (具備優雅降級)。"""
        try:
            # 擷取 query 前 200 字元避免過長
            short_query = query[:200].replace("\n", " ")
            print(f"🧠 [Recall] Searching dynamic experience for: {short_query[:50]}...")
            
            cmd = [
                UV_BIN, "run", 
                "--with", "lancedb", 
                "--with", "pandas", 
                BRAIN_SEARCH_BIN, short_query
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if res.returncode == 0 and res.stdout.strip():
                return f"--- Dynamic Experience Recall ---\n{res.stdout.strip()}"
        except Exception as e:
            print(f"⚠️ [Recall Warning] Dynamic experience search skipped: {e}")
        return None

    def _get_aesthetic_rules(self, files):
        """讀取 ui_taste.md 並產出美學審核斷言 (Phase 4)。"""
        ui_exts = {".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".vue"}
        if not any(Path(f).suffix in ui_exts for f in files):
            return ""
            
        if os.path.exists(UI_TASTE_MD):
            try:
                content = Path(UI_TASTE_MD).read_text(encoding="utf-8")
                return f"\n🎨 **[AESTHETIC SHIELD] UI Detected! Enforce Premium Taste:**\n{content}\n"
            except Exception: pass
        return ""

    def _check_intent_drift(self):
        """執行意圖漂移攔截 (Phase 5)。"""
        if not os.path.exists(DRIFT_DETECTOR_BIN):
            return True
            
        print("🛡️ [Intent Guard] Checking for philosophical drift...")
        try:
            # 這裡調用外部 drift_detector.py
            # 由於它是一個獨立腳本，我們直接運行它
            res = subprocess.run(["python3", DRIFT_DETECTOR_BIN], capture_output=True, text=True)
            if res.returncode != 0:
                print(f"🚨 [DRIFT DETECTED] {res.stdout.strip()}")
                return False
            print("✅ [Intent Guard] Alignment confirmed.")
            return True
        except Exception as e:
            print(f"⚠️ [Intent Guard Warning] Skip check due to error: {e}")
            return True

    def _export_report(self, data):
        """導出雜湊隔離的報告。"""
        try:
            self.reporter.write_markdown_report(self.report_file, data)
            # 同步全域報告 (供 UI)
            Path("/tmp/codex_loop_report.md").write_text(self.report_file.read_text(), encoding="utf-8")
        except Exception as e:
            print(f"⚠️ [Report Error] {e}")

    def run_review(self, manual_files=None):
        if self.isolated:
            return self._run_isolated_review(manual_files)
        return self._do_review(manual_files)

    def _run_isolated_review(self, manual_files):
        """租借沙盒，執行隔離審核與原子合併。"""
        task_id, branch, sandbox_path = self.workspace_manager.lease()
        if not task_id:
            return False
            
        try:
            # 同步當前變更至沙盒
            self.workspace_manager.sync_staged_to_sandbox(sandbox_path)
            
            # 在沙盒內重新初始化一個暫時的 Engine 執行實體審核
            # 注意：沙盒內引擎必須關閉 --isolated 否則會無限遞迴
            sandbox_engine = CodexLoopV2(
                mode=self.mode, 
                scope="all", # 沙盒內直接全量掃描
                apply_patch=self.apply_patch,
                base_ref="HEAD"
            )
            
            # 🛡️ 切換至沙盒目錄執行
            original_cwd = os.getcwd()
            os.chdir(sandbox_path)
            try:
                passed = sandbox_engine._do_review(manual_files)
            finally:
                os.chdir(original_cwd)
            
            if passed:
                # 審核通過，執行原子收割
                success = self.workspace_manager.harvest(branch, sandbox_path)
                return success
            else:
                print(f"❌ [ISOLATION] Audit failed in sandbox {task_id}. Changes NOT merged.")
                return False
        finally:
            self.workspace_manager.cleanup(task_id, branch)

    def _do_review(self, manual_files=None):
        """核心審核循環邏輯 (從原有 run_review 提煉)。"""
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
                
                # 🛡️ Lvl 18 Phase 2: 在第一次 Strike 前執行肌肉自癒 (Pre-emptive Heal)
                if strike == 1 and code_files:
                    self.linter.heal(code_files)
                    # 重新獲取 diff (因為自癒可能改變了代碼內容)
                    if not manual_files:
                        files, diff_text = self.git.get_changes(self.scope, self.base_ref)
                
                # 🛡️ Lvl 18 Phase 5: 意圖漂移攔截 (Intent Guard) - 僅在 Strike 1 執行
                if strike == 1 and not self.isolated: # 隔離沙盒內不重跑意圖檢查，由外層發起
                    if not self._check_intent_drift():
                        return False
                
                if not code_files and not diff_text.strip():
                    print("✅ [SKIPPED] No significant changes.")
                    return True

                linter_json = self.linter.scan(code_files)
                prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8") if PROMPT_TEMPLATE.exists() else "Review:"
                
                # 🛡️ Lvl 18: 根據變更內容動態獲取教訓
                lessons = self._get_lessons(query=diff_text)
                
                # 🛡️ Lvl 18 Phase 4: 前端品味注入
                aesthetic_hint = self._get_aesthetic_rules(files if not manual_files else manual_files)
                
                # 注入 Persona Hint
                full_prompt = f"{self.persona_hint}\n{aesthetic_hint}\n\n{prompt}\n\nLESSONS:\n{lessons}\n\nLINTER:\n{linter_json}\n"
                
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
    parser.add_argument("--profile", default=None, choices=["solo-dev"], help="Quick-start profile")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--isolated", action="store_true", help="Launch in a leased UUID workspace to prevent Index contention")
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
        
    engine = CodexLoopV2(mode=args.mode, scope=scope, apply_patch=args.apply, base_ref=args.base, profile=args.profile, isolated=args.isolated)
    sys.exit(0 if engine.run_review(args.files) else 1)
