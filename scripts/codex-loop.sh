#!/bin/bash
# 🛡️ Codex-Loop (Lvl 13 Quality Guard: Ping-Pong Loop for Code)
# Muse-Core 的強制跨模型程式碼防護鎖 (內建 5 次熔斷直接給 Code 機制)

echo "🔍 [Codex-Loop] 啟動跨模型程式碼審查..."

# ===== [新增] Git 環境與路徑檢查 =====
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ [ERROR] Codex-Loop 執行失敗：當前目錄不屬於任何 Git 儲存庫，無法執行版本比對。"
    exit 1
fi
# ===================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="/tmp/codex_loop_report.md"
STAMPER="$SCRIPT_DIR/quality_stamper.py"
# [P2 Fix] 將計數器隔離在各專案的 .git 目錄中
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
COUNT_FILE="$GIT_DIR/codex_loop_count.txt"

# 讀取當前失敗次數
if [ ! -f "$COUNT_FILE" ]; then
    echo "0" > "$COUNT_FILE"
fi
FAIL_COUNT=$(cat "$COUNT_FILE")

# 定義需要被審查的程式碼副檔名
CODE_EXT_REGEX="\.\(py\|js\|ts\|html\|css\|sh\|cpp\|c\|go\|rs\|java\)$"

STASHED=0

cleanup() {
    if [ "$STASHED" -eq 1 ]; then
        echo "🛡️  [Codex-Loop] 恢復尚未暫存的髒檔案..."
        if ! git stash pop -q; then
            echo "❌ [ERROR] Codex-Loop: Git 恢復 Stash 失敗（可能有衝突）！您的變更仍保留在 Git Stash 中。"
            # 不要 exit 1 否則會觸發無限循環，但要發出明確警告
        fi
    fi
}
trap cleanup EXIT

if [ "$#" -ge 1 ]; then
    BASE_COMMIT="$1"
    echo "📊 審查範圍：自 $BASE_COMMIT 以來的變更"
    FILES=$(git diff --name-only "$BASE_COMMIT" | grep -i "$CODE_EXT_REGEX" || true)

    if [ -z "$FILES" ]; then
        echo "✅ [SKIPPED] 未偵測到目標程式碼檔案（.py, .js 等）的變更，無痛放行。"
        echo "0" > "$COUNT_FILE"
        exit 0
    fi
    
    UNCOMMITTED_FLAG="--base $BASE_COMMIT"
    DIFF_CMD="git diff $BASE_COMMIT"
else
    echo "📊 審查範圍：已暫存的變更 (Staged changes)"
    FILES=$(git diff --cached --name-only | grep -i "$CODE_EXT_REGEX" || true)

    if [ -z "$FILES" ]; then
        echo "✅ [SKIPPED] 未偵測到目標程式碼檔案（.py, .js 等）的變更，無痛放行。"
        echo "0" > "$COUNT_FILE"
        exit 0
    fi
    
    # [防禦機制] 隔離未暫存的變更，避免干擾 Codex 掃描
    HAS_UNSTAGED=$(git diff --name-only)
    HAS_UNTRACKED=$(git ls-files --others --exclude-standard)
    if [ ! -z "$HAS_UNSTAGED" ] || [ ! -z "$HAS_UNTRACKED" ]; then
        echo "🔒 工作區存在未暫存或未追蹤檔案，暫時收入 Stash (keep-index) 以隔離審查..."
        if git stash push -u --keep-index -m "codex-loop-isolation" -q; then
            STASHED=1
        fi
    fi
    
    BASE_COMMIT="staged"
    UNCOMMITTED_FLAG="--uncommitted"
    DIFF_CMD="git diff --cached"
fi

echo "📄 偵測到以下程式碼變更，準備發送給 Codex:"
echo "$FILES" | awk '{print "  - "$0}'

