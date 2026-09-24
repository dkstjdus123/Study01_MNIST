# -*- coding: utf-8 -*-
"""마우스로 숫자를 그리면 학습된 CNN이 실시간으로 인식하는 프로그램입니다."""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox


def 오류창_띄우기(메시지):
    """탐색기에서 더블클릭으로 실행하면 콘솔 출력이 바로 사라지므로 오류를 대화상자로 보여 줍니다."""
    창 = tk.Tk()
    창.withdraw()
    messagebox.showerror("손글씨 숫자 인식기", 메시지)
    창.destroy()


# 무거운 라이브러리는 설치되어 있지 않을 수 있으므로 오류를 잡아 안내합니다.
try:
    import numpy as np
    import torch
    from PIL import Image, ImageDraw

    from model import 숫자인식CNN
except ImportError as 오류:
    오류창_띄우기(f"필요한 라이브러리를 불러오지 못했습니다.\n\n{오류}\n\n"
                  "설치 명령: python -m pip install torch torchvision pillow numpy")
    sys.exit(1)

# ===== 설정 =====
# 어느 폴더에서 실행하든 이 파일과 같은 폴더의 파일을 찾도록 절대 경로로 지정합니다.
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
아이콘경로 = os.path.join(프로젝트폴더, "app_icon.ico")
# 작업 표시줄에서 이 앱을 구별하는 ID입니다. 바로가기(make_shortcut.py)에도 같은 값을 넣어야
# 고정된 아이콘과 실행 중인 창이 하나의 작업 표시줄 버튼으로 묶입니다.
앱ID = "Study01.MNIST.HandwritingRecognizer"
캔버스크기 = 280      # 그림판 크기 (픽셀)
펜두께 = 18           # 붓 굵기
평균, 표준편차 = 0.1307, 0.3081


def 모델_불러오기():
    """저장된 가중치를 불러와 추론용 모델을 준비합니다."""
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()
    return 모델


