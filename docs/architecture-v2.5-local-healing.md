# 🛡️ Codex-Loop v2.5 架構 RFC: 本地自癒閉環與 Dr. Claw 整合
**Status**: Implemented | **Date**: 2026-03-09

## 💡 TL;DR
- **本地診斷核心 (`diagnoser.py`)**：完全去除對 Dr. Claw 外部伺服器與公有 RAG 的依賴，保障代碼 100% 隱私。
- **雙引擎 Layer 1**：改掛 QMD + LanceDB，對於常見錯誤可實現 0 成本、秒級命中。
- **無人值守自癒**：Codex-Loop 審核失敗自動觸發診斷，實現 `Audit -> [FAILED] -> Diagnose` 的全自動管線。
- **統一輸出與 TOON 壓縮**：診斷輸出統一為 JSON + TOON 介面層，同時優化 QMD 的 Chunking 精準度與 LLM 傳遞的 Token 成本。

---

## 🧩 1. 架構演化：Local Diagnoser vs 原版 Dr. Claw
我們汲取了 [Dr. Claw](https://github.com/sstklen/drclaw) 的「三層瀑布流」與「望聞問切」神髓，但進行了徹底的本地化改造：
- **原版 Dr. Claw**：HTTP API + 雲端 Qdrant + 外部 LLM（Voyage/Claude）。
- **本版 Local Diagnoser**：直接攔截 Codex-Loop 的 audit log。Layer 1 走本地 QMD/LanceDB；Layer 2 走本地配置的 LLM Profile。

### 自癒管線流程圖 (Pipeline Pseudo-flow)
`codex-loop 審查` ➔ 偵測到 `[FAILED]` ➔ 啟動 `diagnoser.py` ➔ **(Layer 1 QMD/LanceDB ➔ Layer 2 LLM)** ➔ 產生 `TOON/JSON 處方` ➔ 交由 `steward.py` 寫入 `.codex_lessons.md` ➔ 下一次錯誤時於 Layer 1 零成本命中。

---

## 🧠 2. 雙引擎本地 RAG 掛載 (Layer 1)
- **實作規則**：當 QMD 或 LanceDB 檢索出的歷史教訓，其相似度/信心分數 **≥ 0.85**，診斷引擎將直接採用 Layer 1 建議並回傳，**終止後續昂貴的 LLM 呼叫**。否則，才進入 Layer 2 的 LLM 深度解析。
- **戰略意義**：這是一套純本地的 RAG 防線。只要是本專案踩過的坑，系統能在 1 秒內給出解答。

---

## 🗂️ 3. 結構化教訓卡片 (QMD-Optimized Chunking)
為了讓 QMD 在檢索時能精準切塊 (Chunking)，我們將 `MemorySteward` 寫入 `.codex_lessons.md` 的格式嚴格限制為「四段式 Markdown 卡片」。

**標準卡片範例 (Standard Template)：**
```markdown
## [FastAPI CORS misconfigured on /auth] (auth.py, main.py)

### Context
- Python 3.12, FastAPI middleware order
- Local dev environment

### Root Cause
Browser preflight OPTIONS request not allowed; CORS middleware was added after the router was mounted.

### Fix Steps
- 1. Move CORSMiddleware before app.include_router()
- 2. Add OPTIONS to allow_methods
```
**效益**：QMD 會以 `##` 作為 Chunk 邊界，避免多個 Bug 混在一起，讓語義搜尋從「大海撈針」變成「精準狙擊」。

---

## ⚡ 4. TOON 介面層 (Token-Economic Serializer)
- **設計**：在 Agent 之間傳遞診斷結果時，提供 `--format toon` 選項。
- **效益評估**：以單一診斷卡片約 1–2k 字元測試，JSON vs TOON 格式在主流模型上實測，預計可節省約 **20%~30% 的輸入 Token**。這在長期運行的 Multi-Agent Loop 中是極具經濟效益的防護。

---

## 🛡️ 5. 工業級防護加固 (Industrial Hardening)
- **原子化存檔 (Atomic Write)**：使用 `.tmp` + `os.replace` 確保 Session 狀態檔絕不因斷電損毀。
- **自動掛鉤 (Auto-Hooking)**：透過暫存檔 `/tmp/codex_audit.md` 傳遞日誌，完美避開 Bash `ARG_MAX` 指令長度限制。
- **類型安全**：全面實裝 `_safe_json_get` 防禦髒資料崩潰，外部 API 強制 `timeout=10`。
