<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();

// ── Constants ──────────────────────────────────────────────
const CW = 640, CH = 320;
const FLOOR = 248;
const NPC_X = 548;
const NEAR_DIST = 64;
const SPD = 2.8;
const JUMP_VY = -7.5;
const GRAVITY = 0.40;

// ── Reactive state ─────────────────────────────────────────
const gameCanvas = ref(null);
const sceneIndex = ref(0);
const interactionOpen = ref(false);
const introSpeechDismissed = ref(false);
const answers = ref([]);
const saveMessage = ref("");
const resultSaving = ref(false);
const resultSaved = ref(false);
// Reactive playerX so computed props stay in sync
const playerX = ref(60);

// ── Mutable game state (non-reactive for perf) ─────────────
const pl = { x: 60, y: FLOOR, vy: 0, grounded: true, dir: 1, frame: 0, ft: 0 };
let ctx = null, raf = null, prev = 0;
const keys = {};
let interactLock = false;

// ── Audio ──────────────────────────────────────────────────
let aCtx = null;
function ac() { if (!aCtx) aCtx = new (window.AudioContext || window.webkitAudioContext)(); return aCtx; }
function beep(freq, dur = 0.08, type = "square", vol = 0.1) {
  try {
    const a = ac(), o = a.createOscillator(), g = a.createGain();
    o.connect(g); g.connect(a.destination);
    o.type = type; o.frequency.setValueAtTime(freq, a.currentTime);
    g.gain.setValueAtTime(vol, a.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, a.currentTime + dur);
    o.start(); o.stop(a.currentTime + dur);
  } catch {}
}
const sndStep    = () => beep(140 + Math.random() * 20, 0.035, "square", 0.05);
const sndJump    = () => { beep(330, 0.05); setTimeout(() => beep(520, 0.08), 50); };
const sndHit     = () => [440, 550, 660].forEach((f, i) => setTimeout(() => beep(f, 0.09), i * 55));
const sndChoose  = () => [330, 440, 550, 880].forEach((f, i) => setTimeout(() => beep(f, 0.07), i * 45));

// ── Scenes ─────────────────────────────────────────────────
const scenes = [
  { id:"gate",    type:"intro",  title:"원정의 시작",      theme:"gate",    actor:"fairy",
    npcName:"루미", fairy:"A·D (또는 ← →) 이동, W (또는 ↑) 점프, Z (또는 Space) 상호작용!",
    text:"NPC 곁에 다가가 Z를 눌러. 장면마다 선택지를 고르면 다음 스테이지가 열려.", tags:["튜토리얼"] },
  { id:"rival",   title:"다리 위의 라이벌",  theme:"arena",   actor:"rival",
    npcName:"도전자", fairy:"저 플레이어가 길을 막고 있어. 다가가서 말을 걸어봐.",
    text:"우하하 나와 실력을 겨루자!!", tags:["경쟁","대전"],
    choices:[
      { text:"바로 승부한다",    tone:"승부욕이 올라온다",   scores:{competitive:3,action:1},    tags:["경쟁형","PvP선호"] },
      { text:"패턴 보고 공략",   tone:"이길 방법부터 찾는다", scores:{strategy:3,challenge:1},    tags:["전략형","공략선호"] },
      { text:"돌아가는 길 찾기", tone:"굳이 싸울 필요는 없다", scores:{cozy:2,exploration:2},     tags:["탐험형","평화선호"] },
    ]},
  { id:"helper",  title:"고장 난 수레",      theme:"village", actor:"helper",
    npcName:"여행자", fairy:"수레 바퀴가 빠졌대. 다가가서 도움을 줄 수 있어.",
    text:"도와줘!! 내 수레에 바퀴가 빠져서 집에 갈 수 없어!ㅠㅠ", tags:["협동","선택"],
    choices:[
      { text:"같이 고쳐준다",    tone:"같이 해결하는 게 좋다", scores:{social:3,story:1},         tags:["협동형","서포터"] },
      { text:"도구만 건네준다",  tone:"효율적으로 돕는다",     scores:{strategy:2,social:1},      tags:["실용형","균형형"] },
      { text:"먼저 목표로 간다", tone:"메인 목표가 우선이다",  scores:{action:2,competitive:1},   tags:["목표지향","속도중시"] },
    ]},
  { id:"scenery", title:"노을빛 숲길",        theme:"forest",  actor:"scenery",
    npcName:"샛길", fairy:"저쪽 샛길이 엄청 예뻐. 가볼 만할 것 같아.",
    text:"이 샛길로 가면 오래걸리지만 숨겨진 멋진 풍경과 작은 선물들이 있어", tags:["탐험","감성"],
    choices:[
      { text:"샛길로 돌아간다",  tone:"맵 구경은 못 참아",     scores:{exploration:3,cozy:1},     tags:["탐험형","오픈월드"] },
      { text:"풍경만 보고 복귀", tone:"분위기와 진행 둘 다",   scores:{story:2,strategy:1},       tags:["균형형","서사선호"] },
      { text:"메인 길로 간다",   tone:"목표 동선이 중요해",     scores:{challenge:2,action:1},     tags:["진행중시","목표형"] },
    ]},
  { id:"ruin",    title:"어두운 유적",        theme:"dungeon", actor:"dungeon",
    npcName:"수상한 문", fairy:"문 앞까지 가보자. 안쪽은 위험하지만 보상이 있을 수도 있어.",
    text:"이 문으로 들어오면 강한 몬스터와 함정이 있지만 숨겨진 보물들이 있다", tags:["도전","공포"],
    choices:[
      { text:"위험해도 들어간다",  tone:"실패해도 다시 하면 돼", scores:{challenge:3,action:1},    tags:["도전형","하드코어"] },
      { text:"단서 모은 뒤 진입", tone:"준비한 만큼 편해진다",  scores:{strategy:3,exploration:1},tags:["전략형","퍼즐선호"] },
      { text:"오늘은 밝은 곳이 좋아", tone:"긴장감은 피하고 싶어", scores:{cozy:3,story:1},       tags:["힐링형","라이트유저"] },
    ]},
  { id:"market",  title:"보드게임 상인의 마차",   theme:"market",  actor:"shop",
    npcName:"상인", fairy:"마지막이야! 상인이 게임 살 때의 습관을 물어볼 거야.",
    text:"없는게 없지만 우리 상점 보드게임 가격은 항상 변한다구!", tags:["구매성향"],
    choices:[
      { text:"가격 변동 파악하기",     tone:"가격 타이밍이 제일 중요해", scores:{strategy:2,cozy:1},       tags:["할인헌터","가성비"] },
      { text:"같이 할 수 있는지 본다", tone:"같이 하면 훨씬 재밌어",      scores:{social:3,competitive:1},  tags:["파티플레이","멀티선호"] },
      { text:"보드게임 표지 보고 바로 구매", tone:"꽂히면 바로 시작!",           scores:{action:2,story:2},        tags:["직감형","몰입형"] },
    ]},
  { id:"result",  type:"result", title:"선택의 제단",  theme:"result",  actor:"fairy",
    npcName:"루미", fairy:"여기까지 직접 걸어온 선택들이 꽤 선명해졌어.",
    text:"이번 모험에서 고른 행동을 바탕으로 취향 태그를 만들었어.", tags:["결과"] },
];

