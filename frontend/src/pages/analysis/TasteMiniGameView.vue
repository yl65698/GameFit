<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();

const stageRef = ref(null);
const sceneIndex = ref(0);
const playerX = ref(14);
const facing = ref("right");
const isMoving = ref(false);
const interactionOpen = ref(false);
const answers = ref([]);
const saveMessage = ref("");

let moveTimer = null;

const startX = 14;
const npcX = 76;
const nearDistance = 8;

const scenes = [
  {
    id: "gate",
    type: "intro",
    title: "취향의 관문",
    theme: "gate",
    npcName: "루미",
    actor: "fairy",
    fairy: "좋아, 이번엔 네가 직접 움직여서 취향을 찾아가는 거야.",
    text: "WASD 또는 방향키로 이동하고, NPC 옆에서 Space를 누르면 상호작용해. 장면마다 선택을 고르면 다음 길이 열려.",
    tags: ["튜토리얼", "직접조작"],
  },
  {
    id: "rival",
    title: "다리 위의 라이벌",
    theme: "arena",
    npcName: "도전하는 플레이어",
    actor: "rival",
    fairy: "저 플레이어가 길을 막고 있어. 가까이 가서 말을 걸어보자.",
    text: "상대는 바로 대결을 걸어왔다. 빠르게 이기고 길을 열 수도 있고, 싸우지 않고 다른 길을 찾을 수도 있다.",
    tags: ["경쟁", "대전", "긴장감"],
    choices: [
      { text: "바로 승부한다", tone: "승부욕이 올라온다", scores: { competitive: 3, action: 1 }, tags: ["경쟁형", "PvP선호"] },
      { text: "패턴을 보고 천천히 공략한다", tone: "이길 방법부터 찾는다", scores: { strategy: 3, challenge: 1 }, tags: ["전략형", "공략선호"] },
      { text: "돌아가는 길을 찾는다", tone: "굳이 싸울 필요는 없다", scores: { cozy: 2, exploration: 2 }, tags: ["탐험형", "평화선호"] },
    ],
  },
  {
    id: "helper",
    title: "고장 난 수레",
    theme: "village",
    npcName: "곤란한 여행자",
    actor: "helper",
    fairy: "누군가 도움이 필요해 보여. 이번에도 직접 다가가서 얘기해보자.",
    text: "여행자의 수레 바퀴가 빠졌다. 도와주면 시간이 걸리지만, 마을의 작은 이야기를 얻을 수 있다.",
    tags: ["협동", "선택", "역할"],
    choices: [
      { text: "같이 고쳐준다", tone: "같이 해결하는 게 좋다", scores: { social: 3, story: 1 }, tags: ["협동형", "서포터"] },
      { text: "필요한 도구만 건네준다", tone: "효율적으로 돕는다", scores: { strategy: 2, social: 1 }, tags: ["실용형", "균형형"] },
      { text: "목표가 급해서 먼저 간다", tone: "메인 목표가 우선이다", scores: { action: 2, competitive: 1 }, tags: ["목표지향", "속도중시"] },
    ],
  },
  {
    id: "scenery",
    title: "노을빛 숲길",
    theme: "forest",
    npcName: "반짝이는 샛길",
    actor: "scenery",
    fairy: "저쪽 길이 엄청 예뻐. 가까이 가면 어떤 길인지 볼 수 있을 것 같아.",
    text: "샛길에는 숨겨진 풍경과 작은 이야기들이 있다. 빠른 진행을 포기하면 뜻밖의 발견을 할 수 있다.",
    tags: ["탐험", "감성", "월드"],
    choices: [
      { text: "샛길로 돌아간다", tone: "맵 구경은 못 참는다", scores: { exploration: 3, cozy: 1 }, tags: ["탐험형", "오픈월드"] },
      { text: "풍경만 보고 바로 복귀한다", tone: "분위기는 챙기고 진행도 챙긴다", scores: { story: 2, strategy: 1 }, tags: ["균형형", "서사선호"] },
      { text: "메인 길로 계속 간다", tone: "목표 동선이 중요하다", scores: { challenge: 2, action: 1 }, tags: ["진행중시", "목표형"] },
    ],
  },
  {
    id: "ruin",
    title: "어두운 유적 입구",
    theme: "dungeon",
    npcName: "수상한 문",
    actor: "dungeon",
    fairy: "문 앞까지 가보자. 안쪽은 위험하지만 보상이 클 수도 있어.",
    text: "문 너머에는 강한 적, 퍼즐, 숨겨진 보상이 기다린다. 실패하면 다시 도전해야 한다.",
    tags: ["도전", "공포", "퍼즐"],
    choices: [
      { text: "위험해도 들어간다", tone: "실패해도 다시 하면 된다", scores: { challenge: 3, action: 1 }, tags: ["도전형", "하드코어"] },
      { text: "단서를 모은 뒤 들어간다", tone: "준비한 만큼 편해진다", scores: { strategy: 3, exploration: 1 }, tags: ["전략형", "퍼즐선호"] },
      { text: "오늘은 밝은 곳이 좋다", tone: "무리한 긴장감은 피하고 싶다", scores: { cozy: 3, story: 1 }, tags: ["힐링형", "라이트유저"] },
    ],
  },
  {
    id: "market",
    title: "할인 상인의 마차",
    theme: "market",
    npcName: "할인 상인",
    actor: "shop",
    fairy: "마지막이야. 상인이 게임 살 때의 습관을 물어보려나 봐.",
    text: "신작, 할인, 평가, 친구 추천까지 전부 눈에 들어온다. 지금 사는 선택도 취향이다.",
    tags: ["구매성향", "할인", "추천"],
    choices: [
      { text: "할인율부터 확인한다", tone: "가격 타이밍이 제일 중요하다", scores: { strategy: 2, cozy: 1 }, tags: ["할인헌터", "가성비"] },
      { text: "친구랑 같이 할 수 있는지 본다", tone: "같이 하면 훨씬 재밌다", scores: { social: 3, competitive: 1 }, tags: ["파티플레이", "멀티선호"] },
      { text: "트레일러 보고 감으로 고른다", tone: "꽂히면 바로 시작한다", scores: { action: 2, story: 2 }, tags: ["직감형", "몰입형"] },
    ],
  },
  {
    id: "result",
    type: "result",
    title: "취향 결정의 제단",
    theme: "result",
    npcName: "루미",
    actor: "fairy",
    fairy: "여기까지 직접 걸어온 선택들이 꽤 선명해졌어.",
    text: "이번 모험에서 고른 행동을 바탕으로 프로필에 쓸 수 있는 취향 태그를 만들었어.",
    tags: ["결과", "프로필태그"],
  },
];

