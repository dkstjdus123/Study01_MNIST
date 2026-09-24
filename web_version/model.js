// 작성: 2026-09-24 17:50 KST
/**
 * 순수 자바스크립트로 구현한 CNN 순전파입니다. 외부 라이브러리 없이
 * desktop_version/model.py의 숫자인식CNN과 같은 층 구조를 그대로 계산합니다.
 * 가중치는 weights.js의 전역 변수 `가중치`에서 가져옵니다 (index.html에서 이 파일보다 먼저 불러옵니다).
 */

// (채널, 높이, 너비) 형태의 3차원 배열을 data[c*H*W + h*W + w]로 저장하는 1차원 배열로 다룹니다.

function 합성곱(입력, C입력, H, W, 가중치배열, 편향배열, C출력) {
  // 3x3 커널, 패딩 1, 스트라이드 1인 합성곱입니다. 출력 크기는 입력과 같습니다(H x W).
  const 출력 = new Float32Array(C출력 * H * W);
  for (let 출력채널 = 0; 출력채널 < C출력; 출력채널++) {
    const 필터 = 가중치배열[출력채널];   // 형태: [C입력][3][3]
    const 편향값 = 편향배열[출력채널];
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        let 합 = 편향값;
        for (let 입력채널 = 0; 입력채널 < C입력; 입력채널++) {
          const 채널필터 = 필터[입력채널];
          const 입력오프셋 = 입력채널 * H * W;
          for (let dy = -1; dy <= 1; dy++) {
            const 행 = y + dy;
            if (행 < 0 || 행 >= H) continue;
            const 필터행 = 채널필터[dy + 1];
            const 행오프셋 = 입력오프셋 + 행 * W;
            for (let dx = -1; dx <= 1; dx++) {
              const 열 = x + dx;
              if (열 < 0 || 열 >= W) continue;
              합 += 입력[행오프셋 + 열] * 필터행[dx + 1];
            }
          }
        }
        출력[출력채널 * H * W + y * W + x] = 합;
      }
    }
  }
  return 출력;
}

function 배치정규화_ReLU(입력, C, H, W, 감마, 베타, 평균, 분산, 엡실론) {
  // 학습 때 저장된 이동평균/이동분산을 사용하는 추론 모드 배치정규화이며, 바로 이어서 ReLU를 적용합니다.
  const 출력 = new Float32Array(입력.length);
  for (let c = 0; c < C; c++) {
    const 척도 = 감마[c] / Math.sqrt(분산[c] + 엡실론);
    const 이동 = 베타[c] - 평균[c] * 척도;
    const 오프셋 = c * H * W;
    for (let i = 0; i < H * W; i++) {
      const 값 = 입력[오프셋 + i] * 척도 + 이동;
      출력[오프셋 + i] = 값 > 0 ? 값 : 0;
    }
  }
  return 출력;
}

function 최대풀링(입력, C, H, W) {
  // 2x2 영역에서 최댓값을 뽑아 가로세로를 절반으로 줄입니다.
  const 출력H = H / 2, 출력W = W / 2;
  const 출력 = new Float32Array(C * 출력H * 출력W);
  for (let c = 0; c < C; c++) {
    const 입력오프셋 = c * H * W;
    const 출력오프셋 = c * 출력H * 출력W;
    for (let y = 0; y < 출력H; y++) {
      for (let x = 0; x < 출력W; x++) {
        const 기준행 = 입력오프셋 + (y * 2) * W + x * 2;
        const a = 입력[기준행], b = 입력[기준행 + 1];
        const c2 = 입력[기준행 + W], d = 입력[기준행 + W + 1];
        출력[출력오프셋 + y * 출력W + x] = Math.max(a, b, c2, d);
      }
    }
  }
  return 출력;
}

function 완전연결(입력, 가중치배열, 편향배열, 출력크기) {
  // 가중치배열 형태: [출력크기][입력크기]
  const 출력 = new Float32Array(출력크기);
  for (let o = 0; o < 출력크기; o++) {
    const 행 = 가중치배열[o];
    let 합 = 편향배열[o];
    for (let i = 0; i < 입력.length; i++) 합 += 입력[i] * 행[i];
    출력[o] = 합;
  }
  return 출력;
}

function ReLU(배열) {
  const 출력 = new Float32Array(배열.length);
  for (let i = 0; i < 배열.length; i++) 출력[i] = 배열[i] > 0 ? 배열[i] : 0;
  return 출력;
}

function 소프트맥스(점수) {
  const 최대값 = Math.max(...점수);
  const 지수 = Array.from(점수, v => Math.exp(v - 최대값));
  const 합 = 지수.reduce((a, b) => a + b, 0);
  return 지수.map(v => v / 합);
}

/**
 * 28x28 흑백 이미지(Float32Array, 길이 784, 정규화까지 끝난 상태)를 받아
 * 0~9 각 숫자에 대한 확률(길이 10 배열)을 반환합니다.
 */
function 추론(입력28x28) {
  const w = 가중치;
  let x;

  x = 합성곱(입력28x28, 1, 28, 28, w.conv1_w, w.conv1_b, 32);
  x = 배치정규화_ReLU(x, 32, 28, 28, w.bn1_gamma, w.bn1_beta, w.bn1_mean, w.bn1_var, w.bn_eps);
  x = 합성곱(x, 32, 28, 28, w.conv2_w, w.conv2_b, 32);
  x = 배치정규화_ReLU(x, 32, 28, 28, w.bn2_gamma, w.bn2_beta, w.bn2_mean, w.bn2_var, w.bn_eps);
  x = 최대풀링(x, 32, 28, 28);   // → 32 x 14 x 14

  x = 합성곱(x, 32, 14, 14, w.conv3_w, w.conv3_b, 64);
  x = 배치정규화_ReLU(x, 64, 14, 14, w.bn3_gamma, w.bn3_beta, w.bn3_mean, w.bn3_var, w.bn_eps);
  x = 합성곱(x, 64, 14, 14, w.conv4_w, w.conv4_b, 64);
  x = 배치정규화_ReLU(x, 64, 14, 14, w.bn4_gamma, w.bn4_beta, w.bn4_mean, w.bn4_var, w.bn_eps);
  x = 최대풀링(x, 64, 14, 14);   // → 64 x 7 x 7 (길이 3136, fc1 입력과 순서가 같음)

  x = 완전연결(x, w.fc1_w, w.fc1_b, 256);
  x = ReLU(x);
  const 로짓 = 완전연결(x, w.fc2_w, w.fc2_b, 10);

  return 소프트맥스(로짓);
}
