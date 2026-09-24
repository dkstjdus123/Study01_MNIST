# 작성: 2026-09-24 21:46 (수정: 2026-09-24 22:30 재내보내기 실패 메시지에 되돌리는 방법 추가)
"""태스크 2 검사: 가중치.bin과 가중치정보.json이 서로 맞고, 다시 내보내도 같은 파일이 나오며, 변환 오차가 1e-4 미만인지 확인합니다."""

import json
import re
import subprocess
import sys
import types
from io import StringIO
from pathlib import Path

루트 = Path(__file__).resolve().parent.parent
웹 = 루트 / "web_version"


def 파일_확인():
    정보 = json.loads((웹 / "가중치정보.json").read_text(encoding="utf-8"))
    텐서들 = [층[키] for 층 in 정보["층"] for 키 in ("가중치", "편향") if 키 in 층]
    assert len(텐서들) == 12, f"텐서 {len(텐서들)}개 (기대 12개: 합성곱 4 + 전결합 2의 weight/bias)"
    위치 = 0
    for 텐서 in 텐서들:
        개수 = 1
        for 크기 in 텐서["형상"]:
            개수 *= 크기
        assert 텐서["개수"] == 개수 and 텐서["오프셋"] == 위치, f"형상·오프셋 불일치: {텐서}"
        위치 += 개수
    assert 위치 == 870_634, f"값 {위치}개"
    크기 = (웹 / "가중치.bin").stat().st_size
    assert 크기 == 위치 * 4 == 3_482_536, f"가중치.bin {크기}바이트"
    assert (정보["평균"], 정보["표준편차"]) == (0.1307, 0.3081)
    print("통과: 텐서 12개, 값 870,634개, 3,482,536바이트, 정규화 상수 일치")


def 다시_내보내기_확인():
    # tkinter가 없는 환경에서는 가짜 모듈로 대신합니다.
    try:
        import tkinter  # noqa: F401
    except ImportError:
        가짜 = types.ModuleType("tkinter")
        가짜.messagebox = types.ModuleType("tkinter.messagebox")
        sys.modules["tkinter"] = 가짜
        sys.modules["tkinter.messagebox"] = 가짜.messagebox

    sys.path.insert(0, str(루트 / "desktop_version"))
    import 가중치내보내기

    # 표준출력을 임시로 캡처하면서 main() 실행
    from io import StringIO
    이전_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        가중치내보내기.main()
        출력 = sys.stdout.getvalue()
    finally:
        sys.stdout = 이전_stdout

    차이 = float(re.search(r"최대 차이: ([0-9.e+-]+)", 출력).group(1))
    assert 차이 < 1e-4, f"변환 오차 {차이}"
    바뀜 = subprocess.run(["git", "diff", "--quiet", "--", "web_version/가중치.bin", "web_version/가중치정보.json"], cwd=루트)
    assert 바뀜.returncode == 0, ("다시 내보낸 파일이 커밋된 파일과 다릅니다 "
                                "(의도한 재학습이 아니면 git checkout -- web_version/가중치.bin web_version/가중치정보.json 으로 되돌리세요)")
    print(f"통과: 변환 오차 {차이:.1e}, 다시 내보내도 같은 파일")


if __name__ == "__main__":
    파일_확인()
    다시_내보내기_확인()
