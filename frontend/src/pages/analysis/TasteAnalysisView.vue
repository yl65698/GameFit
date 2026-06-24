<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import api from "../../services/api";

const canvasHost = ref(null);
const selectedNode = ref(null);
const report = ref({
  taste_tags: [],
  vector_map: [],
  games: [],
  report: "",
});
const latestMiniGameResult = ref(null);

let renderer;
let scene;
let camera;
let controls;
let animationId;
let raycaster;
let pointer;
let nodeGroup;
let nodeMeshes = [];
let linkLines = [];
let resizeObserver;

const tasteAxisMeta = [
  { id: "competitive", label: "랭커형", scoreField: "competitive_score", position: [2.8, 1.4, -0.6], color: "#dc2626", summary: "대결, 순위, 성과가 분명한 선택에 끌리는 성향이에요." },
  { id: "strategy", label: "공략가형", scoreField: "strategy_score", position: [1.1, 2.3, 1.2], color: "#ea580c", summary: "정보를 모으고 계획을 세워 안정적으로 해결하는 성향이에요." },
  { id: "exploration", label: "탐험가형", scoreField: "exploration_score", position: [-1.6, 1.7, -1.4], color: "#ca8a04", summary: "숨겨진 길, 풍경, 수집 요소에서 재미를 크게 느끼는 성향이에요." },
  { id: "social", label: "파티형", scoreField: "social_score", position: [-2.7, 0.2, 1.5], color: "#16a34a", summary: "혼자보다 같이 역할을 나누고 진행할 때 몰입하는 성향이에요." },
  { id: "story", label: "서사형", scoreField: "story_score", position: [-1.0, -1.8, -1.9], color: "#2563eb", summary: "분위기, 인물, 선택의 의미를 중요하게 보는 성향이에요." },
  { id: "action", label: "액션형", scoreField: "action_score", position: [1.8, -1.2, 2.1], color: "#1e3a8a", summary: "빠른 판단, 조작감, 즉각적인 피드백을 선호하는 성향이에요." },
  { id: "challenge", label: "하드코어형", scoreField: "challenge_score", position: [0.2, -2.2, -0.4], color: "#7e22ce", summary: "어려운 구간을 넘었을 때의 성취감을 좋아하는 성향이에요." },
  { id: "cozy", label: "힐링형", scoreField: "cozy_score", position: [-2.0, -0.9, 1.0], color: "#0d9488", summary: "부담 없는 진행과 자기 속도에 맞춘 플레이를 선호하는 성향이에요." },
];

const gameGenreAxisMap = {
  strategy: "strategy",
  simulation: "strategy",
  fps: "action",
  sports: "competitive",
  horror: "challenge",
  adventure: "exploration",
  rpg: "story",
  indie: "cozy",
};

const miniGameResultPalettes = {
  competitive: { name: "랭커형", accent: "#dc2626", bg: "linear-gradient(135deg, #fee2e2, #fff7ed)" },
  strategy: { name: "공략가형", accent: "#ea580c", bg: "linear-gradient(135deg, #ffedd5, #fff7ed)" },
  exploration: { name: "탐험가형", accent: "#ca8a04", bg: "linear-gradient(135deg, #fef3c7, #fffbe6)" },
  social: { name: "파티형", accent: "#16a34a", bg: "linear-gradient(135deg, #dcfce7, #f0fdf4)" },
  story: { name: "서사형", accent: "#2563eb", bg: "linear-gradient(135deg, #dbeafe, #eff6ff)" },
  action: { name: "액션형", accent: "#1e3a8a", bg: "linear-gradient(135deg, #dbeafe, #e0e7ff)" },
  challenge: { name: "하드코어형", accent: "#7e22ce", bg: "linear-gradient(135deg, #f3e8ff, #faf5ff)" },
  cozy: { name: "힐링형", accent: "#0d9488", bg: "linear-gradient(135deg, #ccfbf1, #ecfeff)" },
};