const resultProfiles = {
  competitive:{ title:"승부욕 있는 랭커형",       summary:"실시간 대결, 랭크, 성과가 보이는 게임에서 몰입도가 높아요.", tags:["경쟁형","PvP선호","랭크도전"],   games:["Apex Legends","Street Fighter 6","Valorant"] },
  strategy:   { title:"계획 세우는 공략가형",     summary:"정보를 모으고 빌드를 짜서 깔끔하게 해결하는 플레이를 좋아해요.", tags:["전략형","공략선호","퍼즐선호"],  games:["Baldur's Gate 3","Civilization VI","Into the Breach"] },
  exploration:{ title:"샛길 좋아하는 탐험가형",  summary:"메인 목표보다 숨겨진 길, 풍경, 수집 요소에서 재미를 크게 느껴요.", tags:["탐험형","오픈월드","수집선호"],  games:["Elden Ring","Zelda ToTK","No Man's Sky"] },
  social:     { title:"같이 놀 때 강한 파티형",   summary:"혼자보다 같이 역할을 나누고 웃으면서 진행할 때 게임이 살아나요.", tags:["협동형","파티플레이","서포터"],  games:["Helldivers 2","It Takes Two","Monster Hunter"] },
  story:      { title:"서사 몰입형 플레이어",     summary:"인물, 분위기, 선택의 의미가 살아있는 게임에서 가장 오래 머물러요.", tags:["서사선호","몰입형","감성플레이"],games:["Disco Elysium","Life is Strange","Cyberpunk 2077"] },
  action:     { title:"손맛 빠른 액션형",         summary:"빠른 판단, 조작감, 즉각적인 피드백이 있는 게임이 잘 맞아요.", tags:["액션형","속도중시","컨트롤"],    games:["Hades","Devil May Cry 5","Dead Cells"] },
  challenge:  { title:"다시 도전하는 하드코어형", summary:"어려운 구간을 넘었을 때의 성취감이 게임의 핵심 재미예요.", tags:["도전형","하드코어","보스전"],     games:["Sekiro","Hollow Knight","Darkest Dungeon"] },
  cozy:       { title:"천천히 즐기는 힐링형",     summary:"부담 없는 진행, 예쁜 분위기, 내 속도대로 하는 플레이가 좋아요.", tags:["힐링형","라이트유저","평화선호"],games:["Stardew Valley","Dave the Diver","Unpacking"] },
};

// ── Computed ───────────────────────────────────────────────
const currentScene   = computed(() => scenes[sceneIndex.value]);
const playableScenes = computed(() => scenes.filter(s => s.choices));
const completedCount = computed(() => answers.value.length);
const isComplete     = computed(() => currentScene.value.type === "result");
const hudStageLabel  = computed(() => {
  if (currentScene.value.type === "intro") return "START";
  if (isComplete.value) return "RESULT";
  return `STAGE ${Math.min(completedCount.value + 1, playableScenes.value.length)} / ${playableScenes.value.length}`;
});
const isNearNpc      = computed(() => Math.abs(playerX.value - NPC_X) <= NEAR_DIST);
const canInteract    = computed(() => isNearNpc.value && !interactionOpen.value && !isComplete.value);

const scores = computed(() => {
  const t = {};
  answers.value.forEach(a => Object.entries(a.scores).forEach(([k,v]) => { t[k] = (t[k]||0)+v; }));
  return t;
});
const topKey = computed(() => {
  const e = Object.entries(scores.value);
  return e.length ? e.sort((a,b)=>b[1]-a[1])[0][0] : "exploration";
});
const result = computed(() => {
  const base = resultProfiles[topKey.value] || resultProfiles.exploration;
  const picked = answers.value.flatMap(a => a.tags);
  return { ...base, tags: Array.from(new Set([...base.tags, ...picked])).slice(0, 8) };
});

// ── Draw helpers ───────────────────────────────────────────
function r(x, y, w, h, c) { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w, h); }

