// 작성: 2026-09-24 21:56
// 태스크 4~6 검사: 로컬 서버를 켜고 실제 Chromium으로 검증.html과 웹 앱 화면을 확인합니다.
// 실행 (저장소 루트): NODE_PATH="$(npm root -g)" node 검사/웹_검사.cjs [순전파|전처리|화면]  (인자가 없으면 전부)
"use strict";
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");

const 루트 = path.resolve(__dirname, "..");
const 포트 = 8765;
const 주소 = `http://localhost:${포트}`;

function 확인(조건, 메시지) {
  if (!조건) throw new Error("실패: " + 메시지);
  console.log("통과: " + 메시지);
}

async function 서버_켜기() {
  const 파이썬 = process.platform === "win32" ? "python" : "python3";
  const 서버 = spawn(파이썬, ["-m", "http.server", String(포트), "--directory", 루트], { stdio: "ignore" });
  for (let i = 0; i < 50; i++) {
    try { await fetch(주소); return 서버; } catch { await new Promise(r => setTimeout(r, 100)); }
  }
  서버.kill();
  throw new Error("로컬 서버가 켜지지 않았습니다");
}

async function 검증표_읽기(페이지) {
  await 페이지.goto(`${주소}/web_version/검증.html`);
  await 페이지.waitForFunction(() => !document.getElementById("요약").textContent.includes("검증 중"),
                               null, { timeout: 180000 });
  return 페이지.$$eval("#요약 table tbody tr", 줄들 => 줄들.map(줄 => [...줄.children].map(칸 => 칸.textContent)));
}

async function 순전파_검사(브라우저) {
  const 표 = await 검증표_읽기(await 브라우저.newPage());
  const 줄 = 표.find(([항목]) => 항목 === "순전파 일치");
  확인(줄 && 줄[3] === "통과", `순전파 일치: 확률 최대 절대차 ${줄 ? 줄[2] : "없음"} ≤ 1e-4`);
}

const 검사목록 = { 순전파: 순전파_검사 };   // 태스크 5, 6에서 항목을 더함

(async () => {
  const 고른것 = process.argv[2];
  const 서버 = await 서버_켜기();
  const 브라우저 = await chromium.launch();
  try {
    for (const [이름, 검사] of Object.entries(검사목록)) if (!고른것 || 고른것 === 이름) await 검사(브라우저);
  } finally {
    await 브라우저.close();
    서버.kill();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
