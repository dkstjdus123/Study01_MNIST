<!-- 작성: 2026-09-24 18:44 (수정: 2026-09-24 19:25 웹 버전용 스크립트 2개 추가) -->
# CLAUDE.md (desktop_version)

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 손글씨 숫자를 인식하는 데스크톱 버전입니다. 웹 버전에 필요한 가중치·검증 데이터도 여기서 만듭니다. 루트 `CLAUDE.md`의 공통 규칙을 따릅니다.

## 파일

| 파일 | 역할 |
|---|---|
| `model.py` | `숫자인식CNN` 정의 (합성곱 4개 + 배치정규화, 전결합 2개) |
| `train.py` | 학습. MNIST를 `desktop_version/data`에 내려받아 5에폭 학습, 최고 정확도일 때 `mnist_cnn.pt` 저장 |
| `app.py` | tkinter 그림판 앱. `전처리()`, 정규화 상수, `모델_불러오기()`를 다른 스크립트도 가져다 씁니다 |
| `make_shortcut.py` | `app_icon.ico` 생성 + 바탕 화면 바로가기 (`pywin32` 필요) |
| `mnist_cnn.pt` | 학습된 가중치 (이름 고정) |
| `가중치내보내기.py` | 웹 버전용. `mnist_cnn.pt` → `web_version/가중치.bin` + `가중치정보.json` (배치정규화를 합성곱에 합치고, 정규화 상수는 `app.py`에서 읽음) |
| `검증데이터만들기.py` | 웹 버전용. MNIST 테스트 이미지를 280x280으로 키워 `app.py`의 `전처리()` → 모델 결과를 `web_version/검증데이터.*`로 저장 |

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전 (`torch`, `torchvision`, `pillow`, `numpy`). 테스트·린트 설정은 없습니다. 모든 스크립트는 `__file__` 기준 경로를 쓰므로 어느 폴더에서 실행해도 됩니다.

```bash
python desktop_version/train.py              # 학습 (CPU에서 10분 이상, 백그라운드로 실행)
python desktop_version/app.py                # 그림판 GUI (mnist_cnn.pt 필요)
python desktop_version/가중치내보내기.py      # 재학습 후 반드시 실행해야 웹에 반영됨
python desktop_version/검증데이터만들기.py    # 인자로 장수 지정 가능 (기본 200)
python desktop_version/make_shortcut.py
```

- 콘솔에 한글이 깨지면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- `make_shortcut.py`는 `app.py`의 `앱ID`(AppUserModelID)를 가져와 바로가기에 넣으므로 두 값이 같아야 합니다. 폴더를 옮기면 다시 실행해야 합니다.
- `app.py`는 탐색기 더블클릭 실행을 지원합니다. 그래서 가중치는 `__file__` 기준 절대 경로로 찾고, 오류는 대화상자(`오류창_띄우기`)로 보여 주며, 더블클릭으로 생긴 콘솔 창은 `콘솔창_숨기기`가 숨깁니다. 이 동작을 깨지 않도록 유지합니다.
- `가중치내보내기.py`, `검증데이터만들기.py`, `make_shortcut.py`는 `app.py`를 import하므로 `app.py`의 이름(`전처리`, `평균`, `표준편차`, `모델_불러오기`, `캔버스크기`, `앱ID` 등)을 바꾸면 함께 고칩니다.

## 구조와 주의

- 모델 구조를 바꾸면 기존 `mnist_cnn.pt`를 불러올 수 없으므로 다시 학습해야 합니다. 웹용 변환(`가중치내보내기.py`)은 3x3·패딩 1 합성곱 + 배치정규화, ReLU, 최대풀링, 전결합만 지원하므로 `web_version/모델.js`도 함께 맞춥니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`와 `app.py`에 **각각 따로** 정의되어 있으므로 반드시 같게 유지합니다.
- `app.py`의 `전처리()`가 인식률을 좌우합니다: 글씨 영역 자르기 → 긴 변 20px(LANCZOS) → 28x28 가운데 배치 → 무게중심 (14, 14) → 정규화. 그림판은 검은 배경에 흰 글씨입니다. `web_version/전처리.js`에 같은 과정이 있으므로 함께 맞추고 `web_version/검증.html`로 확인합니다.
