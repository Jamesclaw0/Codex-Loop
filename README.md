# 🛡️ Codex-Loop: The Autonomous AI Quality Gate

[繁體中文說明](#-繁體中文說明) | [English Version](#-english-version)

---

## 🇹🇼 繁體中文說明

**別再盲目信任 AI Agent，讓它們用實力和邏輯證明程式碼是正確的。**

`codex-loop` 是一款專為 AI 編裝 Agent 設計的「自律品質閘門」工具。它建立了一個強制性的 "Ping-Pong" 反饋循環：Agent 產出的程式碼必須通過嚴格的跨模型審查，否則系統會鎖定任務並強迫 Agent 持續修復，直到綠燈通過為止。

### ✨ 為什麼需要 Codex-Loop？

- **自主修復機制**：不僅是報告錯誤，更強迫 AI 根據審查報告進行自我修正。
- **跨模型審核 (Cross-Model Judge)**：利用模型間的認知差異（如：用 OpenAI Codex 審核 Claude 的產出），消除單一模型的盲點。
- **5 次熔斷 (5-Strike Policy)**：如果 Agent 陷入死循環，工具會自動升級為「終極指導模式」，強制輸出正確解法，確保開發不中斷。
- **零繞過政策**：深度整合 Git 工作流，檔案未獲得 `Codex-Verified` 標誌前禁止送交。

### 🛠️ 安裝與使用

1. **複製專案**：
   ```bash
   git clone https://github.com/your-username/codex-loop.git
   ```
2. **建立連結**：
   ```bash
   ln -s $(pwd)/scripts/codex-loop.sh /usr/local/bin/codex-loop
   ```
3. **開始執行**：
   在任何 Git 專案執行 `codex-loop` 即可啟動審查。

---

## 🇺🇸 English Version

**Stop trusting your AI agents blindly. Make them prove their code works.**

`codex-loop` is an autonomous quality gate designed for AI coding agents. It creates a "Ping-Pong" feedback loop where the agent must fix its own code until it passes a rigorous, cross-model review—or it won't let the task finish.

### ✨ Key Features

- **Autonomous Correction**: Forces the AI to read the review and fix its own bugs.
- **Cross-Model Integrity**: Eliminate model blind spots by using a judging model to verify a coding model.
- **5-Strike Safety**: Escalates to "Final Instruction Mode" if an agent gets stuck, forcing the correct solution output.
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

---
Built by [Sir] & [Muse-Core]
