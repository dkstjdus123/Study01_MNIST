// 작성: 2026-09-25 09:25
// 280x280 그림판: 검은 배경에 흰 글씨. 마우스·터치·펜을 포인터 이벤트 하나로 처리합니다.
// 한 번에 한 포인터만 그리고(두 번째 손가락 무시), 마우스는 왼쪽 버튼만 씁니다.

(function (전역) {
  "use strict";

  function 그림판_만들기(캔버스, { 펜두께 = 18, 다그렸을때 = () => {} } = {}) {
    const 붓 = 캔버스.getContext("2d", { willReadFrequently: true });
    const 가로 = 캔버스.width, 세로 = 캔버스.height;
    let 그리는포인터 = null, 이전점 = null;

    function 지우기() {
      붓.fillStyle = "black";
      붓.fillRect(0, 0, 가로, 세로);
    }

    // 화면에서 늘어나거나 줄어든 캔버스 좌표를 그림 좌표(0~280)로 바꿉니다.
    function 그림좌표(e) {
      const 틀 = 캔버스.getBoundingClientRect();
      return { x: (e.clientX - 틀.left) * 가로 / 틀.width, y: (e.clientY - 틀.top) * 세로 / 틀.height };
    }

    function 선긋기(점) {
      붓.fillStyle = 붓.strokeStyle = "white";
      if (이전점) {
        붓.lineWidth = 펜두께;
        붓.lineCap = "round";
        붓.beginPath();
        붓.moveTo(이전점.x, 이전점.y);
        붓.lineTo(점.x, 점.y);
        붓.stroke();
      }
      붓.beginPath();
      붓.arc(점.x, 점.y, 펜두께 / 2, 0, Math.PI * 2);
      붓.fill();
      이전점 = 점;
    }

    캔버스.addEventListener("pointerdown", e => {
      if (그리는포인터 !== null) return;                        // 두 번째 손가락은 무시
      if (e.pointerType === "mouse" && e.button !== 0) return;  // 마우스는 왼쪽 버튼만
      e.preventDefault();
      그리는포인터 = e.pointerId;
      캔버스.setPointerCapture(e.pointerId);
      이전점 = null;
      선긋기(그림좌표(e));
    });
    캔버스.addEventListener("pointermove", e => {
      if (e.pointerId === 그리는포인터) 선긋기(그림좌표(e));
    });
    function 붓떼기(e) {
      if (e.pointerId !== 그리는포인터) return;
      그리는포인터 = null;
      이전점 = null;
      다그렸을때();
    }
    캔버스.addEventListener("pointerup", 붓떼기);
    캔버스.addEventListener("pointercancel", 붓떼기);
    캔버스.addEventListener("contextmenu", e => e.preventDefault());   // 오른쪽 클릭 메뉴가 가리지 않게

    // 흑백 그림이므로 빨강 채널을 밝기로 씁니다.
    function 픽셀가져오기() {
      const 자료 = 붓.getImageData(0, 0, 가로, 세로).data;
      const 흑백 = new Uint8Array(가로 * 세로);
      for (let i = 0; i < 흑백.length; i++) 흑백[i] = 자료[i * 4];
      return 흑백;
    }

    지우기();
    return { 픽셀가져오기, 지우기, 가로, 세로 };
  }

  전역.그림판 = { 그림판_만들기 };
})(window);
