# -*- coding: utf-8 -*-
# 작성: 2026-09-24 19:25
"""
웹 버전이 파이썬(데스크톱 버전)과 같은 결과를 내는지 확인할 검증 데이터를 만듭니다.

MNIST 테스트 이미지를 그림판 크기(280x280)로 키운 뒤 app.py의 전처리() → 모델에 넣고,
그 중간 결과와 최종 점수를 저장합니다. web_version/검증.html이 같은 그림을 자바스크립트로
전처리·추론해 이 값들과 대조합니다.

- web_version/검증데이터.bin  : 280x280 흑백 그림 N장 (uint8, 행 우선)
- web_version/검증데이터.json : 정답, 파이썬 전처리 결과(28x28 정규화 값), 파이썬 모델 점수(로짓)

검증 데이터는 크기가 크고 언제든 다시 만들 수 있으므로 저장소에 올리지 않습니다 (.gitignore).
사용법: python desktop_version/검증데이터만들기.py [장수, 기본 200]
"""

import json
import os
import sys

import numpy as np
import torch
from PIL import Image
from torchvision import datasets

from app import 모델_불러오기, 전처리, 캔버스크기

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
데이터경로 = os.path.join(프로젝트폴더, "data")
웹폴더 = os.path.join(os.path.dirname(프로젝트폴더), "web_version")
바이너리경로 = os.path.join(웹폴더, "검증데이터.bin")
정보경로 = os.path.join(웹폴더, "검증데이터.json")


def main():
    장수 = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    모델 = 모델_불러오기()
    테스트셋 = datasets.MNIST(데이터경로, train=False, download=True)

    그림들, 정답들, 입력들, 점수들 = [], [], [], []
    with torch.no_grad():
        for 번호 in range(장수):
            원본, 정답 = 테스트셋[번호]
            # 28x28 → 280x280: 그림판에 그린 것처럼 크게 만듭니다.
            그림 = 원본.resize((캔버스크기, 캔버스크기), Image.BILINEAR)
            입력 = 전처리(그림)
            그림들.append(np.array(그림, dtype=np.uint8).tobytes())
            정답들.append(int(정답))
            입력들.append([round(float(v), 6) for v in 입력.reshape(-1)])
            점수들.append([round(float(v), 6) for v in 모델(입력)[0]])

    os.makedirs(웹폴더, exist_ok=True)
    with open(바이너리경로, "wb") as 파일:
        파일.write(b"".join(그림들))
    with open(정보경로, "w", encoding="utf-8") as 파일:
        json.dump({"장수": 장수, "가로": 캔버스크기, "세로": 캔버스크기, "정답": 정답들,
                   "파이썬입력": 입력들, "파이썬점수": 점수들}, 파일, ensure_ascii=False)

    맞음 = sum(int(np.argmax(s)) == 정답 for s, 정답 in zip(점수들, 정답들))
    print(f"저장 완료: {바이너리경로} ({os.path.getsize(바이너리경로) / 1e6:.1f}MB)")
    print(f"저장 완료: {정보경로}")
    print(f"파이썬 정확도: {맞음}/{장수}")


if __name__ == "__main__":
    main()
