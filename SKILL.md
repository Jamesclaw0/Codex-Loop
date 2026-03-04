# Codex-Loop: The Ultimate AI Quality Gate

## 🛡️ Core Definition
**Codex-Loop** is a "Ping-Pong" enforcement tool designed for AI coding agents. It ensures that no agent can finish a task until their code passes a rigorous, cross-model review.

- **Capabilities**: 
    - Automatically filters for code changes (Python, JS, TS, etc.).
    - Isolates staged changes from dirty workspaces using Git Stash.
    - Truncates and retries reviews until 🟢 `[SUCCESS]`.
    - **5-Strike Mechanism**: If an agent fails 5 times, it triggers a "Final Instruction Mode" to force-output the correct solution.
- **Trigger**: Run `codex-loop` before any code commit or task completion.

## 📂 Structure
- `scripts/codex-loop.sh`: The main bash controller.
- `scripts/quality_stamper.py`: Injects "Codex-Verified" stamps into passed files.

## ⚙️ Installation
1. Copy `scripts/` to your local bin.
2. Ensure `codex` CLI is installed and configured.
3. Run `codex-loop` to start the cycle.

---
%% Built for the Muse-Core level 15 ecosystem %%
