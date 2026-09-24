# CLAUDE.md (desktop_version)

이 폴더는 PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 손글씨 숫자를 실시간으로 인식하는 Windows용 데스크톱 앱입니다. 공통 규칙은 상위 `../CLAUDE.md`를 참고하세요.

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전 (`torch`, `torchvision`, `pillow`, `numpy`). 테스트·린트 설정은 없습니다.

```bash
python train.py                 # MNIST 다운로드(./data) 후 5에폭 학습, 최고 정확도일 때 mnist_cnn.pt 저장 (CPU에서 10분 이상)
python app.py                   # 그림판 GUI 실행 (mnist_cnn.pt 필요)
python export_web_weights.py    # mnist_cnn.pt → ../web_version/weights.js 변환 (재학습 시 반드시 다시 실행)
python make_shortcut.py         # app_icon.ico 생성 + 바탕 화면에 바로가기 생성 (pywin32 필요)
```

- 콘솔에 한글이 깨지거나 인코딩 오류가 나면 `PYTHONIOENCODING=utf-8`을 설정합니다.
- `train.py`는 오래 걸리므로 백그라운드로 실행합니다.
- `make_shortcut.py`가 만드는 바로가기는 `.py` 연결과 무관하게 `sys.executable` 옆의 `pythonw.exe`로 `app.py`를 실행합니다. `app.py`의 `앱ID`(AppUserModelID)를 가져와 바로가기에 넣으므로, 작업 표시줄 고정 시 실행 창과 묶이려면 두 값이 같아야 합니다. 프로젝트 폴더를 옮기면 다시 실행해야 합니다.
- `app.py`는 탐색기 더블클릭 실행도 지원합니다 (`.py`는 Microsoft Store Python 3.13에 연결됨). 그래서 가중치는 `__file__` 기준 절대 경로로 찾고, 오류는 `print` 대신 대화상자(`오류창_띄우기`)로 보여 주며, 더블클릭으로 생긴 콘솔 창은 `콘솔창_숨기기`가 숨깁니다. 이 동작을 깨지 않도록 유지합니다.

## 구조

- `model.py`의 `숫자인식CNN`을 `train.py`(학습), `app.py`(추론), `export_web_weights.py`(가중치 변환)가 함께 사용합니다. 층 구조: `특징추출`(Conv→BN→ReLU ×2 → MaxPool → Dropout, 1→32→32채널 뒤 32→64→64채널) → `분류기`(Flatten → Linear(3136,256) → ReLU → Dropout → Linear(256,10)). 구조를 바꾸면 `state_dict` 키가 달라져 기존 `mnist_cnn.pt`를 불러올 수 없으므로 다시 학습해야 하고, `../web_version/model.js`와 `export_web_weights.py`의 이름 매핑도 함께 고쳐야 합니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`와 `app.py`에 **각각 따로** 정의되어 있고 `../web_version/app.js`에도 같은 값이 있으므로, 셋 모두 같게 유지해야 합니다.
- `app.py`의 `전처리()`가 인식률을 좌우합니다. 그린 그림을 MNIST 형식에 맞춰 변환합니다: 글씨 영역을 잘라내고 → 비율을 유지하며 긴 변을 20px로 맞추고 → 28x28 가운데에 배치한 뒤 → 무게중심을 (14, 14)로 옮기고 → 정규화합니다. 그림판은 검은 배경에 흰 글씨(MNIST와 같은 극성)이며, 화면 캔버스와 PIL 이미지에 동시에 그립니다. `../web_version/app.js`의 `전처리()`가 같은 로직을 자바스크립트로 재구현한 것이므로 한쪽을 고치면 다른 쪽도 맞춰야 합니다.
- 앱 경로 검증 방법: MNIST 테스트 이미지를 280x280으로 키워 `전처리()` → 모델에 넣고 정확도를 확인합니다.
- 웹 버전을 위한 가중치 변환은 `export_web_weights.py`가 담당합니다. 예전에 쓰던 `export_onnx.py`/ONNX(`onnxruntime-web`)는 웹 버전이 순수 자바스크립트 추론으로 바뀌면서 더 이상 쓰지 않습니다.
