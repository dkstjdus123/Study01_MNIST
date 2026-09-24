# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

PyTorch로 MNIST CNN을 학습하고, 손으로 쓴 숫자를 실시간으로 인식하는 학습용 프로젝트입니다. 두 버전으로 나뉩니다.

| 폴더 | 내용 | 자세한 안내 |
|---|---|---|
| `desktop_version/` | 모델 정의·학습(PyTorch)과 tkinter 그림판 앱, 웹용 가중치 변환 스크립트 | `desktop_version/CLAUDE.md` |
| `web_version/` | 외부 라이브러리 없이 순수 자바스크립트로 추론하는 정적 웹 페이지 (GitHub Pages) | `web_version/CLAUDE.md` |

## 규칙

- **모든 코드와 주석은 한글로 작성합니다.** 변수·함수·클래스 이름도 한글 식별자를 사용합니다 (예: `숫자인식CNN`, `전처리`, `모델_불러오기`).
- 학습된 가중치 파일 이름은 `mnist_cnn.pt`로 고정입니다 (`desktop_version/mnist_cnn.pt`).
- 새로 만드는 파일 맨 위에는 작성 시각을 주석으로 적습니다 (`CLAUDE_전역.md` 참고).

## 두 버전이 공유하는 것 (한쪽을 고치면 다른 쪽도 맞춰야 함)

- **가중치**: 웹 버전은 `desktop_version/export_web_weights.py`가 만든 `web_version/mnist_weights.bin/json`을 씁니다. 재학습하거나 모델 구조를 바꾸면 반드시 이 스크립트를 다시 실행해야 웹에 반영됩니다.
- **모델 구조**: `desktop_version/model.py`의 `숫자인식CNN`과 `web_version/inference.js`의 `추론()`이 같은 층 순서를 가져야 합니다.
- **전처리**: `desktop_version/app.py`의 `전처리()`와 `web_version/preprocess.js`의 `전처리()`는 같은 계산을 합니다 (PIL LANCZOS 크기 조절까지 똑같이 구현). 정규화 상수 `평균=0.1307`, `표준편차=0.3081`은 `train.py`, `app.py`, `preprocess.js`에 **각각 따로** 정의되어 있습니다.

## 배포

GitHub Pages는 `main` 브랜치 루트를 배포합니다: https://dkstjdus123.github.io/Study01_MNIST/ . 루트 `index.html`은 `web_version/`으로 이동시키는 안내 페이지일 뿐이고 실제 페이지는 `web_version/index.html`입니다.
