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

let renderer;
let scene;
let camera;
let controls;
let animationId;
let raycaster;
let pointer;
let nodeGroup;
let nodeMeshes = [];
let resizeObserver;

const genreAxes = [
  {
    id: "strategy",
    type: "genre",
    label: "전략",
    score: 92,
    position: [2.8, 1.4, -0.6],
    color: "#17637d",
    summary: "빌드, 자원 관리, 장기 목표를 세우는 게임에서 체류 시간이 길어요.",
    evidence: ["Civilization VII 장시간 플레이", "전략/빌드형 업적 달성률 높음", "구매 전 사양/가격 비교를 자주 확인"],
  },
  {
    id: "coop",
    type: "genre",
    label: "협동",
    score: 81,
    position: [-1.7, 1.9, 1.4],
    color: "#176457",
    summary: "같이 역할을 나누고 진행하는 게임에 반응이 좋아요.",
    evidence: ["It Takes Two 관심/보유 기록", "커뮤니티 그룹 참여 성향", "친구와 함께 할 수 있는지 구매 전에 확인"],
  },
  {
    id: "action",
    type: "genre",
    label: "액션",
    score: 74,
    position: [1.8, -1.2, 2.1],
    color: "#b85f36",
    summary: "빠른 조작감과 반복 전투가 있는 게임도 꾸준히 소화해요.",
    evidence: ["Hades II 플레이 기록", "반복 도전 구간 이탈률 낮음", "전투 피드백이 빠른 게임 선호"],
  },
  {
    id: "explore",
    type: "genre",
    label: "탐험",
    score: 67,
    position: [-2.3, -0.2, -1.6],
    color: "#6f5bb7",
    summary: "메인 목표 외에도 숨겨진 경로, 수집, 세계관 정보를 확인하는 편이에요.",
    evidence: ["오픈월드 관심 게임 비중", "샛길/수집형 선택지 반응", "플레이 시간이 길수록 서브 콘텐츠 비중 증가"],
  },
  {
    id: "puzzle",
    type: "genre",
    label: "퍼즐",
    score: 58,
    position: [0.2, -2.0, -1.2],
    color: "#8a5a00",
    summary: "즉흥 플레이보다 단서를 모으고 해결하는 선택도 꽤 강해요.",
    evidence: ["공략 확인 후 진입하는 선택", "협동 퍼즐 게임 관심", "난이도보다 해결 과정에 반응"],
  },
];

const playedGameNodes = [
  {
    id: "civ7",
    type: "game",
    label: "Civilization VII",
    platform: "Steam",
    playtime: "128시간",
    achievement: "문명 승리 / 전략 빌드 업적 다수",
    position: [1.65, 0.15, -0.8],
    color: "#1d78a6",
    tags: ["전략", "장기플레이", "턴제"],
    summary: "전략 축에 가장 가까운 보유 게임이에요. 긴 플레이타임 때문에 현재 취향 중심을 강하게 끌고 있어요.",
  },
  {
    id: "ittakestwo",
    type: "game",
    label: "It Takes Two",
    platform: "Epic games",
    playtime: "18시간",
    achievement: "협동 챕터 클리어 / 퍼즐 구간 완주",
    position: [-1.0, 0.75, 1.8],
    color: "#22a06b",
    tags: ["협동", "퍼즐", "스토리"],
    summary: "협동 축과 퍼즐 축 사이에 있어요. 같이 진행하는 게임을 추천할 때 중요한 근거가 돼요.",
  },
  {
    id: "hades2",
    type: "game",
    label: "Hades II",
    platform: "Steam",
    playtime: "42시간",
    achievement: "반복 도전 / 보스전 적응",
    position: [1.1, -1.6, 1.9],
    color: "#d66b3d",
    tags: ["액션", "반복성장", "도전"],
    summary: "액션 축에 가까우면서도 도전 성향을 끌어올리는 게임이에요.",
  },
  {
    id: "wishlist-rpg",
    type: "game",
    label: "Baldur's Gate 3",
    platform: "관심 게임",
    playtime: "관심 등록",
    achievement: "서사/선택형 RPG 관심",
    position: [0.75, 1.05, -1.8],
    color: "#7d6ad8",
    tags: ["서사", "전략", "선택"],
    summary: "관심 게임 기준으로 보면 전략과 서사 축 사이의 게임도 끌리고 있어요.",
  },
  {
    id: "wishlist-party",
    type: "game",
    label: "Monster Hunter",
    platform: "관심 게임",
    playtime: "관심 등록",
    achievement: "멀티/장비 파밍 관심",
    position: [-2.2, 0.1, 2.2],
    color: "#2f9d88",
    tags: ["협동", "액션", "파밍"],
    summary: "협동과 액션 사이에 있는 관심 게임이에요. 그룹 플레이 추천 근거로 쓸 수 있어요.",
  },
];

