# 작성: 2026-09-24 23:25
"""MNIST로 숫자인식CNN을 학습하고, 시험 정확도가 가장 높을 때 mnist_cnn.pt로 저장합니다.

실행: python train.py [에폭수]   (기본 5에폭, CPU에서 에폭당 몇 분)
데이터와 가중치는 이 파일이 있는 폴더 기준으로 저장하므로 어느 폴더에서 실행해도 됩니다.
"""

import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import 숫자인식CNN

폴더 = Path(__file__).resolve().parent
데이터폴더 = 폴더 / "data"
저장경로 = 폴더 / "mnist_cnn.pt"
평균, 표준편차 = 0.1307, 0.3081   # app.py와 같은 값


def 데이터_준비(배치크기=64):
    정규화 = [transforms.ToTensor(), transforms.Normalize((평균,), (표준편차,))]
    # 손으로 그린 숫자는 기울기와 위치가 조금씩 다르므로 약하게 회전·이동·확대해 학습합니다.
    학습변환 = transforms.Compose([transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)), *정규화])
    학습셋 = datasets.MNIST(데이터폴더, train=True, download=True, transform=학습변환)
    시험셋 = datasets.MNIST(데이터폴더, train=False, download=True, transform=transforms.Compose(정규화))
    return DataLoader(학습셋, batch_size=배치크기, shuffle=True), DataLoader(시험셋, batch_size=1000)


def 정확도_재기(모델, 로더):
    모델.eval()
    맞음 = 0
    with torch.no_grad():
        for 입력, 정답 in 로더:
            맞음 += (모델(입력).argmax(1) == 정답).sum().item()
    return 맞음 / len(로더.dataset)


def main():
    에폭수 = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    torch.manual_seed(0)
    학습로더, 시험로더 = 데이터_준비()
    모델 = 숫자인식CNN()
    최적화 = torch.optim.Adam(모델.parameters(), lr=1e-3)
    스케줄러 = torch.optim.lr_scheduler.StepLR(최적화, step_size=1, gamma=0.7)
    손실함수 = nn.CrossEntropyLoss()
    최고 = 0.0
    for 에폭 in range(1, 에폭수 + 1):
        모델.train()
        for 번호, (입력, 정답) in enumerate(학습로더, 1):
            최적화.zero_grad()
            손실 = 손실함수(모델(입력), 정답)
            손실.backward()
            최적화.step()
            if 번호 % 200 == 0:
                print(f"  에폭 {에폭} 배치 {번호}/{len(학습로더)} 손실 {손실.item():.4f}", flush=True)
        스케줄러.step()
        정확도 = 정확도_재기(모델, 시험로더)
        print(f"에폭 {에폭}: 시험 정확도 {정확도 * 100:.2f}%", flush=True)
        if 정확도 > 최고:
            최고 = 정확도
            torch.save(모델.state_dict(), 저장경로)
            print(f"  저장: {저장경로}", flush=True)
    print(f"최고 시험 정확도 {최고 * 100:.2f}%")


if __name__ == "__main__":
    main()
