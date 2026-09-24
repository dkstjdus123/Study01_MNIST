# 작성: 2026-09-24 21:43 (수정: 2026-09-24 22:30 CRLF에서도 맞는 블롭 id 비교로 변경 / 22:35 diff에 core.autocrlf=true 직접 지정 / 23:21 데스크톱 앱을 새로 만들어 원본 비교를 파일 확인으로 바꿈)
"""태스크 1 검사: 데스크톱 앱 파일 4개가 있고, app.py의 전처리와 모델이 제대로 동작하는지 확인합니다."""

import sys
import types
from pathlib import Path

루트 = Path(__file__).resolve().parent.parent
데스크톱 = 루트 / "desktop_version"


def 파일_확인():
    for 이름 in ["model.py", "train.py", "app.py", "make_shortcut.py"]:
        assert (데스크톱 / 이름).is_file(), f"{이름}이 없습니다"
    print("통과: 데스크톱 앱 파일 4개가 있음")


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
    파일_확인()
    앱_경로_확인()
