# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 손글씨 숫자를 실시간으로 인식하는 학습용 프로젝트입니다.

## 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 사용합니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- 학습된 가중치 파일 이름은 `mnist_cnn.pt`로 고정입니다.

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전 (`torch`, `torchvision`, `pillow`, `numpy`). 테스트·린트 설정은 없습니다.

```bash
python train.py   # MNIST 다운로드(./data) 후 5에폭 학습, 최고 정확도일 때 mnist_cnn.pt 저장 (CPU에서 10분 이상)
python app.py     # 그림판 GUI 실행 (mnist_cnn.pt 필요)
```

- 콘솔에 한글이 깨지거나 인코딩 오류가 나면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- `train.py`는 오래 걸리므로 백그라운드로 실행합니다.
- `python make_shortcut.py`: `app_icon.ico`를 만들고 바탕 화면에 `손글씨 숫자 인식기.lnk`를 생성합니다 (`pywin32` 필요). 바로가기는 `.py` 연결과 무관하게 `sys.executable` 옆의 `pythonw.exe`로 `app.py`를 실행합니다. `app.py`의 `앱ID`(AppUserModelID)를 가져와 바로가기에 넣으므로, 작업 표시줄 고정 시 실행 창과 묶이려면 두 값이 같아야 합니다. 프로젝트 폴더를 옮기면 다시 실행해야 합니다.
- `python export_onnx.py`: `mnist_cnn.pt`를 웹용 `mnist_cnn.onnx`로 변환합니다. **재학습하면 반드시 다시 실행**해야 웹 페이지에 반영됩니다.
- `app.py`는 탐색기 더블클릭 실행도 지원합니다 (`.py`는 Microsoft Store Python 3.13에 연결됨). 그래서 가중치는 `__file__` 기준 절대 경로로 찾고, 오류는 `print` 대신 대화상자(`오류창_띄우기`)로 보여 주며, 더블클릭으로 생긴 콘솔 창은 `콘솔창_숨기기`가 숨깁니다. 이 동작을 깨지 않도록 유지합니다.

## 구조

- `model.py`의 `숫자인식CNN`을 `train.py`(학습)와 `app.py`(추론)가 함께 사용합니다. 모델 구조를 바꾸면 `state_dict` 키가 달라져 기존 `mnist_cnn.pt`를 불러올 수 없으므로 다시 학습해야 합니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`와 `app.py`에 **각각 따로** 정의되어 있으므로 반드시 같게 유지해야 합니다.
- `app.py`의 `전처리()`가 인식률을 좌우합니다. 그린 그림을 MNIST 형식에 맞춰 변환합니다: 글씨 영역을 잘라내고 → 비율을 유지하며 긴 변을 20px로 맞추고 → 28x28 가운데에 배치한 뒤 → 무게중심을 (14, 14)로 옮기고 → 정규화합니다. 그림판은 검은 배경에 흰 글씨(MNIST와 같은 극성)이며, 화면 캔버스와 PIL 이미지에 동시에 그립니다.
- 웹 버전 `index.html`은 GitHub Pages(`main` 브랜치 루트)로 배포됩니다: https://dkstjdus123.github.io/Study01_MNIST/ . onnxruntime-web(CDN)으로 `mnist_cnn.onnx`를 불러오며, `app.py`의 `전처리()`와 같은 과정을 JavaScript로 다시 구현했으므로 한쪽을 고치면 다른 쪽도 맞춰야 합니다. 페이지 맨 위의 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다.
- 앱 경로 검증 방법: MNIST 테스트 이미지를 280x280으로 키워 `전처리()` → 모델에 넣고 정확도를 확인합니다 (이전 측정값 497/500).
