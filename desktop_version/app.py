# 작성: 2026-09-24 23:33
"""마우스로 그린 숫자를 학습된 CNN이 인식하는 그림판 앱입니다.

실행: python app.py  (탐색기에서 더블클릭해도 됩니다)
다른 스크립트(가중치내보내기.py, 검증데이터만들기.py, make_shortcut.py)가 이 파일의
전처리(), 모델_불러오기(), 상수들을 가져다 씁니다. import해도 창은 뜨지 않습니다.
"""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox

# 어느 폴더에서 실행하든(더블클릭 포함) 이 파일 옆의 파일을 찾도록 절대 경로를 씁니다.
프로젝트폴더 = os.path.dirname(os.path.abspath(__file__))
가중치경로 = os.path.join(프로젝트폴더, "mnist_cnn.pt")
아이콘경로 = os.path.join(프로젝트폴더, "app_icon.ico")
앱ID = "Study01.MNIST.SonGeulssiInsikGi"   # 작업 표시줄 묶음용 (make_shortcut.py와 같은 값)
캔버스크기 = 280
펜두께 = 18
평균, 표준편차 = 0.1307, 0.3081          # train.py와 같은 값


def 오류창_띄우기(메시지):
    """더블클릭으로 실행하면 콘솔 출력이 보이지 않으므로 오류를 대화상자로 알립니다."""
    창 = tk.Tk()
    창.withdraw()
    messagebox.showerror("손글씨 숫자 인식기", 메시지)
    창.destroy()


try:
    import numpy as np
    import torch
    from PIL import Image, ImageDraw

    from model import 숫자인식CNN
except ImportError as 오류:
    if __name__ != "__main__":
        raise
    오류창_띄우기(f"필요한 라이브러리를 불러오지 못했습니다.\n\n{오류}\n\n"
                  "설치 명령: python -m pip install torch torchvision pillow numpy")
    sys.exit(1)


def 모델_불러오기():
    """저장된 가중치로 추론용(eval) 모델을 만듭니다."""
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치경로, map_location="cpu", weights_only=True))
    모델.eval()
    return 모델