// ── Background per theme ───────────────────────────────────
const BG = {
  gate:   { sky:["#5ba3d8","#8ecae6"], g1:"#4a8b3a", g2:"#3a7a2a" },
  arena:  { sky:["#c8703a","#e89a60"], g1:"#a85a28", g2:"#884818" },
  village:{ sky:["#78c0f0","#a8dcff"], g1:"#56a840", g2:"#469030" },
  forest: { sky:["#2a6a48","#4a9060"], g1:"#1a5228", g2:"#0e4020" },
  dungeon:{ sky:["#10121c","#181c28"], g1:"#181c2c", g2:"#101420" },
  market: { sky:["#d8a840","#f0cc70"], g1:"#b88830", g2:"#987020" },
  result: { sky:["#280e52","#482878"], g1:"#1c0a38", g2:"#140626" },
};

function drawBg(theme, t) {
  const b = BG[theme] || BG.gate;
  const g = ctx.createLinearGradient(0, 0, 0, FLOOR);
  g.addColorStop(0, b.sky[0]); g.addColorStop(1, b.sky[1]);
  ctx.fillStyle = g; ctx.fillRect(0, 0, CW, CH);
  r(0, FLOOR, CW, 6, b.g2);
  r(0, FLOOR+6, CW, CH-FLOOR-6, b.g1);

  if (theme === "gate") {
    // Mountains
    for (let i=0;i<4;i++) {
      const mx = (i*180 - t*0.008) % (CW+160) - 80;
      ctx.fillStyle = `hsl(210,${22+i*4}%,${30+i*4}%)`;
      ctx.beginPath(); ctx.moveTo(mx,FLOOR); ctx.lineTo(mx+80,FLOOR-60-i*12); ctx.lineTo(mx+160,FLOOR); ctx.fill();
    }
    cloud(80-t*0.014,22,1); cloud(340-t*0.009,42,0.72);
    sun(CW-80,24);
  }
  if (theme === "arena") {
    ctx.fillStyle = "rgba(200,80,20,0.08)"; ctx.fillRect(0,0,CW,CH);
    for (let i=0;i<4;i++) { r(60+i*160,FLOOR-60,18,60,"#a85028"); r(55+i*160,FLOOR-68,28,12,"#c07040"); }
    cloud(120-t*0.012,30,0.6); cloud(400-t*0.008,50,0.5);
  }
  if (theme === "village") {
    house(30,FLOOR); house(220,FLOOR); house(430,FLOOR);
    cloud(70-t*0.008,28,0.9); cloud(310-t*0.011,46,0.65);
  }
  if (theme === "forest") {
    for (let i=0;i<7;i++) { const tx=(i*100-t*0.018)%(CW+80)-40; tree(tx,FLOOR,["#1a5228","#2a6438","#3a7448"][i%3]); }
    cloud(60-t*0.006,20,0.55);
    // Distant glowing island
    const ig=Math.sin(t*0.0015)*0.4+0.6;
    ctx.fillStyle=`rgba(255,220,100,${ig*0.14})`; ctx.fillRect(428,55,130,90);
    ctx.fillStyle=`rgba(255,235,140,${ig*0.22})`; ctx.fillRect(448,68,90,65);
    r(452,110,78,10,"#4a3820"); r(448,100,82,12,"#5a4828"); r(446,90,84,12,"#6a5830");
    r(446,87,84,5,"#3a8030"); r(446,85,84,3,"#4a9840");
    r(454,73,4,15,"#5a3a1a"); r(450,59,14,16,"#2a6438");
    r(472,74,4,13,"#5a3a1a"); r(468,61,16,15,"#1a5228");
    r(494,73,4,15,"#5a3a1a"); r(490,60,14,15,"#3a7448");
    ctx.fillStyle=`rgba(255,245,170,${ig*0.9})`; ctx.fillRect(481,75,6,6);
    ctx.fillStyle=`rgba(255,255,220,${ig*0.6})`; ctx.fillRect(478,72,12,12);
  }
  if (theme === "dungeon") {
    for (let i=0;i<7;i++) r(40+i*88,0,14,14+(i%3)*10,"#1e2230");
    for (let i=0;i<3;i++) {
      const tx=80+i*240, fl=Math.sin(t*0.01+i*2)*3;
      r(tx,FLOOR-52,8,42,"#5a3810"); r(tx-5,FLOOR-70+fl,18,20,"#ff7700"); r(tx-2,FLOOR-64+fl,12,14,"#ffbb00");
    }
  }
  if (theme === "market") {
    const aw=["#e03030","#3060d8","#30a040"];
    for (let i=0;i<3;i++) { const mx=30+i*210; r(mx,FLOOR-72,96,72,"#c89848"); r(mx-8,FLOOR-80,112,14,aw[i]); for(let s=0;s<6;s++) if(s%2===0) r(mx-8+s*18,FLOOR-80,9,14,"rgba(255,255,255,0.28)"); }
    cloud(90-t*0.009,28,0.7);
  }
  if (theme === "result") {
    const RC={competitive:["#5c0000","#9a1a00"],strategy:["#5c2800","#aa5500"],exploration:["#5c4a00","#aa8800"],social:["#003c00","#007722"],story:["#00148c","#0022d0"],action:["#00005c","#000099"],challenge:["#340066","#5500aa"],cozy:["#004040","#007777"]};
    const sk=RC[topKey.value]||RC.cozy;
    const rg2=ctx.createLinearGradient(0,0,0,FLOOR); rg2.addColorStop(0,sk[0]); rg2.addColorStop(1,sk[1]);
    ctx.fillStyle=rg2; ctx.fillRect(0,0,CW,FLOOR);
    for (let i=0;i<30;i++) {
      const sx=(i*97+t*0.01*(i%4+1))%CW, sy=(i*71.3)%(FLOOR-20);
      ctx.fillStyle=`rgba(255,255,200,${Math.sin(t*0.002+i)*0.45+0.55})`; ctx.fillRect(sx,sy,3,3);
    }
  }
}

