# 작성: 2026-09-24 23:45
"""웹 버전 검증용 정답 데이터를 만듭니다.

280x280 그림 230장을 app.py의 전처리()와 PyTorch 모델에 넣고 결과를 저장합니다.
- web_version/검증데이터.bin: 그림 바이트 (장마다 280x280, 0~255)
- web_version/검증데이터.json: 장수, 크기, 종류, 정답, 파이썬 전처리 결과(784개), 파이썬 점수(10개)
표본은 세 종류입니다: MNIST 10배 확대 50장, 크기·위치를 바꾼 MNIST 150장(30%는 가장자리에 붙임),
app.py 그림판처럼(선 + 둥근 점, 펜 18) 0~9 획을 그린 30장. 난수를 고정해 매번 같은 데이터가 나옵니다.
실행: python 검증데이터만들기.py [MNIST 장수, 기본 200]   (두 산출물은 .gitignore 대상)
"""

import json
import os
import random
import sys

import numpy as np
import torch
from PIL import Image, ImageDraw
from torchvision import datasets

from app import 모델_불러오기, 전처리, 캔버스크기

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
데이터폴더 = os.path.join(프로젝트폴더, "data")
웹폴더 = os.path.normpath(os.path.join(프로젝트폴더, "..", "web_version"))
바이너리경로 = os.path.join(웹폴더, "검증데이터.bin")
정보경로 = os.path.join(웹폴더, "검증데이터.json")
펜두께 = 18

# 0~9를 한 붓으로 그리는 꺾은선 (가로·세로 0~1 좌표). 사람이 마우스로 그리는 모양을 흉내 냅니다.
획모양 = {
    0: [(0.5, 0.1), (0.27, 0.22), (0.2, 0.5), (0.27, 0.78), (0.5, 0.9), (0.73, 0.78), (0.8, 0.5), (0.73, 0.22), (0.5, 0.1)],
    1: [(0.45, 0.2), (0.55, 0.1), (0.55, 0.9)],
    2: [(0.25, 0.3), (0.4, 0.12), (0.62, 0.12), (0.75, 0.3), (0.68, 0.5), (0.25, 0.88), (0.8, 0.88)],
    3: [(0.25, 0.15), (0.72, 0.15), (0.45, 0.45), (0.72, 0.6), (0.7, 0.8), (0.5, 0.9), (0.25, 0.82)],
    4: [(0.62, 0.9), (0.62, 0.1), (0.2, 0.62), (0.82, 0.62)],
    5: [(0.75, 0.12), (0.32, 0.12), (0.28, 0.45), (0.6, 0.42), (0.75, 0.6), (0.7, 0.82), (0.45, 0.9), (0.25, 0.82)],
    6: [(0.68, 0.1), (0.4, 0.3), (0.25, 0.6), (0.35, 0.87), (0.6, 0.88), (0.72, 0.68), (0.55, 0.52), (0.3, 0.62)],
    7: [(0.2, 0.12), (0.8, 0.12), (0.45, 0.9)],
    8: [(0.7, 0.25), (0.5, 0.1), (0.3, 0.25), (0.7, 0.7), (0.5, 0.9), (0.3, 0.7), (0.7, 0.25)],
    9: [(0.72, 0.35), (0.5, 0.12), (0.3, 0.3), (0.45, 0.5), (0.72, 0.38), (0.7, 0.9)],
}


def MNIST_놓기(그림28, 크기, 왼쪽, 위):
    """28x28 MNIST 그림을 크기x크기로 키워 280x280 검은 캔버스의 (왼쪽, 위)에 놓습니다."""
    바탕 = Image.new("L", (캔버스크기, 캔버스크기), 0)
    바탕.paste(그림28.resize((크기, 크기), Image.BILINEAR), (왼쪽, 위))
    return 바탕


def 획_그리기(숫자, 난수):
    """숫자 획을 크기·위치·기울기를 조금씩 바꿔 app.py 그림판과 같은 방식(선 + 둥근 점)으로 그립니다."""
    그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
    붓 = ImageDraw.Draw(그림)
    크기 = 난수.uniform(120, 220)
    왼쪽 = 난수.uniform(10, 캔버스크기 - 10 - 크기)
    위 = 난수.uniform(10, 캔버스크기 - 10 - 크기)
    기울기 = 난수.uniform(-0.12, 0.12)
    점들 = [(왼쪽 + (x + 기울기 * (0.5 - y)) * 크기, 위 + y * 크기) for x, y in 획모양[숫자]]
    붓.line(점들, fill=255, width=펜두께)
    반 = 펜두께 / 2
    for x, y in 점들:
        붓.ellipse((x - 반, y - 반, x + 반, y + 반), fill=255)
    return 그림


def 표본_만들기(MNIST장수, 난수):
    시험셋 = datasets.MNIST(데이터폴더, train=False, download=True)
    표본들 = []   # (종류, 280x280 그림, 정답)
    for i in range(MNIST장수):
        그림28, 정답 = 시험셋[i]
        if i < 50:
            표본들.append(("MNIST 10배", MNIST_놓기(그림28, 캔버스크기, 0, 0), 정답))
            continue
        크기 = 난수.randint(60, 캔버스크기)
        if 난수.random() < 0.3:   # 캔버스 가장자리에 붙이기
            왼쪽, 위 = 난수.choice([0, 캔버스크기 - 크기]), 난수.choice([0, 캔버스크기 - 크기])
        else:
            왼쪽, 위 = 난수.randint(0, 캔버스크기 - 크기), 난수.randint(0, 캔버스크기 - 크기)
        표본들.append(("MNIST 크기·위치", MNIST_놓기(그림28, 크기, 왼쪽, 위), 정답))
    for 숫자 in range(10):
        for _ in range(3):
            표본들.append(("획 그리기", 획_그리기(숫자, 난수), 숫자))
    return 표본들


def main():
    MNIST장수 = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    표본들 = 표본_만들기(MNIST장수, random.Random(0))
    모델 = 모델_불러오기()
    정보 = {"장수": len(표본들), "가로": 캔버스크기, "세로": 캔버스크기,
            "종류": [], "정답": [], "파이썬입력": [], "파이썬점수": []}
    바이트들, 집계 = [], {}
    with torch.no_grad():
        for 종류, 그림, 정답 in 표본들:
            입력 = 전처리(그림)
            점수 = None if 입력 is None else 모델(입력)[0]
            정보["종류"].append(종류)
            정보["정답"].append(int(정답))
            정보["파이썬입력"].append(None if 입력 is None else [float(v) for v in 입력.flatten()])
            정보["파이썬점수"].append(None if 점수 is None else [float(v) for v in 점수])
            바이트들.append(np.asarray(그림, dtype=np.uint8).tobytes())
            맞음, 장수 = 집계.get(종류, (0, 0))
            집계[종류] = (맞음 + int(점수 is not None and int(점수.argmax()) == 정답), 장수 + 1)

    os.makedirs(웹폴더, exist_ok=True)
    with open(바이너리경로, "wb") as 파일:
        파일.write(b"".join(바이트들))
    with open(정보경로, "w", encoding="utf-8") as 파일:
        json.dump(정보, 파일, ensure_ascii=False)
    print(f"저장: {바이너리경로} ({len(표본들)}장)")
    print(f"저장: {정보경로}")
    for 종류, (맞음, 장수) in 집계.items():
        print(f"  {종류}: {장수}장, 파이썬 정확도 {맞음}/{장수}")


if __name__ == "__main__":
    main()