def 전처리(그림):
    """그림판 그림(흑백, 검은 배경에 흰 글씨)을 MNIST 형식 입력 (1, 1, 28, 28)로 바꿉니다. 빈 그림이면 None.

    1) 여백 제거 → 2) 긴 변을 20px로 비율 유지 축소(LANCZOS)해 28x28 가운데에 놓기
    → 3) 밝기 무게중심을 (14, 14)로 옮긴 뒤 정규화. web_version/전처리.js가 같은 계산을 합니다.
    """
    배열 = np.asarray(그림)
    행, 열 = np.nonzero(배열)
    if len(행) == 0:
        return None
    잘린그림 = 그림.crop((int(열.min()), int(행.min()), int(열.max()) + 1, int(행.max()) + 1))

    가로, 세로 = 잘린그림.size
    배율 = 20.0 / max(가로, 세로)
    새가로, 새세로 = max(1, round(가로 * 배율)), max(1, round(세로 * 배율))
    작은그림 = 잘린그림.resize((새가로, 새세로), Image.LANCZOS)
    결과 = Image.new("L", (28, 28), 0)
    결과.paste(작은그림, ((28 - 새가로) // 2, (28 - 새세로) // 2))

    밝기 = np.asarray(결과, dtype=np.float64)
    전체 = 밝기.sum()
    if 전체 == 0:
        return None
    y좌표, x좌표 = np.indices(밝기.shape)
    이동x = round(14 - (x좌표 * 밝기).sum() / 전체)     # .5는 짝수 쪽으로 반올림 (파이썬 round)
    이동y = round(14 - (y좌표 * 밝기).sum() / 전체)
    결과 = 결과.transform((28, 28), Image.AFFINE, (1, 0, -이동x, 0, 1, -이동y), fill=0)

    텐서 = torch.from_numpy(np.asarray(결과, dtype=np.float32) / 255.0)
    return ((텐서 - 평균) / 표준편차).reshape(1, 1, 28, 28)


class 손글씨인식앱:
    """왼쪽 그림판 + 오른쪽 결과(예측 숫자, 신뢰도, 0~9 확률 막대)"""

    def __init__(self, 루트, 모델):
        self.모델 = 모델
        self.이전점 = None
        루트.title("손글씨 숫자 인식기")
        루트.resizable(False, False)

        왼쪽 = tk.Frame(루트, padx=12, pady=12)
        왼쪽.pack(side="left")
        self.캔버스 = tk.Canvas(왼쪽, width=캔버스크기, height=캔버스크기, bg="black",
                               highlightthickness=0, cursor="pencil")
        self.캔버스.pack()
        tk.Button(왼쪽, text="지우기", width=12, command=self.지우기).pack(pady=(8, 0))

        오른쪽 = tk.Frame(루트, padx=12, pady=12)
        오른쪽.pack(side="left", fill="y")
        self.예측표시 = tk.Label(오른쪽, text="?", font=("맑은 고딕", 48, "bold"))
        self.예측표시.pack()
        self.신뢰도표시 = tk.Label(오른쪽, text="숫자를 그려 보세요")
        self.신뢰도표시.pack(pady=(0, 8))
        self.막대판 = tk.Canvas(오른쪽, width=230, height=220, highlightthickness=0)
        self.막대판.pack()

        # 화면 캔버스와 같은 그림을 PIL 이미지에도 그려 두고 인식에 씁니다.
        self.그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
        self.붓 = ImageDraw.Draw(self.그림)
        self.캔버스.bind("<ButtonPress-1>", self.누르기)
        self.캔버스.bind("<B1-Motion>", self.끌기)
        self.캔버스.bind("<ButtonRelease-1>", self.떼기)
        self.막대_그리기(np.zeros(10))

    def 점_찍기(self, x, y):
        반 = 펜두께 / 2
        self.캔버스.create_oval(x - 반, y - 반, x + 반, y + 반, fill="white", outline="white")
        self.붓.ellipse((x - 반, y - 반, x + 반, y + 반), fill=255)

    def 누르기(self, 이벤트):
        self.이전점 = (이벤트.x, 이벤트.y)
        self.점_찍기(이벤트.x, 이벤트.y)

    def 끌기(self, 이벤트):
        x, y = 이벤트.x, 이벤트.y
        if self.이전점:
            self.캔버스.create_line(*self.이전점, x, y, fill="white", width=펜두께, capstyle="round")
            self.붓.line((*self.이전점, x, y), fill=255, width=펜두께)
        self.점_찍기(x, y)
        self.이전점 = (x, y)

    def 떼기(self, 이벤트):
        self.이전점 = None
        self.인식하기()

    def 인식하기(self):
        입력 = 전처리(self.그림)
        if 입력 is None:
            return
        with torch.no_grad():
            확률 = torch.softmax(self.모델(입력), dim=1)[0].numpy()
        예측 = int(확률.argmax())
        self.예측표시.config(text=str(예측))
        self.신뢰도표시.config(text=f"신뢰도 {확률[예측] * 100:.1f}%")
        self.막대_그리기(확률)

    def 막대_그리기(self, 확률):
        self.막대판.delete("all")
        최대 = int(np.argmax(확률)) if 확률.max() > 0 else -1
        for 숫자, p in enumerate(확률):
            y = 숫자 * 22
            self.막대판.create_text(8, y + 10, text=str(숫자))
            self.막대판.create_rectangle(22, y + 3, 172, y + 17, outline="#cccccc")
            self.막대판.create_rectangle(22, y + 3, 22 + 150 * float(p), y + 17, width=0,
                                        fill="#2e7d32" if 숫자 == 최대 else "#90a4ae")
            self.막대판.create_text(228, y + 10, text=f"{p * 100:.1f}%", anchor="e")

    def 지우기(self):
        self.캔버스.delete("all")
        self.붓.rectangle((0, 0, 캔버스크기, 캔버스크기), fill=0)
        self.예측표시.config(text="?")
        self.신뢰도표시.config(text="숫자를 그려 보세요")
        self.막대_그리기(np.zeros(10))


def 콘솔창_숨기기():
    """탐색기에서 더블클릭하면 함께 뜨는 검은 콘솔 창을 숨깁니다. 터미널에서 실행했으면 그대로 둡니다."""
    if sys.platform != "win32":
        return
    커널 = ctypes.windll.kernel32
    창 = 커널.GetConsoleWindow()
    목록 = (ctypes.c_uint * 4)()
    if 창 and 커널.GetConsoleProcessList(목록, 4) == 1:   # 이 프로그램 혼자 쓰는 콘솔 = 더블클릭으로 생긴 창
        ctypes.windll.user32.ShowWindow(창, 0)


def main():
    콘솔창_숨기기()
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(앱ID)
    try:
        모델 = 모델_불러오기()
    except FileNotFoundError:
        오류창_띄우기(f"가중치 파일이 없습니다.\n{가중치경로}\n\n먼저 python train.py 로 학습해 주세요.")
        return
    루트 = tk.Tk()
    if sys.platform == "win32" and os.path.exists(아이콘경로):
        루트.iconbitmap(default=아이콘경로)
    손글씨인식앱(루트, 모델)
    루트.mainloop()


if __name__ == "__main__":
    main()
