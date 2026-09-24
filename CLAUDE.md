# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

MNIST 손글씨 숫자 인식기를 두 가지 형태로 제공하는 학습용 프로젝트입니다.

- `desktop_version/` — PyTorch로 CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 숫자를 인식하는 Windows용 데스크톱 앱. 자세한 내용은 `desktop_version/CLAUDE.md` 참고.
- `web_version/` — 같은 모델을 브라우저에서 그대로 실행하는 정적 웹 페이지. **외부 라이브러리 없이 순수 자바스크립트로 추론**하며 GitHub Pages로 배포됩니다. 자세한 내용은 `web_version/CLAUDE.md` 참고.

## 공통 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 사용합니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- 새로 만드는 파일은 맨 위에 작성 시각을 주석으로 남깁니다 (`CLAUDE_전역.md` 규칙).

## 두 버전을 잇는 연결고리

1. `desktop_version/train.py`로 학습 → `desktop_version/mnist_cnn.pt` 저장.
2. `desktop_version/export_web_weights.py`로 `mnist_cnn.pt`를 읽어 `web_version/weights.js`(가중치를 JSON으로 담은 순수 JS 파일)를 생성.
3. `web_version/model.js`가 `desktop_version/model.py`의 `숫자인식CNN`과 같은 층 구조를 순수 자바스크립트로 재구현해 `weights.js`의 값으로 순전파를 계산합니다.

**모델 구조를 바꾸면 세 가지를 함께 바꿔야 합니다:** `model.py`의 층 구조, `model.js`의 순전파 계산, `export_web_weights.py`의 이름 매핑. 재학습 후에는 `export_web_weights.py`를 다시 실행해야 웹 페이지에 새 가중치가 반영됩니다.

## GitHub Pages 배포

`.github/workflows/deploy-pages.yml`이 `main` 브랜치의 `web_version/**` 변경을 감지해 그 폴더를 GitHub Pages로 자동 배포합니다 (GitHub Pages는 루트나 `/docs`만 기본 지원하므로, 임의 폴더를 배포하려면 이렇게 GitHub Actions 기반 배포가 필요합니다). 저장소 Settings → Pages → Source를 **GitHub Actions**로 한 번 설정해야 동작합니다.
