<!-- 작성: 2026-09-24 19:25 (수정: 2026-09-24 19:39 두 버전 관계와 공통 규칙만 남김) (수정: 2026-09-24 22:16 검사 폴더 안내) -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 두 버전의 관계

MNIST로 학습한 CNN 하나로 손글씨 숫자를 인식하는 프로그램을 두 버전으로 나란히 둡니다.

- `desktop_version/`: **원본**. PyTorch로 학습하고 tkinter 그림판 앱으로 인식합니다. 웹 버전에 필요한 가중치와 검증 데이터도 여기서 만듭니다. → `desktop_version/CLAUDE.md`
- `web_version/`: **이식본**. 데스크톱 버전이 내보낸 가중치로, 외부 라이브러리 없이 순수 자바스크립트로 추론합니다. GitHub Pages에 정적으로 배포합니다. → `web_version/CLAUDE.md`
- 흐름: `train.py`(학습) → `mnist_cnn.pt` → `가중치내보내기.py` → `web_version/가중치.bin` + `가중치정보.json` → 웹에서 추론. 모델이나 전처리를 바꾸면 항상 데스크톱 쪽을 먼저 고치고 웹을 따라 맞춥니다.
- 설계 문서와 구현 계획서: `docs/superpowers/specs/`, `docs/superpowers/plans/`
- 루트 `index.html`은 GitHub Pages 주소(https://dkstjdus123.github.io/Study01_MNIST/)로 들어온 방문자를 `web_version/`으로 보냅니다.

## 공통 규칙

- **한글 식별자**: 모든 코드와 주석은 한글로 작성하고, 변수·함수·클래스 이름도 한글로 짓습니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- **전처리 3단계**: 그린 그림은 두 버전 모두 같은 순서로 MNIST 형식에 맞춥니다.
  1. 여백 제거: 글씨가 있는 영역만 잘라냅니다.
  2. 20x20 비율 유지 축소: 긴 변을 20px로 맞춰(LANCZOS) 28x28 가운데에 놓습니다.
  3. 무게중심 정렬: 밝기 무게중심을 (14, 14)로 옮긴 뒤 정규화(평균 0.1307, 표준편차 0.3081)합니다.

  한쪽(`desktop_version/app.py`의 `전처리()` 또는 `web_version/전처리.js`)을 고치면 다른 쪽도 고치고 `web_version/검증.html`로 확인합니다.
- 페이지 맨 위 "학번 2601953 이름 안서연" 표시줄은 과제 요구사항이므로 지우지 않습니다.
- `CLAUDE_전역.md`(전역 CLAUDE.md 사본)는 과제 제출물이므로 지우지 않습니다.
- **검사**: `검사/` 폴더의 스크립트로 태스크 1~7 결과를 다시 확인합니다. 저장소 루트에서 `python 검사/데스크톱_회귀.py`, `python 검사/가중치_검사.py`, `python 검사/검증데이터_검사.py`, `NODE_PATH="$(npm root -g)" node 검사/웹_검사.cjs`, `python 검사/문서_검사.py` 순서로 실행합니다 (웹 검사는 검증 데이터가 먼저 있어야 함).
