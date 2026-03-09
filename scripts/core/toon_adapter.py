import json

class ToonAdapter:
    """
    輕量級 JSON <-> TOON (Token Object Notation) 轉換器。
    目的：去除 JSON 冗餘的引號、括號與逗號，極大化節省 LLM Token。
    """
    
    @staticmethod
    def json_to_toon(data, indent=0):
        """將 Dict/List 遞迴轉化為高壓縮比的 TOON 格式字串"""
        if isinstance(data, dict):
            lines = []
            for k, v in data.items():
                prefix = "  " * indent + str(k) + ":"
                if isinstance(v, (dict, list)) and len(v) > 0:
                    lines.append(prefix)
                    lines.append(ToonAdapter.json_to_toon(v, indent + 1))
                else:
                    lines.append(f"{prefix} {ToonAdapter.json_to_toon(v, 0)}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append("  " * indent + "-")
                    lines.append(ToonAdapter.json_to_toon(item, indent + 1))
                else:
                    lines.append("  " * indent + "- " + str(item))
            return "\n".join(lines)
        else:
            # 處理字串中的換行，保持排版
            val_str = str(data).strip()
            if "\n" in val_str:
                return "|\n" + "\n".join(["  " * (indent + 1) + line for line in val_str.split("\n")])
            return val_str

if __name__ == "__main__":
    # 測試腳本
    sample = {
        "signature": "Test Error",
        "fix_plan": ["Step 1", "Step 2"],
        "context": "Failed during auth\nCheck config"
    }
    print("=== TOON Output ===")
    print(ToonAdapter.json_to_toon(sample))
