# Codex-Loop: The Ultimate AI Quality Gate

## 🛡️ Core Definition
**Codex-Loop** is a "Ping-Pong" enforcement tool designed for AI coding agents. It ensures that no agent can finish a task until their code passes a rigorous, cross-model review.

- **Capabilities**: 
    - Automatically filters for code changes (Python, JS, TS, etc.).
    - Isolates staged changes from dirty workspaces using Git Stash.
    - Truncates and retries reviews until 🟢 `[SUCCESS]`.
    - **3-Strike Mechanism**: If an agent fails 3 times, it triggers a "Final Instruction Mode" to force-output the correct solution, preventing endless "advice" loops.
    - **Repetition Guard**: Detects if the AI is giving the same suggestions and breaks the loop.
- **Trigger**: Run `codex-loop` before any code commit or task completion.

## 📂 Structure
- `scripts/codex-loop.sh`: The main bash controller.
- `scripts/quality_stamper.py`: Injects "Codex-Verified" stamps into passed files.

## ⚙️ Installation
1. Copy `scripts/` to your local bin.
2. Ensure `codex` CLI is installed and configured.
3. Run `codex-loop` to start the cycle.

## 🤖 Multi-Agent Dispatcher Protocol
When orchestrating parallel tasks (e.g. via `*parallel-fix`), you must act as the **Orchestrator** and route subtasks based on complexity:

1. **Routing Logic**:
   - **Codex Agent (High Complexity)**: Algorithms, core architecture refactoring, complex state migrations.
   - **Gemini Agent (Medium/Low Complexity)**: UI/CSS adjustments, basic CRUD, documentation, config files, lightweight scripts.

2. **Headless Execution Commands**:
   - **Dispatch to Codex**:
     `nohup codex exec --full-auto -m <model> -C <Worktree_Path> "Please read .fix_log and fix this project accordingly." >/dev/null 2>&1 &`
   - **Dispatch to Gemini**:
     `nohup gemini --workspace <Worktree_Path> -y "Please read .fix_log and fix this project accordingly, exit immediately when done." >/dev/null 2>&1 &`
   *(Both agents must be run in the background allowing true parallelism.)*

---
%% Built for the Muse-Core level 15 ecosystem %%
