# 작성: 2026-09-24 23:41
"""mnist_cnn.pt를 웹 버전이 읽는 두 파일로 내보냅니다.

- web_version/가중치.bin: float32 리틀 엔디언 값을 헤더 없이 이어 붙인 파일
- web_version/가중치정보.json: 층 순서, 텐서 이름·형상·위치(float 개수 단위), 정규화 상수
배치정규화는 바로 앞 합성곱에 합쳐 내보내므로, 웹은 합성곱·ReLU·최대풀링·펼치기·전결합만 계산합니다.
실행: python 가중치내보내기.py  (다시 학습한 뒤에는 반드시 다시 실행)
"""

import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app import 가중치경로, 모델_불러오기, 평균, 표준편차

웹폴더 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web_version"))
바이너리경로 = os.path.join(웹폴더, "가중치.bin")
정보경로 = os.path.join(웹폴더, "가중치정보.json")


def 배치정규화_합치기(합성곱, 정규화):
    """합성곱 뒤의 배치정규화를 합성곱의 가중치·편향에 합칩니다 (float64로 계산 후 float32)."""
    배율 = 정규화.weight.double() / torch.sqrt(정규화.running_var.double() + 정규화.eps)
    가중치 = 합성곱.weight.double() * 배율.reshape(-1, 1, 1, 1)
    편향 = (합성곱.bias.double() - 정규화.running_mean.double()) * 배율 + 정규화.bias.double()
    return 가중치.float(), 편향.float()


def 층_목록_만들기(모델):
    """계산 순서대로 (종류, 가중치, 편향) 목록을 만듭니다. 드롭아웃은 추론 때 하는 일이 없어 건너뜁니다."""
    모듈들 = list(모델.특징추출) + list(모델.분류기)
    층들 = []
    i = 0
    while i < len(모듈들):
        모듈 = 모듈들[i]
        if isinstance(모듈, nn.Conv2d):
            다음 = 모듈들[i + 1]
            assert isinstance(다음, nn.BatchNorm2d), "합성곱 다음에는 배치정규화가 와야 합니다."
            assert 모듈.kernel_size == (3, 3) and 모듈.padding == (1, 1) and 모듈.stride == (1, 1), \
                "웹은 3x3·패딩 1·보폭 1 합성곱만 계산합니다."
            층들.append(("conv", *배치정규화_합치기(모듈, 다음)))
            i += 2
            continue
        if isinstance(모듈, nn.Linear):
            층들.append(("linear", 모듈.weight.detach().float(), 모듈.bias.detach().float()))
        elif isinstance(모듈, nn.ReLU):
            층들.append(("relu", None, None))
        elif isinstance(모듈, nn.MaxPool2d):
            assert 모듈.kernel_size == 2 and 모듈.stride == 2, "웹은 2x2 최대풀링만 계산합니다."
            층들.append(("maxpool", None, None))
        elif isinstance(모듈, nn.Flatten):
            층들.append(("flatten", None, None))
        elif not isinstance(모듈, nn.Dropout):
            raise ValueError(f"웹에서 계산할 수 없는 층입니다: {모듈}")
        i += 1
    return 층들


def 합친_계산(층들, 입력):
    """내보낼 층 목록만으로 순전파합니다 (원래 모델과 같은 값이 나오는지 확인용)."""
    x = 입력
    for 종류, 가중치, 편향 in 층들:
        if 종류 == "conv":
            x = F.conv2d(x, 가중치, 편향, padding=1)
        elif 종류 == "relu":
            x = F.relu(x)
        elif 종류 == "maxpool":
            x = F.max_pool2d(x, 2)
        elif 종류 == "flatten":
            x = x.flatten(1)
        else:
            x = F.linear(x, 가중치, 편향)
    return x


def main():
    모델 = 모델_불러오기()
    with torch.no_grad():
        층들 = 층_목록_만들기(모델)
        조각들, 층정보, 위치 = [], [], 0
        for 번호, (종류, 가중치, 편향) in enumerate(층들):
            정보 = {"종류": 종류, "이름": f"{번호}_{종류}"}
            for 키, 텐서 in (("가중치", 가중치), ("편향", 편향)):
                if 텐서 is None:
                    continue
                값 = 텐서.contiguous().numpy().astype("<f4").ravel()
                정보[키] = {"형상": list(텐서.shape), "오프셋": 위치, "개수": int(값.size)}
                조각들.append(값)
                위치 += int(값.size)
            층정보.append(정보)

        os.makedirs(웹폴더, exist_ok=True)
        with open(바이너리경로, "wb") as 파일:
            파일.write(np.concatenate(조각들).tobytes())
        전체정보 = {"원본": os.path.basename(가중치경로), "입력형상": [1, 28, 28],
                    "평균": 평균, "표준편차": 표준편차, "층": 층정보}
        with open(정보경로, "w", encoding="utf-8") as 파일:
            json.dump(전체정보, 파일, ensure_ascii=False, indent=1)
            파일.write("\n")
        print(f"저장: {바이너리경로} (값 {위치:,}개, {os.path.getsize(바이너리경로):,}바이트, 텐서 {len(조각들)}개)")
        print(f"저장: {정보경로}")

        입력 = torch.randn(8, 1, 28, 28, generator=torch.Generator().manual_seed(0))
        차이 = (합친_계산(층들, 입력) - 모델(입력)).abs().max().item()
        print(f"PyTorch와 변환 결과 최대 차이: {차이:.2e}")


if __name__ == "__main__":
    main()
