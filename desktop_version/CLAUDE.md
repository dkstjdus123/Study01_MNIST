<!-- 작성: 2026-09-24 18:44 (수정: 2026-09-24 19:39 파일 연결 관계, 가중치 내보내기, 검증 데이터 추가) -->
# CLAUDE.md (desktop_version)

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 손글씨 숫자를 실시간으로 인식하는 데스크톱 버전입니다. 웹 버전에 필요한 가중치·검증 데이터도 여기서 만듭니다. 루트 `CLAUDE.md`의 공통 규칙을 따릅니다.

## 환경 제약

- Windows, Python 3.13, PyTorch **CPU** 버전 (`torch`, `torchvision`, `pillow`, `numpy`). 테스트·린트 설정은 없습니다.
- 콘솔에 한글이 깨지거나 인코딩 오류가 나면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- 학습된 가중치 파일 이름은 `mnist_cnn.pt`로 고정입니다.
- 모든 스크립트는 `__file__` 기준 경로를 쓰므로 어느 폴더에서 실행해도 됩니다.

## 실행 방식

```bash
python desktop_version/train.py              # MNIST 다운로드(desktop_version/data) 후 5에폭 학습, 최고 정확도일 때 mnist_cnn.pt 저장 (CPU에서 10분 이상 → 백그라운드로)
python desktop_version/app.py                # 그림판 GUI (mnist_cnn.pt 필요)
python desktop_version/가중치내보내기.py      # web_version/가중치.bin + 가중치정보.json (재학습 후 반드시 실행)
python desktop_version/검증데이터만들기.py    # web_version/검증데이터.json/.bin (장수 인자, 기본 200)
python desktop_version/make_shortcut.py      # app_icon.ico + 바탕 화면 "손글씨 숫자 인식기.lnk" (pywin32 필요)
```

- `app.py`는 탐색기 **더블클릭 실행**도 지원합니다 (`.py`는 Microsoft Store Python 3.13에 연결됨). 그래서 가중치는 `__file__` 기준 절대 경로로 찾고, 오류는 `print` 대신 대화상자(`오류창_띄우기`)로 보여 주며, 더블클릭으로 생긴 콘솔 창은 `콘솔창_숨기기`가 숨깁니다. 이 동작을 깨지 않도록 유지합니다.
- 바로가기는 `.py` 연결과 무관하게 `sys.executable` 옆의 `pythonw.exe`로 `app.py`를 실행합니다. `app.py`의 `앱ID`(AppUserModelID)를 바로가기에 넣으므로, 작업 표시줄 고정 시 실행 창과 묶이려면 두 값이 같아야 합니다. 폴더를 옮기면 다시 실행해야 합니다.

## 파일 4개의 연결 관계

```
model.py ──(숫자인식CNN)──▶ train.py ──(학습)──▶ mnist_cnn.pt
    │                                               │
    └──────────(숫자인식CNN)──▶ app.py ◀──(불러오기)──┘
                                 │  전처리(), 평균·표준편차, 모델_불러오기(), 캔버스크기, 앱ID
                                 ▼
                make_shortcut.py (앱ID, 아이콘경로) / 가중치내보내기.py / 검증데이터만들기.py
```

- `model.py`의 `숫자인식CNN`을 `train.py`(학습)와 `app.py`(추론)가 함께 씁니다. 모델 구조를 바꾸면 `state_dict` 키가 달라져 기존 `mnist_cnn.pt`를 불러올 수 없으므로 다시 학습해야 합니다.
- `app.py`는 다른 스크립트들이 import하는 중심입니다. `전처리`, `평균`, `표준편차`, `모델_불러오기`, `캔버스크기`, `앱ID`, `아이콘경로`의 이름을 바꾸면 import하는 쪽도 고칩니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`와 `app.py`에 **각각 따로** 정의되어 있으므로 반드시 같게 유지합니다.
- `app.py`의 `전처리()`가 인식률을 좌우합니다: 글씨 영역 자르기 → 비율 유지하며 긴 변 20px(LANCZOS) → 28x28 가운데 배치 → 무게중심을 (14, 14)로 이동 → 정규화. 그림판은 검은 배경에 흰 글씨(MNIST와 같은 극성)이며, 화면 캔버스와 PIL 이미지에 동시에 그립니다.

## 가중치 내보내기 (`가중치내보내기.py`)

- `mnist_cnn.pt`를 읽어 `web_version/가중치.bin`(float32 리틀 엔디언 텐서 12개)과 `web_version/가중치정보.json`(층 순서, 텐서 이름·형상·오프셋, 정규화 상수)을 만듭니다.
- 배치정규화는 바로 앞 합성곱의 가중치·편향에 합쳐서 내보냅니다. 드롭아웃·펼치기는 추론 때 할 일이 없어 건너뜁니다.
- 정규화 상수는 `app.py`에서 읽어 정보 파일에 넣으므로 웹 쪽에 따로 적지 않습니다.
- 3x3·패딩 1·보폭 1 합성곱, ReLU, 2x2 최대풀링, 전결합만 지원합니다 (`web_version/모델.js`와 같음). 실행하면 합친 결과와 원래 모델의 차이를 출력합니다 (측정값 약 2e-6).

## 검증 데이터 만들기 (`검증데이터만들기.py`)

- 280x280(그림판 크기) 그림을 `app.py`의 `전처리()` → 모델에 넣고, 종류·그림·정답·전처리 결과·점수를 `web_version/검증데이터.json/.bin`으로 저장합니다.
- 표본 편향을 막으려고 세 종류를 섞습니다: MNIST 10배 확대(50장), 60~280px 임의 크기·위치의 MNIST(150장, 30%는 캔버스 가장자리에 붙임), `app.py` 그림판과 같은 방식(PIL 선 + 원, 펜 18)으로 0~9 획을 그린 것(30장). 난수는 고정(`random.Random(0)`)이라 매번 같은 데이터가 나옵니다.
- 크기가 크고(약 18MB) 언제든 다시 만들 수 있으므로 `.gitignore`로 저장소에서 뺍니다.
- 이 데이터로 `web_version/검증.html`이 웹 버전을 파이썬과 대조합니다. 파이썬 정확도 측정값: 230/230 (이전 앱 경로 측정 497/500).