def 전처리(그림: Image.Image):
    """
    그린 그림을 MNIST 형식(28x28, 검은 배경에 흰 글씨, 가운데 정렬)으로 변환합니다.
    MNIST는 숫자를 20x20 상자에 맞춘 뒤 무게중심이 가운데 오도록 28x28에 배치하므로
    같은 방식으로 처리해야 인식률이 높아집니다.
    """
    배열 = np.array(그림)
    # 글씨가 있는 영역(0이 아닌 픽셀)만 잘라냅니다.
    행, 열 = np.nonzero(배열)
    if len(행) == 0:
        return None
    잘린그림 = 그림.crop((열.min(), 행.min(), 열.max() + 1, 행.max() + 1))

    # 가로세로 비율을 유지하면서 긴 변을 20픽셀로 맞춥니다.
    가로, 세로 = 잘린그림.size
    배율 = 20.0 / max(가로, 세로)
    새크기 = (max(1, round(가로 * 배율)), max(1, round(세로 * 배율)))
    잘린그림 = 잘린그림.resize(새크기, Image.LANCZOS)

    # 28x28 검은 배경의 가운데에 붙입니다.
    결과 = Image.new("L", (28, 28), 0)
    결과.paste(잘린그림, ((28 - 새크기[0]) // 2, (28 - 새크기[1]) // 2))

    # 무게중심이 정확히 가운데(14, 14)에 오도록 이동합니다.
    결과배열 = np.array(결과, dtype=np.float32)
    전체밝기 = 결과배열.sum()
    y좌표, x좌표 = np.indices(결과배열.shape)
    중심y = (y좌표 * 결과배열).sum() / 전체밝기
    중심x = (x좌표 * 결과배열).sum() / 전체밝기
    이동x, 이동y = round(14 - 중심x), round(14 - 중심y)
    결과 = 결과.transform((28, 28), Image.AFFINE, (1, 0, -이동x, 0, 1, -이동y), fill=0)

    # 텐서로 변환하고 학습 때와 같은 방식으로 정규화합니다.
    텐서 = torch.from_numpy(np.array(결과, dtype=np.float32) / 255.0)
    텐서 = (텐서 - 평균) / 표준편차
    return 텐서.unsqueeze(0).unsqueeze(0)   # 형태: (1, 1, 28, 28)


class 손글씨인식앱:
    """tkinter로 만든 그림판 + 인식 결과 화면"""

    def __init__(self, 루트, 모델):
        self.모델 = 모델
        self.이전좌표 = None
        루트.title("손글씨 숫자 인식기 (MNIST CNN)")
        루트.resizable(False, False)

        # 왼쪽: 그림판
        왼쪽 = tk.Frame(루트, padx=10, pady=10)
        왼쪽.pack(side=tk.LEFT)
        tk.Label(왼쪽, text="여기에 숫자(0~9)를 그려 주세요", font=("맑은 고딕", 11)).pack()
        self.캔버스 = tk.Canvas(왼쪽, width=캔버스크기, height=캔버스크기,
                               bg="black", cursor="cross")
        self.캔버스.pack(pady=5)
        tk.Button(왼쪽, text="지우기", font=("맑은 고딕", 11), width=12,
                  command=self.지우기).pack()

        # 오른쪽: 인식 결과와 확률 막대
        오른쪽 = tk.Frame(루트, padx=10, pady=10)
        오른쪽.pack(side=tk.LEFT, fill=tk.Y)
        self.결과라벨 = tk.Label(오른쪽, text="?", font=("맑은 고딕", 64, "bold"), fg="#1a73e8")
        self.결과라벨.pack()
        self.신뢰도라벨 = tk.Label(오른쪽, text="숫자를 그려 보세요", font=("맑은 고딕", 11))
        self.신뢰도라벨.pack(pady=(0, 10))
        self.막대캔버스 = tk.Canvas(오른쪽, width=220, height=200)
        self.막대캔버스.pack()

        # 화면에 보이는 캔버스와 같은 내용을 PIL 이미지에도 함께 그립니다.
        self.그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
        self.붓 = ImageDraw.Draw(self.그림)

        # 마우스 이벤트 연결
        self.캔버스.bind("<B1-Motion>", self.그리기)
        self.캔버스.bind("<ButtonRelease-1>", self.붓떼기)
        self.확률막대_그리기(np.zeros(10))

    def 그리기(self, 이벤트):
        """마우스를 끌 때마다 선을 그립니다."""
        x, y = 이벤트.x, 이벤트.y
        r = 펜두께 // 2
        if self.이전좌표:
            px, py = self.이전좌표
            self.캔버스.create_line(px, py, x, y, fill="white", width=펜두께,
                                   capstyle=tk.ROUND, smooth=True)
            self.붓.line([px, py, x, y], fill=255, width=펜두께)
        # 선 끝을 둥글게 하기 위해 원도 함께 그립니다.
        self.캔버스.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="white")
        self.붓.ellipse([x - r, y - r, x + r, y + r], fill=255)
        self.이전좌표 = (x, y)

    def 붓떼기(self, _이벤트):
        """마우스 버튼을 떼면 그린 숫자를 인식합니다."""
        self.이전좌표 = None
        self.인식하기()

    def 지우기(self):
        """그림판과 결과를 초기화합니다."""
        self.캔버스.delete("all")
        self.붓.rectangle([0, 0, 캔버스크기, 캔버스크기], fill=0)
        self.결과라벨.config(text="?")
        self.신뢰도라벨.config(text="숫자를 그려 보세요")
        self.확률막대_그리기(np.zeros(10))

    @torch.no_grad()
    def 인식하기(self):
        """전처리 → 모델 추론 → 결과 표시"""
        입력 = 전처리(self.그림)
        if 입력 is None:
            return
        확률 = torch.softmax(self.모델(입력), dim=1)[0].numpy()
        예측 = int(확률.argmax())
        self.결과라벨.config(text=str(예측))
        self.신뢰도라벨.config(text=f"신뢰도: {확률[예측] * 100:.1f}%")
        self.확률막대_그리기(확률)

    def 확률막대_그리기(self, 확률):
        """0~9 각 숫자에 대한 확률을 가로 막대로 보여 줍니다."""
        c = self.막대캔버스
        c.delete("all")
        최대 = int(확률.argmax()) if 확률.sum() > 0 else -1
        for 숫자 in range(10):
            y = 숫자 * 20 + 2
            c.create_text(10, y + 8, text=str(숫자), font=("맑은 고딕", 10))
            너비 = int(확률[숫자] * 150)
            색 = "#1a73e8" if 숫자 == 최대 else "#9aa0a6"
            c.create_rectangle(22, y + 2, 22 + 너비, y + 15, fill=색, outline="")
            c.create_text(180, y + 8, text=f"{확률[숫자] * 100:5.1f}%", font=("맑은 고딕", 9))


def 콘솔창_숨기기():
    """
    더블클릭으로 실행했을 때 뒤에 뜨는 검은 콘솔 창을 숨깁니다.
    터미널에서 실행한 경우에는 콘솔을 다른 프로세스(셸)와 함께 쓰므로 숨기지 않습니다.
    """
    if sys.platform != "win32":
        return
    커널 = ctypes.windll.kernel32
    콘솔 = 커널.GetConsoleWindow()
    프로세스목록 = (ctypes.c_uint32 * 2)()
    # 이 콘솔을 쓰는 프로세스가 나 하나뿐이면 더블클릭으로 새로 만들어진 콘솔입니다.
    if 콘솔 and 커널.GetConsoleProcessList(프로세스목록, 2) == 1:
        ctypes.windll.user32.ShowWindow(콘솔, 0)   # 0 = SW_HIDE


def main():
    콘솔창_숨기기()
    # 앱 ID는 창을 만들기 전에 지정해야 작업 표시줄에 반영됩니다.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(앱ID)
    try:
        모델 = 모델_불러오기()
    except FileNotFoundError:
        오류창_띄우기(f"가중치 파일이 없습니다.\n{가중치경로}\n\n먼저 'python train.py'로 학습해 주세요.")
        return
    루트 = tk.Tk()
    # 제목 표시줄과 작업 표시줄에 표시될 창 아이콘
    if os.path.exists(아이콘경로):
        루트.iconbitmap(default=아이콘경로)
    손글씨인식앱(루트, 모델)
    루트.mainloop()


if __name__ == "__main__":
    main()