const resultProfiles = {
  competitive: {
    title: "승부욕 있는 랭커형",
    summary: "실시간 대결, 랭크, 성과가 보이는 게임에서 몰입도가 높아요.",
    tags: ["경쟁형", "PvP선호", "랭크도전"],
    games: ["Apex Legends", "Street Fighter 6", "Valorant"],
  },
  strategy: {
    title: "계획 세우는 공략가형",
    summary: "정보를 모으고 빌드를 짜서 깔끔하게 해결하는 플레이를 좋아해요.",
    tags: ["전략형", "공략선호", "퍼즐선호"],
    games: ["Baldur's Gate 3", "Civilization VI", "Into the Breach"],
  },
  exploration: {
    title: "샛길 좋아하는 탐험가형",
    summary: "메인 목표보다 숨겨진 길, 풍경, 수집 요소에서 재미를 크게 느껴요.",
    tags: ["탐험형", "오픈월드", "수집선호"],
    games: ["Elden Ring", "Zelda-like Adventure", "No Man's Sky"],
  },
  social: {
    title: "같이 놀 때 강한 파티형",
    summary: "혼자보다 같이 역할을 나누고 웃으면서 진행할 때 게임이 살아나요.",
    tags: ["협동형", "파티플레이", "서포터"],
    games: ["Helldivers 2", "It Takes Two", "Monster Hunter"],
  },
  story: {
    title: "서사 몰입형 플레이어",
    summary: "인물, 분위기, 선택의 의미가 살아있는 게임에서 가장 오래 머물러요.",
    tags: ["서사선호", "몰입형", "감성플레이"],
    games: ["Disco Elysium", "Life is Strange", "Cyberpunk 2077"],
  },
  action: {
    title: "손맛 빠른 액션형",
    summary: "빠른 판단, 조작감, 즉각적인 피드백이 있는 게임이 잘 맞아요.",
    tags: ["액션형", "속도중시", "컨트롤"],
    games: ["Hades", "Devil May Cry 5", "Dead Cells"],
  },
  challenge: {
    title: "다시 도전하는 하드코어형",
    summary: "어려운 구간을 넘었을 때의 성취감이 게임의 핵심 재미예요.",
    tags: ["도전형", "하드코어", "보스전"],
    games: ["Sekiro", "Hollow Knight", "Darkest Dungeon"],
  },
  cozy: {
    title: "천천히 즐기는 힐링형",
    summary: "부담 없는 진행, 예쁜 분위기, 내 속도대로 하는 플레이가 좋아요.",
    tags: ["힐링형", "라이트유저", "평화선호"],
    games: ["Stardew Valley", "Dave the Diver", "Unpacking"],
  },
};

