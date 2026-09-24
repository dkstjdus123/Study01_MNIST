// 작성: 2026-09-24 19:25
// 그림판.js · 전처리.js · 모델.js를 엮어, 붓을 뗄 때마다 숫자를 인식하고 결과(예측·신뢰도·확률 막대)를 보여 줍니다.

(function () {
  "use strict";

  const 펜두께 = 18;   // app.py와 같은 붓 굵기

  const 예측표시 = document.getElementById("예측");
  const 신뢰도표시 = document.getElementById("신뢰도");
  const 막대목록 = document.getElementById("막대목록");
  let 불러온모델 = null;

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

  function 막대_갱신(확률) {
    const 최대 = 확률.some(p => p > 0) ? 확률.indexOf(Math.max(...확률)) : -1;
    확률.forEach((p, 숫자) => {
      막대들[숫자].style.width = `${p * 100}%`;
      막대들[숫자].classList.toggle("최대", 숫자 === 최대);
      퍼센트들[숫자].textContent = `${(p * 100).toFixed(1)}%`;
    });
  }

  // 점수(로짓)를 소프트맥스로 확률로 바꿉니다.
  function 소프트맥스(점수) {
    const 최대점수 = Math.max(...점수);
    const 지수 = 점수.map(s => Math.exp(s - 최대점수));
    const 합 = 지수.reduce((a, b) => a + b, 0);
    return 지수.map(v => v / 합);
  }

  function 인식하기() {
    if (!불러온모델) return;
    const 입력 = 전처리.전처리하기(판.픽셀가져오기(), 판.가로, 판.세로, 불러온모델.평균, 불러온모델.표준편차);
    if (!입력) return;
    const 확률 = 소프트맥스(Array.from(불러온모델.추론(입력)));
    const 예측 = 확률.indexOf(Math.max(...확률));
    예측표시.textContent = 예측;
    신뢰도표시.textContent = `신뢰도: ${(확률[예측] * 100).toFixed(1)}%`;
    막대_갱신(확률);
  }

  function 초기화() {
    판.지우기();
    예측표시.textContent = "?";
    if (불러온모델) 신뢰도표시.textContent = "숫자를 그려 보세요";
    막대_갱신(new Array(10).fill(0));
  }

  const 판 = 그림판.그림판_만들기(document.getElementById("그림판"), { 펜두께, 다그렸을때: 인식하기 });
  document.getElementById("지우기").addEventListener("click", 초기화);
  초기화();

  모델.모델_불러오기()
    .then(m => { 불러온모델 = m; 신뢰도표시.textContent = "숫자를 그려 보세요"; })
    .catch(e => { 신뢰도표시.textContent = "모델을 불러오지 못했습니다: " + e.message; });
})();
