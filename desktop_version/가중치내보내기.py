# -*- coding: utf-8 -*-
# 작성: 2026-09-24 19:20 (수정: 2026-09-24 19:25 가중치.bin/가중치정보.json 형식으로 변경)
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전이 순수 자바스크립트로 읽을 수 있는 두 파일로 내보냅니다.

- web_version/가중치.bin      : 텐서 12개(합성곱 4개 + 전결합 2개의 weight/bias)를 float32 리틀 엔디언으로 이어 붙인 순수 데이터
- web_version/가중치정보.json : 층 순서, 각 텐서의 이름·형상·위치(오프셋), app.py에서 읽어 온 정규화 상수(평균, 표준편차)

배치정규화는 추론 때 고정된 선형 변환이므로 바로 앞 합성곱의 가중치·편향에 미리 합쳐 둡니다.
정규화 상수를 자바스크립트에 하드코딩하지 않고 정보 파일로 넘기므로, 상수가 웹 쪽에 또 복사되지 않습니다.
재학습한 뒤에는 반드시 이 스크립트를 다시 실행해야 웹 페이지에 반영됩니다.
"""

import json
import os

import numpy as np
import torch
import torch.nn as nn

from app import 가중치경로, 모델_불러오기, 평균, 표준편차

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
웹폴더 = os.path.join(os.path.dirname(프로젝트폴더), "web_version")
바이너리경로 = os.path.join(웹폴더, "가중치.bin")
정보경로 = os.path.join(웹폴더, "가중치정보.json")


def 배치정규화_합치기(합성곱, 배치정규화):
    """합성곱 뒤의 배치정규화를 합성곱 가중치·편향에 합칩니다."""
    배율 = 배치정규화.weight / torch.sqrt(배치정규화.running_var + 배치정규화.eps)
    가중치 = 합성곱.weight * 배율[:, None, None, None]
    편향 = (합성곱.bias - 배치정규화.running_mean) * 배율 + 배치정규화.bias
    return 가중치, 편향


def 층목록_만들기(모델):
    """모델을 웹에서 차례대로 계산할 층 목록 [(종류, 이름, 가중치, 편향)]으로 바꿉니다."""
    층목록 = []
    for 부분이름 in ("특징추출", "분류기"):
        모듈들 = list(getattr(모델, 부분이름))
        for 순번, 모듈 in enumerate(모듈들):
            이름 = f"{부분이름}.{순번}"
            if isinstance(모듈, nn.Conv2d):
                다음 = 모듈들[순번 + 1]
                assert isinstance(다음, nn.BatchNorm2d), "합성곱 다음에는 배치정규화가 와야 합니다."
                assert 모듈.kernel_size == (3, 3) and 모듈.padding == (1, 1) and 모듈.stride == (1, 1), \
                    "웹 버전(모델.js)은 3x3·패딩 1·보폭 1 합성곱만 지원합니다."
                층목록.append(("conv", 이름, *배치정규화_합치기(모듈, 다음)))
            elif isinstance(모듈, nn.ReLU):
                층목록.append(("relu", 이름, None, None))
            elif isinstance(모듈, nn.MaxPool2d):
                층목록.append(("maxpool", 이름, None, None))
            elif isinstance(모듈, nn.Linear):
                층목록.append(("linear", 이름, 모듈.weight, 모듈.bias))
            # 배치정규화(합성곱에 합침), 드롭아웃(추론 때 아무 일도 안 함), 펼치기(메모리 순서 그대로)는 건너뜁니다.
    return 층목록


def 넘파이_추론(입력, 층목록):
    """웹 버전(모델.js)과 같은 순서로 계산하는 검증용 추론입니다. 입력 형태: (1, 28, 28)"""
    x = 입력
    for 종류, _이름, 가중치, 편향 in 층목록:
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


def main():
    모델 = 모델_불러오기()

    조각들, 층정보, 오프셋 = [], [], 0
    with torch.no_grad():
        층목록 = 층목록_만들기(모델)
        for 종류, 이름, 가중치, 편향 in 층목록:
            정보 = {"종류": 종류, "이름": 이름}
            if 가중치 is not None:
                for 키, 값 in (("가중치", 가중치), ("편향", 편향)):
                    배열 = 값.numpy().astype("<f4")
                    정보[키] = {"형상": list(배열.shape), "오프셋": 오프셋, "개수": 배열.size}
                    조각들.append(배열.tobytes())
                    오프셋 += 배열.size
            층정보.append(정보)

        os.makedirs(웹폴더, exist_ok=True)
        with open(바이너리경로, "wb") as 파일:
            파일.write(b"".join(조각들))
        with open(정보경로, "w", encoding="utf-8") as 파일:
            json.dump({"원본": os.path.basename(가중치경로), "입력형상": [1, 28, 28],
                       "평균": 평균, "표준편차": 표준편차, "층": 층정보},
                      파일, ensure_ascii=False, indent=1)
        print(f"저장 완료: {바이너리경로} ({os.path.getsize(바이너리경로) / 1e6:.1f}MB, 텐서 {len(조각들)}개)")
        print(f"저장 완료: {정보경로}")

        # 배치정규화를 합친 결과가 원래 모델과 같은지 확인합니다.
        무작위입력 = torch.randn(1, 1, 28, 28)
        기대값 = 모델(무작위입력).numpy()[0]
        결과 = 넘파이_추론(무작위입력.numpy()[0], 층목록)
    print(f"PyTorch와 변환 결과 최대 차이: {np.abs(기대값 - 결과).max():.2e}")


if __name__ == "__main__":
    main()
