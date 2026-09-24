# 작성: 2026-09-24 21:51
"""태스크 3 검사: 검증 데이터(230장)를 만들고, 파이썬 경로 정확도가 97% 이상인지 확인합니다."""

import re
import sys
import types
from io import StringIO
from pathlib import Path

루트 = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    # tkinter가 없는 환경에서는 가짜 모듈로 대신합니다.
    try:
        import tkinter  # noqa: F401
    except ImportError:
        가짜 = types.ModuleType("tkinter")
        가짜.messagebox = types.ModuleType("tkinter.messagebox")
        sys.modules["tkinter"] = 가짜
        sys.modules["tkinter.messagebox"] = 가짜.messagebox

    sys.path.insert(0, str(루트 / "desktop_version"))
    import 검증데이터만들기

    # 표준출력을 임시로 캡처하면서 main() 실행
    이전_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        검증데이터만들기.main()
        출력 = sys.stdout.getvalue()
    finally:
        sys.stdout = 이전_stdout

    print(출력)
    줄들 = re.findall(r"(\S+): (\d+)장, 파이썬 정확도 (\d+)/\d+", 출력)
    assert 줄들, "정확도 출력을 찾지 못했습니다"
    장수 = sum(int(n) for _, n, _ in 줄들)
    맞음 = sum(int(m) for _, _, m in 줄들)
    assert 장수 == 230, f"표본 {장수}장 (기대 230장)"
    assert 맞음 / 장수 >= 0.97, f"파이썬 정확도 {맞음}/{장수}"
    for 이름 in ("검증데이터.json", "검증데이터.bin"):
        assert (루트 / "web_version" / 이름).exists(), f"{이름} 없음"
    import subprocess
    무시됨 = subprocess.run(["git", "check-ignore", "-q", "web_version/검증데이터.json"], cwd=루트)
    assert 무시됨.returncode == 0, "검증 데이터가 .gitignore에 없습니다"
    print(f"통과: 표본 {장수}장, 파이썬 정확도 {맞음}/{장수}, git 제외 확인")
