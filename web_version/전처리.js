// 작성: 2026-09-24 19:25 (수정: 2026-09-24 19:37 밝기 합이 0인 경우 처리)
// desktop_version/app.py의 전처리()를 순수 자바스크립트로 옮긴 것입니다. 한쪽을 고치면 다른 쪽도 맞춰야 합니다.
// 글씨 영역 자르기 → 비율 유지하며 긴 변 20px로 축소(LANCZOS) → 28x28 가운데 배치 → 밝기 무게중심을 (14, 14)로 이동 → 정규화
// 브라우저 drawImage 축소는 PIL LANCZOS와 결과가 달라서, PIL(Pillow)의 LANCZOS 리샘플링 계산 방식을 그대로 구현했습니다.

(function (전역) {
  "use strict";

  const 정밀도비트 = 22;           // Pillow의 PRECISION_BITS (32 - 8 - 2)
  const 란초스지지 = 3;            // LANCZOS 필터 반경

  // 파이썬 round()와 같은 반올림 (정확히 .5이면 짝수 쪽으로)
  function 파이썬반올림(값) {
    const 내림 = Math.floor(값), 차이 = 값 - 내림;
    if (차이 > 0.5) return 내림 + 1;
    if (차이 < 0.5) return 내림;
    return 내림 % 2 === 0 ? 내림 : 내림 + 1;
  }

  function 싱크(x) {
    if (x === 0) return 1;
    x *= Math.PI;
    return Math.sin(x) / x;
  }

  function 란초스(x) {
    return (-란초스지지 <= x && x < 란초스지지) ? 싱크(x) * 싱크(x / 란초스지지) : 0;
  }

  // 한 방향 축소에 쓸 계수를 미리 계산합니다 (Pillow precompute_coeffs + normalize_coeffs_8bpc).
  function 계수_계산(입력크기, 출력크기) {
    const 배율 = 입력크기 / 출력크기;
    const 필터배율 = Math.max(배율, 1);
    const 반경 = 란초스지지 * 필터배율;
    const 목록 = [];
    for (let xx = 0; xx < 출력크기; xx++) {
      const 중심 = (xx + 0.5) * 배율;
      const 시작 = Math.max(Math.trunc(중심 - 반경 + 0.5), 0);
      const 끝 = Math.min(Math.trunc(중심 + 반경 + 0.5), 입력크기);
      const 가중치 = [];
      let 합 = 0;
      for (let x = 시작; x < 끝; x++) {
        const w = 란초스((x - 중심 + 0.5) / 필터배율);
        가중치.push(w); 합 += w;
      }
      // 합이 1이 되도록 나눈 뒤 22비트 고정소수점 정수로 바꿉니다.
      const 정수계수 = 가중치.map(w => {
        const k = 합 !== 0 ? w / 합 : w;
        return Math.trunc(k < 0 ? -0.5 + k * (1 << 정밀도비트) : 0.5 + k * (1 << 정밀도비트));
      });
      목록.push({ 시작, 정수계수 });
    }
    return 목록;
  }

  function 잘라_8비트(합) {
    if (합 >= 2 ** (정밀도비트 + 8)) return 255;
    if (합 <= 0) return 0;
    return Math.floor(합 / 2 ** 정밀도비트);
  }

  /** 8비트 흑백 이미지를 PIL Image.resize(크기, Image.LANCZOS)와 같은 방식으로 크기 변경합니다. */
  function 란초스_크기변경(픽셀, 가로, 세로, 새가로, 새세로) {
    let 현재 = 픽셀, 현재가로 = 가로;
    if (새가로 !== 가로) {         // 가로 방향 먼저
      const 계수 = 계수_계산(가로, 새가로);
      const 출력 = new Uint8Array(새가로 * 세로);
      for (let y = 0; y < 세로; y++) for (let xx = 0; xx < 새가로; xx++) {
        const { 시작, 정수계수 } = 계수[xx];
        let 합 = 1 << (정밀도비트 - 1);
        for (let i = 0; i < 정수계수.length; i++) 합 += 현재[y * 가로 + 시작 + i] * 정수계수[i];
        출력[y * 새가로 + xx] = 잘라_8비트(합);
      }
      현재 = 출력; 현재가로 = 새가로;
    }
    if (새세로 !== 세로) {         // 그다음 세로 방향
      const 계수 = 계수_계산(세로, 새세로);
      const 출력 = new Uint8Array(현재가로 * 새세로);
      for (let yy = 0; yy < 새세로; yy++) {
        const { 시작, 정수계수 } = 계수[yy];
        for (let x = 0; x < 현재가로; x++) {
          let 합 = 1 << (정밀도비트 - 1);
          for (let i = 0; i < 정수계수.length; i++) 합 += 현재[(시작 + i) * 현재가로 + x] * 정수계수[i];
          출력[yy * 현재가로 + x] = 잘라_8비트(합);
        }
      }
      현재 = 출력;
    }
    return 현재 === 픽셀 ? Uint8Array.from(픽셀) : 현재;
  }

  /**
   * 그림판의 흑백 픽셀(검은 배경 0, 흰 글씨 255)을 모델 입력(정규화된 28x28 = 784개)으로 바꿉니다.
   * 아무것도 그리지 않았으면 null을 돌려줍니다.
   */
  function 전처리하기(픽셀, 가로, 세로, 평균, 표준편차) {
    // 1) 글씨가 있는 영역(0이 아닌 픽셀)만 잘라냅니다.
    let 왼 = 가로, 위 = 세로, 오른 = -1, 아래 = -1;
    for (let y = 0; y < 세로; y++) for (let x = 0; x < 가로; x++) {
      if (픽셀[y * 가로 + x] > 0) {
        if (x < 왼) 왼 = x;
        if (x > 오른) 오른 = x;
        if (y < 위) 위 = y;
        if (y > 아래) 아래 = y;
      }
    }
    if (오른 < 0) return null;
    const 잘린가로 = 오른 - 왼 + 1, 잘린세로 = 아래 - 위 + 1;
    const 잘린그림 = new Uint8Array(잘린가로 * 잘린세로);
    for (let y = 0; y < 잘린세로; y++)
      잘린그림.set(픽셀.subarray((위 + y) * 가로 + 왼, (위 + y) * 가로 + 왼 + 잘린가로), y * 잘린가로);

    // 2) 가로세로 비율을 유지하면서 긴 변을 20픽셀로 맞춥니다.
    const 배율 = 20 / Math.max(잘린가로, 잘린세로);
    const 새가로 = Math.max(1, 파이썬반올림(잘린가로 * 배율));
    const 새세로 = Math.max(1, 파이썬반올림(잘린세로 * 배율));
    const 작은그림 = 란초스_크기변경(잘린그림, 잘린가로, 잘린세로, 새가로, 새세로);

    // 3) 28x28 검은 배경의 가운데에 붙입니다.
    const 결과 = new Uint8Array(28 * 28);
    const 붙일x = Math.floor((28 - 새가로) / 2), 붙일y = Math.floor((28 - 새세로) / 2);
    for (let y = 0; y < 새세로; y++) for (let x = 0; x < 새가로; x++)
      결과[(붙일y + y) * 28 + 붙일x + x] = 작은그림[y * 새가로 + x];

    // 4) 밝기 무게중심이 정확히 가운데(14, 14)에 오도록 옮깁니다.
    let 전체밝기 = 0, 중심x = 0, 중심y = 0;
    for (let i = 0; i < 28 * 28; i++) {
      전체밝기 += 결과[i]; 중심x += (i % 28) * 결과[i]; 중심y += Math.floor(i / 28) * 결과[i];
    }
    // 아주 옅은 점만 있으면 축소 후 모두 0이 될 수 있습니다. 이때 0으로 나누면 NaN이 되므로 빈 그림으로 봅니다.
    if (전체밝기 === 0) return null;
    const 이동x = 파이썬반올림(14 - 중심x / 전체밝기), 이동y = 파이썬반올림(14 - 중심y / 전체밝기);

    // 5) 옮기면서 학습 때와 같은 방식으로 정규화합니다. (빈 곳은 검은색 0)
    const 입력 = new Float32Array(28 * 28).fill((0 - 평균) / 표준편차);
    for (let y = 0; y < 28; y++) for (let x = 0; x < 28; x++) {
      const 원x = x - 이동x, 원y = y - 이동y;
      if (원x >= 0 && 원x < 28 && 원y >= 0 && 원y < 28)
        입력[y * 28 + x] = (결과[원y * 28 + 원x] / 255 - 평균) / 표준편차;
    }
    return 입력;
  }

  const 내보내기 = { 전처리하기, 란초스_크기변경, 파이썬반올림 };
  if (typeof module !== "undefined" && module.exports) module.exports = 내보내기;   // Node.js 검증용
  else 전역.전처리 = 내보내기;
})(typeof window !== "undefined" ? window : globalThis);
