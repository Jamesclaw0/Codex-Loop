# 🧬 Codex-Loop v2.0 Developer Guide

## 🚀 簡介
Codex-Loop v2.0 是一個具備「雙模式認知」的代碼品質防護引擎。它不僅能進行靜態分析，還能透過 AI 進行語義級審查，並提供自動修復 (Patch) 建議。

---

## 🛠️ CLI 參數規範

### 1. 模式切換
- `--developer` (預設): 提供技術性報表、ANSI 表格以及 Patch 建議。
- `--user`: 提供給非技術用戶的白話文摘要，專注於風險解釋。

### 2. 輸出格式
- `--sarif`: 輸出符合 SARIF v2.1.0 標準的 JSON。可用於 VS Code SARIF Viewer 插件，直接在 Problem 面板查看結果。
- `(無)`: 預設輸出美化後的終端表格。

### 3. 自動修復
- `--apply`: **[強大功能]** 自動解析 AI 提供的 Patch 並執行 `git apply --3way --recount`。
    - 支援 `@@` 計數誤差修正。
    - 支援空白符號容錯。

### 4. 掃描範圍
- `--staged` (預設): 僅審查已暫存 (Staged) 的變更。
- `--all`: 審查所有變更，包含 **未追蹤 (Untracked)** 的新檔案。

---

## 🔗 工作流整合

### 與 `parallel_fix.py` 整合
當 `parallel_fix.py` 在並行分支執行時，會自動調用 `Codex-Loop`。如果審核失敗，會導出報告至 `/tmp/codex_loop_report.md`，並觸發 AI 下一輪的自動校正。

---

## 🧪 自癒哲學
Codex-Loop 不僅是警示工具，更是修復工具。我們信奉「診斷即修復」：
1. **發現問題** (Ruff + AI)
2. **解釋原因** (Traditional Chinese)
3. **提供處方** (Unified Diff)
4. **一鍵套用** (`--apply`)

Sir, the loop is closed.
