#!/bin/bash
# 🛡️ Codex-Loop 2.0 (Lvl 16 Cognitive Loop)
# 🛡️ SSoT: Relocatable Public Version
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRAIN_SCRIPT="${SCRIPT_DIR}/codex_loop_brain.py"
DIAGNOSER="${SCRIPT_DIR}/core/diagnoser.py"
TEMP_REPORT="/tmp/codex_audit_$(date +%s).md"

# 執行主腦邏輯：
# 1. 保持即時輸出 (stdout/stderr) 到終端機
# 2. 同時將所有輸出捕捉到暫存檔中以便後續診斷
python3 "$BRAIN_SCRIPT" "$@" 2>&1 | tee "$TEMP_REPORT"
EXIT_CODE=${PIPESTATUS[0]}

# [核心進化] 若審查失敗，自動啟動 Dr. Claw 診斷醫師
if [ $EXIT_CODE -ne 0 ] && grep -q "\[FAILED\]" "$TEMP_REPORT"; then
    echo -e "\n\033[1;31m🚨 [Dr. Claw] 偵測到審查失敗，正在發動自動診斷醫師...\033[0m"
    if [ -f "$DIAGNOSER" ]; then
        # 改用暫存檔路徑傳遞報告，徹底避開 ARG_MAX 限制
        python3 "$DIAGNOSER" --audit_file "$TEMP_REPORT"
    fi
fi

# 清理暫存檔
rm "$TEMP_REPORT"

exit $EXIT_CODE
