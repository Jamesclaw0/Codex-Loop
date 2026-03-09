#!/bin/bash
# 🧪 Codex-Loop & Dr.Claw 一鍵安裝腳本
# 目的：自動化環境配置、套件安裝與路徑授權
set -euo pipefail

echo "🚀 正在啟動 Codex-Loop 工業級環境配置..."

# 1. 檢查並安裝 Python 依賴
if command -v uv &> /dev/null; then
    echo "[*] 偵測到 uv，正在安裝必要套件..."
    # 嘗試系統安裝，失敗則回退到一般安裝
    uv pip install --system lancedb requests rich pyyaml python-dateutil || uv pip install lancedb requests rich pyyaml python-dateutil
else
    echo "[*] 正在透過 pip 安裝必要套件..."
    pip install lancedb requests rich pyyaml python-dateutil
fi

# 2. 處理 Git 安全目錄 (防禦 Codex-Loop 報錯)
REPO_ROOT=$(pwd)
echo "⚠️ [SECURITY] 為了讓 Codex-Loop 正常運行，建議將此目錄加入 Git 信任名單。"
echo "如果您在執行 codex-loop 時遇到 'Not inside a trusted directory' 錯誤，請手動執行以下指令："
echo "    git config --global --add safe.directory \"$REPO_ROOT\""


# 3. 配置權限
echo "[*] 配置腳本執行權限..."
chmod +x scripts/codex-loop.sh
chmod +x scripts/core/diagnoser.py
chmod +x scripts/core/knowledge_engine.py
chmod +x install.sh

# 4. 建立軟連結至 bin (可選)
if [ ! -f "/usr/local/bin/codex-diag" ]; then
    echo "[*] 建議：您可以手動建立軟連結以方便呼叫"
    echo "    sudo ln -s $REPO_ROOT/scripts/core/diagnoser.py /usr/local/bin/codex-diag"
fi

echo "✅ 安裝完成！"
echo "💡 現在您可以執行：codex-loop audit <file> 來發動診斷。"
echo "💡 或是直接測試診斷引擎：python3 scripts/core/diagnoser.py --audit 'Findings: **High**...'"
