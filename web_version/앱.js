// 작성: 2026-09-25 09:25
// 그림판.js · 전처리.js · 모델.js를 엮습니다. 붓을 뗄 때마다 전처리 → 추론 → 소프트맥스 후
// 예측 숫자, 신뢰도, 0~9 확률 막대를 보여 줍니다.

(function () {
  "use strict";

  const 펜두께 = 18;   // app.py와 같은 붓 굵기
  const 예측표시 = document.getElementById("예측");
  const 신뢰도표시 = document.getElementById("신뢰도");
  const 막대목록 = document.getElementById("막대목록");
  let 불러온모델 = null;
  let 그린것있음 = false;   // 모델을 불러오는 동안 그린 그림도 불러온 뒤 인식하려고 기억합니다.

  // 가장 큰 값의 위치 (Math.max(...배열)은 큰 배열에서 스택이 넘칠 수 있어 반복문을 씁니다)
  function 최대위치(배열) {
    let 위치 = 0;
    for (let i = 1; i < 배열.length; i++) if (배열[i] > 배열[위치]) 위치 = i;
    return 위치;
  }

  function 소프트맥스(점수) {
    const 최대 = 점수[최대위치(점수)];
    const 지수 = Array.from(점수, v => Math.exp(v - 최대));
    const 합 = 지수.reduce((a, b) => a + b, 0);
    return 지수.map(v => v / 합);
  }

  const 막대들 = [], 퍼센트들 = [];
  for (let 숫자 = 0; 숫자 < 10; 숫자++) {
    const 줄 = document.createElement("div");
    줄.className = "막대줄";
    줄.innerHTML = `<span class="숫자">${숫자}</span><div class="막대틀"><div class="막대"></div></div><span class="퍼센트">0.0%</span>`;
    막대목록.appendChild(줄);
    막대들.push(줄.querySelector(".막대"));
    퍼센트들.push(줄.querySelector(".퍼센트"));
  }

  function 막대_갱신(확률) {
    const 최대 = 확률.some(p => p > 0) ? 최대위치(확률) : -1;
    확률.forEach((p, 숫자) => {
      막대들[숫자].style.width = `${(p * 100).toFixed(1)}%`;
      막대들[숫자].classList.toggle("최대", 숫자 === 최대);
      퍼센트들[숫자].textContent = `${(p * 100).toFixed(1)}%`;
    });
  }

  function 인식하기() {
    그린것있음 = true;
    if (!불러온모델) return;   // 불러오기가 끝나면 다시 부릅니다.
    const 입력 = 전처리.전처리하기(판.픽셀가져오기(), 판.가로, 판.세로, 불러온모델.평균, 불러온모델.표준편차);
    if (!입력) return;
    const 확률 = 소프트맥스(불러온모델.추론(입력));
    const 예측 = 최대위치(확률);
    예측표시.textContent = String(예측);
    신뢰도표시.textContent = `신뢰도 ${(확률[예측] * 100).toFixed(1)}%`;
    막대_갱신(확률);
  }

  function 초기화() {
    판.지우기();
    그린것있음 = false;
    예측표시.textContent = "?";
    if (불러온모델) 신뢰도표시.textContent = "숫자를 그려 보세요";
    막대_갱신(new Array(10).fill(0));
  }

  const 판 = 그림판.그림판_만들기(document.getElementById("그림판"), { 펜두께, 다그렸을때: 인식하기 });
  document.getElementById("지우기").addEventListener("click", 초기화);
  막대_갱신(new Array(10).fill(0));

  모델.모델_불러오기()
    .then(m => {
      불러온모델 = m;
      신뢰도표시.textContent = "숫자를 그려 보세요";
      if (그린것있음) 인식하기();
    })
    .catch(오류 => {
      // file://로 열면 브라우저가 fetch를 막으므로 로컬 서버로 여는 방법을 알려 줍니다.
      신뢰도표시.textContent = location.protocol === "file:"
        ? "파일을 직접 열면 모델을 불러올 수 없습니다. 저장소 폴더에서 python -m http.server 8000 을 실행한 뒤 http://localhost:8000/web_version/ 으로 여세요."
        : `모델을 불러오지 못했습니다: ${오류.message}`;
    });
})();