# 實際呼叫 Codex API 進行 Review
codex review $UNCOMMITTED_FLAG > "$REPORT_FILE" 2>&1

# === [新增防禦] 檢查是否發生 API 配額、Git 錯誤或底層崩潰 ===
if grep -qiE "fatal:|quota_exhausted|api error|usage:" "$REPORT_FILE"; then
    echo "⚠️  [SYSTEM ERROR] 系統異常：偵測到 API 配額用盡、Git 錯誤或指令不合法，審查被迫中斷！"
    cat "$REPORT_FILE"
    exit 1
fi

# [P1 Fix] 檢查審查結果 (必須明確含有 VERDICT: PASS 且不含有任何 [P0-9] 或 [Bug] 標記)
if grep -qi "VERDICT: PASS" "$REPORT_FILE" && ! grep -qiE "\[P[0-9]\]|\[Bug\]" "$REPORT_FILE"; then
    echo "🎉 [PASSED] Codex 審查通過！準備蓋章..."
    
    COMMIT_ID=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
    
    # [P3 Fix] 使用 while read 確保含有空格的檔名不會被切斷
    echo "$FILES" | while read -r f; do
        if [ -n "$f" ] && [ -f "$f" ]; then
            python3 "$STAMPER" "$f" "$COMMIT_ID" || true
            # [P2 Fix] 如果是暫存模式，標註後必須重新 add 以確保標記進入 commit
            if [ "$BASE_COMMIT" = "staged" ]; then
                git add "$f"
            fi
        fi
    done
    cat "$REPORT_FILE"
    echo "🟢 [SUCCESS] 您現在可以順利結案了！"
    echo "0" > "$COUNT_FILE" # 通過後歸零
    exit 0
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "$FAIL_COUNT" > "$COUNT_FILE"
    
    echo "⚠️  [REJECTED - EXIT 1] Codex 發現潛在問題/Bug，或是未達到品質要求！"
    
    if [ "$FAIL_COUNT" -ge 5 ]; then
        echo "🚨 =============== [STRIKE 5: 啟動終極指導模式] ==============="
        echo "⚠️ 您已經連續被退回 $FAIL_COUNT 次！正在強制要求 Codex 給出完美解答..."
        # 終極解法：使用 Unix {} 複合指令將 Prompt 與 Diff 拼接成單一流，安全餵給 codex exec 的 stdin (-)
        if [ "$BASE_COMMIT" = "staged" ]; then
            { echo "This is the 5th failed attempt. The AI Agent is stuck. Please read following git diff and provide the PERFECT, COMPLETE, AND FULLY CORRECTED code for all files with issues. You MUST output the ENTIRE file content so the Agent can just copy and paste it to fix the problems. DIFF:"; git diff --cached; } | codex exec -
        else
            { echo "This is the 5th failed attempt. The AI Agent is stuck. Please read following git diff and provide the PERFECT, COMPLETE, AND FULLY CORRECTED code for all files with issues. You MUST output the ENTIRE file content so the Agent can just copy and paste it to fix the problems. DIFF:"; git diff "$BASE_COMMIT"; } | codex exec -
        fi
        echo "0" > "$COUNT_FILE" # 重置計數器以防無限累積
        echo "👆 ================================================================="
        echo "❌ [系統指令] 上方是 Codex 強制吐出的終極解法，請 (Agent) 直接照抄並覆蓋現有檔案，然後再次呼叫 \`codex-loop\` 過關。"
        exit 1
    else
        echo "👇 =============== [REVIEW REPORT] ==============="
        cat "$REPORT_FILE"
        echo "👆 ================================================"
        echo "❌ 任務被 Codex-Loop 鎖死！(這是第 $FAIL_COUNT/5 次退回)。"
        echo "👉 系統要求您 (Agent) 必須閱讀上方建議修改程式碼，並再次呼叫 \`codex-loop\` 直到 PASS 才能繼續執行下去。"
        exit 1
    fi
fi