const tasteTags = computed(() => {
  if (latestMiniGameResult.value?.tags?.length) return latestMiniGameResult.value.tags;
  const tags = report.value.taste_tags?.filter((tag) => tag && !looksBroken(tag)) || [];
  return tags;
});

const recommendedGames = computed(() => {
  const apiGames = report.value.games?.filter(Boolean) || [];
  return apiGames.slice(0, 3).map((game) => ({
    ...game,
    genre: normalizeText(game.genre, "추천"),
    buy_signal: normalizeText(game.buy_signal, "추천"),
    summary: normalizeText(game.summary, ""),
  }));
});

const baseAxisStats = computed(() => {
  if (report.value.taste_axes?.length) {
    return tasteAxisMeta.map((axis) => {
      const item = report.value.taste_axes.find((entry) => entry.id === axis.id);
      const score = Number(item?.score || 0);
      const sources = item?.sources || {};
      return {
        ...axis,
        type: "genre",
        score,
        rawScore: score,
        evidence: item
          ? [
              `도트 원정대 반영 ${sources.minigame ?? 0}%`,
              `보유 게임 장르 반영 ${sources.owned ?? 0}%`,
              `관심 게임 장르 반영 ${sources.interested ?? 0}%`,
            ]
          : ["도트 원정대와 보유/관심 게임을 기반으로 계산돼요."],
      };
    });
  }

  const result = latestMiniGameResult.value;
  const total = tasteAxisMeta.reduce((sum, axis) => sum + Number(result?.[axis.scoreField] || 0), 0);
  return tasteAxisMeta.map((axis) => {
    const rawScore = Number(result?.[axis.scoreField] || 0);
    const score = total > 0 ? Math.round((rawScore / total) * 100) : 0;
    return {
      ...axis,
      type: "genre",
      score,
      rawScore,
      evidence: result
        ? [`도트 원정대 선택 점수 ${rawScore}점`, `전체 선택 점수 중 ${score}%`]
        : ["도트 원정대를 완료하면 실제 점수가 표시돼요."],
    };
  });
});
const userGameNodes = computed(() => {
  const activeAxisIds = new Set(baseAxisStats.value.filter((axis) => axis.score > 0).map((axis) => axis.id));
  const games = [
    ...(report.value.owned_games || []).map((game) => ({ ...game, userStatus: "보유" })),
    ...(report.value.interested_games || []).map((game) => ({ ...game, userStatus: "관심" })),
  ];
  return games
    .map((game, index) => {
      const axisId = axisIdForGame(game);
      const axis = baseAxisStats.value.find((item) => item.id === axisId);
      if (!axis || !activeAxisIds.has(axis.id)) return null;
      const offset = gameNodeOffset(index);
      return {
        id: `game-${game.id}`,
        type: "game",
        axisId: axis.id,
        label: game.title,
        genre: game.genre,
        userStatus: game.userStatus,
        platform: game.platform,
        position: [
          axis.position[0] + offset[0],
          axis.position[1] + offset[1],
          axis.position[2] + offset[2],
        ],
        color: axis.color,
        tags: uniqueGameTags(game).slice(0, 4),
        summary: game.summary || game.description || `${axis.label} 축에 가까운 ${game.userStatus} 게임이에요.`,
      };
    })
    .filter(Boolean);
});
const connectedAxisIds = computed(() => new Set(userGameNodes.value.map((node) => node.axisId)));
const genreAxes = computed(() => {
  return baseAxisStats.value.filter((axis) => axis.score > 0 || connectedAxisIds.value.has(axis.id));
});
const topGenre = computed(() => genreAxes.value.slice().sort((a, b) => b.score - a.score)[0] || tasteAxisMeta[0]);
const selectedDetail = computed(() => selectedNode.value);
const visualNodes = computed(() => []);
const latestMiniGamePalette = computed(() => {
  return miniGameResultPalettes[latestMiniGameResult.value?.result_key] || {
    name: "결과",
    accent: "#17637d",
    bg: "linear-gradient(135deg, #e8f6ff, #f8fafc)",
  };
});
const latestMiniGameCardStyle = computed(() => ({
  "--mini-result-accent": latestMiniGamePalette.value.accent,
  background: latestMiniGamePalette.value.bg,
}));
const analysisSummary = computed(() => {
  if (!latestMiniGameResult.value) {
    return "아직 도트 원정대 결과가 없어요. 미니게임을 완료하고 저장하면 8개 성향 축의 실제 점수 분포가 여기에 표시돼요.";
  }
  if (!genreAxes.value.length) {
    return "도트 원정대 결과는 있지만, 현재 보유/관심 게임 장르와 연결되는 성향 축이 없어요. 게임을 보유하거나 관심 등록하면 연결된 축이 함께 표시돼요.";
  }
  if (report.value.report && !looksBroken(report.value.report)) return report.value.report;
  return `최근 도트 원정대 결과는 ${topGenre.value.label} 축이 ${topGenre.value.score}%로 가장 높아요. 선택 기록을 기준으로 8개 성향 축의 비중을 계산했어요.`;
});