const fallbackGames = [
  {
    id: 1,
    title: "Civilization VII",
    genre: "전략",
    buy_signal: "할인 때 구매 추천",
    summary: "계획을 세우고 장기적으로 판을 굴리는 성향에 잘 맞아요.",
  },
  {
    id: 2,
    title: "It Takes Two",
    genre: "협동",
    buy_signal: "같이 할 사람 있으면 지금",
    summary: "협동 선택 비중이 높은 플레이어에게 추천해요.",
  },
  {
    id: 3,
    title: "Hades II",
    genre: "액션 로그라이트",
    buy_signal: "도전 취향이면 구매",
    summary: "반복 도전과 빠른 액션을 좋아하면 잘 맞아요.",
  },
];

const tasteTags = computed(() => {
  const tags = report.value.taste_tags?.filter((tag) => tag && !looksBroken(tag)) || [];
  return tags.length ? tags : ["전략형", "협동형", "반복성장", "할인헌터"];
});

const recommendedGames = computed(() => {
  const apiGames = report.value.games?.filter(Boolean) || [];
  const games = apiGames.length ? apiGames : fallbackGames;
  return games.slice(0, 3).map((game, index) => ({
    ...fallbackGames[index % fallbackGames.length],
    ...game,
    genre: normalizeText(game.genre, fallbackGames[index % fallbackGames.length].genre),
    buy_signal: normalizeText(game.buy_signal, fallbackGames[index % fallbackGames.length].buy_signal),
    summary: normalizeText(game.summary, fallbackGames[index % fallbackGames.length].summary),
  }));
});

const topGenre = computed(() => genreAxes.slice().sort((a, b) => b.score - a.score)[0]);
const selectedDetail = computed(() => selectedNode.value);
const visualNodes = computed(() => []);
const analysisSummary = computed(() => {
  return `현재 벡터 중심은 ${topGenre.value.label} 축에 가장 가깝고, 보유 게임은 전략/협동/반복 성장 쪽으로 묶여 있어요. 관심 게임까지 포함하면 액션 협동과 서사 선택형 RPG로 확장되는 흐름이 보여요.`;
});

