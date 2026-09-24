# 작성: 2026-09-24 21:43 (수정: 2026-09-24 22:30 CRLF에서도 맞는 블롭 id 비교로 변경 / 22:35 diff에 core.autocrlf=true 직접 지정)
"""태스크 1 검사: 데스크톱 파이썬 파일 4개가 분리 전 원본과 같고, app.py의 전처리와 모델이 그대로 동작하는지 확인합니다."""

import subprocess
import sys
import types
from pathlib import Path

루트 = Path(__file__).resolve().parent.parent
데스크톱 = 루트 / "desktop_version"
원본커밋 = "55382a4"   # 폴더 분리 전 첫 커밋


def 원본과_같은지_확인():
    # git show로 받은 원본 바이트를 작업트리 바이트와 직접 비교하면, Windows의
    # core.autocrlf=true로 체크아웃했을 때 줄바꿈만 달라도 실패한다. 블롭 id로 비교하면
    # 체크아웃 방식과 무관하게 커밋된 내용만 비교되므로, 커밋 안 된 수정은 git diff로 따로 잡는다.
    # 이 diff 호출에는 -c core.autocrlf=true를 직접 지정해, 저장소 설정에 그 값이 없어도
    # (예: clone 명령에 준 -c가 새 저장소 설정에 남지 않는 경우) 줄바꿈 차이만으로 오탐하지 않게 한다.
    for 이름 in ["model.py", "train.py", "app.py", "make_shortcut.py"]:
        원본_블롭 = subprocess.run(["git", "rev-parse", f"{원본커밋}:{이름}"], cwd=루트,
                                  capture_output=True, text=True, check=True).stdout.strip()
        현재_블롭 = subprocess.run(["git", "rev-parse", f"HEAD:desktop_version/{이름}"], cwd=루트,
                                  capture_output=True, text=True, check=True).stdout.strip()
        assert 원본_블롭 == 현재_블롭, f"{이름}이 원본과 다릅니다"
        커밋안된변경 = subprocess.run(
            ["git", "-c", "core.autocrlf=true", "diff", "--quiet", "HEAD", "--", f"desktop_version/{이름}"],
            cwd=루트, capture_output=True)
        assert 커밋안된변경.returncode == 0, f"{이름}이 원본과 다릅니다"
    print("통과: 파이썬 파일 4개가 원본과 같음")
    이력 = subprocess.run(["git", "log", "--follow", "--format=%h", "--", "desktop_version/app.py"],
                          cwd=루트, capture_output=True, text=True, check=True).stdout.split()
    assert 원본커밋 in 이력, "git mv 이력이 끊겼습니다"
    print("통과: git mv로 옮긴 app.py의 이력이 첫 커밋까지 이어짐")


def 앱_경로_확인(장수=1000):
    # 화면이 없는 환경에는 tkinter가 없을 수 있으므로 빈 모듈로 대신합니다 (창은 만들지 않음).
    try:
        import tkinter  # noqa: F401
    except ImportError:
        가짜 = types.ModuleType("tkinter")
        가짜.messagebox = types.ModuleType("tkinter.messagebox")
        sys.modules["tkinter"], sys.modules["tkinter.messagebox"] = 가짜, 가짜.messagebox
    sys.path.insert(0, str(데스크톱))
    import torch
    from PIL import Image
    from torchvision import datasets
    import app

    모델 = app.모델_불러오기()
    테스트셋 = datasets.MNIST(str(데스크톱 / "data"), train=False, download=True)
    맞음 = 0
    for i in range(장수):
        그림, 정답 = 테스트셋[i]
        입력 = app.전처리(그림.resize((app.캔버스크기, app.캔버스크기), Image.LANCZOS))
        with torch.no_grad():
            맞음 += int(모델(입력).argmax(1).item() == 정답)
    assert 맞음 / 장수 >= 0.97, f"app.py 경로 정확도 {맞음}/{장수}"
    print(f"통과: app.py 경로 정확도 {맞음}/{장수}")
    assert app.전처리(Image.new("L", (app.캔버스크기, app.캔버스크기), 0)) is None
    print("통과: 빈 그림은 None")


if __name__ == "__main__":
    원본과_같은지_확인()
    앱_경로_확인()
