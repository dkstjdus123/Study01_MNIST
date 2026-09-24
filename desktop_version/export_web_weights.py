# -*- coding: utf-8 -*-
# 작성: 2026-09-24 18:14
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전(../web_version)이 순수 자바스크립트로 읽을 수 있는 형식으로 변환합니다.

만드는 파일 (모두 web_version 폴더):
- mnist_weights.bin  : 모든 가중치를 float32(리틀 엔디언)로 이어 붙인 바이너리
- mnist_weights.json : 각 텐서의 이름·형태·시작 위치(원소 단위)를 적은 목록
- tests/reference.json : 무작위 입력과 PyTorch 출력(로짓). 자바스크립트 추론이 같은 값을 내는지 테스트에 씁니다.

배치정규화는 추론 때 고정된 선형 변환이므로 바로 앞 합성곱의 가중치·편향에 미리 합쳐 둡니다.
그래서 웹에서는 합성곱 → ReLU → 최대풀링 → 완전연결만 구현하면 됩니다.
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
바이너리경로 = os.path.join(웹폴더, "mnist_weights.bin")
목록경로 = os.path.join(웹폴더, "mnist_weights.json")
기준출력경로 = os.path.join(웹폴더, "tests", "reference.json")


def 배치정규화_합치기(합성곱: nn.Conv2d, 배치정규화: nn.BatchNorm2d):
    """y = γ(conv(x) - μ)/√(σ²+ε) + β 를 하나의 합성곱 가중치·편향으로 바꿉니다."""
    배율 = 배치정규화.weight / torch.sqrt(배치정규화.running_var + 배치정규화.eps)
    가중치 = 합성곱.weight * 배율[:, None, None, None]
    편향 = (합성곱.bias - 배치정규화.running_mean) * 배율 + 배치정규화.bias
    return 가중치, 편향


def 텐서목록_만들기(모델: 숫자인식CNN):
    """웹에서 쓸 순서대로 (이름, 텐서) 목록을 만듭니다."""
    층들 = list(모델.특징추출)
    합성곱들 = [층 for 층 in 층들 if isinstance(층, nn.Conv2d)]
    배치정규화들 = [층 for 층 in 층들 if isinstance(층, nn.BatchNorm2d)]
    선형들 = [층 for 층 in 모델.분류기 if isinstance(층, nn.Linear)]

    목록 = []
    for 번호, (합성곱, 배치정규화) in enumerate(zip(합성곱들, 배치정규화들), start=1):
        가중치, 편향 = 배치정규화_합치기(합성곱, 배치정규화)
        목록 += [(f"합성곱{번호}.가중치", 가중치), (f"합성곱{번호}.편향", 편향)]
    for 번호, 선형 in enumerate(선형들, start=1):
        목록 += [(f"완전연결{번호}.가중치", 선형.weight), (f"완전연결{번호}.편향", 선형.bias)]
    return 목록


@torch.no_grad()
def main():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()

    # 가중치를 하나의 float32 바이너리로 이어 붙이고, 위치 정보는 JSON으로 저장합니다.
    텐서정보 = []
    조각들 = []
    오프셋 = 0
    for 이름, 텐서 in 텐서목록_만들기(모델):
        배열 = 텐서.detach().numpy().astype("<f4").ravel()
        텐서정보.append({"이름": 이름, "형태": list(텐서.shape), "오프셋": 오프셋})
        조각들.append(배열)
        오프셋 += 배열.size
    np.concatenate(조각들).tofile(바이너리경로)
    with open(목록경로, "w", encoding="utf-8") as 파일:
        json.dump({"원소수": 오프셋, "텐서": 텐서정보}, 파일, ensure_ascii=False, indent=2)
    print(f"가중치 저장 완료: {바이너리경로} ({os.path.getsize(바이너리경로) / 1e6:.1f}MB, {오프셋:,}개)")

    # 자바스크립트 추론 결과와 비교할 기준 출력을 만듭니다.
    생성기 = torch.Generator().manual_seed(0)
    입력들 = torch.randn(3, 1, 28, 28, generator=생성기)
    출력들 = 모델(입력들)
    os.makedirs(os.path.dirname(기준출력경로), exist_ok=True)
    with open(기준출력경로, "w", encoding="utf-8") as 파일:
        json.dump([{"입력": 입력.ravel().tolist(), "로짓": 출력.tolist()}
                   for 입력, 출력 in zip(입력들, 출력들)], 파일)
    print(f"기준 출력 저장 완료: {기준출력경로}")


if __name__ == "__main__":
    main()
