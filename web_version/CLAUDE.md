<!-- 작성: 2026-09-24 18:33 -->
# CLAUDE.md (web_version)

브라우저에서 손글씨 숫자를 인식하는 정적 웹 페이지입니다. **외부 라이브러리(onnxruntime, TensorFlow.js, CDN 등) 없이** 순수 자바스크립트로 CNN을 추론하며, 빌드 과정 없이 GitHub Pages에 그대로 올립니다. 저장소 전체 규칙(한글 코드·주석, 작성 시각 주석)은 루트 `CLAUDE.md`를 따릅니다.

## 파일

- `index.html`: 그림판 UI. `<script type="module">`로 아래 두 모듈을 불러옵니다. 페이지 맨 위의 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다.
- `inference.js`: `가중치_해석()`, `모델_불러오기()`(fetch), `추론()`(합성곱3x3+ReLU ×2 → 최대풀링 → ×2 → 최대풀링 → 완전연결 256 → 10), `소프트맥스()`. 특징맵은 CHW 순서 `Float32Array`입니다.
- `preprocess.js`: `전처리(회색조, 가로, 세로)`. `desktop_version/app.py`의 `전처리()`를 캔버스 기능 없이 그대로 옮긴 것으로, Pillow의 LANCZOS 크기 조절(22비트 고정소수점 계수, 가로→세로 순서)과 파이썬식 반올림까지 재현합니다. 그래서 Node에서도 테스트할 수 있습니다. 한쪽을 고치면 다른 쪽도 맞춥니다.
- `mnist_weights.bin` / `mnist_weights.json`: 배치정규화를 합친 float32 가중치와 텐서 목록(이름·형태·오프셋). **직접 고치지 말고** `desktop_version/export_web_weights.py`로 다시 만듭니다.
- `tests/web.test.js`, `tests/reference.json`: Node 내장 테스트. `reference.json`도 변환 스크립트가 만듭니다.
- `package.json`: 의존성 없음. `"type": "module"`과 테스트 명령만 있습니다.

## 명령어

```bash
node --test                        # web_version 폴더에서 실행 (Node 18 이상, 설치할 것 없음). npm test도 같음
python -m http.server 8000         # 저장소 루트에서 실행 후 http://localhost:8000/web_version/ 접속
```

- 테스트 내용: PyTorch 출력과 로짓 비교(오차 1e-3 이내), 소프트맥스, 빈 그림, 전처리 크기·무게중심, MNIST 테스트 500장 인식률(≥485, 측정값 497/500).
- MNIST 인식률 테스트는 `desktop_version/data/MNIST/raw/`가 있을 때만 돌고, 없으면 건너뜁니다 (`python desktop_version/train.py`를 한 번 실행하면 생김). 500장에 약 25초 걸립니다.
- `index.html`을 파일로 바로 열면(`file://`) `fetch`와 모듈이 막혀 가중치를 불러오지 못합니다. 반드시 HTTP 서버로 엽니다.

## 배포

GitHub Pages(`main` 브랜치 루트)로 배포되어 https://dkstjdus123.github.io/Study01_MNIST/web_version/ 에서 열립니다. 루트 `index.html`이 기존 주소(https://dkstjdus123.github.io/Study01_MNIST/)로 들어온 사람을 이 폴더로 옮겨 줍니다. 모든 경로는 상대 경로(`./inference.js`, `./mnist_weights.bin`)이므로 폴더 이름을 바꿔도 동작합니다.
