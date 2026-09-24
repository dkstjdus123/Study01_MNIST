// 작성: 2026-09-24 19:25
// 캔버스 그리기 (마우스 + 터치): 검은 배경에 흰 글씨로 그립니다 (MNIST와 같은 극성, app.py 그림판과 같은 방식).

(function (전역) {
  "use strict";

  /**
   * 캔버스를 그림판으로 만듭니다.
   * 설정.펜두께: 붓 굵기(캔버스 내부 픽셀 기준), 설정.다그렸을때: 붓을 뗄 때마다 불리는 함수
   * 돌려주는 값: { 지우기(), 픽셀가져오기() → 흑백 Uint8Array(가로*세로), 가로, 세로 }
   */
  function 그림판_만들기(캔버스, 설정) {
    const 붓 = 캔버스.getContext("2d", { willReadFrequently: true });
    const 펜두께 = 설정.펜두께;
    let 그리는중 = false, 이전좌표 = null;

    function 지우기() {
      붓.fillStyle = "#000";
      붓.fillRect(0, 0, 캔버스.width, 캔버스.height);
    }

    // 화면 좌표를 캔버스 내부 좌표로 바꿉니다 (화면에서 캔버스가 줄어들어 보여도 정확히 그리도록).
    function 캔버스좌표(이벤트) {
      const 영역 = 캔버스.getBoundingClientRect();
      return [(이벤트.clientX - 영역.left) * 캔버스.width / 영역.width,
              (이벤트.clientY - 영역.top) * 캔버스.height / 영역.height];
    }

    function 선긋기(좌표) {
      붓.strokeStyle = "#fff"; 붓.fillStyle = "#fff";
      붓.lineWidth = 펜두께; 붓.lineCap = "round"; 붓.lineJoin = "round";
      if (이전좌표) {
        붓.beginPath(); 붓.moveTo(...이전좌표); 붓.lineTo(...좌표); 붓.stroke();
      }
      // 선 끝을 둥글게 하기 위해 원도 함께 그립니다.
      붓.beginPath(); 붓.arc(좌표[0], 좌표[1], 펜두께 / 2, 0, Math.PI * 2); 붓.fill();
      이전좌표 = 좌표;
    }

    function 붓떼기() {
      if (!그리는중) return;
      그리는중 = false; 이전좌표 = null;
      if (설정.다그렸을때) 설정.다그렸을때();
    }

    // 포인터 이벤트 하나로 마우스·터치·펜을 모두 처리합니다.
    캔버스.addEventListener("pointerdown", e => {
      그리는중 = true; 캔버스.setPointerCapture(e.pointerId); 선긋기(캔버스좌표(e));
    });
    캔버스.addEventListener("pointermove", e => { if (그리는중) 선긋기(캔버스좌표(e)); });
    캔버스.addEventListener("pointerup", 붓떼기);
    캔버스.addEventListener("pointercancel", 붓떼기);

    /** 캔버스 내용을 흑백 픽셀(0~255)로 꺼냅니다. 흰색으로만 그리므로 빨강 채널이 곧 밝기입니다. */
    function 픽셀가져오기() {
      const rgba = 붓.getImageData(0, 0, 캔버스.width, 캔버스.height).data;
      const 흑백 = new Uint8Array(캔버스.width * 캔버스.height);
      for (let i = 0; i < 흑백.length; i++) 흑백[i] = rgba[i * 4];
      return 흑백;
    }

    지우기();
    return { 지우기, 픽셀가져오기, 가로: 캔버스.width, 세로: 캔버스.height };
  }

  전역.그림판 = { 그림판_만들기 };
})(window);
