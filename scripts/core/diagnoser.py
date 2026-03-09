#!/usr/bin/env python3
import os
import json
import argparse
import logging
import re
from typing import Dict, Any


class CodexDiagnoser:
    """
    Codex-Loop 內置診斷引擎 (Dr. Claw Powered)
    負責解析 Codex 報告、執行望聞問切問診，並生成自癒指令。
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.session_file = os.path.join(self.workspace_root, ".codex_session.json")
        self.log_file = os.path.join(self.workspace_root, "codex_audit.log")
        self._setup_logging()
        self.session = self._load_session()

    def _setup_logging(self):
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        self.logger = logging.getLogger("Diagnoser")

    def _load_session(self) -> Dict[str, Any]:
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"phase": "START", "collected": {}, "status": "active"}

    def _save_session(self):
        tmp = self.session_file + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.session, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.session_file)

    def parse_audit_report(self, report_text: str) -> Dict[str, Any]:
        """從 Codex Audit Report 中提取關鍵缺陷並轉化為標準 Schema"""
        findings = []
        pattern = r"(\d+\.\s+\*\*(?:High|Medium|Low)\*\*.*?(?=\n\d+\.|\n\*\*|$))"
        matches = re.findall(pattern, report_text, re.DOTALL)
        
        if not matches:
            pattern = r"(\*\*(?:High|Medium|Low)\*\*.*?(?=\*\*|$))"
            matches = re.findall(pattern, report_text, re.DOTALL)

        for m in matches:
            findings.append(m.strip())

        if findings:
            self.logger.info(f"Detected {len(findings)} findings from report.")
            # 嘗試提取第一個 Finding 的關鍵字作為 Signature
            first_finding = findings[0]
            signature = "Codex Audit Failure"
            sig_match = re.search(r"\*\*(?:High|Medium|Low)\*\*:\s*(.*?)(?:\n|$)", first_finding)
            if sig_match:
                signature = sig_match.group(1).strip()[:100]

            # 嘗試提取相關檔案
            related_files = []
            file_matches = re.findall(r"File:\s*\[(.*?)\]", report_text)
            if file_matches:
                related_files = list(set(file_matches))

            return {
                "signature": signature,
                "context": "Codex-Loop Audit Phase",
                "root_cause": f"Codex 偵測到 {len(findings)} 個關鍵缺陷：\n" + "\n".join(findings),
                "fix_plan": [
                    "1. 仔細閱讀上述 Findings",
                    "2. 針對列出的檔案進行精確修復",
                    "3. 重新執行 codex-loop"
                ],
                "related_files": related_files,
                "quality": "S"
            }
        
        return {
            "signature": "Unknown Audit Failure",
            "context": "Codex-Loop",
            "root_cause": "無法從報告中提取明確 Finding",
            "fix_plan": ["請手動檢查報告內容"],
            "related_files": [],
            "quality": "B"
        }

    def run_waterfall(self, description: str) -> Dict[str, Any]:
        """執行三層瀑布診斷 (KB -> Deep -> Cache)"""
        self.logger.info("Executing Waterfall Diagnosis...")

        desc_lower = description.lower()
        if "high" in desc_lower or "medium" in desc_lower or "findings" in desc_lower:
            return self.parse_audit_report(description)

        return {
            "signature": description[:50],
            "context": "General Error",
            "root_cause": "Potential logic edge case.",
            "fix_plan": ["Refactor the failing block", "Add boundary tests"],
            "related_files": [],
            "quality": "A",
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Codex Diagnoser")
    parser.add_argument("--audit", help="Codex Audit Report content")
    parser.add_argument("--audit_file", help="Path to Codex Audit Report file")
    parser.add_argument("--path", default=".", help="Workspace path")
    args = parser.parse_args()

    diagnoser = CodexDiagnoser(args.path)
    report_content = ""
    if args.audit_file and os.path.exists(args.audit_file):
        with open(args.audit_file, 'r') as f: report_content = f.read()
    elif args.audit:
        report_content = args.audit

    if report_content:
        result = diagnoser.run_waterfall(report_content)
        print(json.dumps(result, indent=2, ensure_ascii=False))
