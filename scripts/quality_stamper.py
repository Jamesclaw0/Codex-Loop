#!/usr/bin/env python3
import sys, os, re
from datetime import datetime

def stamp_file(file_path, commit_id):
    if not os.path.exists(file_path): return
    ext = os.path.splitext(file_path)[1].lower()
    
    # [P3 Fix] 擴充支援範圍，確保與 codex-loop 審核的 regex 100% 匹配
    supported_exts = [".md", ".py", ".sh", ".js", ".ts", ".html", ".css", ".cpp", ".c", ".go", ".rs", ".java"]
    if ext not in supported_exts: return
    
    stamp_text = f"Codex-Verified: {commit_id} ({datetime.now().strftime('%Y-%m-%d')})"
    with open(file_path, "r", encoding="utf-8") as f: content = f.read()
    
    if ext == ".md":
        if content.startswith("---"):
            if "codex_verified:" in content:
                content = re.sub(r"codex_verified:.*", f"codex_verified: \"{stamp_text}\"", content)
            else:
                content = content.replace("---", f"---\ncodex_verified: \"{stamp_text}\"", 1)
        else:
            content = f"---\ncodex_verified: \"{stamp_text}\"\n---\n\n" + content
    elif ext == ".html":
        stamp = f"<!-- 🛡️ {stamp_text} -->"
        if stamp not in content:
            content = f"{stamp}\n" + content
    elif ext == ".css" or ext == ".c" or ext == ".cpp":
        stamp = f"/* 🛡️ {stamp_text} */"
        if stamp not in content:
            content = f"{stamp}\n" + content
    else:
        # 處理多種通用註解格式 (# 或 //)
        sym = "#" if ext in [".py", ".sh"] else "//"
        stamp = f"{sym} 🛡️ {stamp_text}"
        lines = content.split("\n")
        new_lines = []
        
        # 處理 Shebang
        start_idx = 0
        if lines and lines[0].startswith("#!"):
            new_lines.append(lines[0])
            start_idx = 1
        
        new_lines.append(stamp)
        
        for i in range(start_idx, len(lines)):
            if "🛡️ Codex-Verified:" in lines[i]:
                continue
            new_lines.append(lines[i])
        content = "\n".join(new_lines)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    stamp_file(sys.argv[1], sys.argv[2])
