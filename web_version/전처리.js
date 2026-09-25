// 작성: 2026-09-25 09:19
// 그림판 그림을 MNIST 형식 입력으로 바꿉니다. desktop_version/app.py의 전처리()와 같은 값을 냅니다.
// 여백 자르기 → 긴 변 20px로 비율 유지 축소(Pillow LANCZOS와 같은 계산) → 28x28 가운데 배치
// → 밝기 무게중심을 (14, 14)로 이동(파이썬 round) → 정규화

(function (전역) {
  "use strict";

  const 정밀비트 = 22;              // Pillow의 PRECISION_BITS (32 - 8 - 2)
  const 한단위 = 2 ** 정밀비트;

  // 파이썬 round(): 정확히 .5이면 짝수 쪽으로 반올림합니다.
  function 파이썬반올림(값) {
    const 내림 = Math.floor(값), 나머지 = 값 - 내림;
    if (나머지 > 0.5) return 내림 + 1;
    if (나머지 < 0.5) return 내림;
    return 내림 % 2 === 0 ? 내림 : 내림 + 1;
  }

  function 싱크(x) {
    if (x === 0) return 1;
    x *= Math.PI;
    return Math.sin(x) / x;
  }

  function 란초스(x) {
    return -3 <= x && x < 3 ? 싱크(x) * 싱크(x / 3) : 0;
  }

  // Pillow precompute_coeffs + normalize_coeffs_8bpc: 출력 칸마다 (시작 위치, 정수 계수 목록)
  function 계수_구하기(입력크기, 출력크기) {
    const 배율 = 입력크기 / 출력크기;
    const 필터배율 = 배율 < 1 ? 1 : 배율;
    const 지지 = 3 * 필터배율;
    const 역수 = 1 / 필터배율;
    const 목록 = [];
    for (let 칸 = 0; 칸 < 출력크기; 칸++) {
      const 중심 = (칸 + 0.5) * 배율;
      let 시작 = Math.trunc(중심 - 지지 + 0.5);
      if (시작 < 0) 시작 = 0;
      let 끝 = Math.trunc(중심 + 지지 + 0.5);
      if (끝 > 입력크기) 끝 = 입력크기;
      const 개수 = 끝 - 시작, 실수계수 = new Array(개수);
      let 합 = 0;
      for (let k = 0; k < 개수; k++) {
        const w = 란초스((k + 시작 - 중심 + 0.5) * 역수);
        실수계수[k] = w;
        합 += w;
      }
      const 정수계수 = new Array(개수);
      for (let k = 0; k < 개수; k++) {
        const 값 = 합 !== 0 ? 실수계수[k] / 합 : 실수계수[k];
        정수계수[k] = Math.trunc(값 < 0 ? -0.5 + 값 * 한단위 : 0.5 + 값 * 한단위);
      }
      목록.push({ 시작, 계수: 정수계수 });
    }
    return 목록;
  }

  // Pillow clip8: 고정소수점 합을 0~255 정수로
  function 클립8(합) {
    if (합 >= 2 ** (정밀비트 + 8)) return 255;
    if (합 <= 0) return 0;
    return Math.floor(합 / 한단위);
  }

  // Pillow Image.resize(LANCZOS)와 같은 계산: 가로 방향 먼저, 그다음 세로 방향 (크기가 같은 방향은 건너뜀)
  function 란초스_크기바꾸기(픽셀, 가로, 세로, 새가로, 새세로) {
    let 중간 = 픽셀;
    if (새가로 !== 가로) {
      const 계수들 = 계수_구하기(가로, 새가로);
      중간 = new Uint8Array(새가로 * 세로);
      for (let y = 0; y < 세로; y++) {
        for (let x = 0; x < 새가로; x++) {
          const { 시작, 계수 } = 계수들[x];
          let 합 = 한단위 / 2;
          for (let k = 0; k < 계수.length; k++) 합 += 픽셀[y * 가로 + 시작 + k] * 계수[k];
          중간[y * 새가로 + x] = 클립8(합);
        }
      }
    }
    if (새세로 === 세로) return 중간;
    const 계수들 = 계수_구하기(세로, 새세로);
    const 출력 = new Uint8Array(새가로 * 새세로);
    for (let y = 0; y < 새세로; y++) {
      const { 시작, 계수 } = 계수들[y];
      for (let x = 0; x < 새가로; x++) {
        let 합 = 한단위 / 2;
        for (let k = 0; k < 계수.length; k++) 합 += 중간[(시작 + k) * 새가로 + x] * 계수[k];
        출력[y * 새가로 + x] = 클립8(합);
      }
    }
    return 출력;
  }

  function 전처리하기(픽셀, 가로, 세로, 평균, 표준편차) {
    // 1) 글씨가 있는 영역(0이 아닌 픽셀)만 잘라냅니다.
    let 왼 = 가로, 오 = -1, 위 = 세로, 아래 = -1;
    for (let y = 0; y < 세로; y++) {
      for (let x = 0; x < 가로; x++) {
        if (픽셀[y * 가로 + x] > 0) {
          if (x < 왼) 왼 = x;
          if (x > 오) 오 = x;
          if (y < 위) 위 = y;
          if (y > 아래) 아래 = y;
        }
      }
    }
    if (오 < 0) return null;
    const 잘린가로 = 오 - 왼 + 1, 잘린세로 = 아래 - 위 + 1;
    const 잘린 = new Uint8Array(잘린가로 * 잘린세로);
    for (let y = 0; y < 잘린세로; y++) {
      잘린.set(픽셀.subarray((위 + y) * 가로 + 왼, (위 + y) * 가로 + 왼 + 잘린가로), y * 잘린가로);
    }

    // 2) 긴 변을 20px로 맞춰 축소하고 28x28 가운데에 놓습니다.
    const 배율 = 20 / Math.max(잘린가로, 잘린세로);
    const 새가로 = Math.max(1, 파이썬반올림(잘린가로 * 배율));
    const 새세로 = Math.max(1, 파이썬반올림(잘린세로 * 배율));
    const 작은 = 란초스_크기바꾸기(잘린, 잘린가로, 잘린세로, 새가로, 새세로);
    const 가운데 = new Uint8Array(28 * 28);
    const 왼여백 = Math.floor((28 - 새가로) / 2), 위여백 = Math.floor((28 - 새세로) / 2);
    for (let y = 0; y < 새세로; y++) {
      for (let x = 0; x < 새가로; x++) 가운데[(위여백 + y) * 28 + 왼여백 + x] = 작은[y * 새가로 + x];
    }

    // 3) 밝기 무게중심을 (14, 14)로 옮기고 정규화합니다.
    let 전체 = 0, x합 = 0, y합 = 0;
    for (let y = 0; y < 28; y++) {
      for (let x = 0; x < 28; x++) {
        const 밝기 = 가운데[y * 28 + x];
        전체 += 밝기;
        x합 += x * 밝기;
        y합 += y * 밝기;
      }
    }
    if (전체 === 0) return null;
    const 이동x = 파이썬반올림(14 - x합 / 전체), 이동y = 파이썬반올림(14 - y합 / 전체);
    const 입력 = new Float32Array(28 * 28);
    for (let y = 0; y < 28; y++) {
      for (let x = 0; x < 28; x++) {
        const 원래x = x - 이동x, 원래y = y - 이동y;
        const 밝기 = 원래x >= 0 && 원래x < 28 && 원래y >= 0 && 원래y < 28 ? 가운데[원래y * 28 + 원래x] : 0;
        입력[y * 28 + x] = (밝기 / 255 - 평균) / 표준편차;
      }
    }
    return 입력;
  }

  const 내보내기 = { 전처리하기 };
  전역.전처리 = 내보내기;
  if (typeof module !== "undefined" && module.exports) module.exports = 내보내기;
})(typeof window !== "undefined" ? window : globalThis);
