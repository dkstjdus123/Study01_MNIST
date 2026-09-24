// 작성: 2026-09-24 19:20 (수정: 2026-09-24 19:25 가중치.bin/가중치정보.json 형식, 파일 이름 변경 / 19:37 가중치 파일 검사 추가)
// 가중치 적재 + 순전파: 외부 라이브러리 없이 순수 자바스크립트로 숫자인식CNN을 계산합니다.
// 가중치는 desktop_version/가중치내보내기.py가 만든 가중치정보.json(층 구조·형상·정규화 상수) + 가중치.bin(float32 값)을 씁니다.
// 배치정규화는 내보낼 때 합성곱에 미리 합쳤고, 드롭아웃은 추론 때 항등이므로
// 여기서는 합성곱(3x3, 패딩 1)·ReLU·2x2 최대풀링·전결합만 계산합니다.

(function (전역) {
  "use strict";

  // 3x3 합성곱 (패딩 1, 보폭 1): [입력채널][높이][너비] → [출력채널][높이][너비]
  function 합성곱(입력, 채널, 높이, 너비, 층) {
    const [출력채널, 입력채널] = 층.가중치형상;
    if (입력채널 !== 채널) throw new Error(`${층.이름}: 입력 채널이 맞지 않습니다 (${채널} ≠ ${입력채널})`);
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

  // 전결합: 출력 = 가중치 · 입력 + 편향 (입력은 PyTorch Flatten과 같은 [채널][높이][너비] 순서)
  function 전결합(입력, 층) {
    const [출력수, 입력수] = 층.가중치형상;
    if (입력.length !== 입력수) throw new Error(`${층.이름}: 입력 크기가 맞지 않습니다 (${입력.length} ≠ ${입력수})`);
    const 출력 = new Float32Array(출력수);
    for (let o = 0; o < 출력수; o++) {
      let 합 = 층.편향[o];
      const 시작 = o * 입력수;
      for (let i = 0; i < 입력수; i++) 합 += 층.가중치[시작 + i] * 입력[i];
      출력[o] = 합;
    }
    return 출력;
  }

  /** 가중치정보(JSON 객체)와 가중치 바이너리(ArrayBuffer)로 모델을 만듭니다. */
  function 모델_만들기(정보, 바이너리) {
    // 파일이 잘렸거나 정보와 맞지 않으면 Float32Array가 알아보기 힘든 RangeError를 내므로 미리 검사합니다.
    if (바이너리.byteLength % 4 !== 0)
      throw new Error(`가중치.bin 크기(${바이너리.byteLength}바이트)가 4의 배수가 아닙니다. 파일이 손상되었을 수 있습니다.`);
    const 전체개수 = 바이너리.byteLength / 4;
    const 값 = (조각) => {
      const 형상곱 = 조각.형상.reduce((a, b) => a * b, 1);
      if (형상곱 !== 조각.개수 || 조각.오프셋 < 0 || 조각.오프셋 + 조각.개수 > 전체개수)
        throw new Error(`가중치정보.json과 가중치.bin이 맞지 않습니다 (형상 ${조각.형상}, 오프셋 ${조각.오프셋}). 가중치내보내기.py를 다시 실행하세요.`);
      return new Float32Array(바이너리, 조각.오프셋 * 4, 조각.개수);
    };
    const 층들 = 정보.층.map(층 => 층.가중치
      ? { 종류: 층.종류, 이름: 층.이름, 가중치: 값(층.가중치), 가중치형상: 층.가중치.형상, 편향: 값(층.편향) }
      : { 종류: 층.종류, 이름: 층.이름 });

    /** 정규화된 28x28 입력(784개)을 받아 0~9 각 숫자의 점수(로짓) 10개를 돌려줍니다. */
    function 추론(입력) {
      let x = Float32Array.from(입력), 채널 = 1, 높이 = 28, 너비 = 28;
      for (const 층 of 층들) {
        if (층.종류 === "conv") [x, 채널, 높이, 너비] = 합성곱(x, 채널, 높이, 너비, 층);
        else if (층.종류 === "relu") x = 렐루(x);
        else if (층.종류 === "maxpool") [x, 채널, 높이, 너비] = 최대풀링(x, 채널, 높이, 너비);
        else if (층.종류 === "linear") x = 전결합(x, 층);
        else throw new Error("알 수 없는 층 종류: " + 층.종류);
      }
      return x;
    }
    // 정규화 상수는 파이썬이 내보낸 값을 그대로 씁니다 (자바스크립트에 따로 적지 않음).
    return { 추론, 평균: 정보.평균, 표준편차: 정보.표준편차 };
  }

  async function 파일받기(경로, 형식) {
    const 응답 = await fetch(경로);
    if (!응답.ok) throw new Error(`${경로}를 내려받지 못했습니다 (${응답.status})`);
    return 형식 === "json" ? 응답.json() : 응답.arrayBuffer();
  }

  /** 같은 폴더의 가중치정보.json + 가중치.bin을 내려받아 모델을 만듭니다. */
  async function 모델_불러오기(폴더 = "") {
    const [정보, 바이너리] = await Promise.all([
      파일받기(폴더 + "가중치정보.json", "json"),
      파일받기(폴더 + "가중치.bin", "bin"),
    ]);
    return 모델_만들기(정보, 바이너리);
  }

  const 내보내기 = { 모델_만들기, 모델_불러오기 };
  if (typeof module !== "undefined" && module.exports) module.exports = 내보내기;   // Node.js 검증용
  else 전역.모델 = 내보내기;
})(typeof window !== "undefined" ? window : globalThis);