onMounted(async () => {
  try {
    const { data } = await api.get("/catalog/recommendations/");
    report.value = data;
  } catch {
    report.value = {
      taste_tags: ["전략형", "협동형", "반복성장", "할인헌터"],
      games: fallbackGames,
      report: "",
    };
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
  connectNearbyGames();

  renderer.domElement.addEventListener("pointerdown", handlePointerDown);
  resizeObserver = new ResizeObserver(resizeThreeMap);
  resizeObserver.observe(canvasHost.value);

  renderer.render(scene, camera);
  animateThreeMap();
}

function createNodes() {
  const allNodes = [...genreAxes, ...playedGameNodes];
  nodeMeshes = allNodes.map((node) => {
    const radius = node.type === "genre" ? 0.28 + node.score / 420 : 0.2;
    const geometry =
      node.type === "genre"
        ? new THREE.SphereGeometry(radius, 32, 24)
        : new THREE.OctahedronGeometry(radius, 1);
    const material = new THREE.MeshStandardMaterial({
      color: node.color,
      roughness: node.type === "genre" ? 0.32 : 0.5,
      metalness: node.type === "genre" ? 0.28 : 0.06,
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
      node.label,
      node.color,
      [node.position[0], node.position[1] + radius + 0.34, node.position[2]],
      node.type === "genre" ? 0.76 : 0.52,
      { isGenre: node.type === "genre" },
    );
    nodeGroup.add(label);
    return mesh;
  });
}

function connectNearbyGames() {
  const lines = [
    ["strategy", "civ7"],
    ["coop", "ittakestwo"],
    ["action", "hades2"],
    ["strategy", "wishlist-rpg"],
    ["coop", "wishlist-party"],
    ["action", "wishlist-party"],
  ];

  lines.forEach(([fromId, toId]) => {
    const from = [...genreAxes, ...playedGameNodes].find((item) => item.id === fromId);
    const to = [...genreAxes, ...playedGameNodes].find((item) => item.id === toId);
    if (!from || !to) return;
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...from.position),
      new THREE.Vector3(...to.position),
    ]);
    const material = new THREE.LineBasicMaterial({ color: "#9fb4c9", transparent: true, opacity: 0.55 });
    scene.add(new THREE.Line(geometry, material));
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
        <h1>3D 플레이 성향 벡터 맵</h1>
        <p>지금까지 한 게임과 관심 게임을 word2vec처럼 성향 공간에 배치해서 보여줘요.</p>
      </div>
    </header>

    <section class="panel taste-report-board">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">GameFit Vector Space</p>
          <h2>보유 / 관심 게임 기반 플레이 성향 분석</h2>
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
              <h3>게임들이 어떤 성향 축에 가까운지 보기</h3>
            </div>
            <div class="vector3d-legend">
              <span><i class="legend-genre"></i>성향 축</span>
              <span><i class="legend-game"></i>게임 노드</span>
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
            <h3>보유 / 관심 게임 기반 플레이 성향</h3>
            <p>{{ analysisSummary }}</p>

            <div class="tag-row">
              <span v-for="tag in tasteTags" :key="tag">#{{ tag }}</span>
            </div>

            <div class="achievement-list">
              <strong>주요 성향 분포</strong>
              <span v-for="genre in genreAxes" :key="genre.id" :style="{ borderLeftColor: genre.color }">
                {{ genre.label }} {{ genre.score }}%
              </span>
            </div>

            <div class="vector-summary-box">
              <strong>노드 상세 보기</strong>
              <p>왼쪽 3D 맵에서 성향 노드나 게임 노드를 클릭하면 해당 노드의 분석 근거를 확인할 수 있어요.</p>
            </div>
          </template>

          <template v-else>
          <span class="eyebrow">{{ selectedDetail.type === "genre" ? "성향 노드" : "게임 노드" }}</span>
          <h3>{{ selectedDetail.label }}</h3>
          <p>{{ selectedDetail.summary }}</p>

          <div v-if="selectedDetail.type === 'game'" class="selected-game-meta">
            <div>
              <strong>플랫폼</strong>
              <span>{{ selectedDetail.platform }}</span>
            </div>
            <div>
              <strong>플레이/상태</strong>
              <span>{{ selectedDetail.playtime }}</span>
            </div>
            <div>
              <strong>업적/기록</strong>
              <span>{{ selectedDetail.achievement }}</span>
            </div>
          </div>

          <div class="tag-row">
            <span v-for="tag in selectedDetail.tags || [selectedDetail.label]" :key="tag">#{{ tag }}</span>
          </div>

          <div class="achievement-list">
            <strong>{{ selectedDetail.type === "genre" ? "분석 근거" : "이 게임이 끌어당기는 성향" }}</strong>
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
              <h2>벡터 기반 추천 게임</h2>
            </div>
            <RouterLink to="/games">게임 탐색으로</RouterLink>
          </div>
          <div class="taste-recommend-cards">
            <RouterLink v-for="game in recommendedGames" :key="game.id" :to="`/games/${game.id}`">
              <span>{{ game.genre }}</span>
              <strong>{{ game.title }}</strong>
              <p>{{ game.summary }}</p>
              <em>{{ game.buy_signal }}</em>
            </RouterLink>
          </div>
        </section>

        <RouterLink class="mini-game-cta" to="/taste/minigame">
          <span>설문 / 게임 하러 가기</span>
          <strong>8비트 취향 원정대</strong>
          <small>직접 움직여 NPC와 상호작용하며 취향 태그 만들기</small>
        </RouterLink>
      </div>
    </section>
  </section>
</template>
