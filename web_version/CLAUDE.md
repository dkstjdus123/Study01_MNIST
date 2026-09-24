# CLAUDE.md (web_version)

`desktop_version`에서 학습한 CNN을 브라우저에서 그대로 실행하는 정적 웹 페이지입니다. **외부 라이브러리(onnxruntime-web, tensorflow.js 등)를 쓰지 않고 순수 자바스크립트로 추론**하며, 빌드 단계 없이 파일을 그대로 GitHub Pages에 올려 동작합니다. 공통 규칙은 상위 `../CLAUDE.md`를 참고하세요.

## 파일 구성

- `index.html` — 그림판 UI (검은 캔버스에 흰 글씨, `desktop_version/app.py`의 그림판과 같은 극성). 맨 위 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다.
- `app.js` — 캔버스 그리기, `desktop_version/app.py`의 `전처리()`와 같은 순서(잘라내기 → 20px로 축소 → 28x28 가운데 배치 → 무게중심 이동 → 정규화)를 재구현한 전처리, 결과/확률 막대 표시.
- `model.js` — 순수 자바스크립트 CNN 순전파(`추론()`). `desktop_version/model.py`의 `숫자인식CNN`과 **완전히 같은 층 구조**(Conv→BatchNorm→ReLU ×2 → MaxPool, 1→32→32채널 뒤 32→64→64채널 → Flatten → Linear(3136,256) → ReLU → Linear(256,10))를 합성곱·배치정규화·최대풀링·완전연결을 손으로 구현해 계산합니다. 외부 라이브러리를 쓰지 않으므로 속도가 느려도 정확도를 우선합니다.
- `weights.js` — `desktop_version/export_web_weights.py`가 `mnist_cnn.pt`로부터 자동 생성하는 가중치 데이터(JSON을 담은 `const 가중치 = {...}`). **직접 수정하지 않습니다.** 재학습했다면 `export_web_weights.py`를 다시 실행해서 갱신해야 합니다.

`index.html`은 `weights.js` → `model.js` → `app.js` 순서로 스크립트를 불러옵니다. `<script>` 태그만 쓰므로 로컬에서 `index.html`을 파일로 직접 열어도 동작합니다(별도 서버 불필요).

## 모델 구조를 바꿀 때

`model.py`(학습 구조), `model.js`(순전파 재구현), `export_web_weights.py`(가중치 이름 매핑) 세 곳을 함께 고쳐야 합니다. 하나라도 어긋나면 `weights.js`의 배열 형태와 `model.js`가 기대하는 형태가 맞지 않아 오류가 나거나 엉뚱한 결과가 나옵니다.

## 검증 방법

Node.js로 `weights.js` + `model.js`를 불러와 같은 입력을 PyTorch 모델과 웹 버전 양쪽에 넣고 확률 출력을 비교하면(무작위 입력 기준 오차 1e-7 수준) 두 구현이 같은 계산을 하는지 확인할 수 있습니다. 브라우저에서는 Playwright 등으로 캔버스에 그림을 그려 추론 결과를 확인합니다.

## GitHub Pages 배포

`../.github/workflows/deploy-pages.yml`이 `main` 브랜치에서 이 폴더가 바뀔 때마다 GitHub Pages로 자동 배포합니다. GitHub Pages는 저장소 루트나 `/docs`만 기본 지원해서 임의 폴더(`web_version`)를 그대로 배포할 수 없으므로, GitHub Actions로 이 폴더만 골라 올리는 방식을 씁니다. 저장소 Settings → Pages → Source를 **GitHub Actions**로 한 번 설정해야 동작합니다.
