// 작성: 2026-09-24 19:20
// 외부 라이브러리 없이 순수 자바스크립트로 숫자인식CNN을 계산하는 추론 엔진입니다.
// 가중치는 desktop_version/export_web.py가 만든 model_weights.json(구조) + model_weights.bin(float32 값)을 씁니다.
// 배치정규화는 변환할 때 합성곱에 미리 합쳐 두었으므로 여기서는 합성곱·ReLU·최대풀링·완전연결만 계산합니다.

(function (전역) {
  "use strict";

  // 3x3 합성곱 (패딩 1, 보폭 1): [입력채널][높이][너비] → [출력채널][높이][너비]
  function 합성곱(입력, 채널, 높이, 너비, 층) {
    const [출력채널, 입력채널] = 층.가중치모양;
    if (입력채널 !== 채널) throw new Error(`합성곱 입력 채널이 맞지 않습니다: ${채널} ≠ ${입력채널}`);
    const 면적 = 높이 * 너비;
    const 출력 = new Float32Array(출력채널 * 면적);
    const W = 층.가중치, B = 층.편향;
    for (let oc = 0; oc < 출력채널; oc++) {
      const 출력판 = 출력.subarray(oc * 면적, (oc + 1) * 면적);
      출력판.fill(B[oc]);
      for (let ic = 0; ic < 입력채널; ic++) {
        const 입력판 = 입력.subarray(ic * 면적, (ic + 1) * 면적);
        const 커널시작 = (oc * 입력채널 + ic) * 9;
        for (let ky = 0; ky < 3; ky++) {
          const dy = ky - 1;
          const y시작 = Math.max(0, -dy), y끝 = Math.min(높이, 높이 - dy);
          for (let kx = 0; kx < 3; kx++) {
            const dx = kx - 1;
            const w = W[커널시작 + ky * 3 + kx];
            const x시작 = Math.max(0, -dx), x끝 = Math.min(너비, 너비 - dx);
            for (let y = y시작; y < y끝; y++) {
              const 출력줄 = y * 너비, 입력줄 = (y + dy) * 너비 + dx;
              for (let x = x시작; x < x끝; x++) 출력판[출력줄 + x] += w * 입력판[입력줄 + x];
            }
          }
        }
      }
    }
    return [출력, 출력채널, 높이, 너비];
  }

  function 렐루(입력) {
    for (let i = 0; i < 입력.length; i++) if (입력[i] < 0) 입력[i] = 0;
    return 입력;
  }

  // 2x2 최대풀링 (보폭 2)
  function 최대풀링(입력, 채널, 높이, 너비) {
    const 새높이 = Math.floor(높이 / 2), 새너비 = Math.floor(너비 / 2);
    const 출력 = new Float32Array(채널 * 새높이 * 새너비);
    for (let c = 0; c < 채널; c++) {
      const 입력시작 = c * 높이 * 너비, 출력시작 = c * 새높이 * 새너비;
      for (let y = 0; y < 새높이; y++) for (let x = 0; x < 새너비; x++) {
        const i = 입력시작 + 2 * y * 너비 + 2 * x;
        출력[출력시작 + y * 새너비 + x] = Math.max(입력[i], 입력[i + 1], 입력[i + 너비], 입력[i + 너비 + 1]);
      }
    }
    return [출력, 채널, 새높이, 새너비];
  }

  // 완전연결: 출력 = 가중치 · 입력 + 편향 (입력은 PyTorch Flatten과 같은 [채널][높이][너비] 순서)
  function 완전연결(입력, 층) {
    const [출력수, 입력수] = 층.가중치모양;
    if (입력.length !== 입력수) throw new Error(`완전연결 입력 크기가 맞지 않습니다: ${입력.length} ≠ ${입력수}`);
    const 출력 = new Float32Array(출력수);
    for (let o = 0; o < 출력수; o++) {
      let 합 = 층.편향[o];
      const 시작 = o * 입력수;
      for (let i = 0; i < 입력수; i++) 합 += 층.가중치[시작 + i] * 입력[i];
      출력[o] = 합;
    }
    return 출력;
  }

  /** 구조 정보(JSON)와 가중치 바이너리(ArrayBuffer)로 모델을 만듭니다. */
  function 모델_만들기(정보, 바이너리) {
    const 값 = (조각) => new Float32Array(바이너리, 조각.offset * 4, 조각.length);
    const 층들 = 정보.layers.map(층 => 층.weight
      ? { 종류: 층.type, 가중치: 값(층.weight), 가중치모양: 층.weight.shape, 편향: 값(층.bias) }
      : { 종류: 층.type });

    /** 정규화된 28x28 입력(Float32Array 784개)을 받아 10개 숫자의 점수(로짓)를 돌려줍니다. */
    function 추론(입력) {
      let x = Float32Array.from(입력), 채널 = 1, 높이 = 28, 너비 = 28;
      for (const 층 of 층들) {
        if (층.종류 === "conv") [x, 채널, 높이, 너비] = 합성곱(x, 채널, 높이, 너비, 층);
        else if (층.종류 === "relu") x = 렐루(x);
        else if (층.종류 === "maxpool") [x, 채널, 높이, 너비] = 최대풀링(x, 채널, 높이, 너비);
        else if (층.종류 === "linear") x = 완전연결(x, 층);
        else throw new Error("알 수 없는 층: " + 층.종류);
      }
      return x;
    }
    return { 추론 };
  }

  /** 웹 페이지에서 같은 폴더의 가중치 파일을 내려받아 모델을 만듭니다. */
  async function 모델_불러오기(폴더 = "") {
    const [정보, 바이너리] = await Promise.all([
      fetch(폴더 + "model_weights.json").then(r => { if (!r.ok) throw new Error("model_weights.json " + r.status); return r.json(); }),
      fetch(폴더 + "model_weights.bin").then(r => { if (!r.ok) throw new Error("model_weights.bin " + r.status); return r.arrayBuffer(); }),
    ]);
    return 모델_만들기(정보, 바이너리);
  }

  const 내보내기 = { 모델_만들기, 모델_불러오기 };
  if (typeof module !== "undefined" && module.exports) module.exports = 내보내기;   // Node.js 검증용
  else 전역.숫자인식CNN = 내보내기;
})(typeof window !== "undefined" ? window : globalThis);