onMounted(async () => {
  try {
    const { data } = await api.get("/catalog/recommendations/");
    report.value = data;
  } catch {
    report.value = {
      taste_tags: [],
      games: [],
      report: "",
    };
  }

  try {
    const { data } = await api.get("/accounts/taste-results/");
    latestMiniGameResult.value = Array.isArray(data) && data.length ? data[0] : null;
  } catch {
    latestMiniGameResult.value = null;
  }

  await nextTick();
  initThreeMap();
});

onBeforeUnmount(() => {
  teardownThreeMap();
});

function initThreeMap() {
  if (!canvasHost.value) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color("#eef5f8");

  const { width, height } = getHostSize();
  camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 100);
  camera.position.set(0, 1.2, 8);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
  renderer.setClearColor("#eef5f8", 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height);
  canvasHost.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 4;
  controls.maxDistance = 12;

  raycaster = new THREE.Raycaster();
  pointer = new THREE.Vector2();
  nodeGroup = new THREE.Group();
  scene.add(nodeGroup);

  scene.add(new THREE.AmbientLight("#ffffff", 1.6));
  const directional = new THREE.DirectionalLight("#ffffff", 2.4);
  directional.position.set(3, 5, 4);
  scene.add(directional);

  createNodes();
  connectInterestedGames();

  renderer.domElement.addEventListener("pointerdown", handlePointerDown);
  resizeObserver = new ResizeObserver(resizeThreeMap);
  resizeObserver.observe(canvasHost.value);

  renderer.render(scene, camera);
  animateThreeMap();
}

function createNodes() {
  const allNodes = [...genreAxes.value, ...userGameNodes.value];
  nodeMeshes = allNodes.map((node) => {
    const radius = node.type === "genre" ? 0.24 + node.score / 260 : 0.18;
    const geometry =
      node.type === "genre"
        ? new THREE.SphereGeometry(radius, 32, 24)
        : new THREE.OctahedronGeometry(radius, 1);
    const material = new THREE.MeshStandardMaterial({
      color: node.color,
      roughness: node.type === "genre" ? 0.32 : 0.5,
      metalness: node.type === "genre" ? 0.28 : 0.08,
      emissive: node.color,
      emissiveIntensity: node.type === "genre" ? 0.16 : 0.04,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...node.position);
    mesh.userData = node;
    nodeGroup.add(mesh);

    if (node.type === "genre") {
      const ringGeometry = new THREE.TorusGeometry(radius * 1.35, 0.025, 10, 48);
      const ringMaterial = new THREE.MeshBasicMaterial({ color: node.color, transparent: true, opacity: 0.8 });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.position.copy(mesh.position);
      ring.rotation.x = Math.PI / 2;
      nodeGroup.add(ring);
    }

    const label = createTextSprite(
      node.type === "genre" ? `${node.label} ${node.score}%` : node.label,
      node.color,
      [node.position[0], node.position[1] + radius + 0.34, node.position[2]],
      node.type === "genre" ? 0.76 : 0.52,
      { isGenre: node.type === "genre" },
    );
    nodeGroup.add(label);
    return mesh;
  });
}

function connectInterestedGames() {
  userGameNodes.value.forEach((gameNode) => {
    const axis = genreAxes.value.find((item) => item.id === gameNode.axisId);
    if (!axis) return;
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...axis.position),
      new THREE.Vector3(...gameNode.position),
    ]);
    const material = new THREE.LineBasicMaterial({ color: gameNode.color, transparent: true, opacity: 0.5 });
    const line = new THREE.Line(geometry, material);
    linkLines.push(line);
    scene.add(line);
  });
}

