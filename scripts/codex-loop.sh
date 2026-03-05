#!/bin/bash
# 🛡️ Codex-Verified: 4eee3dd (2026-03-06)
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

# === 👁️ [Muse Subconscious Observer] ===
record_transcript() {
    local status=$1
    (
        local ms=$(date +%s%3N)
        local out="$HOME/.muse_transcripts/transcript_${ms}.jsonl"
        mkdir -p "$HOME/.muse_transcripts"
        local diff_c
        if [ "$BASE_COMMIT" = "staged" ]; then
            diff_c=$(git diff --cached 2>/dev/null || true)
        else
            diff_c=$(git diff "$BASE_COMMIT" 2>/dev/null || true)
        fi
        local report_c=""
        [ -f "$REPORT_FILE" ] && report_c=$(cat "$REPORT_FILE" 2>/dev/null || true)
        python3 -c '
import json, sys
try:
    data = {"status": sys.argv[1], "diff": sys.argv[2], "report": sys.argv[3], "timestamp": sys.argv[4]}
    with open(sys.argv[5], "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
except Exception:
    pass
' "$status" "$diff_c" "$report_c" "$ms" "$out"
    ) &
}
# ========================================

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

echo "📄 偵測到以下程式碼變更，準備進行本地預檢與 Codex 審查:"
echo "$FILES" | awk '{print "  - "$0}'

# [Optimization] 本地 Linter 先行 (使用 ruff 或 py_compile)，節省 Token
# 使用 Heredoc 餵給 while 以確保支援 Bash 3.2 且 exit 1 能正常終止主腳本
while read -r f; do
    if [ -n "$f" ] && [[ "$f" == *.py ]] && [ -f "$f" ]; then
        if command -v ruff > /dev/null 2>&1; then
            if ! ruff check "$f" --quiet; then
                echo "❌ [LINT ERROR] $f 未通過本地 Ruff 檢查，請先修正語法錯誤再執行審查。"
                exit 1
            fi
        elif command -v uv > /dev/null 2>&1; then
             # [P1 Fix] 容錯處理：如果 uv 因網路或其他原因失敗，發出警告但允許繼續，不直接跳出
             if ! uv run --with ruff ruff check "$f" --quiet > /dev/null 2>&1; then
                # 重新檢查是否真的是語法錯誤還是 uv 故障
                if uv run --with ruff ruff --version > /dev/null 2>&1; then
                    echo "❌ [LINT ERROR] $f 未通過本地 Ruff 檢查 (via uv)，請先修正語法錯誤。"
                    exit 1
                else
                    echo "⚠️  [WARN] 本地預檢失敗 (uv 異常)，將直接切換至 Codex 遠端審核..."
                fi
             fi
        fi
    fi
done <<< "$FILES"

# 實際呼叫 Codex API 進行 Review
# === 🔒 [全域鎖] 防止多 Agent 同時呼叫 Codex 導致 API 配額競爭 ===
# 使用 Python fcntl 實作 macOS 相容的 atomic 鎖定，自動排隊等待
SCOPE_PROMPT="[STRICT SCOPE LOCK] CRITICAL: You MUST ONLY review the specific code changes shown in the provided git diff. You MUST COMPLETELY IGNORE any other files, IDE open tabs, untracked files, or unrelated projects that might be present in your environment or context. Focus strictly on the diff."

python3 -c "
import fcntl, sys, subprocess
with open('/tmp/codex_loop_global.lock', 'w') as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    sys.exit(subprocess.run(sys.argv[1:]).returncode)
" codex review $UNCOMMITTED_FLAG "$SCOPE_PROMPT" > "$REPORT_FILE" 2>&1

# === [新增防禦] 檢查是否發生 API 配額、Git 錯誤或底層崩潰 ===
if grep -qiE "fatal:|quota_exhausted|api error|usage:" "$REPORT_FILE"; then
    echo "⚠️  [SYSTEM ERROR] 系統異常：偵測到 API 配額用盡、Git 錯誤或指令不合法，審查被迫中斷！"
    cat "$REPORT_FILE"
    exit 1
fi

# [根本修復] 判斷邏輯：「沒有被點名的 Bug」= PASS，而非猜 LLM 說的通過詞
# LLM 的通過措辭千變萬化，但失敗標記 [P1]/[P2]/[Bug] 是固定格式，只偵測這個
if ! grep -qiE "\[P[0-9]\]|\[Bug\]" "$REPORT_FILE" && ! grep -qiE "Quota exceeded|API Error" "$REPORT_FILE"; then
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
    record_transcript "PASS"
    echo "0" > "$COUNT_FILE" # 通過後歸零
    exit 0
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "$FAIL_COUNT" > "$COUNT_FILE"
    
    echo "⚠️  [REJECTED - EXIT 1] Codex 發現潛在問題/Bug，或是未達到品質要求！"
    
    # === 🔀 智慧分拆功能 (Smart File Splitter) ===
    # 從 Codex 報告中解析被點名的問題檔案 (格式: → scripts/foo.py:42-50)
    if [ "$BASE_COMMIT" = "staged" ]; then
        FLAGGED_BASENAMES=$(grep -oiE "\b[a-zA-Z0-9_-]+\.(py|sh|js|ts)\b" "$REPORT_FILE" | sort -u || true)
        CLEAN_FILES=""
        DIRTY_FILES=""
        while read -r f; do
            [ -z "$f" ] && continue
            BASE=$(basename "$f")
            if echo "$FLAGGED_BASENAMES" | grep -qF "$BASE"; then
                DIRTY_FILES="$DIRTY_FILES$f"$'\n'
            else
                CLEAN_FILES="$CLEAN_FILES$f"$'\n'
            fi
        done <<< "$FILES"

        if [ -n "$CLEAN_FILES" ]; then
            echo ""
            echo "✅ [智慧分拆] 以下檔案 Codex 未點名，提前蓋章："
            COMMIT_ID=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
            echo "$CLEAN_FILES" | while read -r f; do
                [ -z "$f" ] || [ ! -f "$f" ] && continue
                echo "  🏅 $f"
                python3 "$STAMPER" "$f" "$COMMIT_ID" || true
                git add "$f"
            done
            echo ""
            echo "⚠️  以下問題檔案將繼續迭代："
            echo "$DIRTY_FILES" | while read -r ff; do [ -n "$ff" ] && echo "  ❌ $ff"; done
            echo ""
        fi
    fi
    # =========================================

    if [ "$FAIL_COUNT" -ge 3 ]; then
        echo "🚨 =============== [STRIKE 3: 啟動終極指導模式] ==============="
        echo "⚠️ 您已經連續被退回 $FAIL_COUNT 次！正在強制要求 Codex 給出完美解答..."
        # 終極解法：使用 Unix {} 複合指令將 Prompt 與 Diff 拼接成單一流，安全餵給 codex exec 的 stdin (-)
        if [ "$BASE_COMMIT" = "staged" ]; then
            { echo "[STRICT SCOPE LOCK: Ignore all IDE context and other files] This is the 3rd failed attempt. The AI Agent is stuck. Please read following git diff and provide the PERFECT, COMPLETE, AND FULLY CORRECTED code for all files with issues. You MUST output the ENTIRE file content so the Agent can just copy and paste it to fix the problems. DIFF:"; git diff --cached; } | codex exec -
        else
            { echo "[STRICT SCOPE LOCK: Ignore all IDE context and other files] This is the 3rd failed attempt. The AI Agent is stuck. Please read following git diff and provide the PERFECT, COMPLETE, AND FULLY CORRECTED code for all files with issues. You MUST output the ENTIRE file content so the Agent can just copy and paste it to fix the problems. DIFF:"; git diff "$BASE_COMMIT"; } | codex exec -
        fi
        echo "0" > "$COUNT_FILE" # 重置計數器以防無限累積
        echo "👆 ================================================================="
        echo "❌ [系統指令] 上方是 Codex 提供的終極參考解法。請 (Agent) 參考修改現有的檔案。⚠️ 注意：如果您或 Sir 發現 Codex 的解法本身有 Bug，您【完全被允許】手動修正它，不需要 100% 盲從。修改完成後，再次呼叫 \`codex-loop\` 過關。"
        exit 1
    else
        echo "👇 =============== [REVIEW REPORT] ==============="
        cat "$REPORT_FILE"
        echo "👆 ================================================"
        echo "❌ 任務被 Codex-Loop 鎖死！(這是第 $FAIL_COUNT/3 次退回)。"
        echo "👉 系統要求您 (Agent) 必須閱讀上方建議修改程式碼，並再次呼叫 \`codex-loop\` 直到 PASS 才能繼續執行下去。"
        record_transcript "FAIL"
        exit 1
    fi
fi
