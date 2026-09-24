// 작성: 2026-09-24 18:17
// 웹 버전 추론·전처리 테스트입니다. 실행: web_version 폴더에서 `node --test` 또는 `npm test` (Node 18 이상)
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { 가중치_해석, 추론, 소프트맥스 } from "../inference.js";
import { 전처리 } from "../preprocess.js";

const 테스트폴더 = path.dirname(fileURLToPath(import.meta.url));
const 웹폴더 = path.dirname(테스트폴더);

function 가중치_읽기() {
  const 목록 = JSON.parse(readFileSync(path.join(웹폴더, "mnist_weights.json"), "utf-8"));
  const 파일 = readFileSync(path.join(웹폴더, "mnist_weights.bin"));
  return 가중치_해석(목록, 파일.buffer.slice(파일.byteOffset, 파일.byteOffset + 파일.byteLength));
}
const 가중치 = 가중치_읽기();

test("자바스크립트 추론이 PyTorch 출력(reference.json)과 같다", () => {
  const 기준 = JSON.parse(readFileSync(path.join(테스트폴더, "reference.json"), "utf-8"));
  for (const { 입력, 로짓 } of 기준) {
    const 결과 = 추론(가중치, Float32Array.from(입력));
    assert.equal(결과.length, 10);
    결과.forEach((값, i) => assert.ok(Math.abs(값 - 로짓[i]) < 1e-3, `${i}번 로짓: ${값} ≠ ${로짓[i]}`));
  }
});

test("소프트맥스 합은 1이고 가장 큰 로짓이 가장 큰 확률이 된다", () => {
  const 확률 = 소프트맥스([1, 3, 2, 1000]);
  assert.ok(Math.abs(확률.reduce((a, b) => a + b, 0) - 1) < 1e-9);
  assert.equal(확률.indexOf(Math.max(...확률)), 3);
});

test("빈 그림판은 전처리 결과가 null이다", () => {
  assert.equal(전처리(new Uint8Array(280 * 280), 280, 280), null);
});

test("전처리는 긴 변을 20px로 맞추고 무게중심을 (14, 14) 근처로 옮긴다", () => {
  // 왼쪽 위 구석에 가로 40 x 세로 100 짜리 흰 직사각형을 그립니다.
  const 그림 = new Uint8Array(280 * 280);
  for (let y = 10; y < 110; y++) for (let x = 5; x < 45; x++) 그림[y * 280 + x] = 255;
  const 입력 = 전처리(그림, 280, 280);
  assert.equal(입력.length, 784);

  const 배경 = (0 - 0.1307) / 0.3081;
  let 합 = 0, 중심x = 0, 중심y = 0, 위 = 28, 아래 = -1;
  for (let i = 0; i < 784; i++) {
    const 밝기 = 입력[i] * 0.3081 + 0.1307;
    if (입력[i] > 배경 + 1e-6) { 위 = Math.min(위, Math.floor(i / 28)); 아래 = Math.max(아래, Math.floor(i / 28)); }
    합 += 밝기; 중심x += (i % 28) * 밝기; 중심y += Math.floor(i / 28) * 밝기;
  }
  assert.ok(아래 - 위 + 1 >= 20 && 아래 - 위 + 1 <= 22, `세로 길이 ${아래 - 위 + 1}`);
  assert.ok(Math.abs(중심x / 합 - 14) <= 0.5 && Math.abs(중심y / 합 - 14) <= 0.5);
});

// MNIST 테스트 이미지를 280x280으로 키워 앱과 같은 경로(전처리 → 추론)로 인식률을 잽니다.
// desktop_version에서 train.py를 한 번 실행해 데이터가 있을 때만 동작합니다.
const MNIST경로 = path.join(웹폴더, "..", "desktop_version", "data", "MNIST", "raw");
test("MNIST 테스트 이미지 500장 인식률이 97% 이상이다", { skip: !existsSync(path.join(MNIST경로, "t10k-images-idx3-ubyte")) }, () => {
  const 이미지들 = readFileSync(path.join(MNIST경로, "t10k-images-idx3-ubyte")).subarray(16);
  const 정답들 = readFileSync(path.join(MNIST경로, "t10k-labels-idx1-ubyte")).subarray(8);
  let 맞은개수 = 0;
  for (let n = 0; n < 500; n++) {
    const 큰그림 = new Uint8Array(280 * 280);
    for (let y = 0; y < 280; y++) for (let x = 0; x < 280; x++)
      큰그림[y * 280 + x] = 이미지들[n * 784 + Math.floor(y / 10) * 28 + Math.floor(x / 10)];
    const 확률 = 소프트맥스(추론(가중치, 전처리(큰그림, 280, 280)));
    if (확률.indexOf(Math.max(...확률)) === 정답들[n]) 맞은개수++;
  }
  console.log(`  MNIST 인식률: ${맞은개수}/500`);
  assert.ok(맞은개수 >= 485, `${맞은개수}/500`);
});