function cloud(x, y, s) {
  ctx.fillStyle = "rgba(255,255,255,0.82)";
  r(x,y,44*s,14*s,"rgba(255,255,255,0.82)"); r(x+8*s,y-10*s,28*s,12*s,"rgba(255,255,255,0.82)"); r(x-8*s,y+2*s,18*s,8*s,"rgba(255,255,255,0.7)");
}
function sun(x, y) {
  r(x,y,40,40,"#ffe040"); r(x-10,y+12,10,16,"#ffe040"); r(x+40,y+12,10,16,"#ffe040"); r(x+12,y-10,16,10,"#ffe040"); r(x+12,y+40,16,10,"#ffe040");
}
function tree(x, y, c) {
  r(x+9,y-38,8,38,"#5a3a1a"); r(x,y-78,26,44,c); r(x+4,y-96,18,22,c); r(x+8,y-110,10,16,c);
}
function house(x, y) {
  r(x,y-64,76,64,"#e4d0a4"); r(x+12,y-40,20,40,"#7a4820"); r(x+44,y-54,18,18,"#90c8e8");
  for (let i=0;i<38;i++) r(x-i+38,y-64-i,i*2,5,"#b83828");
}

function drawFloor(theme) {
  const cols = { gate:["#5a9838","#4a8828"], arena:["#9a5220","#7a3a10"], village:["#5aaa40","#4a9a30"],
    forest:["#2a6828","#1e5020"], dungeon:["#20263a","#181e2c"], market:["#b07828","#906020"] };
  const RFC={competitive:["#4a0000","#340000"],strategy:["#4a1c00","#341000"],exploration:["#4a3800","#342800"],social:["#003000","#002000"],story:["#001066","#000a44"],action:["#000044","#00002c"],challenge:["#280050","#1a0038"],cozy:["#003030","#002020"]};
  const [c1,c2] = theme==="result" ? (RFC[topKey.value]||RFC.cozy) : (cols[theme]||cols.gate);
  for (let i=0;i<Math.ceil(CW/36)+1;i++) {
    r(i*36,FLOOR+6,36,16,i%2===0?c1:c2); r(i*36+18,FLOOR+22,36,16,i%2===0?c2:c1);
    r(i*36,FLOOR+38,36,CH-FLOOR-38,i%2===0?c2:c1);
  }
}

// ── Kid Explorer hero (smaller than NPCs, ~58px tall) ─────
function hero(x, y, dir, frame, grounded) {
  ctx.save();
  // Flip canvas for left-facing
  if (dir < 0) { ctx.translate(x + 17, 0); ctx.scale(-1, 1); x = 0; }

  // Walk: [leftLeg, rightLeg, leftArm, rightArm] Y-offsets
  const wf = grounded
    ? [[0,0,0,0],[4,-4,-3,3],[0,0,0,0],[-4,4,3,-3]][frame % 4]
    : [0, 0, 0, 0];

  // Shadow
  ctx.fillStyle = "rgba(0,0,0,0.18)";
  ctx.fillRect(x - 2, FLOOR + 3, 21, 6);

  // ── Backpack (behind body) ────────────────────────────
  r(x - 7, y - 34,  6, 16, "#7a5010");  // pack body
  r(x - 7, y - 34,  6,  4, "#8b6222");  // top flap
  r(x - 5, y - 21,  4,  4, "#5a3a0e");  // lower pocket

  // ── Boots ─────────────────────────────────────────────
  r(x + 1, y - 7 + wf[0],  7, 8, "#2a1a0c");
  r(x + 9, y - 7 + wf[1],  7, 8, "#2a1a0c");
  r(x + 1, y - 7 + wf[0],  7, 2, "#3a2a1a");  // boot highlight L
  r(x + 9, y - 7 + wf[1],  7, 2, "#3a2a1a");

  // ── Legs (khaki/olive shorts) ─────────────────────────
  r(x + 2, y - 17 + wf[0],  5, 11, "#787c40");  // left leg
  r(x + 9, y - 17 + wf[1],  5, 11, "#686c34");

  // Shorts waistband (static)
  r(x + 0, y - 22, 16,  7, "#8c9050");
  r(x + 0, y - 22, 16,  3, "#9ca860");  // highlight

  // ── Body / shirt ──────────────────────────────────────
  r(x + 0, y - 36, 16, 16, "#3070b8");
  r(x + 0, y - 36, 16,  4, "#4282cc");  // shirt highlight stripe
  r(x + 4, y - 32,  8, 10, "#3a7ece");  // centre chest

  // ── Arms ──────────────────────────────────────────────
  r(x - 5, y - 34 + wf[2],  5, 13, "#f0c7a5");  // left arm (skin)
  r(x + 16,y - 34 + wf[3],  5, 13, "#f0c7a5");
  r(x - 5, y - 23 + wf[2],  5,  5, "#e0b898");  // hands L
  r(x + 16,y - 23 + wf[3],  5,  5, "#e0b898");

  // ── Neck ──────────────────────────────────────────────
  r(x + 5, y - 39,  6,  5, "#f0c7a5");

  // ── Head (round, chibi-kid sized) ─────────────────────
  r(x + 0, y - 52, 16, 15, "#f5c89a");  // face
  // Ears
  r(x - 2, y - 48,  3,  6, "#e8b888");
  r(x + 15,y - 48,  3,  6, "#e8b888");

  // ── Explorer hat (adventure brim hat) ─────────────────
  r(x - 3, y - 55, 22,  5, "#a07828");  // wide brim
  r(x + 1, y - 63, 14, 10, "#b88c30");  // crown
  r(x + 2, y - 65, 12,  3, "#d0aa40");  // crown highlight
  r(x + 1, y - 55, 14,  3, "#7a5618");  // hat band
  // Band pin (tiny star detail)
  r(x + 7, y - 54,  3,  2, "#ffe040");

  // ── Hair peeking under brim ───────────────────────────
  r(x + 0, y - 53,  3,  3, "#5a3810");
  r(x + 13,y - 53,  3,  3, "#5a3810");

  // ── Eyes — simple dot + single highlight ──────────────
  r(x + 2, y - 45,  5,  5, "#1c1c28");   // left dot
  r(x + 9, y - 45,  5,  5, "#1c1c28");   // right dot
  r(x + 5, y - 44,  2,  2, "#ffffff");   // left shine
  r(x + 12,y - 44,  2,  2, "#ffffff");   // right shine

  // ── Eyebrows (expression) ─────────────────────────────
  r(x + 2, y - 48,  4,  2, "#5a3820");
  r(x + 9, y - 48,  4,  2, "#5a3820");

  // ── Blush (cheeks) ────────────────────────────────────
  r(x + 0, y - 41,  4,  2, "rgba(255,130,100,0.40)");
  r(x + 12,y - 41,  4,  2, "rgba(255,130,100,0.40)");

  // ── Mouth — simple "w" smile ──────────────────────────
  r(x + 4, y - 38,  2,  2, "#c07060");
  r(x + 6, y - 37,  4,  2, "#c07060");
  r(x + 10,y - 38,  2,  2, "#c07060");

  ctx.restore();
}

