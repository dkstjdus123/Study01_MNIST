<!-- 작성: 2026-09-24 18:44 -->
# CLAUDE.md (web_version)

브라우저에서 손글씨 숫자를 인식하는 웹 버전입니다. 루트 `CLAUDE.md`의 규칙(한글 코드·주석, 한글 식별자)을 그대로 따릅니다.

## 파일

- `index.html`: 그림판 + 인식 결과 화면. onnxruntime-web(CDN)으로 같은 폴더의 `mnist_cnn.onnx`를 불러와 브라우저 안에서 추론합니다. 빌드 과정은 없습니다.
- `mnist_cnn.onnx`: `desktop_version/export_onnx.py`가 만든 모델 파일입니다. 직접 고치지 않습니다. **재학습하면 `python desktop_version/export_onnx.py`를 다시 실행**해야 반영됩니다.

## 배포

- GitHub Pages는 `main` 브랜치 루트를 배포합니다. 루트의 `index.html`이 이 폴더(`web_version/`)로 이동시키므로, 공개 주소 https://dkstjdus123.github.io/Study01_MNIST/ 로 들어오면 이 페이지가 열립니다.
- 이 폴더 이름이나 위치를 바꾸면 루트 `index.html`의 이동 경로도 함께 고쳐야 합니다.
- 로컬 확인: `file://`로 열면 onnx 파일을 못 불러오므로 `python -m http.server`로 저장소 루트를 띄운 뒤 `http://localhost:8000/` 에서 확인합니다.

## 주의

- 페이지 맨 위 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다 (루트 `index.html`에도 있습니다).
- JavaScript 전처리는 `desktop_version/app.py`의 `전처리()`와 같은 과정(글씨 영역 자르기 → 긴 변 20px → 28x28 가운데 배치 → 무게중심 (14, 14) → 정규화)을 다시 구현한 것입니다. 한쪽을 고치면 다른 쪽도 맞춰야 합니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 학습 때와 같아야 합니다.
