"""Security and path sanitation audit script."""

import re
from pathlib import Path

user_path_pattern = re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE)
secret_pattern = re.compile(r"(api_key|secret_key|private_key|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE)

violations = []
root = Path(".")
for p in root.rglob("*"):
    if p.is_file() and not any(part.startswith(".") for part in p.parts):
        if p.suffix in [".py", ".json", ".md", ".toml", ".txt"]:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(text.splitlines(), 1):
                    if user_path_pattern.search(line):
                        violations.append((str(p), line_no, "Hardcoded User Path", line.strip()[:80]))
                    if secret_pattern.search(line) and "schema" not in str(p).lower():
                        violations.append((str(p), line_no, "Potential Secret", line.strip()[:80]))
            except Exception:
                pass

print(f"Total audit findings: {len(violations)}")
for f, l, typ, snip in violations[:25]:
    print(f"[{typ}] {f}:{l} -> {snip}")