// ── Fairy Lumi ─────────────────────────────────────────────
function fairy(x, y, t) {
  const b = Math.sin(t*0.003)*7, fy = y+b;
  // Wings
  ctx.fillStyle="rgba(200,240,255,0.68)";
  ctx.fillRect(x-20,fy-14,18,24); ctx.fillRect(x+14,fy-14,18,24);
  ctx.fillStyle="rgba(200,240,255,0.42)";
  ctx.fillRect(x-16,fy-20,14,16); ctx.fillRect(x+14,fy-20,14,16);
  // Body
  r(x-7,fy-10,14,22,"#f8d66d");
  // Head
  r(x-5,fy-22,10,14,"#f5c840");
  // Hair
  r(x-7,fy-26,14,7,"#ff9920");
  // Eyes
  r(x-3,fy-17,3,3,"#4b3416"); r(x+2,fy-17,3,3,"#4b3416");
  r(x-2,fy-15,1,1,"#fff");    r(x+3,fy-15,1,1,"#fff");
  // Wand star
  const s=Math.sin(t*0.006)*0.5+0.5;
  ctx.fillStyle=`rgba(255,220,60,${0.7+s*0.3})`;
  r(x+8,fy-32,6,6,"#ffe040"); r(x+10,fy-36,2,4,"#ffe040"); r(x+10,fy-28,2,4,"#ffe040");
  r(x+6,fy-32,4,2,"#ffe040"); r(x+12,fy-32,4,2,"#ffe040");
  // Glow
  ctx.fillStyle=`rgba(248,214,109,${0.10+s*0.06})`; ctx.fillRect(x-18,fy-30,36,46);
}

// ── NPC Sprites ────────────────────────────────────────────
function npcRival(x, y) {
  // Legs
  r(x+3,y-20,10,20,"#1a0a2a"); r(x+15,y-20,10,20,"#1a0a2a");
  // Boots
  r(x+1,y-6,14,7,"#0a0014"); r(x+13,y-6,14,7,"#0a0014");
  // Body (red armor)
  r(x,y-52,28,34,"#aa2838"); r(x,y-52,28,8,"#cc3848"); r(x+8,y-48,12,18,"#cc3848");
  // Shoulder pads
  r(x-6,y-52,8,12,"#aa2838"); r(x+26,y-52,8,12,"#aa2838");
  // Arms
  r(x-8,y-50,10,22,"#f0c7a5"); r(x+26,y-50,10,22,"#f0c7a5");
  // Gloves
  r(x-8,y-30,10,8,"#1a0a2a"); r(x+26,y-30,10,8,"#1a0a2a");
  // Neck/Head
  r(x+9,y-58,10,8,"#f0c7a5");
  r(x+3,y-76,22,20,"#f0c7a5");
  r(x+1,y-82,26,8,"#1a1a2e"); r(x+4,y-90,20,10,"#1a1a2e"); // hair
  // Eyes (menacing)
  r(x+5,y-70,5,4,"#1a1a28"); r(x+18,y-70,5,4,"#1a1a28");
  r(x+6,y-69,3,2,"#ee2200"); r(x+19,y-69,3,2,"#ee2200");
  r(x+9,y-66,6,2,"#cc0000"); // angry mouth
  // Sword
  r(x+32,y-80,6,58,"#bccad8"); r(x+24,y-62,20,6,"#daa520"); r(x+33,y-86,4,8,"#daa520");
}

