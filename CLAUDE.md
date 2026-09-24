<!-- 작성: 2026-09-24 19:25 (두 버전 안내 + 공통 규칙으로 다시 씀) -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

MNIST로 학습한 CNN으로 마우스(또는 터치)로 쓴 손글씨 숫자를 인식하는 학습용 프로젝트입니다. 같은 모델을 두 버전으로 나란히 둡니다.

| 폴더 | 내용 | 자세한 안내 |
|---|---|---|
| `desktop_version/` | PyTorch 학습 + tkinter 그림판 앱 (Windows), 웹용 가중치 내보내기·검증 데이터 스크립트 | `desktop_version/CLAUDE.md` |
| `web_version/` | 외부 라이브러리 없이 순수 자바스크립트로 추론하는 웹 앱 (GitHub Pages 정적 배포) | `web_version/CLAUDE.md` |

- 루트 `index.html`: GitHub Pages(`main` 브랜치 루트)로 들어온 방문자를 `web_version/`으로 이동시킵니다. 배포 주소: https://dkstjdus123.github.io/Study01_MNIST/
- `CLAUDE_전역.md`: 전역 CLAUDE.md 사본 (과제 제출물이므로 지우지 않습니다).

## 공통 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 사용합니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- 새로 만드는 파일은 맨 위에 작성 시각을 주석으로 적습니다 (`CLAUDE_전역.md` 참고).
- 학습된 가중치 파일 이름은 `desktop_version/mnist_cnn.pt`로 고정입니다.
- 파일을 옮길 때는 `git mv`를 써서 커밋 이력을 유지합니다.
- 페이지 맨 위 "학번 2601953 이름 안서연" 표시줄(`web_version/index.html`, `web_version/검증.html`, 루트 `index.html`)은 과제 요구사항이므로 지우지 않습니다.

## 두 버전을 함께 맞춰야 하는 것

- **전처리**: `desktop_version/app.py`의 `전처리()`와 `web_version/전처리.js`는 같은 과정(글씨 영역 자르기 → 긴 변 20px LANCZOS 축소 → 28x28 가운데 배치 → 무게중심 (14, 14) → 정규화)입니다. 한쪽을 고치면 다른 쪽도 고치고 `검증.html`로 확인합니다.
- **정규화 상수**(`평균=0.1307`, `표준편차=0.3081`): `train.py`와 `app.py`에 각각 정의되어 있으므로 같게 유지합니다. 웹은 `가중치내보내기.py`가 `app.py`에서 읽어 `가중치정보.json`에 넣은 값을 쓰므로 자바스크립트에는 적지 않습니다.
- **모델 구조**(`desktop_version/model.py`)를 바꾸면: 재학습 → `가중치내보내기.py` 다시 실행, 필요하면 `web_version/모델.js`의 층 계산도 맞춥니다.

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전. 테스트·린트 설정은 없습니다.

```bash
python desktop_version/train.py              # 학습 → desktop_version/mnist_cnn.pt (오래 걸리므로 백그라운드로)
python desktop_version/app.py                # 데스크톱 그림판 앱
python desktop_version/가중치내보내기.py      # web_version/가중치.bin + 가중치정보.json (재학습 후 반드시 실행)
python desktop_version/검증데이터만들기.py    # web_version/검증데이터.* (저장소에 올리지 않음)
python -m http.server 8000                   # 저장소 루트에서 → http://localhost:8000/ (웹 앱), /web_version/검증.html (검증)
```
