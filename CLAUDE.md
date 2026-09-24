# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch로 MNIST CNN을 학습하고, tkinter 그림판에서 마우스로 쓴 손글씨 숫자를 실시간으로 인식하는 학습용 프로젝트입니다.

## 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 사용합니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- 학습된 가중치 파일 이름은 `mnist_cnn.pt`로 고정입니다.

## 폴더 구조

- `desktop_version/`: PyTorch 학습(`train.py`), tkinter 그림판 앱(`app.py`), 모델(`model.py`), 가중치(`mnist_cnn.pt`), 웹용 가중치 변환(`export_web.py`), 바로가기 생성(`make_shortcut.py`). 자세한 내용은 `desktop_version/CLAUDE.md`.
- `web_version/`: 브라우저용 웹 앱. 외부 라이브러리 없이 순수 자바스크립트(`cnn.js`)로 추론하며 가중치는 `model_weights.json`/`.bin`. 자세한 내용은 `web_version/CLAUDE.md`.
- 루트 `index.html`: GitHub Pages(`main` 브랜치 루트)로 들어온 방문자를 `web_version/`으로 이동시킵니다. 배포 주소: https://dkstjdus123.github.io/Study01_MNIST/
- `CLAUDE_전역.md`: 전역 CLAUDE.md 사본 (과제 제출물이므로 지우지 않습니다).

## 명령어

환경: Windows, Python 3.13, PyTorch CPU 버전. 테스트·린트 설정은 없습니다.

```bash
python desktop_version/train.py        # 학습 → desktop_version/mnist_cnn.pt (오래 걸리므로 백그라운드로)
python desktop_version/app.py          # 그림판 GUI
python desktop_version/export_web.py   # web_version/model_weights.json/.bin 생성 (재학습 후 반드시 실행)
```

## 함께 맞춰야 하는 것

- `desktop_version/app.py`의 `전처리()`와 `web_version/index.html`의 JavaScript 전처리는 같은 과정이므로 한쪽을 고치면 다른 쪽도 고칩니다.
- 정규화 상수(`평균=0.1307`, `표준편차=0.3081`)는 `train.py`, `app.py`, `index.html`에서 같아야 합니다.
- 페이지 맨 위 "학번 2601953 이름 안서연" 표시줄(`web_version/index.html`, 루트 `index.html`)은 과제 요구사항이므로 지우지 않습니다.