function npcHelper(x, y) {
  // Legs
  r(x+4,y-20,9,20,"#172235"); r(x+15,y-20,9,20,"#172235");
  r(x+2,y-6,13,7,"#0f1a28"); r(x+14,y-6,13,7,"#0f1a28");
  // Body (brown traveler)
  r(x+1,y-50,22,32,"#7a5030"); r(x+1,y-50,22,8,"#9a6840"); r(x+7,y-46,8,14,"#9a6840");
  // Arms + hands
  r(x-7,y-48,9,20,"#7a5030"); r(x+22,y-48,9,20,"#7a5030");
  r(x-7,y-30,9,10,"#f0c7a5"); r(x+22,y-30,9,10,"#f0c7a5");
  // Head
  r(x+8,y-56,8,8,"#f0c7a5");
  r(x+3,y-74,20,20,"#f0c7a5");
  r(x+1,y-80,24,8,"#6b4020"); r(x+4,y-88,18,10,"#6b4020");
  r(x+5,y-68,5,5,"#2d210e"); r(x+14,y-68,5,5,"#2d210e");
  r(x+7,y-62,8,3,"#c07060");
  // Cart (broken wheel)
  r(x-56,y-42,44,42,"#8b6a3a"); r(x-52,y-38,36,34,"#a88050");
  r(x-34-2,y-42,4,42,"#6b4a20"); r(x-56,y-22-2,44,4,"#6b4a20");
  r(x-50,y-4,32,6,"#5a3a10");
  r(x-42,y-4,6,6,"rgba(255,200,100,0.5)"); // wheel glint
}

function npcScenery(x, y) {
  r(x+10,y-92,8,92,"#6b4a2a");
  r(x-36,y-90,70,22,"#d4b060"); r(x-32,y-84,62,12,"#c4a050");
  r(x-8,y-66,64,20,"#d4b060");  r(x-4,y-60,56,12,"#c4a050");
  r(x-68,y-44,66,18,"#d4b060"); r(x-64,y-38,58,10,"#c4a050");
  // Arrow symbols
  for (const [ax,ay] of [[x-20,y-82],[x+42,y-58],[x-52,y-38]]) {
    r(ax,ay+4,12,4,"#7a4a20"); r(ax+8,ay,4,12,"#7a4a20");
  }
}

function npcDungeon(x, y) {
  // Stone door frame
  r(x-46,y-110,92,110,"#363a48"); r(x-30,y-102,60,102,"#282c38"); r(x-24,y-98,48,98,"#141820");
  // Stone line details
  ctx.strokeStyle="#2e3240"; ctx.lineWidth=2;
  for (let i=0;i<5;i++) { ctx.beginPath(); ctx.moveTo(x-46,y-22*i); ctx.lineTo(x+46,y-22*i); ctx.stroke(); }
  // Skull ornament
  r(x-10,y-124,20,18,"#ddd0b0"); r(x-7,y-120,6,6,"#141820"); r(x+3,y-120,6,6,"#141820");
  r(x-5,y-112,10,4,"#141820");
  // Glowing eyes in door
  ctx.fillStyle="rgba(255,50,0,0.7)"; ctx.fillRect(x-12,y-60,8,10); ctx.fillRect(x+4,y-60,8,10);
  ctx.fillStyle="rgba(255,100,0,0.4)"; ctx.fillRect(x-14,y-62,12,14); ctx.fillRect(x+2,y-62,12,14);
}

function npcShop(x, y, t) {
  const b = Math.sin(t*0.002)*2;
  // Legs
  r(x+3,y-20,10,20,"#282050"); r(x+15,y-20,10,20,"#282050");
  r(x+1,y-6,14,7,"#181030"); r(x+13,y-6,14,7,"#181030");
  // Body (merchant robe, purple+gold)
  r(x,y-54,28,36,"#5828a0"); r(x,y-54,28,10,"#7040b8"); r(x+8,y-50,12,18,"#7040b8");
  r(x,y-22,28,4,"#daa520");  // gold waistband
  // Arms + hands
  r(x-8,y-52,10,24,"#5828a0"); r(x+26,y-52,10,24,"#5828a0");
  r(x-8,y-30,10,10,"#f5c840"); r(x+26,y-30,10,10,"#f5c840");
  // Head + big hat
  r(x+8,y-60+b,8,8,"#f5c840");
  r(x+2,y-78+b,22,20,"#f5c840");
  r(x-2,y-84+b,30,8,"#2d1a08");  // hat brim
  r(x+4,y-98+b,18,16,"#2d1a08"); // hat top
  r(x+2,y-86+b,24,4,"#daa520");  // hat band
  // Hat star
  r(x+10,y-104+b,6,6,"#ffe040"); r(x+12,y-108+b,2,4,"#ffe040"); r(x+8,y-102+b,4,2,"#ffe040"); r(x+14,y-102+b,4,2,"#ffe040");
  // Eyes (friendly)
  r(x+5,y-72+b,5,5,"#2d210e"); r(x+16,y-72+b,5,5,"#2d210e");
  r(x+6,y-71+b,2,2,"#fff");   r(x+17,y-71+b,2,2,"#fff");
  // Beard/mustache
  r(x+2,y-64+b,22,8,"#8b6018");
  r(x+4,y-66+b,18,4,"#a07022");
  // Floating coins
  const sp=Math.sin(t*0.005)*0.5+0.5;
  r(x-18,y-50,10,10,`rgba(255,200,50,${0.5+sp*0.5})`); r(x+36,y-44,10,10,`rgba(255,200,50,${0.5+sp*0.4})`);
}

function drawNpc(actor, t) {
  const x = NPC_X - 14, y = FLOOR;
  switch(actor) {
    case "fairy":   fairy(NPC_X, y-24, t); break;
    case "rival":   npcRival(x-4, y); break;
    case "helper":  npcHelper(x+10, y); break;
    case "scenery": npcScenery(x+6, y); break;
    case "dungeon": npcDungeon(x+14, y); break;
    case "shop":    npcShop(x, y, t); break;
    default:        fairy(NPC_X, y-24, t);
  }
}

