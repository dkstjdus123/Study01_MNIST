<!-- 작성: 2026-09-25 09:31 -->
# CLAUDE.md (desktop_version)

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 숫자를 인식하는 데스크톱 버전입니다. 웹 버전이 쓰는 가중치와 검증 데이터도 여기서 만듭니다. 루트 `CLAUDE.md`의 공통 규칙을 따릅니다.

## 환경

- Windows, Python 3.13, PyTorch **CPU** (`torch`, `torchvision`, `pillow`, `numpy`). 바로가기에는 `pywin32`가 필요합니다.
- 콘솔에서 한글이 깨지면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- 모든 스크립트가 `__file__` 기준 경로를 쓰므로 어느 폴더에서 실행해도 됩니다. MNIST 원본은 `desktop_version/data/`에 내려받습니다 (git 제외).

## 실행

```bash
python desktop_version/train.py              # 5에폭 학습 → mnist_cnn.pt (CPU에서 20분 정도)
python desktop_version/app.py                # 그림판 앱 (더블클릭도 됨)
python desktop_version/make_shortcut.py      # app_icon.ico + 바탕 화면 바로가기 (Windows)
python desktop_version/가중치내보내기.py      # web_version/가중치.bin + 가중치정보.json (재학습 후 반드시)
python desktop_version/검증데이터만들기.py    # web_version/검증데이터.json/.bin (git 제외)
```

## 파일 연결 관계

- `model.py`의 `숫자인식CNN`을 `train.py`(학습)와 `app.py`(추론)가 함께 씁니다. 구조를 바꾸면 기존 `mnist_cnn.pt`를 못 읽으므로 다시 학습하고, 웹의 `모델.js`가 계산할 수 있는 층(3x3·패딩 1 합성곱 + 배치정규화, ReLU, 2x2 최대풀링, 펼치기, 전결합)인지 확인합니다.
- `app.py`가 중심입니다. `가중치내보내기.py`, `검증데이터만들기.py`, `make_shortcut.py`가 `전처리`, `모델_불러오기`, `평균`, `표준편차`, `캔버스크기`, `가중치경로`, `아이콘경로`, `앱ID`, `프로젝트폴더`를 가져다 쓰므로 이름을 바꾸면 그쪽도 고칩니다. `app.py`는 import해도 창이 뜨지 않아야 합니다.
- 정규화 상수는 `train.py`와 `app.py`에 따로 적혀 있으니 같게 유지합니다.
- `app.py` 더블클릭 실행: 오류는 대화상자로 보여 주고, 더블클릭으로 생긴 콘솔 창은 숨기며, `앱ID`로 작업 표시줄 묶음을 맞춥니다. 바로가기는 `pythonw.exe`로 실행하므로 검은 창이 없습니다.

## 가중치 내보내기

`가중치내보내기.py`는 배치정규화를 앞 합성곱에 합쳐 텐서 12개(값 870,634개)를 `가중치.bin`(float32 리틀 엔디언, 헤더 없음)에 쓰고, 층 순서·형상·위치·정규화 상수를 `가중치정보.json`에 씁니다. 마지막에 PyTorch와의 최대 차이를 출력합니다.

## 검증 데이터

`검증데이터만들기.py`는 280x280 그림 230장(MNIST 10배 50장, 크기·위치를 바꾼 MNIST 150장, 그림판 방식으로 그린 획 30장)을 `app.py`의 `전처리()`와 모델에 넣고 결과를 저장합니다. `web_version/검증.html`이 이 데이터로 자바스크립트 결과를 대조합니다.
