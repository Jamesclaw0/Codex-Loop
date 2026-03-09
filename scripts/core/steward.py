import os
from pathlib import Path

class MemorySteward:
    """負責將審查教訓結晶為長期記憶。"""

    def __init__(self, project_root):
        self.project_root = Path(project_root) if project_root else None
        self.lessons_file = self.project_root / ".codex_lessons.md" if self.project_root else None

    def crystallize(self, structured_lessons):
        """將結構化診斷 (或 violations) 轉化為 QMD 友善的卡片並寫入。"""
        if not self.lessons_file: return
        
        new_lessons = []
        for v in structured_lessons:
            # 支援舊版 violation 格式與新版 drclaw 格式
            signature = v.get("signature") or v.get("reason", "Unknown Issue")[:50]
            context = v.get("context", "General Execution")
            root_cause = v.get("root_cause", v.get("reason", "N/A"))
            
            # 處理 fix_plan (可能是列表或字串)
            fix_plan_raw = v.get("fix_plan") or v.get("suggestion", "N/A")
            if isinstance(fix_plan_raw, list):
                fix_plan = "\n".join([f"- {step}" for step in fix_plan_raw])
            else:
                fix_plan = f"- {fix_plan_raw}"
            
            files = v.get("related_files", [])
            files_str = f" ({', '.join(files)})" if files else ""

            # 建立 QMD 結構化教訓
            lesson = f"## [{signature}]{files_str}\n"
            lesson += f"### Context\n- {context}\n\n"
            lesson += f"### Root Cause\n{root_cause}\n\n"
            lesson += f"### Fix Steps\n{fix_plan}\n\n"
            new_lessons.append(lesson)

        if not new_lessons: return

        # 讀取現有內容，避免重複
        existing_content = ""
        if self.lessons_file.exists():
            existing_content = self.lessons_file.read_text(encoding="utf-8")

        with open(self.lessons_file, "a", encoding="utf-8") as f:
            if not existing_content:
                f.write("# 🧬 Project Evolution Lessons\n\n")
            
            for l in new_lessons:
                # 基於 signature 檢查重複 (簡單去重)
                sig_line = l.splitlines()[0]
                if sig_line not in existing_content:
                    f.write(f"---\n{l}")
                    print(f"   💎 [Memory] Crystallized structural lesson: {sig_line}")

        return True