function createTextSprite(text, color, position, scale = 0.6, options = {}) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = options.isGenre ? "rgba(255,255,255,0.98)" : "rgba(20,33,49,0.78)";
  roundRect(context, 12, 18, 232, 56, 16);
  context.fill();
  context.strokeStyle = color;
  context.lineWidth = options.isGenre ? 5 : 3;
  context.stroke();
  context.fillStyle = options.isGenre ? color : "#ffffff";
  context.font = options.isGenre ? "bold 28px sans-serif" : "bold 23px sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, 128, 46);

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.position.set(...position);
  sprite.scale.set(scale * 2.2, scale * 0.82, 1);
  return sprite;
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.lineTo(x + width - radius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + radius);
  context.lineTo(x + width, y + height - radius);
  context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  context.lineTo(x + radius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - radius);
  context.lineTo(x, y + radius);
  context.quadraticCurveTo(x, y, x + radius, y);
  context.closePath();
}

function handlePointerDown(event) {
  if (!renderer || !camera) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(nodeMeshes)[0];
  if (hit?.object?.userData) {
    selectedNode.value = hit.object.userData;
  }
}

function selectVisualNode(node) {
  selectedNode.value = node;
}

function selectOverallAnalysis() {
  selectedNode.value = null;
}

function recommendCardStyle(game) {
  const image = game.image_url ? `, url(${game.image_url})` : "";
  return {
    backgroundImage: `linear-gradient(180deg, rgba(10, 18, 30, 0.22), rgba(10, 18, 30, 0.88))${image}`,
  };
}

