<!-- 작성: 2026-09-24 18:44 (수정: 2026-09-24 19:20 순수 자바스크립트 추론으로 변경) -->
# CLAUDE.md (web_version)

브라우저에서 손글씨 숫자를 인식하는 웹 버전입니다. **외부 라이브러리 없이 순수 자바스크립트로 추론**하며, 빌드 과정 없이 GitHub Pages에 정적 파일로 올립니다. 루트 `CLAUDE.md`의 규칙(한글 코드·주석, 한글 식별자)을 그대로 따릅니다.

## 파일

- `index.html`: 그림판 + 인식 결과 화면. 그림 → `전처리()` → `모델.추론()` → 소프트맥스 순서로 처리합니다.
- `cnn.js`: 순수 자바스크립트 추론 엔진. `숫자인식CNN.모델_불러오기()`가 같은 폴더의 가중치를 `fetch`로 받아 모델을 만들고, 합성곱(3x3, 패딩 1)·ReLU·2x2 최대풀링·완전연결을 차례로 계산합니다. 브라우저에서는 `window.숫자인식CNN`, Node.js에서는 `require`로 씁니다.
- `model_weights.json` / `model_weights.bin`: `desktop_version/export_web.py`가 만든 가중치(구조 정보 + float32 값). 배치정규화는 합성곱에 미리 합쳐져 있습니다. 직접 고치지 않습니다.

## 명령어

```bash
python desktop_version/export_web.py   # mnist_cnn.pt → model_weights.json/.bin (재학습 후 반드시 실행)
python -m http.server 8000             # 저장소 루트에서 실행 후 http://localhost:8000/ 로 확인 (file://로 열면 fetch가 막힘)
```

## 배포

- GitHub Pages는 `main` 브랜치 루트를 배포합니다. 루트 `index.html`이 이 폴더(`web_version/`)로 이동시키므로 https://dkstjdus123.github.io/Study01_MNIST/ 로 들어오면 이 페이지가 열립니다.
- 이 폴더 이름이나 위치를 바꾸면 루트 `index.html`의 이동 경로도 함께 고칩니다.

## 주의

- 외부 CDN·라이브러리를 추가하지 않습니다. 필요한 계산은 `cnn.js`에 직접 구현합니다.
- 모델 구조(`desktop_version/model.py`)를 바꾸면 `export_web.py`의 층 변환과 `cnn.js`의 층 계산도 함께 맞춰야 합니다.
- 페이지 맨 위 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다 (루트 `index.html`에도 있습니다).
- `index.html`의 `전처리()`는 `desktop_version/app.py`의 `전처리()`와 같은 과정(글씨 영역 자르기 → 긴 변 20px → 28x28 가운데 배치 → 무게중심 (14, 14) → 정규화)입니다. 한쪽을 고치면 다른 쪽도 맞춥니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 학습 때와 같아야 합니다.
- 검증: MNIST 테스트 이미지를 280x280으로 키워 그림판에 그린 뒤 `전처리()` → `모델.추론()` 정확도를 확인합니다 (측정값 496/500). `cnn.js`는 Node.js에서 PyTorch 로짓과 비교해 확인합니다 (2000장 예측 일치, 최대 차이 약 1e-5).
