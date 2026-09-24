// 작성: 2026-09-24 21:56 (수정: 2026-09-24 22:00 서버 정리 보강 / 22:03 전처리 검사 추가 / 22:07 화면 검사 추가 / 22:13 루트 이동 검사 보강 / 22:30 NaN 검사와 Windows file URL 보정)
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

async function 전처리_검사(브라우저) {
  const 표 = await 검증표_읽기(await 브라우저.newPage());
  for (const 항목 of ["전처리 일치", "예측 일치", "전체 정확도"]) {
    const 줄 = 표.find(([이름]) => 이름 === 항목);
    확인(줄 && 줄[3] === "통과", `${항목}: ${줄 ? 줄[2] : "없음"}`);
  }
}

const 학번이름 = "학번 2601953 이름 안서연";

// 그림판 좌표(0~280) 점들을 마우스로 잇습니다.
async function 획_긋기(페이지, 점들, 버튼 = "left") {
  const 틀 = await 페이지.locator("#그림판").boundingBox();
  const 배율 = 틀.width / 280;
  await 페이지.mouse.move(틀.x + 점들[0][0] * 배율, 틀.y + 점들[0][1] * 배율);
  await 페이지.mouse.down({ button: 버튼 });
  for (const [x, y] of 점들.slice(1)) await 페이지.mouse.move(틀.x + x * 배율, 틀.y + y * 배율, { steps: 5 });
  await 페이지.mouse.up({ button: 버튼 });
}
const 일자 = [[140, 40], [140, 240]];
const 동그라미 = Array.from({ length: 41 }, (_, i) =>
  [140 + 70 * Math.sin(i / 40 * 2 * Math.PI), 140 - 95 * Math.cos(i / 40 * 2 * Math.PI)]);

async function 새_페이지(브라우저) {
  const 페이지 = await 브라우저.newPage();
  페이지.외부요청 = []; 페이지.오류 = [];
  페이지.on("request", 요청 => { const u = 요청.url(); if (!u.startsWith(주소) && !u.startsWith("file:")) 페이지.외부요청.push(u); });
  페이지.on("pageerror", 오류 => 페이지.오류.push(오류.message));
  return 페이지;
}
const 예측읽기 = 페이지 => 페이지.locator("#예측").textContent();
const 모델준비 = 페이지 => 페이지.waitForFunction(() => document.getElementById("신뢰도").textContent.includes("그려 보세요"));

async function 화면_검사(브라우저) {
  // 루트 주소 → web_version/ 이동
  let 페이지 = await 새_페이지(브라우저);
  await 페이지.goto(`${주소}/`);
  const 이동함 = await 페이지.waitForURL(/\/web_version\/(index\.html)?$/, { timeout: 5000 }).then(() => true, () => false);
  확인(이동함, "루트 주소가 web_version/으로 이동");
  확인(await 페이지.getByText(학번이름).isVisible(), "맨 위에 학번·이름 표시");
  await 모델준비(페이지);

  await 획_긋기(페이지, 일자);
  await 페이지.waitForFunction(() => document.getElementById("예측").textContent !== "?");
  확인(await 예측읽기(페이지) === "1", "세로 한 획을 1로 인식");
  await 페이지.click("#지우기");
  확인(await 예측읽기(페이지) === "?", "[집중 2] 지우기 후 예측이 ?");
  await 획_긋기(페이지, 동그라미);
  await 페이지.waitForFunction(() => document.getElementById("예측").textContent !== "?");
  확인(await 예측읽기(페이지) === "0", "동그라미를 0으로 인식");

  await 페이지.click("#지우기");
  await 획_긋기(페이지, [[2, 2], [4, 3]]);
  await 페이지.waitForTimeout(300);
  const 신뢰도글 = await 페이지.locator("#신뢰도").textContent();
  확인(/^[0-9?]$/.test(await 예측읽기(페이지)) && 페이지.오류.length === 0 && !신뢰도글.includes("NaN"), "[집중 3] 가장자리 작은 점에도 오류·NaN 없음");

  await 페이지.click("#지우기");
  await 획_긋기(페이지, 일자, "right");
  await 페이지.waitForTimeout(300);
  확인(await 예측읽기(페이지) === "?", "[집중 4] 오른쪽 버튼으로는 그려지지 않음");
  확인(페이지.외부요청.length === 0, `외부 요청 0건 (${페이지.외부요청.join(", ")})`);
  await 페이지.close();

  // [집중 1] 모델을 불러오는 중에 그린 숫자도 불러온 뒤 인식
  페이지 = await 새_페이지(브라우저);
  await 페이지.route("**/*.bin", async 경로 => { await new Promise(r => setTimeout(r, 1500)); await 경로.continue(); });   // 파일명(가중치.bin)이 URL에서 퍼센트 인코딩되어 한글 패턴이 매칭되지 않아 확장자 패턴으로 조정
  await 페이지.goto(`${주소}/web_version/`, { waitUntil: "domcontentloaded" });
  await 획_긋기(페이지, 일자);
  확인(await 예측읽기(페이지) === "?", "[집중 1] 불러오기 전에는 아직 ?");
  await 페이지.waitForFunction(() => document.getElementById("예측").textContent !== "?", null, { timeout: 10000 });
  확인(await 예측읽기(페이지) === "1", "[집중 1] 불러온 뒤 그려 둔 1을 인식");
  await 페이지.close();

  // [집중 5] 파일로 직접 열기
  페이지 = await 새_페이지(브라우저);
  await 페이지.goto(require("url").pathToFileURL(path.join(루트, "web_version", "index.html")).href);
  await 페이지.waitForFunction(() => document.getElementById("신뢰도").textContent.includes("http.server"));
  확인(await 페이지.getByText(학번이름).isVisible(), "[집중 5] file://로 열어도 학번·이름 표시와 로컬 서버 안내");
  await 페이지.close();
}

const 검사목록 = { 순전파: 순전파_검사, 전처리: 전처리_검사, 화면: 화면_검사 };

(async () => {
  const 고른것 = process.argv[2];
  const 서버 = await 서버_켜기();
  let 브라우저;
  try {
    브라우저 = await chromium.launch();
    for (const [이름, 검사] of Object.entries(검사목록)) if (!고른것 || 고른것 === 이름) await 검사(브라우저);
  } finally {
    if (브라우저) await 브라우저.close().catch(() => {});
    서버.kill();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
