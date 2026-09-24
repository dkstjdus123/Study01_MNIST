// 작성: 2026-09-24 17:50 KST
/**
 * 그림판 UI와 전처리를 담당합니다. 실제 추론은 model.js의 추론() 함수(순수 자바스크립트,
 * 외부 라이브러리 없음)가 weights.js의 가중치로 계산합니다.
 */

const 펜두께 = 18;
const 평균 = 0.1307, 표준편차 = 0.3081;

const 그림판 = document.getElementById("그림판");
const 붓 = 그림판.getContext("2d");
const 예측표시 = document.getElementById("예측");
const 신뢰도표시 = document.getElementById("신뢰도");
const 막대목록 = document.getElementById("막대목록");
let 그리는중 = false, 이전좌표 = null;

// 0~9 확률 막대를 만듭니다.
const 막대들 = [], 퍼센트들 = [];
for (let 숫자 = 0; 숫자 < 10; 숫자++) {
  const 줄 = document.createElement("div");
  줄.className = "막대줄";
  줄.innerHTML = `<span>${숫자}</span><div class="막대틀"><div class="막대"></div></div><span class="퍼센트">0.0%</span>`;
  막대목록.appendChild(줄);
  막대들.push(줄.querySelector(".막대"));
  퍼센트들.push(줄.querySelector(".퍼센트"));
}

// 그림판을 검은색으로 초기화합니다. (MNIST처럼 검은 배경에 흰 글씨)
function 지우기() {
  붓.fillStyle = "#000";
  붓.fillRect(0, 0, 그림판.width, 그림판.height);
  예측표시.textContent = "?";
  신뢰도표시.textContent = "숫자를 그려 보세요";
  막대_갱신(new Array(10).fill(0));
}

// 화면 좌표를 캔버스 내부 좌표(280x280)로 바꿉니다.
function 캔버스좌표(이벤트) {
  const 영역 = 그림판.getBoundingClientRect();
  return [(이벤트.clientX - 영역.left) * 그림판.width / 영역.width,
          (이벤트.clientY - 영역.top) * 그림판.height / 영역.height];
}

function 선긋기(좌표) {
  붓.strokeStyle = "#fff"; 붓.fillStyle = "#fff";
  붓.lineWidth = 펜두께; 붓.lineCap = "round"; 붓.lineJoin = "round";
  if (이전좌표) {
    붓.beginPath(); 붓.moveTo(...이전좌표); 붓.lineTo(...좌표); 붓.stroke();
  }
  붓.beginPath(); 붓.arc(좌표[0], 좌표[1], 펜두께 / 2, 0, Math.PI * 2); 붓.fill();
  이전좌표 = 좌표;
}

// 마우스와 터치를 모두 처리하도록 포인터 이벤트를 사용합니다.
그림판.addEventListener("pointerdown", e => { 그리는중 = true; 그림판.setPointerCapture(e.pointerId); 선긋기(캔버스좌표(e)); });
그림판.addEventListener("pointermove", e => { if (그리는중) 선긋기(캔버스좌표(e)); });
function 붓떼기() { if (!그리는중) return; 그리는중 = false; 이전좌표 = null; 인식하기(); }
그림판.addEventListener("pointerup", 붓떼기);
그림판.addEventListener("pointercancel", 붓떼기);
document.getElementById("지우기").addEventListener("click", 지우기);

/**
 * 그림을 MNIST 형식으로 바꿉니다. (desktop_version/app.py의 전처리와 같은 순서)
 * 글씨 영역 잘라내기 → 긴 변을 20px로 축소 → 28x28 가운데 배치 → 무게중심을 (14,14)로 이동 → 정규화
 */
function 전처리() {
  const { width: 가로, height: 세로 } = 그림판;
  const 픽셀 = 붓.getImageData(0, 0, 가로, 세로).data;
  let 왼 = 가로, 위 = 세로, 오른 = -1, 아래 = -1;
  for (let y = 0; y < 세로; y++) for (let x = 0; x < 가로; x++) {
    if (픽셀[(y * 가로 + x) * 4] > 0) {
      if (x < 왼) 왼 = x; if (x > 오른) 오른 = x;
      if (y < 위) 위 = y; if (y > 아래) 아래 = y;
    }
  }
  if (오른 < 0) return null;   // 아무것도 그리지 않음

  const 너비 = 오른 - 왼 + 1, 높이 = 아래 - 위 + 1;
  const 배율 = 20 / Math.max(너비, 높이);
  const 새너비 = Math.max(1, Math.round(너비 * 배율)), 새높이 = Math.max(1, Math.round(높이 * 배율));

  const 작은판 = document.createElement("canvas");
  작은판.width = 28; 작은판.height = 28;
  const 작은붓 = 작은판.getContext("2d");
  작은붓.fillStyle = "#000"; 작은붓.fillRect(0, 0, 28, 28);
  작은붓.imageSmoothingEnabled = true; 작은붓.imageSmoothingQuality = "high";
  작은붓.drawImage(그림판, 왼, 위, 너비, 높이,
                   Math.floor((28 - 새너비) / 2), Math.floor((28 - 새높이) / 2), 새너비, 새높이);

  // 밝기(0~1)와 무게중심을 구합니다.
  const 작은픽셀 = 작은붓.getImageData(0, 0, 28, 28).data;
  const 밝기 = new Float32Array(28 * 28);
  let 합 = 0, 중심x = 0, 중심y = 0;
  for (let i = 0; i < 28 * 28; i++) {
    const v = 작은픽셀[i * 4] / 255;
    밝기[i] = v; 합 += v; 중심x += (i % 28) * v; 중심y += Math.floor(i / 28) * v;
  }
  const 이동x = Math.round(14 - 중심x / 합), 이동y = Math.round(14 - 중심y / 합);

  // 무게중심이 가운데 오도록 옮긴 뒤 학습 때와 같이 정규화합니다.
  const 입력 = new Float32Array(28 * 28).fill((0 - 평균) / 표준편차);
  for (let y = 0; y < 28; y++) for (let x = 0; x < 28; x++) {
    const 새x = x + 이동x, 새y = y + 이동y;
    if (새x >= 0 && 새x < 28 && 새y >= 0 && 새y < 28)
      입력[새y * 28 + 새x] = (밝기[y * 28 + x] - 평균) / 표준편차;
  }
  return 입력;
}

function 인식하기() {
  const 입력 = 전처리();
  if (!입력) return;
  const 확률 = 추론(입력);   // model.js
  const 예측 = 확률.indexOf(Math.max(...확률));
  예측표시.textContent = 예측;
  신뢰도표시.textContent = `신뢰도: ${(확률[예측] * 100).toFixed(1)}%`;
  막대_갱신(확률);
}

function 막대_갱신(확률) {
  const 최대 = 확률.some(p => p > 0) ? 확률.indexOf(Math.max(...확률)) : -1;
  확률.forEach((p, 숫자) => {
    막대들[숫자].style.width = `${p * 100}%`;
    막대들[숫자].classList.toggle("최대", 숫자 === 최대);
    퍼센트들[숫자].textContent = `${(p * 100).toFixed(1)}%`;
  });
}

지우기();
