# -*- coding: utf-8 -*-
"""MNIST 데이터셋으로 CNN을 학습하고 가중치를 mnist_cnn.pt로 저장합니다."""

import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import 숫자인식CNN

# ===== 학습 설정 =====
에폭수 = 5
배치크기 = 128
학습률 = 1e-3
# 어느 폴더에서 실행하든 이 파일과 같은 폴더에 데이터와 가중치를 두도록 절대 경로로 지정합니다.
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
데이터경로 = os.path.join(프로젝트폴더, "data")
저장경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")

# MNIST 전체 데이터의 평균과 표준편차 (정규화에 사용)
평균, 표준편차 = 0.1307, 0.3081


def 데이터로더_만들기():
    """학습용/테스트용 데이터로더를 생성합니다."""
    # 학습 데이터에는 약간의 회전·이동을 주어 실제 손글씨에 더 강인하게 만듭니다.
    학습변환 = transforms.Compose([
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])
    테스트변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])

    학습셋 = datasets.MNIST(데이터경로, train=True, download=True, transform=학습변환)
    테스트셋 = datasets.MNIST(데이터경로, train=False, download=True, transform=테스트변환)

    학습로더 = DataLoader(학습셋, batch_size=배치크기, shuffle=True)
    테스트로더 = DataLoader(테스트셋, batch_size=1000, shuffle=False)
    return 학습로더, 테스트로더


def 한_에폭_학습(모델, 로더, 손실함수, 옵티마이저, 장치, 에폭):
    """한 에폭 동안 모델을 학습합니다."""
    모델.train()
    누적손실 = 0.0
    for 배치번호, (이미지, 정답) in enumerate(로더, start=1):
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)

        옵티마이저.zero_grad()          # 이전 기울기 초기화
        출력 = 모델(이미지)             # 순전파
        손실 = 손실함수(출력, 정답)     # 손실 계산
        손실.backward()                 # 역전파
        옵티마이저.step()               # 가중치 갱신

        누적손실 += 손실.item()
        if 배치번호 % 100 == 0:
            print(f"  [에폭 {에폭}] 배치 {배치번호}/{len(로더)}  평균 손실: {누적손실 / 100:.4f}")
            누적손실 = 0.0


@torch.no_grad()
def 평가(모델, 로더, 장치):
    """테스트 데이터에 대한 정확도를 계산합니다."""
    모델.eval()
    맞은개수 = 0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        예측 = 모델(이미지).argmax(dim=1)
        맞은개수 += (예측 == 정답).sum().item()
    return 맞은개수 / len(로더.dataset) * 100


def main():
    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {장치}")

    학습로더, 테스트로더 = 데이터로더_만들기()
    모델 = 숫자인식CNN().to(장치)
    손실함수 = nn.CrossEntropyLoss()
    옵티마이저 = optim.Adam(모델.parameters(), lr=학습률)
    # 에폭마다 학습률을 점점 줄여 안정적으로 수렴하게 합니다.
    스케줄러 = optim.lr_scheduler.StepLR(옵티마이저, step_size=2, gamma=0.5)

    최고정확도 = 0.0
    for 에폭 in range(1, 에폭수 + 1):
        한_에폭_학습(모델, 학습로더, 손실함수, 옵티마이저, 장치, 에폭)
        정확도 = 평가(모델, 테스트로더, 장치)
        스케줄러.step()
        print(f"에폭 {에폭} 완료 → 테스트 정확도: {정확도:.2f}%")

        # 가장 좋은 성능의 가중치만 저장합니다.
        if 정확도 > 최고정확도:
            최고정확도 = 정확도
            torch.save(모델.state_dict(), 저장경로)
            print(f"  가중치 저장 완료: {저장경로}")

    print(f"\n학습 종료! 최고 테스트 정확도: {최고정확도:.2f}%")


if __name__ == "__main__":
    main()