const currentScene = computed(() => scenes[sceneIndex.value]);
const playableScenes = computed(() => scenes.filter((scene) => scene.choices));
const completedChoiceCount = computed(() => answers.value.length);
const isComplete = computed(() => currentScene.value.type === "result");
const isNearNpc = computed(() => Math.abs(playerX.value - npcX) <= nearDistance);
const canInteract = computed(() => isNearNpc.value && !interactionOpen.value && !isComplete.value);
const stageMessage = computed(() => {
  if (isComplete.value) return "결과가 열렸어. 프로필 태그로 저장할 수 있어.";
  if (interactionOpen.value) return "대화 중이야. 선택지를 골라 다음 장면으로 가자.";
  if (canInteract.value) return "Space를 눌러 상호작용";
  return "WASD / 방향키로 NPC에게 다가가기";
});

const scores = computed(() => {
  const total = {};
  answers.value.forEach((answer) => {
    Object.entries(answer.scores).forEach(([key, value]) => {
      total[key] = (total[key] || 0) + value;
    });
  });
  return total;
});

const topKey = computed(() => {
  const entries = Object.entries(scores.value);
  if (!entries.length) return "exploration";
  return entries.sort((a, b) => b[1] - a[1])[0][0];
});

const result = computed(() => {
  const base = resultProfiles[topKey.value] || resultProfiles.exploration;
  const pickedTags = answers.value.flatMap((answer) => answer.tags);
  return {
    ...base,
    tags: Array.from(new Set([...base.tags, ...pickedTags])).slice(0, 8),
  };
});

function handleKeydown(event) {
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "w", "a", "s", "d", "W", "A", "S", "D", " "].includes(event.key)) {
    event.preventDefault();
  }

  if (event.key === " " || event.code === "Space") {
    openInteraction();
    return;
  }

  if (interactionOpen.value || isComplete.value) return;

  if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") {
    movePlayer(-4);
  }

  if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") {
    movePlayer(4);
  }

  if (event.key === "ArrowUp" || event.key.toLowerCase() === "w") {
    movePlayer(2);
  }

  if (event.key === "ArrowDown" || event.key.toLowerCase() === "s") {
    movePlayer(-2);
  }
}

function movePlayer(delta) {
  const next = Math.max(8, Math.min(npcX, playerX.value + delta));
  facing.value = delta < 0 ? "left" : "right";
  playerX.value = next;
  isMoving.value = true;
  window.clearTimeout(moveTimer);
  moveTimer = window.setTimeout(() => {
    isMoving.value = false;
  }, 160);
}

function openInteraction() {
  if (isComplete.value) return;
  if (!isNearNpc.value) {
    stageRef.value?.focus();
    return;
  }
  interactionOpen.value = true;
}

function choose(choice) {
  answers.value.push({
    sceneId: currentScene.value.id,
    label: choice.text,
    scores: choice.scores,
    tags: choice.tags,
    tone: choice.tone,
  });
  goToScene(sceneIndex.value + 1);
}

function goToScene(nextIndex) {
  saveMessage.value = "";
  interactionOpen.value = false;
  isMoving.value = true;
  window.setTimeout(() => {
    sceneIndex.value = Math.min(nextIndex, scenes.length - 1);
    playerX.value = startX;
    facing.value = "right";
    isMoving.value = false;
    nextTick(() => stageRef.value?.focus());
  }, 420);
}

function resetJourney() {
  sceneIndex.value = 0;
  playerX.value = startX;
  facing.value = "right";
  interactionOpen.value = false;
  answers.value = [];
  saveMessage.value = "";
  isMoving.value = false;
  nextTick(() => stageRef.value?.focus());
}

async function saveTasteTags() {
  if (!auth.user) return;
  await auth.updateProfile({
    ...auth.user,
    hashtags: result.value.tags,
  });
  saveMessage.value = "프로필 취향 태그에 저장했어.";
}

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
  nextTick(() => stageRef.value?.focus());
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.clearTimeout(moveTimer);
});
</script>

