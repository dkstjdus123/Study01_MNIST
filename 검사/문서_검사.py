# 작성: 2026-09-24 22:16
"""태스크 7 검사: CLAUDE.md 3개가 가리키는 파일이 실제로 있는지(또는 .gitignore로 일부러 뺀 산출물인지) 확인합니다."""

import re
import subprocess
from pathlib import Path

루트 = Path(__file__).resolve().parent.parent
파일이름 = r"`([^` ]+\.(?:py|js|cjs|html|css|json|bin|pt|md|ico))`"

if __name__ == "__main__":
    없음 = []
    for 문서 in ["CLAUDE.md", "web_version/CLAUDE.md", "desktop_version/CLAUDE.md"]:
        폴더 = (루트 / 문서).parent
        for 이름 in set(re.findall(파일이름, (루트 / 문서).read_text(encoding="utf-8"))):
            대상 = 이름.removesuffix("/.bin")   # "검증데이터.json/.bin"처럼 두 파일을 한 번에 적은 경우
            후보 = [폴더 / 대상, 루트 / 대상, 루트 / "desktop_version" / 대상, 루트 / "web_version" / 대상]
            if any(p.exists() for p in 후보):
                continue
            # .gitignore로 일부러 뺀 산출물(검증 데이터 등)은 없어도 됩니다.
            무시 = subprocess.run(["git", "check-ignore", "-q", *map(str, 후보)], cwd=루트)
            if 무시.returncode != 0:
                없음.append(f"{문서} → {이름}")
    assert not 없음, "없는 파일: " + ", ".join(없음)
    print("통과: CLAUDE.md 3개가 가리키는 파일이 모두 있음")