function uniqueGameTags(game) {
  const seen = new Set();
  return [game.genre, ...(game.genres || []).map((genre) => genre.name)]
    .filter(Boolean)
    .filter((tag) => {
      const key = String(tag).trim().toLowerCase();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function axisIdForGame(game) {
  const candidates = [
    game.genre_key,
    game.genre,
    ...(game.genres || []).flatMap((genre) => [genre.key, genre.name]),
  ]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase());

  for (const value of candidates) {
    if (gameGenreAxisMap[value]) return gameGenreAxisMap[value];
    if (value.includes("strategy") || value.includes("전략") || value.includes("simulation")) return "strategy";
    if (value.includes("fps") || value.includes("shooter") || value.includes("액션")) return "action";
    if (value.includes("sports") || value.includes("racing") || value.includes("대전")) return "competitive";
    if (value.includes("horror") || value.includes("공포") || value.includes("souls")) return "challenge";
    if (value.includes("adventure") || value.includes("open") || value.includes("탐험")) return "exploration";
    if (value.includes("rpg") || value.includes("story") || value.includes("스토리")) return "story";
    if (value.includes("indie") || value.includes("casual") || value.includes("힐링")) return "cozy";
    if (value.includes("coop") || value.includes("multi") || value.includes("협동")) return "social";
  }
  return null;
}

function gameNodeOffset(index) {
  const offsets = [
    [0.6, -0.42, 0.34],
    [-0.58, -0.36, -0.28],
    [0.36, 0.44, -0.52],
    [-0.34, 0.34, 0.5],
  ];
  return offsets[index % offsets.length];
}

function animateThreeMap() {
  animationId = window.requestAnimationFrame(animateThreeMap);
  const time = performance.now() * 0.001;
  nodeMeshes.forEach((mesh, index) => {
    mesh.position.y += Math.sin(time + index) * 0.0008;
  });
  controls?.update();
  renderer?.render(scene, camera);
}

function resizeThreeMap() {
  if (!renderer || !camera) return;
  const { width, height } = getHostSize();
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function getHostSize() {
  const rect = canvasHost.value?.getBoundingClientRect();
  return {
    width: Math.max(320, rect?.width || 720),
    height: Math.max(420, rect?.height || 520),
  };
}

function teardownThreeMap() {
  window.cancelAnimationFrame(animationId);
  resizeObserver?.disconnect();
  renderer?.domElement?.removeEventListener("pointerdown", handlePointerDown);
  renderer?.dispose();
  if (renderer?.domElement?.parentNode) {
    renderer.domElement.parentNode.removeChild(renderer.domElement);
  }
  nodeMeshes = [];
  linkLines = [];
}

function normalizeText(value, fallback) {
  return value && !looksBroken(value) ? value : fallback;
}

function looksBroken(value = "") {
  return /[�]|[蹂댁쑀愿痍⑦뼢꾨왂묐룞]/.test(String(value));
}
</script>

<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">게임 성향 분석</p>
        <h1>게임 성향 통합 분석</h1>
        <p>도트 원정대 결과와 보유/관심 게임 장르를 함께 계산해서 보여줘요.</p>
      </div>
    </header>

    <section class="panel taste-report-board">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">GameFit Vector Space</p>
          <h2>데이터 기반 게임 성향 분석</h2>
        </div>
        <div class="tag-row">
          <span v-for="tag in tasteTags" :key="tag">#{{ tag }}</span>
        </div>
      </div>

      <div class="taste-report-grid vector3d-layout">
        <section class="vector3d-card">
          <div class="vector3d-header">
            <div>
              <span class="eyebrow">Interactive 3D Vector Map</span>
              <h3>내 선택이 어떤 성향 축에 가까운지 보기</h3>
            </div>
            <div class="vector3d-legend">
              <span><i class="legend-genre"></i>성향 축</span>
              <span><i class="legend-game"></i>관심 게임</span>
            </div>
          </div>

          <div class="vector3d-stage">
            <div ref="canvasHost" class="vector3d-canvas" aria-label="3D 게임 성향 벡터 맵"></div>
            <div class="vector3d-overlay" aria-label="클릭 가능한 게임 성향 노드">
              <button
                v-for="node in visualNodes"
                :key="node.id"
                type="button"
                class="vector3d-node"
                :class="[`node-${node.type}`, { active: selectedDetail?.id === node.id }]"
                :style="{
                  left: `${node.screenX}%`,
                  top: `${node.screenY}%`,
                  width: `${node.size}px`,
                  height: `${node.size}px`,
                  background: node.color,
                  zIndex: node.depth,
                }"
                @click="selectVisualNode(node)"
              >
                <span>{{ node.label }}</span>
              </button>
            </div>
          </div>

          <div class="vector3d-help">
            <span>드래그: 회전</span>
            <span>휠: 확대/축소</span>
            <span>노드 클릭: 상세 보기</span>
          </div>
        </section>

        <aside class="ai-analysis-card vector-node-detail">
          <template v-if="!selectedDetail">
            <span class="eyebrow">통합 분석</span>
            <h3>{{ topGenre.label }} 플레이어</h3>
            <p>{{ analysisSummary }}</p>

            <div class="tag-row">
              <span v-for="tag in tasteTags" :key="tag">#{{ tag }}</span>
            </div>

            <div class="achievement-list">
              <strong>주요 성향 분포</strong>
              <div
                v-for="genre in genreAxes"
                :key="genre.id"
                class="taste-axis-bar"
                :style="{ '--axis-color': genre.color, '--axis-score': `${genre.score}%` }"
              >
                <div class="taste-axis-bar-label">
                  <span>{{ genre.label }}</span>
                  <strong>{{ genre.score }}%</strong>
                </div>
                <div class="taste-axis-bar-track">
                  <i></i>
                </div>
              </div>
            </div>

            <div class="vector-summary-box">
              <strong>노드 상세 보기</strong>
              <p>왼쪽 3D 맵에서 성향 노드를 클릭하면 해당 축의 점수와 계산 근거를 확인할 수 있어요.</p>
            </div>
          </template>

          <template v-else>
          <span class="eyebrow">{{ selectedDetail.type === "genre" ? "성향 노드" : "관심 게임 노드" }}</span>
          <h3>{{ selectedDetail.label }}</h3>
          <p>{{ selectedDetail.summary }}</p>

          <div v-if="selectedDetail.type === 'game'" class="selected-game-meta">
            <div>
              <strong>장르</strong>
              <span>{{ selectedDetail.genre }}</span>
            </div>
            <div>
              <strong>상태</strong>
              <span>{{ selectedDetail.userStatus }}</span>
            </div>
            <div>
              <strong>플랫폼 / 연결 축</strong>
              <span>{{ selectedDetail.platform }} / {{ genreAxes.find((axis) => axis.id === selectedDetail.axisId)?.label || "성향 축" }}</span>
            </div>
          </div>

          <div class="tag-row">
            <span v-for="tag in selectedDetail.tags || [selectedDetail.label]" :key="tag">#{{ tag }}</span>
          </div>

          <div class="achievement-list">
            <strong>{{ selectedDetail.type === "genre" ? "분석 근거" : "연결 근거" }}</strong>
            <span v-for="item in selectedDetail.evidence || selectedDetail.tags" :key="item">{{ item }}</span>
          </div>
          <div class="vector-detail-switch">
            <button type="button" @click="selectOverallAnalysis">전체 분석으로 돌아가기</button>
          </div>
          </template>
        </aside>
      </div>

      <div class="taste-action-grid">
        <section class="recommendation-strip">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Recommendation</p>
              <h2>성향 기반 추천 게임</h2>
            </div>
            <RouterLink to="/games">게임 탐색으로</RouterLink>
          </div>
          <div class="taste-recommend-cards">
            <RouterLink
              v-for="game in recommendedGames"
              :key="game.id"
              :to="`/games/${game.id}`"
              :style="recommendCardStyle(game)"
            >
              <span>{{ game.genre }}</span>
              <strong>{{ game.title }}</strong>
              <p>{{ game.summary }}</p>
              <em>{{ game.buy_signal }}</em>
            </RouterLink>
          </div>
        </section>

        <div class="mini-game-column">
          <article v-if="latestMiniGameResult" class="mini-game-result-card" :style="latestMiniGameCardStyle">
            <span>{{ latestMiniGamePalette.name }}</span>
            <strong>{{ latestMiniGameResult.result_title }}</strong>
            <p>{{ latestMiniGameResult.result_summary }}</p>
          </article>

          <RouterLink class="mini-game-cta" to="/taste/minigame">
            <span>{{ latestMiniGameResult ? "결과 갱신하기" : "설문 / 게임 하러 가기" }}</span>
            <strong>{{ latestMiniGameResult ? "도트 원정대 다시하기" : "도트 원정대" }}</strong>
            <small>{{ latestMiniGameResult ? "다시 플레이하고 저장하면 최신 결과로 바뀌어요" : "직접 움직여 NPC와 상호작용하며 취향 태그 만들기" }}</small>
          </RouterLink>
        </div>
      </div>
    </section>
  </section>
</template>