<template>
  <div class="page-shell">
    <div class="page-heading">
      <div>
        <RouterLink class="text-link" to="/taste">← 게임 성향 분석으로</RouterLink>
        <h1>8비트 취향 원정대</h1>
        <p>직접 걸어가 NPC와 상호작용하며 내 게임 취향을 찾는 벨트스크롤형 미니게임</p>
      </div>
      <button class="ghost-button" type="button" @click="resetJourney">처음부터</button>
    </div>

    <section class="sidequest-shell">
      <main
        ref="stageRef"
        class="sidequest-stage"
        :class="[`stage-${currentScene.theme}`, { 'is-walking': isMoving }]"
        tabindex="0"
      >
        <div class="sidequest-hud">
          <span>STAGE {{ Math.min(completedChoiceCount + 1, playableScenes.length) }} / {{ playableScenes.length }}</span>
          <strong>{{ currentScene.title }}</strong>
          <span>{{ currentScene.tags.join(" · ") }}</span>
        </div>

        <div class="sidequest-world" :class="{ 'is-walking': isMoving, 'is-near-npc': isNearNpc }">
          <div class="skyline layer-back"></div>
          <div class="skyline layer-mid"></div>
          <div class="pixel-cloud cloud-one"></div>
          <div class="pixel-cloud cloud-two"></div>
          <div class="scene-prop prop-left"></div>
          <div class="scene-prop prop-right"></div>

          <div
            class="runner-hero"
            :class="{ 'is-facing-left': facing === 'left' }"
            :style="{ left: `${playerX}%` }"
            aria-label="플레이어 캐릭터"
          >
            <i></i>
          </div>
          <div class="runner-fairy" :style="{ left: `calc(${playerX}% + 54px)` }" aria-label="안내 요정 루미">
            <i></i>
          </div>
          <div class="scene-actor" :class="`actor-${currentScene.actor}`" :style="{ left: `${npcX}%` }">
            <i></i>
          </div>

          <div class="interaction-banner" :class="{ active: canInteract }">
            {{ stageMessage }}
          </div>
          <div class="sidequest-floor"></div>
        </div>

        <section class="dialogue-panel" :class="{ 'is-locked': !interactionOpen && !isComplete }">
          <div class="speaker-row">
            <span>{{ currentScene.npcName }}</span>
            <strong>{{ interactionOpen || isComplete ? currentScene.title : "상호작용 대기" }}</strong>
          </div>

          <template v-if="interactionOpen || isComplete">
            <p class="fairy-line">루미: {{ currentScene.fairy }}</p>
            <p>{{ currentScene.text }}</p>

            <div v-if="currentScene.type === 'intro'" class="choice-grid">
              <button class="primary-button" type="button" @click="goToScene(1)">길을 나선다</button>
            </div>

            <div v-else-if="currentScene.choices" class="choice-grid">
              <button v-for="choice in currentScene.choices" :key="choice.text" type="button" @click="choose(choice)">
                <strong>{{ choice.text }}</strong>
                <span>{{ choice.tone }}</span>
              </button>
            </div>

            <div v-else class="result-panel">
              <div>
                <span class="eyebrow">RESULT</span>
                <h2>{{ result.title }}</h2>
                <p>{{ result.summary }}</p>
              </div>
              <div class="tag-row">
                <span v-for="tag in result.tags" :key="tag">#{{ tag }}</span>
              </div>
              <div class="recommended-games">
                <strong>추천 후보</strong>
                <span v-for="game in result.games" :key="game">{{ game }}</span>
              </div>
              <div class="form-actions">
                <button class="primary-button" type="button" @click="saveTasteTags">프로필에 태그 저장</button>
                <button class="ghost-button" type="button" @click="resetJourney">다시 플레이</button>
              </div>
              <p v-if="saveMessage" class="success-text">{{ saveMessage }}</p>
            </div>
          </template>

          <template v-else>
            <p class="fairy-line">루미: NPC에게 가까이 가서 Space를 눌러봐.</p>
            <p>조작: A/D 또는 ←/→ 이동, W/S 또는 ↑/↓로 살짝 전후 이동, Space 상호작용</p>
          </template>
        </section>
      </main>

      <aside class="sidequest-panel">
        <section class="fairy-guide-card">
          <div class="pixel-fairy big"><i></i></div>
          <div>
            <span class="eyebrow">GUIDE</span>
            <h2>루미의 조작 메모</h2>
            <p>NPC에게 닿을 만큼 가까워지면 상호작용 문구가 바뀌어. 그때 Space를 누르면 돼.</p>
          </div>
        </section>

        <section class="control-help-card">
          <h2>조작</h2>
          <div class="key-grid">
            <span>W</span>
            <span>A</span>
            <span>S</span>
            <span>D</span>
            <strong>Space</strong>
          </div>
          <p>방향키도 동일하게 작동해.</p>
        </section>

        <section class="quest-progress-card">
          <h2>장면 진행</h2>
          <div class="sidequest-progress">
            <span
              v-for="(scene, index) in playableScenes"
              :key="scene.id"
              :class="{ done: completedChoiceCount > index, active: completedChoiceCount === index && !isComplete }"
            >
              {{ index + 1 }}
            </span>
          </div>
        </section>

        <section class="story-log-card">
          <h2>내 선택</h2>
          <div v-if="answers.length" class="story-log">
            <article v-for="answer in answers" :key="answer.sceneId">
              <strong>{{ answer.label }}</strong>
              <span>{{ answer.tone }}</span>
            </article>
          </div>
          <p v-else>아직 선택한 장면이 없어.</p>
        </section>
      </aside>
    </section>
  </div>
</template>
