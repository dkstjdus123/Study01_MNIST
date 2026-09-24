<!-- 작성: 2026-09-24 21:10 -->
# 손글씨 숫자 인식기 (데스크톱 버전)

MNIST로 학습한 CNN(합성곱 신경망)이 그림판에 마우스로 쓴 숫자 0~9를 실시간으로 인식하는 프로그램입니다.

## 파일 구성

| 파일 | 하는 일 |
|---|---|
| `model.py` | 모델 구조(`숫자인식CNN`) 정의 |
| `train.py` | MNIST를 내려받아 5에폭 학습하고 `mnist_cnn.pt`로 저장 |
| `app.py` | tkinter 그림판 앱. 그린 숫자를 전처리해 인식 결과와 확률을 보여 줌 |
| `mnist_cnn.pt` | 학습된 가중치 (MNIST 테스트 정확도 99.39%) |
| `make_shortcut.py` | 바탕 화면에 "손글씨 숫자 인식기" 바로가기를 만듦 (검은 창 없이 실행, 아이콘, 작업 표시줄 고정) |
| `가중치내보내기.py`, `검증데이터만들기.py` | 웹 버전(`../web_version/`)에 쓸 가중치와 검증 데이터를 만듦 |

## 실행 방법 (Windows PowerShell)

1. 필요한 라이브러리를 설치합니다.
   ```
   python -m pip install torch torchvision pillow numpy
   ```
2. 그림판 앱을 실행합니다. `app.py`를 탐색기에서 더블클릭해도 됩니다.
   ```
   python app.py
   ```
3. (선택) 바탕 화면 바로가기를 만듭니다.
   ```
   python -m pip install pywin32
   python make_shortcut.py
   ```
   바탕 화면의 "손글씨 숫자 인식기"를 우클릭 → (추가 옵션 표시) → 작업 표시줄에 고정을 누르면 작업 표시줄에 넣을 수 있습니다.

## 다시 학습하기

`train.py`는 반드시 이 폴더 안에서 실행합니다. 데이터(`./data`)와 가중치(`mnist_cnn.pt`)를 현재 폴더 기준으로 저장하기 때문입니다.

```
cd desktop_version
python train.py
```

다시 학습한 뒤에는 `python 가중치내보내기.py`를 실행해 웹 버전 가중치도 새로 만듭니다.