function drawIndicator(t) {
  if (Math.floor(t*0.003)%2 === 0) {
    r(NPC_X-5, FLOOR-118, 12, 30, "#ffe040");
    r(NPC_X-5, FLOOR-82,  12, 12, "#ffe040");
  }
}

// ── Main render ────────────────────────────────────────────
function draw(t) {
  if (!ctx) return;
  ctx.clearRect(0, 0, CW, CH);
  const scene = currentScene.value;
  drawBg(scene.theme, t);
  drawFloor(scene.theme);
  if (scene.id !== "gate") fairy(pl.x+20, pl.y-62, t);
  if (!isComplete.value) drawNpc(scene.actor, t);
  if (isNearNpc.value && !interactionOpen.value && !isComplete.value) drawIndicator(t);
  hero(pl.x, pl.y, pl.dir, pl.frame, pl.grounded);
}

// ── Game loop ──────────────────────────────────────────────
function loop(t) {
  if (!prev) prev = t;
  const dt = Math.min(t - prev, 32);
  prev = t;

  if (!interactionOpen.value && !isComplete.value) {
    let moving = false;
    if (keys["ArrowLeft"]||keys["a"]||keys["A"]) { pl.x=Math.max(18,pl.x-SPD*dt/16); pl.dir=-1; moving=true; introSpeechDismissed.value=true; }
    if (keys["ArrowRight"]||keys["d"]||keys["D"]) { pl.x=Math.min(NPC_X+8,pl.x+SPD*dt/16); pl.dir=1; moving=true; introSpeechDismissed.value=true; }
    if (!pl.grounded) { pl.vy+=GRAVITY*dt/16; pl.y=Math.min(FLOOR,pl.y+pl.vy*dt/16); if(pl.y>=FLOOR){pl.y=FLOOR;pl.vy=0;pl.grounded=true;} }
    if (moving&&pl.grounded) { pl.ft+=dt; if(pl.ft>105){pl.frame=(pl.frame+1)%4;pl.ft=0;if(pl.frame%2===0)sndStep();} }
    else if (!moving) pl.frame=0;
  }

  // *** CRITICAL: sync reactive ref so computed props stay live ***
  if (Math.abs(pl.x - playerX.value) > 0.5) playerX.value = pl.x;

  draw(t);
  raf = requestAnimationFrame(loop);
}

// ── Input ──────────────────────────────────────────────────
function onKeydown(e) {
  const gameKeys = ["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","w","a","s","d","W","A","S","D"," ","z","Z"];
  if (gameKeys.includes(e.key)) e.preventDefault();
  keys[e.key] = true;

  // Jump
  if ((e.key==="ArrowUp"||e.key==="w"||e.key==="W") && pl.grounded && !interactionOpen.value && !isComplete.value) {
    pl.grounded=false; pl.vy=JUMP_VY; sndJump();
  }

  // Interact — check pl.x directly (never stale)
  if ((e.key===" "||e.key==="z"||e.key==="Z") && !interactLock) {
    interactLock = true;
    const near = Math.abs(pl.x - NPC_X) <= NEAR_DIST;
    if (!isComplete.value && near && !interactionOpen.value) {
      sndHit();
      interactionOpen.value = true;
    }
  }
}

function onKeyup(e) {
  keys[e.key] = false;
  if (e.key===" "||e.key==="z"||e.key==="Z") interactLock = false;
}

// ── Game logic ─────────────────────────────────────────────
function choose(choice) {
  sndChoose();
  answers.value.push({ sceneId:currentScene.value.id, label:choice.text, scores:choice.scores, tags:choice.tags, tone:choice.tone });
  advance(sceneIndex.value + 1);
}

function advance(idx) {
  saveMessage.value = ""; interactionOpen.value = false;
  setTimeout(() => {
    sceneIndex.value = Math.min(idx, scenes.length-1);
    pl.x=60; pl.y=FLOOR; pl.dir=1; pl.frame=0; pl.grounded=true;
    playerX.value = 60;
    introSpeechDismissed.value = false;
  }, 350);
}

function reset() {
  sceneIndex.value=0; pl.x=60; pl.y=FLOOR; pl.dir=1; pl.frame=0; pl.grounded=true;
  playerX.value=60; interactionOpen.value=false; introSpeechDismissed.value=false;
  answers.value=[]; saveMessage.value=""; resultSaving.value=false; resultSaved.value=false;
}

async function saveTags() {
  if (!auth.user || resultSaving.value || resultSaved.value) return;
  resultSaving.value = true;
  const scoreMap = scores.value;
  try {
    await api.post("/accounts/taste-results/", {
      result_key: topKey.value,
      result_title: result.value.title,
      result_summary: result.value.summary,
      competitive_score: scoreMap.competitive || 0,
      strategy_score: scoreMap.strategy || 0,
      exploration_score: scoreMap.exploration || 0,
      social_score: scoreMap.social || 0,
      story_score: scoreMap.story || 0,
      action_score: scoreMap.action || 0,
      challenge_score: scoreMap.challenge || 0,
      cozy_score: scoreMap.cozy || 0,
      tags: result.value.tags,
      recommended_games: result.value.games,
      answers: answers.value.map((answer) => ({
        scene_id: answer.sceneId,
        choice: answer.label,
        tone: answer.tone,
        scores: answer.scores,
        tags: answer.tags,
      })),
    });
    resultSaved.value = true;
    await auth.updateProfile({ ...auth.user, hashtags: result.value.tags });
    saveMessage.value = "미니게임 결과와 프로필 취향 태그를 저장했어!";
  } finally {
    resultSaving.value = false;
  }
}

