# -*- coding: utf-8 -*-
# 작성: 2026-09-24 19:20
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전이 순수 자바스크립트로 읽을 수 있는 형식으로 변환합니다.

- web_version/model_weights.bin : 모든 가중치를 float32(리틀 엔디언)로 이어 붙인 이진 파일
- web_version/model_weights.json: 각 층의 종류·모양·바이너리 안 위치(오프셋)

배치정규화는 추론 때 고정된 선형 변환이므로 바로 앞 합성곱의 가중치·편향에 미리 합쳐 둡니다.
그래서 웹에서는 합성곱 → ReLU → 최대풀링 → 완전연결만 계산하면 됩니다.
재학습한 뒤에는 반드시 이 스크립트를 다시 실행해야 웹 페이지에 반영됩니다.
"""

import json
import os

import numpy as np
import torch
import torch.nn as nn

from model import 숫자인식CNN

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
웹폴더 = os.path.join(os.path.dirname(프로젝트폴더), "web_version")
바이너리경로 = os.path.join(웹폴더, "model_weights.bin")
정보경로 = os.path.join(웹폴더, "model_weights.json")


def 배치정규화_합치기(합성곱, 배치정규화):
    """합성곱 뒤의 배치정규화를 합성곱 가중치·편향에 합칩니다."""
    배율 = 배치정규화.weight / torch.sqrt(배치정규화.running_var + 배치정규화.eps)
    가중치 = 합성곱.weight * 배율[:, None, None, None]
    편향 = (합성곱.bias - 배치정규화.running_mean) * 배율 + 배치정규화.bias
    return 가중치, 편향


def 층목록_만들기(모델):
    """모델을 웹에서 차례대로 계산할 층 목록(종류, 가중치, 편향)으로 바꿉니다."""
    층목록 = []
    모듈들 = list(모델.특징추출) + list(모델.분류기)
    for 순번, 모듈 in enumerate(모듈들):
        if isinstance(모듈, nn.Conv2d):
            다음 = 모듈들[순번 + 1]
            assert isinstance(다음, nn.BatchNorm2d), "합성곱 다음에는 배치정규화가 와야 합니다."
            가중치, 편향 = 배치정규화_합치기(모듈, 다음)
            층목록.append(("conv", 가중치, 편향))
        elif isinstance(모듈, nn.ReLU):
            층목록.append(("relu", None, None))
        elif isinstance(모듈, nn.MaxPool2d):
            층목록.append(("maxpool", None, None))
        elif isinstance(모듈, nn.Linear):
            층목록.append(("linear", 모듈.weight, 모듈.bias))
        # 배치정규화(합성곱에 합침), 드롭아웃(추론 때 아무 일도 안 함), 펼치기(메모리 순서 그대로)는 건너뜁니다.
    return 층목록


def main():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()

    조각들, 층정보, 오프셋 = [], [], 0
    with torch.no_grad():
        for 종류, 가중치, 편향 in 층목록_만들기(모델):
            정보 = {"type": 종류}
            if 가중치 is not None:
                for 이름, 값 in (("weight", 가중치), ("bias", 편향)):
                    배열 = 값.detach().numpy().astype("<f4")
                    정보[이름] = {"shape": list(배열.shape), "offset": 오프셋, "length": 배열.size}
                    조각들.append(배열.tobytes())
                    오프셋 += 배열.size
            층정보.append(정보)

    os.makedirs(웹폴더, exist_ok=True)
    with open(바이너리경로, "wb") as 파일:
        파일.write(b"".join(조각들))
    with open(정보경로, "w", encoding="utf-8") as 파일:
        json.dump({"input": [1, 28, 28], "layers": 층정보}, 파일, ensure_ascii=False, indent=1)
    print(f"저장 완료: {바이너리경로} ({os.path.getsize(바이너리경로) / 1e6:.1f}MB)")
    print(f"저장 완료: {정보경로}")

    # 배치정규화를 합친 결과가 원래 모델과 같은지 numpy로 확인합니다.
    무작위입력 = torch.randn(1, 1, 28, 28)
    with torch.no_grad():
        기대값 = 모델(무작위입력).numpy()[0]
        결과 = 넘파이_추론(무작위입력.numpy()[0], 층목록_만들기(모델))
    print(f"PyTorch와 변환 결과 최대 차이: {np.abs(기대값 - 결과).max():.2e}")


def 넘파이_추론(입력, 층목록):
    """웹 버전과 같은 순서로 계산하는 검증용 추론입니다."""
    x = 입력
    for 종류, 가중치, 편향 in 층목록:
        if 종류 == "conv":
            x = torch.nn.functional.conv2d(torch.from_numpy(x)[None], 가중치, 편향, padding=1)[0].numpy()
        elif 종류 == "relu":
            x = np.maximum(x, 0)
        elif 종류 == "maxpool":
            c, h, w = x.shape
            x = x.reshape(c, h // 2, 2, w // 2, 2).max(axis=(2, 4))
        elif 종류 == "linear":
            x = 가중치.numpy() @ x.reshape(-1) + 편향.numpy()
    return x


if __name__ == "__main__":
    main()
