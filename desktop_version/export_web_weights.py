# -*- coding: utf-8 -*-
# 작성: 2026-09-24 17:50 KST
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전(web_version)이 순수 자바스크립트로 읽을 수 있는
weights.js 파일로 변환합니다. onnxruntime 같은 외부 라이브러리 없이 브라우저에서 직접
순전파를 계산하므로, model.py의 층 구조와 이름이 같은 형태로 그대로 내보냅니다.

재학습(train.py)한 뒤에는 반드시 이 스크립트를 다시 실행해야 웹 페이지에 반영됩니다.
"""

import json
import os

import torch

from model import 숫자인식CNN

프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
저장경로 = os.path.join(os.path.dirname(프로젝트폴더), "web_version", "weights.js")

# state_dict 키(예: "특징추출.0.weight") → model.js에서 쓰는 이름(예: "conv1_w")으로 매핑합니다.
이름_매핑 = {
    "특징추출.0.weight": "conv1_w", "특징추출.0.bias": "conv1_b",
    "특징추출.1.weight": "bn1_gamma", "특징추출.1.bias": "bn1_beta",
    "특징추출.1.running_mean": "bn1_mean", "특징추출.1.running_var": "bn1_var",

    "특징추출.3.weight": "conv2_w", "특징추출.3.bias": "conv2_b",
    "특징추출.4.weight": "bn2_gamma", "특징추출.4.bias": "bn2_beta",
    "특징추출.4.running_mean": "bn2_mean", "특징추출.4.running_var": "bn2_var",

    "특징추출.8.weight": "conv3_w", "특징추출.8.bias": "conv3_b",
    "특징추출.9.weight": "bn3_gamma", "특징추출.9.bias": "bn3_beta",
    "특징추출.9.running_mean": "bn3_mean", "특징추출.9.running_var": "bn3_var",

    "특징추출.11.weight": "conv4_w", "특징추출.11.bias": "conv4_b",
    "특징추출.12.weight": "bn4_gamma", "특징추출.12.bias": "bn4_beta",
    "특징추출.12.running_mean": "bn4_mean", "특징추출.12.running_var": "bn4_var",

    "분류기.1.weight": "fc1_w", "분류기.1.bias": "fc1_b",
    "분류기.4.weight": "fc2_w", "분류기.4.bias": "fc2_b",
}


def 반올림(값):
    """float32는 유효자리가 7자리 정도이므로, JSON 파일 용량을 줄이기 위해 소수점 6자리로 반올림합니다."""
    if isinstance(값, list):
        return [반올림(항목) for 항목 in 값]
    return round(값, 6)


def main():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()

    상태사전 = 모델.state_dict()
    가중치 = {}
    for 원래이름, 새이름 in 이름_매핑.items():
        가중치[새이름] = 반올림(상태사전[원래이름].tolist())
    가중치["bn_eps"] = 1e-5  # nn.BatchNorm2d 기본값, model.js의 배치정규화 계산에 필요합니다.

    with open(저장경로, "w", encoding="utf-8") as 파일:
        파일.write("// 작성: 2026-09-24 17:50 KST\n")
        파일.write("// export_web_weights.py가 mnist_cnn.pt로부터 자동 생성한 파일입니다. 직접 수정하지 마세요.\n")
        파일.write("const 가중치 = ")
        json.dump(가중치, 파일, separators=(",", ":"))
        파일.write(";\n")

    용량_MB = os.path.getsize(저장경로) / 1e6
    print(f"저장 완료: {저장경로} ({용량_MB:.1f}MB)")


if __name__ == "__main__":
    main()
