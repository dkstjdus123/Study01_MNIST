# -*- coding: utf-8 -*-
# 작성: 2026-09-24 19:25 (수정: 2026-09-24 19:37 표본 편향 해소 — 크기·위치 변화, 획 그리기 표본 추가)
"""
웹 버전이 파이썬(데스크톱 버전)과 같은 결과를 내는지 확인할 검증 데이터를 만듭니다.

280x280 그림판 크기의 그림을 app.py의 전처리() → 모델에 넣고, 그 중간 결과와 최종 점수를 저장합니다.
web_version/검증.html이 같은 그림을 자바스크립트로 전처리·추론해 이 값들과 대조합니다.

사람이 직접 그린 그림에서만 생기는 상황(어중간한 크기, 부드러운 획 가장자리, 캔버스 가장자리 접촉)도
시험하도록 세 종류의 표본을 섞습니다. (예전처럼 MNIST를 정확히 10배로만 키우면 크기가 늘 10의 배수라
LANCZOS 축소가 쉬운 경우만 시험하게 됩니다.)

- "MNIST 10배"        : MNIST 테스트 이미지를 280x280으로 그대로 키운 것 (이전 검증과 비교용)
- "MNIST 크기·위치"   : 60~280px 사이 임의 크기로 키워 임의 위치에 놓은 것 (일부는 캔버스 가장자리에 붙임)
- "획 그리기"         : app.py 그림판과 같은 방식(PIL 선 + 원, 펜 두께 18)으로 0~9 획을 크기·위치·떨림을 바꿔 그린 것

저장 파일
- web_version/검증데이터.bin  : 280x280 흑백 그림 N장 (uint8, 행 우선)
- web_version/검증데이터.json : 종류, 정답, 파이썬 전처리 결과(28x28 정규화 값), 파이썬 모델 점수(로짓)

검증 데이터는 크기가 크고 언제든 다시 만들 수 있으므로 저장소에 올리지 않습니다 (.gitignore).
사용법: python desktop_version/검증데이터만들기.py [MNIST 장수, 기본 200]   (획 그리기 30장은 항상 추가)
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
데이터경로 = os.path.join(프로젝트폴더, "data")
웹폴더 = os.path.join(os.path.dirname(프로젝트폴더), "web_version")
바이너리경로 = os.path.join(웹폴더, "검증데이터.bin")
정보경로 = os.path.join(웹폴더, "검증데이터.json")

펜두께 = 18          # app.py 그림판과 같은 붓 굵기
획표본수 = 30         # 숫자마다 3장

# 0~9 획 모양 (280x280 캔버스 좌표). 각 숫자는 획 여러 개, 각 획은 점 목록입니다.
숫자획 = {
    0: [[(140 + 60 * np.sin(t / 20 * 2 * np.pi), 140 - 90 * np.cos(t / 20 * 2 * np.pi)) for t in range(21)]],
    1: [[(140, 50), (140, 230)]],
    2: [[(80, 90), (110, 55), (170, 55), (195, 95), (175, 140), (80, 225), (205, 225)]],
    3: [[(85, 65), (190, 65), (130, 130), (195, 175), (160, 225), (85, 215)]],
    4: [[(170, 50), (80, 160), (210, 160)], [(170, 50), (170, 230)]],
    5: [[(190, 55), (100, 55), (95, 130), (165, 120), (195, 170), (165, 225), (90, 215)]],
    6: [[(180, 50), (110, 110), (90, 180), (130, 228), (185, 195), (170, 145), (110, 150), (95, 180)]],
    7: [[(80, 60), (200, 60), (120, 230)]],
    8: [[(185, 70), (140, 45), (95, 70), (140, 135), (190, 185), (140, 230), (90, 185), (140, 135), (185, 70)]],
    9: [[(185, 90), (140, 55), (95, 90), (140, 130), (185, 95), (185, 90), (175, 230)]],
}


def 획_그리기(획들, 난수):
    """app.py 그림판처럼 마우스가 지나간 점마다 선과 원을 그립니다. 크기·위치·떨림은 무작위로 바꿉니다."""
    그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
    붓 = ImageDraw.Draw(그림)
    배율 = 난수.uniform(0.45, 1.1)
    이동x = 난수.uniform(-1, 1) * (1 - 배율) * 140 + 140
    이동y = 난수.uniform(-1, 1) * (1 - 배율) * 140 + 140
    r = 펜두께 // 2
    for 획 in 획들:
        # 꼭짓점 사이를 약 5px 간격으로 촘촘히 나눠 마우스 이동 이벤트처럼 만듭니다.
        점들 = []
        for (x0, y0), (x1, y1) in zip(획, 획[1:]):
            칸수 = max(1, int(np.hypot(x1 - x0, y1 - y0) * 배율 / 5))
            점들 += [(x0 + (x1 - x0) * t / 칸수, y0 + (y1 - y0) * t / 칸수) for t in range(칸수)]
        점들.append(획[-1])
        이전 = None
        for x, y in 점들:
            x = int(round((x - 140) * 배율 + 이동x + 난수.uniform(-2, 2)))
            y = int(round((y - 140) * 배율 + 이동y + 난수.uniform(-2, 2)))
            if 이전:
                붓.line([이전[0], 이전[1], x, y], fill=255, width=펜두께)
            붓.ellipse([x - r, y - r, x + r, y + r], fill=255)
            이전 = (x, y)
    return 그림


def 크기위치_바꾸기(원본, 난수):
    """MNIST 28x28 그림을 60~280px 임의 크기로 키워 280x280 캔버스의 임의 위치(가끔 가장자리)에 놓습니다."""
    크기 = 난수.randint(60, 캔버스크기)
    확대 = 원본.resize((크기, 크기), Image.BILINEAR)
    여유 = 캔버스크기 - 크기
    if 난수.random() < 0.3:   # 30%는 캔버스 가장자리에 붙입니다.
        x, y = 난수.choice([0, 여유]), 난수.randint(0, 여유)
        if 난수.random() < 0.5:
            x, y = y, x
    else:
        x, y = 난수.randint(0, 여유), 난수.randint(0, 여유)
    캔버스 = Image.new("L", (캔버스크기, 캔버스크기), 0)
    캔버스.paste(확대, (x, y))
    return 캔버스


def main():
    MNIST장수 = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    난수 = random.Random(0)   # 매번 같은 검증 데이터가 나오도록 고정
    모델 = 모델_불러오기()
    테스트셋 = datasets.MNIST(데이터경로, train=False, download=True)

    표본들 = []   # (종류, 정답, 280x280 PIL 그림)
    for 번호 in range(MNIST장수):
        원본, 정답 = 테스트셋[번호]
        if 번호 % 4 == 0:
            표본들.append(("MNIST 10배", int(정답), 원본.resize((캔버스크기, 캔버스크기), Image.BILINEAR)))
        else:
            표본들.append(("MNIST 크기·위치", int(정답), 크기위치_바꾸기(원본, 난수)))
    for 번호 in range(획표본수):
        정답 = 번호 % 10
        표본들.append(("획 그리기", 정답, 획_그리기(숫자획[정답], 난수)))

    그림들, 종류들, 정답들, 입력들, 점수들 = [], [], [], [], []
    with torch.no_grad():
        for 종류, 정답, 그림 in 표본들:
            입력 = 전처리(그림)
            그림들.append(np.array(그림, dtype=np.uint8).tobytes())
            종류들.append(종류)
            정답들.append(정답)
            if 입력 is None:   # 빈 그림 (웹도 null이어야 일치)
                입력들.append(None)
                점수들.append(None)
            else:
                입력들.append([round(float(v), 6) for v in 입력.reshape(-1)])
                점수들.append([round(float(v), 6) for v in 모델(입력)[0]])

    os.makedirs(웹폴더, exist_ok=True)
    with open(바이너리경로, "wb") as 파일:
        파일.write(b"".join(그림들))
    with open(정보경로, "w", encoding="utf-8") as 파일:
        json.dump({"장수": len(표본들), "가로": 캔버스크기, "세로": 캔버스크기, "종류": 종류들, "정답": 정답들,
                   "파이썬입력": 입력들, "파이썬점수": 점수들}, 파일, ensure_ascii=False)

    print(f"저장 완료: {바이너리경로} ({os.path.getsize(바이너리경로) / 1e6:.1f}MB, {len(표본들)}장)")
    print(f"저장 완료: {정보경로}")
    for 종류 in dict.fromkeys(종류들):
        번호들 = [i for i, k in enumerate(종류들) if k == 종류]
        맞음 = sum(점수들[i] is not None and int(np.argmax(점수들[i])) == 정답들[i] for i in 번호들)
        print(f"  {종류}: {len(번호들)}장, 파이썬 정확도 {맞음}/{len(번호들)}")


if __name__ == "__main__":
    main()
