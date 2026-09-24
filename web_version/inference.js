// 작성: 2026-09-24 18:19
// 외부 라이브러리 없이 순수 자바스크립트로 숫자인식CNN(desktop_version/model.py)을 추론합니다.
// 가중치는 desktop_version/export_web_weights.py가 만든 mnist_weights.bin/json을 씁니다.
// 배치정규화는 변환할 때 합성곱에 합쳐 두었고, 드롭아웃은 추론 때 아무 일도 하지 않으므로 구현하지 않습니다.
//
// 모든 특징맵은 [채널][세로][가로] 순서의 Float32Array입니다. (PyTorch의 CHW 순서와 같음)

/** mnist_weights.json(목록)과 mnist_weights.bin(ArrayBuffer)을 이름별 가중치로 나눕니다. */
export function 가중치_해석(목록, 버퍼) {
  const 전체 = new Float32Array(버퍼);   // 리틀 엔디언 float32 (브라우저·Node 모두 리틀 엔디언)
  if (전체.length !== 목록.원소수) {
    throw new Error(`가중치 개수가 맞지 않습니다: ${전체.length} ≠ ${목록.원소수}`);
  }
  const 가중치 = {};
  for (const { 이름, 형태, 오프셋 } of 목록.텐서) {
    const 개수 = 형태.reduce((a, b) => a * b, 1);
    가중치[이름] = { 값: 전체.subarray(오프셋, 오프셋 + 개수), 형태 };
  }
  return 가중치;
}

/** 브라우저에서 가중치 파일 두 개를 내려받아 해석합니다. */
export async function 모델_불러오기(폴더 = ".") {
  const [목록응답, 바이너리응답] = await Promise.all([
    fetch(`${폴더}/mnist_weights.json`), fetch(`${폴더}/mnist_weights.bin`),
  ]);
  if (!목록응답.ok || !바이너리응답.ok) throw new Error("가중치 파일을 내려받지 못했습니다");
  return 가중치_해석(await 목록응답.json(), await 바이너리응답.arrayBuffer());
}

/** 3x3 합성곱(패딩 1, 보폭 1) + ReLU. 크기는 그대로 유지됩니다. */
function 합성곱_ReLU(입력, 입력채널, 크기, { 값: 가중치, 형태 }, { 값: 편향 }) {
  const 출력채널 = 형태[0];
  const 면적 = 크기 * 크기;
  const 출력 = new Float32Array(출력채널 * 면적);
  for (let o = 0; o < 출력채널; o++) {
    const 출력면 = 출력.subarray(o * 면적, (o + 1) * 면적);
    출력면.fill(편향[o]);
    for (let c = 0; c < 입력채널; c++) {
      const 입력면 = 입력.subarray(c * 면적, (c + 1) * 면적);
      const 커널시작 = (o * 입력채널 + c) * 9;
      for (let ky = 0; ky < 3; ky++) {
        for (let kx = 0; kx < 3; kx++) {
          const w = 가중치[커널시작 + ky * 3 + kx];
          const dy = ky - 1, dx = kx - 1;
          // 입력 좌표가 범위 밖(패딩 0)인 부분은 건너뜁니다.
          const y시작 = Math.max(0, -dy), y끝 = Math.min(크기, 크기 - dy);
          const x시작 = Math.max(0, -dx), x끝 = Math.min(크기, 크기 - dx);
          for (let y = y시작; y < y끝; y++) {
            const 출력줄 = y * 크기, 입력줄 = (y + dy) * 크기 + dx;
            for (let x = x시작; x < x끝; x++) 출력면[출력줄 + x] += w * 입력면[입력줄 + x];
          }
        }
      }
    }
    for (let i = 0; i < 면적; i++) if (출력면[i] < 0) 출력면[i] = 0;
  }
  return 출력;
}

/** 2x2 최대풀링. 가로·세로가 절반이 됩니다. */
function 최대풀링(입력, 채널, 크기) {
  const 절반 = 크기 / 2;
  const 출력 = new Float32Array(채널 * 절반 * 절반);
  for (let c = 0; c < 채널; c++) {
    for (let y = 0; y < 절반; y++) {
      for (let x = 0; x < 절반; x++) {
        const i = c * 크기 * 크기 + 2 * y * 크기 + 2 * x;
        출력[(c * 절반 + y) * 절반 + x] = Math.max(입력[i], 입력[i + 1], 입력[i + 크기], 입력[i + 크기 + 1]);
      }
    }
  }
  return 출력;
}

/** 완전연결층: 출력 = 가중치 · 입력 + 편향 (가중치 형태: [출력수, 입력수]) */
function 완전연결(입력, { 값: 가중치, 형태: [출력수, 입력수] }, { 값: 편향 }, ReLU사용) {
  const 출력 = new Float32Array(출력수);
  for (let o = 0; o < 출력수; o++) {
    let 합 = 편향[o];
    const 시작 = o * 입력수;
    for (let i = 0; i < 입력수; i++) 합 += 가중치[시작 + i] * 입력[i];
    출력[o] = ReLU사용 && 합 < 0 ? 0 : 합;
  }
  return 출력;
}

/** 정규화된 28x28 입력(Float32Array 784개)을 받아 0~9 점수(로짓) 10개를 돌려줍니다. */
export function 추론(가중치, 입력) {
  const g = 가중치;
  let x = 합성곱_ReLU(입력, 1, 28, g["합성곱1.가중치"], g["합성곱1.편향"]);   // 32x28x28
  x = 합성곱_ReLU(x, 32, 28, g["합성곱2.가중치"], g["합성곱2.편향"]);          // 32x28x28
  x = 최대풀링(x, 32, 28);                                                      // 32x14x14
  x = 합성곱_ReLU(x, 32, 14, g["합성곱3.가중치"], g["합성곱3.편향"]);          // 64x14x14
  x = 합성곱_ReLU(x, 64, 14, g["합성곱4.가중치"], g["합성곱4.편향"]);          // 64x14x14
  x = 최대풀링(x, 64, 14);                                                      // 64x7x7 → 펼치면 3136
  x = 완전연결(x, g["완전연결1.가중치"], g["완전연결1.편향"], true);            // 256
  return 완전연결(x, g["완전연결2.가중치"], g["완전연결2.편향"], false);        // 10
}

/** 로짓을 확률로 바꿉니다. (큰 값에서도 넘치지 않도록 최댓값을 빼고 계산) */
export function 소프트맥스(로짓) {
  const 최대 = Math.max(...로짓);
  const 지수 = Array.from(로짓, v => Math.exp(v - 최대));
  const 합 = 지수.reduce((a, b) => a + b, 0);
  return 지수.map(v => v / 합);
}