onMounted(() => {
  ctx = gameCanvas.value.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  window.addEventListener("keydown", onKeydown);
  window.addEventListener("keyup", onKeyup);
  raf = requestAnimationFrame(loop);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  window.removeEventListener("keyup", onKeyup);
  if (raf) cancelAnimationFrame(raf);
  if (aCtx) { aCtx.close(); aCtx = null; }
});
</script>

<template>
  <div class="bit-page">
    <div class="bit-page-header">
      <RouterLink class="bit-back" to="/taste">← 성향 분석으로</RouterLink>
      <div>
        <h1 class="bit-title">도트 원정대</h1>
        <p class="bit-subtitle">직접 걸어가 NPC와 상호작용하며 내 게임 취향을 찾는 미니게임</p>
      </div>
      <button class="bit-reset-btn" @click="reset">↺ 처음부터</button>
    </div>

    <div class="bit-layout">
      <div class="bit-game-col">
        <!-- HUD -->
        <div class="bit-hud">
          <span class="bit-hud-stage">{{ hudStageLabel }}</span>
          <strong class="bit-hud-title">{{ currentScene.title }}</strong>
          <span class="bit-hud-tags">{{ currentScene.tags.join(" · ") }}</span>
        </div>

        <!-- Game screen -->
        <div class="bit-screen-wrap">
          <canvas ref="gameCanvas" :width="CW" :height="CH" class="bit-canvas"></canvas>
          <div class="bit-scanlines" aria-hidden="true"></div>
          <div class="bit-vignette" aria-hidden="true"></div>

          <!-- Fairy speech bubble -->
          <div v-if="!introSpeechDismissed && !interactionOpen && !isComplete" class="bit-bubble">
            <span class="bit-bubble-name">루미</span>
            {{ currentScene.fairy }}
          </div>

          <!-- Hint -->
          <div v-if="!interactionOpen && !isComplete" class="bit-hint" :class="{ 'bit-hint--glow': canInteract }">
            {{ canInteract ? "[ Z / Space ] 상호작용!" : "→ A·D 이동  |  W 점프  |  NPC에 가까이 가면 상호작용 가능" }}
          </div>

          <!-- Choice overlay -->
          <Transition name="bit-slide">
            <div v-if="interactionOpen && !isComplete" class="bit-overlay">
              <div class="bit-dlg-box">
                <span class="bit-dlg-name">{{ currentScene.npcName }}</span>
                <p>{{ currentScene.text }}</p>
              </div>
              <div v-if="currentScene.type==='intro'" class="bit-choices bit-choices--single">
                <button class="bit-choice bit-choice--go" @click="advance(1)">▶ 길을 나선다!</button>
              </div>
              <div v-else-if="currentScene.choices" class="bit-choices">
                <button
                  v-for="(c, i) in currentScene.choices" :key="c.text"
                  class="bit-choice" :class="`bit-choice--${i+1}`"
                  @click="choose(c)"
                >
                  <span class="bit-choice-num">{{ i+1 }}</span>
                  <span class="bit-choice-main">{{ c.text }}</span>
                  <span class="bit-choice-sub">{{ c.tone }}</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Result -->
        <div v-if="isComplete" class="bit-result">
          <div class="bit-result-top">
            <span class="bit-eyebrow">RESULT</span>
            <h2>{{ result.title }}</h2>
            <p>{{ result.summary }}</p>
          </div>
          <div class="bit-result-tags">
            <span v-for="tag in result.tags" :key="tag">#{{ tag }}</span>
          </div>
          <div class="bit-result-games">
            <strong>추천 게임</strong>
            <span v-for="game in result.games" :key="game">{{ game }}</span>
          </div>
          <div class="bit-result-actions">
            <button class="bit-btn-primary" :disabled="resultSaving || resultSaved" @click="saveTags">
              {{ resultSaved ? "저장 완료" : resultSaving ? "저장 중" : "프로필에 저장" }}
            </button>
            <button class="bit-btn-ghost" @click="reset">↺ 다시 플레이</button>
          </div>
          <p v-if="saveMessage" class="bit-save-msg">{{ saveMessage }}</p>
        </div>
      </div>

      <!-- Sidebar -->
      <aside class="bit-side">
        <section class="bit-panel">
          <h3>조작법</h3>
          <div class="bit-keys">
            <div><kbd>← / A</kbd><span>왼쪽</span></div>
            <div><kbd>→ / D</kbd><span>오른쪽</span></div>
            <div><kbd>↑ / W</kbd><span>점프</span></div>
            <div><kbd>Z / Space</kbd><span>상호작용</span></div>
          </div>
        </section>

        <section class="bit-panel">
          <h3>진행 상황</h3>
          <div class="bit-progress">
            <span
              v-for="(s, i) in playableScenes" :key="s.id"
              :class="{ done: completedCount>i, active: completedCount===i && !isComplete }"
            >{{ i+1 }}</span>
          </div>
        </section>

        <section class="bit-panel">
          <h3>내 선택</h3>
          <div v-if="answers.length" class="bit-log">
            <div v-for="a in answers" :key="a.sceneId" class="bit-log-item">
              <strong>{{ a.label }}</strong>
              <span>{{ a.tone }}</span>
            </div>
          </div>
          <p v-else class="bit-log-empty">아직 선택한 게 없어.</p>
        </section>
      </aside>
    </div>
  </div>
</template>
