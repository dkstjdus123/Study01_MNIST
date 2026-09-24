# 작성: 2026-09-24 23:25
"""MNIST 손글씨 숫자를 분류하는 합성곱 신경망(CNN)을 정의합니다."""

import torch.nn as nn


def 합성곱묶음(입력채널, 출력채널):
    """3x3 합성곱(패딩 1) → 배치정규화 → ReLU"""
    return [nn.Conv2d(입력채널, 출력채널, kernel_size=3, padding=1), nn.BatchNorm2d(출력채널), nn.ReLU()]


class 숫자인식CNN(nn.Module):
    """28x28 흑백 이미지를 받아 0~9 점수 10개를 냅니다."""

    def __init__(self):
        super().__init__()
        self.특징추출 = nn.Sequential(
            *합성곱묶음(1, 32), *합성곱묶음(32, 32), nn.MaxPool2d(2), nn.Dropout(0.25),    # 32x14x14
            *합성곱묶음(32, 64), *합성곱묶음(64, 64), nn.MaxPool2d(2), nn.Dropout(0.25),   # 64x7x7
        )
        self.분류기 = nn.Sequential(
            nn.Flatten(), nn.Linear(64 * 7 * 7, 256), nn.ReLU(), nn.Dropout(0.5), nn.Linear(256, 10),
        )

    def forward(self, x):
        return self.분류기(self.특징추출(x))
