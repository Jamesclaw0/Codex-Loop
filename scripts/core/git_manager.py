import subprocess
import os
from pathlib import Path

class GitManager:
    """負責 Git 倉儲的操作與變更偵測。"""
    
    def __init__(self, project_root=None):
        self.project_root = project_root or self._get_project_root()
        self.git_dir = self._get_git_dir()

    def _get_project_root(self):
        """獲取 Git 倉庫根目錄 (支援 Worktree)。"""
        try:
            return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError): 
            return os.getcwd()

    def _get_git_dir(self):
        """獲取 Git 內部目錄 (支援絕對路徑，Git 2.13+)。"""
        try:
            return subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_changes(self, scope="staged", base_ref="HEAD"):
        """
        獲取變更檔案列表與 Diff 內容。
        scope: staged, base, all
        """
        try:
            # 1. 檔案過濾與列表獲取
            if scope == "staged":
                files_cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=d"]
                diff_cmd = ["git", "diff", "--cached", "--relative"]
            elif scope == "base":
                files_cmd = ["git", "diff", base_ref, "--name-only", "--diff-filter=d"]
                diff_cmd = ["git", "diff", base_ref, "--relative"]
            else: # all (追蹤中變動 + 未追蹤)
                files_cmd = ["git", "ls-files", "--modified", "--others", "--exclude-standard"]
                # 'all' 模式的 diff 需要手動處理未追蹤檔案
                diff_text = subprocess.check_output(["git", "diff", "HEAD", "--relative"]).decode()
                untracked_files = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"]).decode().splitlines()
                for uf in untracked_files:
                    if uf.endswith(".py") and Path(uf).is_file():
                        try:
                            lines = Path(uf).read_text(encoding="utf-8").splitlines()
                            header = f"\ndiff --git a/{uf} b/{uf}\nnew file mode 100644\n--- /dev/null\n+++ b/{uf}\n@@ -0,0 +1,{len(lines)} @@\n"
                            diff_text += header + "\n".join([f"+{line}" for line in lines]) + ("\n" if lines else "")
                        except: pass
                
                all_files = subprocess.check_output(files_cmd).decode().splitlines()
                code_files = [f for f in all_files if Path(f).is_file()]
                return code_files, diff_text

            files = subprocess.check_output(files_cmd).decode().splitlines()
            diff_text = subprocess.check_output(diff_cmd).decode()
            return files, diff_text
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git Error: {e}")
            return [], ""
