import json
from pathlib import Path

class Reporter:
    """負責結果的呈現與持久化報告。"""

    @staticmethod
    def render_ansi_table(violations):
        """繪製終端視覺表格。"""
        if not violations: return ""
        
        header = f"\n{'-'*100}\n| {'TYPE':<12} | {'FILE:LINE':<25} | {'REASON & SUGGESTION':<53} |\n{'-'*100}"
        rows = []
        for v in violations:
            loc = f"{v.get('file')}:{v.get('line', 1)}"
            reason = f"{v.get('reason')}\nSuggestion: {v.get('suggestion')}"
            # 簡單的自動換行處理
            rows.append(f"| {v.get('type', 'INFO'):<12} | {loc:<25} | {v.get('reason')[:51]:<53} |")
            rows.append(f"| {'':<12} | {'':<25} | Suggestion: {v.get('suggestion')[:39]:<53} |")
            rows.append("-" * 100)
        
        return header + "\n" + "\n".join(rows)

    @staticmethod
    def write_markdown_report(report_path, data):
        """寫入精準的 Markdown 結晶報告。"""
        violations = data.get("violations", [])
        lines = [
            f"# Codex-Loop Audit Report\n",
            f"**Status**: {data.get('status', 'N/A')}",
            f"**Summary**: {data.get('summary', 'No summary provided.')}\n",
            "## Violations\n"
        ]
        
        for v in violations:
            lines.append(f"### [{v.get('type', 'INFO')}] {v.get('file')}:{v.get('line', 1)}")
            lines.append(f"- **Reason**: {v.get('reason')}")
            lines.append(f"- **Suggestion**: {v.get('suggestion')}\n")
            if v.get("patch"):
                lines.append("```diff\n" + v.get("patch") + "\n```\n")
        
        Path(report_path).write_text("\n".join(lines), encoding="utf-8")
