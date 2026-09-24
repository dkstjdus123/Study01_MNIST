<!-- 작성: 2026-09-24 18:44 -->
# CLAUDE.md (desktop_version)

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 손글씨 숫자를 인식하는 데스크톱 버전입니다. 루트 `CLAUDE.md`의 규칙(한글 코드·주석, 한글 식별자, 가중치 파일 이름 `mnist_cnn.pt` 고정)을 그대로 따릅니다.

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전 (`torch`, `torchvision`, `pillow`, `numpy`). 테스트·린트 설정은 없습니다. 모든 스크립트는 `__file__` 기준 경로를 쓰므로 어느 폴더에서 실행해도 됩니다.

```bash
python desktop_version/train.py        # MNIST 다운로드(desktop_version/data) 후 5에폭 학습, 최고 정확도일 때 mnist_cnn.pt 저장 (CPU에서 10분 이상, 백그라운드로 실행)
python desktop_version/app.py          # 그림판 GUI 실행 (mnist_cnn.pt 필요)
python desktop_version/export_onnx.py  # mnist_cnn.pt → web_version/mnist_cnn.onnx 변환 (재학습 후 반드시 실행)
python desktop_version/make_shortcut.py  # app_icon.ico 생성 + 바탕 화면 바로가기 (pywin32 필요)
```

- 콘솔에 한글이 깨지면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- `make_shortcut.py`는 `app.py`의 `앱ID`(AppUserModelID)를 가져와 바로가기에 넣으므로 두 값이 같아야 합니다. 폴더를 옮기면 다시 실행해야 합니다.
- `app.py`는 탐색기 더블클릭 실행을 지원합니다. 그래서 가중치는 `__file__` 기준 절대 경로로 찾고, 오류는 대화상자(`오류창_띄우기`)로 보여 주며, 더블클릭으로 생긴 콘솔 창은 `콘솔창_숨기기`가 숨깁니다. 이 동작을 깨지 않도록 유지합니다.

## 구조

- `model.py`의 `숫자인식CNN`을 `train.py`(학습), `app.py`(추론), `export_onnx.py`(변환)가 함께 사용합니다. 모델 구조를 바꾸면 기존 `mnist_cnn.pt`를 불러올 수 없으므로 다시 학습해야 합니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`와 `app.py`에 **각각 따로** 정의되어 있으므로 반드시 같게 유지합니다.
- `app.py`의 `전처리()`가 인식률을 좌우합니다: 글씨 영역 자르기 → 긴 변 20px → 28x28 가운데 배치 → 무게중심 (14, 14) → 정규화. 그림판은 검은 배경에 흰 글씨입니다. `web_version/index.html`에 같은 과정이 JavaScript로 구현되어 있으므로 함께 맞춥니다.
- 검증 방법: MNIST 테스트 이미지를 280x280으로 키워 `전처리()` → 모델에 넣고 정확도를 확인합니다 (이전 측정값 497/500).
