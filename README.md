# 🛡️ Codex-Loop: The Autonomous AI Quality Gate

[繁體中文說明](#-繁體中文說明) | [English Version](#-english-version)

---

## 🇹🇼 繁體中文說明

**別再盲目信任 AI Agent，讓它們用實力和邏輯證明程式碼是正確的。**

`codex-loop` 是一款專為 AI 編裝 Agent 設計的「自律品質閘門」工具。它建立了一個強制性的 "Ping-Pong" 反饋循環：Agent 產出的程式碼必須通過嚴格的跨模型審查，否則系統會鎖定任務並強迫 Agent 持續修復，直到綠燈通過為止。

### ✨ 為什麼需要 Codex-Loop？

- **自主修復機制**：不僅是報告錯誤，更強迫 AI 根據審查報告進行自我修正。
- **跨模型審核 (Cross-Model Judge)**：利用模型間的認知差異（如：用 OpenAI Codex 審核 Claude 的產出），消除單一模型的盲點。
- **3 次熔斷 (3-Strike Policy)**：如果 Agent 陷入死循環，工具會自動升級為「終極指導模式」，強制輸出正確解法，確保開發不中斷且節省 Token。
- **本地 Linter 支援 (Local Linter)**：內建 Python `ruff` 與 `py_compile` 語法預檢，在呼叫昂貴 LLM 前先過濾基礎錯誤。
- **零繞過政策**：深度整合 Git 工作流，檔案未獲得 `Codex-Verified` 標誌前禁止送交。

### 🛠️ 安裝與使用

1. **複製專案**：
   ```bash
   git clone https://github.com/Jamesclaw0/Codex-Loop.git
   ```
2. **建立連結**：
   ```bash
   ln -s $(pwd)/scripts/codex-loop.sh /usr/local/bin/codex-loop
   ```
3. **開始執行**：
   在任何 Git 專案執行 `codex-loop` 即可啟動審查。

### 🤖 如何讓 AI Agent 自動使用 Codex-Loop？

AI 代理（如 Devin、OpenClaw 或 Gemini）**不會**在寫完程式碼後主動執行 `codex-loop`。

為打造堅不可摧的自動化品質流水線，請將以下嚴格指令加入您 Agent 的 **System Prompt (系統提示詞)** 或 **Global Memory (全域記憶)** 中：

```markdown
## 🛡️ 程式碼送審鐵律 (Code Ping-Pong Protocol) - 強制執行
- **[強制流程]**: 每次修改完任何程式碼檔案，準備告知完成前，Agent 必須「自動」安排一組 Tool Call 執行：
  1. 執行 `git add <修改的檔案>`
  2. 執行全域指令 `codex-loop` (或您的絕對路徑)
- **[退回處理]**: 如果 codex-loop 輸出為 Exit 1 甚至出現錯誤，Agent **絕對不准**向使用者報告任務完成！必須自行閱讀終端機中的評估建議，修改程式碼後，再重複這兩步送審，直到獲得 PASS。
```

---

## 🇺🇸 English Version

**Stop trusting your AI agents blindly. Make them prove their code works.**

`codex-loop` is an autonomous quality gate designed for AI coding agents. It creates a "Ping-Pong" feedback loop where the agent must fix its own code until it passes a rigorous, cross-model review—or it won't let the task finish.

### ✨ Key Features

- **Autonomous Correction**: Forces the AI to read the review and fix its own bugs.
- **Cross-Model Integrity**: Eliminate model blind spots by using a judging model to verify a coding model.
- **3-Strike Safety**: Escalates to "Final Instruction Mode" if an agent gets stuck, forcing the correct solution output.
- **Local Linter Precheck**: Validates Python syntax via `ruff` or `py_compile` locally, catching basic errors before expensive LLM calls.
- **Verification Stamping**: Automatically injects `Codex-Verified` stamps into files that pass the gate.

### 🛠️ Installation & Usage

1. **Clone it**:
   ```bash
   git clone https://github.com/your-username/codex-loop.git
   ```
2. **Setup CLI**:
   ```bash
   ln -s $(pwd)/scripts/codex-loop.sh /usr/local/bin/codex-loop
   ```
3. **Run**:
   Execute `codex-loop` in your repository before any commit or task completion.

### 🤖 How to Make AI Agents Use Codex-Loop Automatically

AI agents (like Devin, OpenClaw, or Gemini) will **NOT** automatically run `codex-loop` after coding unless you explicitly instruct them to. 

To create a virtually unbreakable code quality pipeline, add this strict instruction to your agent's **System Prompt** or **Global Memory / Instructions**:

```markdown
## 🛡️ Code Ping-Pong Protocol (Mandatory)
- **[Mandatory Flow]**: Every time you modify ANY code file and are about to announce task completion, you MUST "automatically" execute these Tool Calls:
  1. `git add <modified_files>`
  2. Run the global command `codex-loop`
- **[Rejection Handling]**: If codex-loop outputs `Exit 1` or any error, you are **STRICTLY FORBIDDEN** from reporting task completion to the user! You MUST read the evaluation report in the terminal, modify the code yourself, and repeat these two steps to submit for review again until you get `PASS (Exit 0)`.
```

---
Built by [Sir] & [Muse-Core]
