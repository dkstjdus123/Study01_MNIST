// 작성: 2026-09-25 09:19
// 가중치를 불러와 숫자인식CNN을 순수 자바스크립트로 계산합니다 (외부 라이브러리 없음).
// 가중치는 desktop_version/가중치내보내기.py가 만든 가중치정보.json(층 구조) + 가중치.bin(float32 값)을 씁니다.
// 배치정규화는 합성곱에 합쳐져 있으므로 합성곱(3x3, 패딩 1)·ReLU·2x2 최대풀링·펼치기·전결합만 계산합니다.
// 텐서는 PyTorch와 같은 [채널][높이][너비] 순서의 Float32Array입니다.

(function (전역) {
  "use strict";

  function 합성곱(입력, 입력채널, 높이, 너비, 가중치, 편향, 출력채널) {
    const 면적 = 높이 * 너비;
    const 출력 = new Float32Array(출력채널 * 면적);
    for (let o = 0; o < 출력채널; o++) {
      const 출력면 = o * 면적;
      출력.fill(편향[o], 출력면, 출력면 + 면적);
      for (let c = 0; c < 입력채널; c++) {
        const 입력면 = c * 면적;
        for (let ky = 0; ky < 3; ky++) {
          for (let kx = 0; kx < 3; kx++) {
            const w = 가중치[((o * 입력채널 + c) * 3 + ky) * 3 + kx];
            const dy = ky - 1, dx = kx - 1;
            const y시작 = Math.max(0, -dy), y끝 = Math.min(높이, 높이 - dy);
            const x시작 = Math.max(0, -dx), x끝 = Math.min(너비, 너비 - dx);
            for (let y = y시작; y < y끝; y++) {
              const 출력줄 = 출력면 + y * 너비, 입력줄 = 입력면 + (y + dy) * 너비 + dx;
              for (let x = x시작; x < x끝; x++) 출력[출력줄 + x] += w * 입력[입력줄 + x];
            }
          }
        }
      }
    }
    return 출력;
  }

  function 렐루(입력) {
    const 출력 = new Float32Array(입력.length);
    for (let i = 0; i < 입력.length; i++) 출력[i] = 입력[i] > 0 ? 입력[i] : 0;
    return 출력;
  }

  function 최대풀링(입력, 채널, 높이, 너비) {
    const 새높이 = 높이 >> 1, 새너비 = 너비 >> 1;
    const 출력 = new Float32Array(채널 * 새높이 * 새너비);
    for (let c = 0; c < 채널; c++) {
      for (let y = 0; y < 새높이; y++) {
        for (let x = 0; x < 새너비; x++) {
          const 왼위 = c * 높이 * 너비 + 2 * y * 너비 + 2 * x;
          출력[(c * 새높이 + y) * 새너비 + x] =
            Math.max(입력[왼위], 입력[왼위 + 1], 입력[왼위 + 너비], 입력[왼위 + 너비 + 1]);
        }
      }
    }
    return 출력;
  }

  function 전결합(입력, 가중치, 편향, 출력수) {
    const 입력수 = 입력.length, 출력 = new Float32Array(출력수);
    for (let o = 0; o < 출력수; o++) {
      let 합 = 편향[o];
      const 줄 = o * 입력수;
      for (let i = 0; i < 입력수; i++) 합 += 가중치[줄 + i] * 입력[i];
      출력[o] = 합;
    }
    return 출력;
  }

  // 가중치.bin의 한 텐서를 복사 없이 Float32Array로 봅니다. 형상·범위가 맞지 않으면 알아보기 쉬운 오류를 냅니다.
  function 텐서_꺼내기(버퍼, 정보, 이름) {
    let 개수 = 1;
    for (const n of 정보.형상) 개수 *= n;
    if (개수 !== 정보.개수) throw new Error(`${이름}: 형상과 개수가 맞지 않습니다.`);
    if (정보.오프셋 < 0 || (정보.오프셋 + 정보.개수) * 4 > 버퍼.byteLength) {
      throw new Error(`${이름}: 가중치.bin의 범위를 벗어납니다.`);
    }
    return new Float32Array(버퍼, 정보.오프셋 * 4, 정보.개수);
  }

  async function 모델_불러오기(기본주소 = "") {
    const [정보응답, 가중치응답] = await Promise.all([
      fetch(기본주소 + "가중치정보.json"), fetch(기본주소 + "가중치.bin"),
    ]);
    if (!정보응답.ok || !가중치응답.ok) throw new Error("가중치 파일을 불러오지 못했습니다.");
    const 정보 = await 정보응답.json();
    const 버퍼 = await 가중치응답.arrayBuffer();
    if (버퍼.byteLength % 4 !== 0) throw new Error("가중치.bin의 크기가 4의 배수가 아닙니다.");

    const 층들 = 정보.층.map(층 => ({
      종류: 층.종류,
      형상: 층.가중치 ? 층.가중치.형상 : null,
      가중치: 층.가중치 ? 텐서_꺼내기(버퍼, 층.가중치, 층.이름) : null,
      편향: 층.편향 ? 텐서_꺼내기(버퍼, 층.편향, 층.이름) : null,
    }));
    const [시작채널, 시작높이, 시작너비] = 정보.입력형상;

    function 추론(입력) {
      let x = 입력, 채널 = 시작채널, 높이 = 시작높이, 너비 = 시작너비;
      for (const 층 of 층들) {
        if (층.종류 === "conv") {
          x = 합성곱(x, 채널, 높이, 너비, 층.가중치, 층.편향, 층.형상[0]);
          채널 = 층.형상[0];
        } else if (층.종류 === "relu") {
          x = 렐루(x);
        } else if (층.종류 === "maxpool") {
          x = 최대풀링(x, 채널, 높이, 너비);
          높이 >>= 1;
          너비 >>= 1;
        } else if (층.종류 === "flatten") {
          // [채널][높이][너비] 순서가 PyTorch의 flatten 순서와 같으므로 할 일이 없습니다.
        } else if (층.종류 === "linear") {
          x = 전결합(x, 층.가중치, 층.편향, 층.형상[0]);
        } else {
          throw new Error(`계산할 수 없는 층입니다: ${층.종류}`);
        }
      }
      return x;
    }

    return { 추론, 평균: 정보.평균, 표준편차: 정보.표준편차 };
  }

  const 내보내기 = { 모델_불러오기 };
  전역.모델 = 내보내기;
  if (typeof module !== "undefined" && module.exports) module.exports = 내보내기;
})(typeof window !== "undefined" ? window : globalThis);
