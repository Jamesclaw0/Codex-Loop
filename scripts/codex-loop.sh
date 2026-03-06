#!/bin/bash
# 🛡️ Codex-Verified: 0a91537 (2026-03-06)
# 🛡️ Codex-Loop (Lvl 14 Quality Guard: Inclusive Review - Staged + Unstaged + Untracked)
# Muse-Core 的強制跨模型程式碼防護鎖 (內建 5 次熔斷直接給 Code 機制)

echo "🔍 [Codex-Loop] 啟動跨模型程式碼審查..."

# ===== [Orchestrator Integration] =====
TASK_ID=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "default-task")
if command -v task-orchestrator > /dev/null 2>&1; then
    task-orchestrator claim "$TASK_ID" >/dev/null 2>&1 || true
    task-orchestrator start "$TASK_ID" >/dev/null 2>&1 || true
fi
# ======================================

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

# 定義需要被審查的程式碼副檔名 (EERE 格式，支援中文字元與特殊路徑)
CODE_EXT_REGEX="\.(py|js|ts|html|css|sh|cpp|c|go|rs|java)$"

# === 👁️ [Muse Subconscious Observer] ===
record_transcript() {
    local status=$1
    (
        local ms
        ms=$(date +%s%3N)
        local out="$HOME/.muse_transcripts/transcript_${ms}.jsonl"
        mkdir -p "$HOME/.muse_transcripts"
        local diff_c
        if [ "$BASE_COMMIT" = "staged" ]; then
            diff_c=$({ git diff --cached; git diff; } 2>/dev/null || true)
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

# [P7 Fix - Root Cause Fix] 蓋章函式：只對 staged index 中的版本蓋章，完全不動工作目錄
# 流程： git cat-file blob ":$f" 取得 staged 版本 -> 寫臨臨時檔 -> 蓋章 -> hash-object -> update-index
# 這樣即使工作目錄還有 unstaged hunks，也不會被体入 commit
stamp_staged_file() {
    local f="$1" commit_id="$2"
    local _tmp_staged
    _tmp_staged=$(mktemp)
    # 從 index 读取 staged 版本
    if ! git cat-file blob ":$f" > "$_tmp_staged" 2>/dev/null; then
        rm -f "$_tmp_staged"
        return 1
    fi
    # 對臨時檔中的 staged 版本蓋章
    python3 "$STAMPER" "$_tmp_staged" "$commit_id" || true
    # 獲取 staged 的檔案模式
    local _file_mode
    _file_mode=$(git ls-files --stage "$f" | awk '{print $1}')
    # 將蓋章後的臨時檔寫入 git object store
    local _new_blob
    _new_blob=$(git hash-object -w "$_tmp_staged")
    rm -f "$_tmp_staged"
    # 只更新 index，不動工作目錄
    git update-index --cacheinfo "${_file_mode:-100644},${_new_blob},${f}"
}

# [P8 Fix-P2] 統一的 diff 輸出函式，直接輸出至 stdout
print_review_diff() {
    if [ "$BASE_COMMIT" = "staged" ]; then
        # staged + unstaged modified
        { git diff --cached; git diff; }
        # [P6 Fix-P2] untracked 檔案不在任何 diff 輸出中，需額外生成
        if [ -n "$HAS_UNTRACKED" ]; then
            while read -r uf; do
                [ -z "$uf" ] && continue
                git diff --no-index /dev/null "$uf" 2>/dev/null || true
            done <<< "$HAS_UNTRACKED"
        fi
    else
        git diff "$BASE_COMMIT"
    fi
}

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

CONTINUATION=0
if [ "$#" -ge 1 ] && [ "$1" = "--continuation" ]; then
    CONTINUATION=1
    shift
fi

if [ "$#" -ge 1 ] && [ "$1" != "staged" ]; then
    BASE_COMMIT="$1"
    echo "📊 審查範圍：自 $BASE_COMMIT 以來的變更"
    FILES=$(git -c core.quotepath=false diff --name-only "$BASE_COMMIT" | grep -Ei "$CODE_EXT_REGEX" || true)

    if [ -z "$FILES" ]; then
        echo "✅ [SKIPPED] 未偵測到目標程式碼檔案（.py, .js 等）的變更，無痛放行。"
        echo "0" > "$COUNT_FILE"
        exit 0
    fi

    UNCOMMITTED_FLAG="--base $BASE_COMMIT"
else
    echo "📊 審查範圍：已暫存的變更 (Staged changes)"
    STAGED_FILES=$(git -c core.quotepath=false diff --cached --name-only | grep -Ei "$CODE_EXT_REGEX" || true)

    # [P4 Fix] 也把未暫存 (modified) 與未追蹤 (untracked) 的程式碼檔納入審查
    #   ⚠️ 這些檔案只會被「審查」，通過後不會自動 git add（保留用戶控制權）
    HAS_UNSTAGED=$(git -c core.quotepath=false diff --name-only --diff-filter=AM | grep -Ei "$CODE_EXT_REGEX" || true)
    HAS_UNTRACKED=$(git -c core.quotepath=false ls-files --others --exclude-standard | grep -Ei "$CODE_EXT_REGEX" || true)

    if [ -n "$HAS_UNSTAGED" ] || [ -n "$HAS_UNTRACKED" ]; then
        echo "⚠️  [NOTICE] 偵測到尚未暫存的程式碼檔案，將一併納入 Codex 審查（但不會自動 git add）："
        [ -n "$HAS_UNSTAGED" ] && echo "$HAS_UNSTAGED" | awk '{print "  📝 未暫存 (modified): "$0}'
        [ -n "$HAS_UNTRACKED" ] && echo "$HAS_UNTRACKED" | awk '{print "  🆕 未追蹤 (untracked): "$0}'
        echo "  👉 若希望這些檔案進入 commit，請在審查通過後執行 git add。"
        echo ""
    fi

    # 合併 Staged + Unstaged + Untracked 到完整審查清單
    FILES=$(printf "%s\n%s\n%s" "$STAGED_FILES" "$HAS_UNSTAGED" "$HAS_UNTRACKED" | sort -u | grep -Ei "$CODE_EXT_REGEX" || true)

    if [ -z "$FILES" ]; then
        echo "✅ [SKIPPED] 未偵測到目標程式碼檔案（.py, .js 等）的變更，無痛放行。"
        echo "0" > "$COUNT_FILE"
        exit 0
    fi

    BASE_COMMIT="staged"
    UNCOMMITTED_FLAG="--uncommitted"
fi

echo "📄 偵測到以下程式碼變更，準備進行本地預檢與 Codex 審查:"
echo "$FILES" | awk '{print "  - "$0}'

# [Optimization] 本地 Linter 先行 (使用 ruff 或 py_compile)，節省 Token
# 使用 Heredoc 餵給 while 以確保支援 Bash 3.2 且 exit 1 能正常終止主腳本
# [P1 Fix] 智慧處理路徑：優先嘗試原始路徑，若不存在則嘗試去除 git 引號
while read -r f_raw; do
    f="$f_raw"
    if [ ! -f "$f" ]; then
        f=$(echo "$f_raw" | sed 's/^"//;s/"$//')
    fi
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

if [ "$CONTINUATION" -eq 1 ]; then
    # Read state
    STATE_FILE="/tmp/codex-loop-state.json"
    LAST_ACTION=$(grep -o '"last_action": *"[^"]*"' "$STATE_FILE" 2>/dev/null | cut -d'"' -f4 || echo "Unknown action")
    PROMPT="[Continuation Turn] Continue from previous turn. Last completed: $LAST_ACTION. If PERFECT, DO NOT output [P1]/[P2]/[Bug]. Output ONLY issues in [P1]/[Bug] format. DIFF:"
    echo "🔄 執行增量 Prompt (Continuation Turn)..."
    INPUT_FILE="/tmp/codex_loop_input.txt"
    echo "$PROMPT" > "$INPUT_FILE"
    # [P5 Fix-P2] 使用 print_review_diff 函式以正確涵蓋 staged + unstaged + untracked 的 diff
    print_review_diff >> "$INPUT_FILE"
    python3 -c "
import fcntl, sys, subprocess
with open('/tmp/codex_loop_global.lock', 'w') as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    with open('/tmp/codex_loop_input.txt', 'r') as stdin:
        sys.exit(subprocess.run(['codex', 'exec', '-'], stdin=stdin).returncode)
" > "$REPORT_FILE" 2>&1
else
    python3 -c "
import fcntl, sys, subprocess
with open('/tmp/codex_loop_global.lock', 'w') as fh:
    fcntl.flock(fh, fcntl.LOCK_EX)
    sys.exit(subprocess.run(sys.argv[1:]).returncode)
" codex review $UNCOMMITTED_FLAG > "$REPORT_FILE" 2>&1
fi

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

    # [P5 Fix-P2] 蓋章只針對原本已 staged 的檔案，不會誤改 WIP 檔案
    # 如果是非 staged 模式（如 codex-loop <commit>），STAGED_FILES 未定義，改用 FILES
    if [ -n "${STAGED_FILES+x}" ]; then
        STAMP_TARGETS="$STAGED_FILES"
    else
        STAMP_TARGETS="$FILES"
    fi

    echo "$STAMP_TARGETS" | while read -r f_raw; do
        f="$f_raw"
        if [ ! -f "$f" ]; then
            f=$(echo "$f_raw" | sed 's/^"//;s/"$//')
        fi

        if [ -n "$f" ] && [ -f "$f" ]; then
            # [P7 Fix] 蓋章只针對 staged 版本，不修改工作目錄
            if [ "$BASE_COMMIT" = "staged" ] && echo "$STAGED_FILES" | grep -qxF "$f"; then
                stamp_staged_file "$f" "$COMMIT_ID" || true
            else
                # 非 staged 模式下，直接對工作目錄蓋章後 git add
                python3 "$STAMPER" "$f" "$COMMIT_ID" || true
            fi
        fi
    done

    cat "$REPORT_FILE"
    echo "🟢 [SUCCESS] 您現在可以順利結案了！"
    record_transcript "PASS"
    echo "0" > "$COUNT_FILE" # 通過後歸零
    echo "{\"last_action\": \"Codex Loop 通過審查\"}" > /tmp/codex-loop-state.json
    if command -v task-orchestrator >/dev/null 2>&1; then
        task-orchestrator done "$TASK_ID" >/dev/null 2>&1 || true
    fi
    exit 0
else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "$FAIL_COUNT" > "$COUNT_FILE"

    echo "⚠️  [REJECTED - EXIT 1] Codex 發現潛在問題/Bug，或是未達到品質要求！"

    # === 🔀 智慧分拆功能 (Smart File Splitter) ===
    # 如果是 staged 模式，只對「已暫存 (STAGED_FILES)」的檔案進行分拆
    # [P5 Fix-P1] 未暫存/未追蹤的檔案只等待審查，不會被自動 commit
    if [ "$BASE_COMMIT" = "staged" ] && [ -n "$STAGED_FILES" ]; then
        FLAGGED_BASENAMES=$(grep -oiE "\b[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+\b" "$REPORT_FILE" | sort -u || true)
        CLEAN_FILES=""
        DIRTY_FILES=""

        while read -r f; do
            [ -z "$f" ] && continue
            BASE=$(basename "$f")
            if echo "$FLAGGED_BASENAMES" | grep -qF "$BASE"; then
                DIRTY_FILES="${DIRTY_FILES}${f}"$'\n'
            else
                CLEAN_FILES="${CLEAN_FILES}${f}"$'\n'
            fi
        done <<< "$STAGED_FILES"

        if [ -n "$CLEAN_FILES" ]; then
            echo ""
            echo "✅ [智慧分拆] 以下檔案 Codex 未點名，提前蓋章並立即提交："
            COMMIT_ID=$(git rev-parse --short HEAD 2>/dev/null || echo "dev")
            CLEAN_ARRAY=()

            while read -r f; do
                [ -z "$f" ] && continue
                [ ! -f "$f" ] && continue
                echo "  🏅 $f"
                # [P7 Fix] 蓋章只针對 staged 版本，不修改工作目錄
                stamp_staged_file "$f" "$COMMIT_ID" || true
                CLEAN_ARRAY+=("$f")
            done <<< "$CLEAN_FILES"

            # 立即提交乾淨的 staged 檔案，避免下輪審查還是包含它們
            if [ ${#CLEAN_ARRAY[@]} -gt 0 ]; then
                git commit -m "chore: [Codex-Split-PASS] auto-stamp clean files from smart splitter" --no-verify -q -- "${CLEAN_ARRAY[@]}" && \
                    echo "🟢 [智慧分拆] 乾淨檔案已自動提交，下輪審查只需面對問題檔案。"
            fi

            echo ""
            echo "⚠️  以下問題檔案將繼續迭代："
            echo "$DIRTY_FILES" | while read -r ff; do
                [ -n "$ff" ] && echo "  ❌ $ff"
            done
            echo ""
        fi
    fi
    # =========================================

    if [ "$FAIL_COUNT" -ge 3 ]; then
        echo "🚨 =============== [STRIKE 3: 啟動終極指導模式] ==============="
        echo "⚠️ 您已經連續被退回 $FAIL_COUNT 次！正在強制要求 Codex 給出完美解答..."
        # 終極解法：使用 Unix {} 複合指令將 Prompt 與 Diff 拼接成單一流，安全餵給 codex exec 的 stdin (-)
        {
            echo "[STRICT SCOPE LOCK: Ignore all IDE context and other files] This is the 3rd failed attempt. The AI Agent is stuck. Please read following git diff and provide the PERFECT, COMPLETE, AND FULLY CORRECTED code for all files with issues. You MUST output the ENTIRE file content so the Agent can just copy and paste it to fix the problems. DIFF:"
            # [P8 Fix-P2] 使用 print_review_diff 統一取得完整 diff (包含 untracked)
            print_review_diff
        } | codex exec -
        echo "0" > "$COUNT_FILE" # 重置計數器以防無限累積
        echo '👆 ================================================================='
        echo '❌ [系統指令] 上方是 Codex 提供的終極參考解法。請 (Agent) 參考修改現有的檔案。⚠️ 注意：如果您或 Sir 發現 Codex 的解法本身有 Bug，您【完全被允許】手動修正它，不需要 100% 盲從。修改完成後，再次呼叫 `codex-loop` 過關。'
        echo "{\"last_action\": \"Codex Loop 提供終極參考解法，等待 Agent 修正\"}" > /tmp/codex-loop-state.json
        if command -v task-orchestrator >/dev/null 2>&1; then
            task-orchestrator retry "$TASK_ID" >/dev/null 2>&1 || true
        fi
        exit 1
    else
        echo "👇 =============== [REVIEW REPORT] ==============="
        cat "$REPORT_FILE"
        echo "👆 ================================================"
        echo "❌ 任務被 Codex-Loop 鎖死！(這是第 $FAIL_COUNT/3 次退回)。"
        echo "👉 系統要求您 (Agent) 必須閱讀上方建議修改程式碼，並再次呼叫 \`codex-loop\` 直到 PASS 才能繼續執行下去。"
        record_transcript "FAIL"
        echo "{\"last_action\": \"Codex Loop 提出了修改建議，等待 Agent 修正\"}" > /tmp/codex-loop-state.json
        if command -v task-orchestrator >/dev/null 2>&1; then
            task-orchestrator retry "$TASK_ID" >/dev/null 2>&1 || true
        fi
        exit 1
    fi
fi
