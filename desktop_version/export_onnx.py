# -*- coding: utf-8 -*-
# 작성: 2026-09-22 02:10
"""
학습된 가중치(mnist_cnn.pt)를 웹 브라우저에서 쓸 수 있는 ONNX 형식(mnist_cnn.onnx)으로 변환합니다.
웹 페이지(../web_version/index.html)는 onnxruntime-web으로 이 파일을 불러와 추론합니다.
"""

import os

import numpy as np
import onnxruntime as ort
import torch

from model import 숫자인식CNN

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
# 웹 페이지가 쓰는 파일이므로 web_version 폴더에 저장합니다.
저장경로 = os.path.join(os.path.dirname(프로젝트폴더), "web_version", "mnist_cnn.onnx")


def main():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()

    예시입력 = torch.zeros(1, 1, 28, 28)
    # 웹에서 한 파일만 내려받으면 되도록 가중치를 ONNX 파일 안에 함께 저장합니다.
    torch.onnx.export(모델, (예시입력,), 저장경로, input_names=["input"], output_names=["logits"],
                      opset_version=17, dynamo=False)
    print(f"ONNX 저장 완료: {저장경로} ({os.path.getsize(저장경로) / 1e6:.1f}MB)")

    # 변환 결과가 PyTorch와 같은지 확인합니다.
    무작위입력 = torch.randn(1, 1, 28, 28)
    with torch.no_grad():
        기대값 = 모델(무작위입력).numpy()
    세션 = ort.InferenceSession(저장경로)
    결과 = 세션.run(None, {"input": 무작위입력.numpy()})[0]
    print(f"PyTorch와 ONNX 출력 최대 차이: {np.abs(기대값 - 결과).max():.2e}")


if __name__ == "__main__":
    main()
