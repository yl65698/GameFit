<template>
  <section class="game-detail-page">
    <RouterLink class="detail-back" to="/games">← 목록으로 돌아가기</RouterLink>

    <div class="game-detail-shell">
      <main class="game-detail-main">
        <section class="game-hero-image" :style="{ backgroundImage: `linear-gradient(120deg, rgba(12, 18, 28, 0.2), rgba(12, 18, 28, 0.72)), url(${gameImage})` }">
          <span>{{ game.title || "게임 이미지" }}</span>
        </section>

        <section class="game-title-row">
          <div>
            <h1>{{ game.title || "게임이름" }}</h1>
            <p>{{ game.summary || "간단한 게임 설명" }}</p>
            <div class="tag-pill-row">
              <span v-for="keyword in gameKeywords" :key="keyword">{{ keyword }}</span>
            </div>
          </div>
          <div class="detail-action-stack">
            <button :class="isOwned ? 'secondary-button' : 'primary-button'" @click="handleOwnedClick">
              {{ isOwned ? "내 게임에서 제거" : "내 게임 추가" }}
            </button>
            <button :class="isInterested ? 'secondary-button danger-soft-button' : 'secondary-button'" @click="handleInterestedClick">
              {{ isInterested ? "관심게임 삭제" : "관심게임 등록" }}
            </button>
            <button v-if="isInterested" class="alert-toggle-button" @click="toggleInterestAlert">
              <span :class="{ active: isAlertEnabled }"></span>
              {{ isAlertEnabled ? "알림 끄기" : "알림 켜기" }}
            </button>
          </div>
        </section>

        <section v-if="showPlatformPicker" class="platform-picker">
          <label>
            구매 플랫폼
            <select v-model="selectedPlatform">
              <option v-for="platform in platforms" :key="platform.value" :value="platform.value">
                {{ platform.label }}
              </option>
            </select>
          </label>
          <button class="primary-button" @click="confirmOwnedAdd">확인</button>
          <button class="secondary-button" @click="showPlatformPicker = false">취소</button>
        </section>

        <p v-if="actionMessage" class="action-message">{{ actionMessage }}</p>

        <section class="detail-panel price-trend-panel">
          <div class="panel-heading compact">
            <h2>가격 변동 추이</h2>
            <span>최근 6개월</span>
          </div>
          <svg class="line-chart" viewBox="0 0 600 180" role="img" aria-label="가격 변동 선 그래프">
            <polyline class="line-chart-grid" points="0,36 600,36" />
            <polyline class="line-chart-grid" points="0,90 600,90" />
            <polyline class="line-chart-grid" points="0,144 600,144" />
            <polyline class="line-chart-line" :points="priceChartPoints" />
            <circle v-for="point in priceHistoryPoints" :key="point.label" class="line-chart-dot" :cx="point.x" :cy="point.y" r="5" />
          </svg>
          <div class="chart-labels">
            <span v-for="point in priceHistoryPoints" :key="point.label">{{ point.label }}</span>
          </div>
        </section>

        <div class="detail-info-grid">
          <section class="detail-panel">
            <h2>가격 비교</h2>
            <div class="price-market-list">
              <article v-for="market in priceMarkets" :key="market.platform">
                <strong>{{ market.platform }}</strong>
                <span>{{ market.price.toLocaleString("ko-KR") }}원</span>
                <em>{{ market.discount }}%</em>
                <a class="price-link-button" :href="market.url" target="_blank" rel="noreferrer">이동</a>
              </article>
            </div>
          </section>

          <section class="detail-panel">
            <h2>구매 추천 시점</h2>
            <strong class="buy-timing">{{ timingHeadline }}</strong>
            <p>{{ timingMessage }}</p>
          </section>

          <section class="detail-panel">
            <div class="panel-heading compact">
              <h2>게임 정보</h2>
              <a :href="infoUrl" target="_blank" rel="noreferrer">정보 사이트</a>
            </div>
            <dl class="game-info-list">
              <div v-for="item in gameInfo" :key="item.label">
                <dt>{{ item.label }}</dt>
                <dd>{{ item.value }}</dd>
              </div>
            </dl>
          </section>

          <section class="detail-panel">
            <h2>게임 최소 / 권장 사양</h2>
            <div class="requirement-list">
              <article>
                <strong>최소</strong>
                <p>{{ requirements.minimum }}</p>
              </article>
              <article>
                <strong>권장</strong>
                <p>{{ requirements.recommended }}</p>
              </article>
            </div>
          </section>
        </div>

        <section class="review-section">
          <div class="review-heading">
            <h2>게임 의견 및 평가</h2>
            <RouterLink class="secondary-button" :to="`/games/${game.id}/community`">게임 커뮤니티</RouterLink>
          </div>

          <form class="review-form" @submit.prevent="submitReview">
            <div class="recommend-toggle">
              <button type="button" :class="{ active: reviewForm.recommend === true }" @click="reviewForm.recommend = true">
                추천
              </button>
              <button type="button" :class="{ active: reviewForm.recommend === false }" @click="reviewForm.recommend = false">
                비추천
              </button>
            </div>
            <textarea v-model="reviewForm.body" placeholder="이 게임에 대한 의견을 남겨주세요." />
            <button class="primary-button">댓글 남기기</button>
          </form>

          <article v-for="review in reviews" :key="review.id" class="review-card">
            <RouterLink class="review-avatar" :to="`/players/${review.username}`">{{ review.avatar }}</RouterLink>
            <div>
              <div class="review-meta">
                <RouterLink :to="`/players/${review.username}`">{{ review.username }}</RouterLink>
                <span :class="['review-vote', review.recommend ? 'good' : 'bad']">
                  {{ review.recommend ? "추천" : "비추천" }}
                </span>
              </div>
              <strong>{{ review.title }}</strong>
              <p>{{ review.body }}</p>
            </div>
          </article>
        </section>
      </main>

      <aside class="game-compat-sidebar">
        <h2>내 장비로 가능할까?</h2>
        <p class="compat-summary">{{ compatibilitySummary }}</p>

        <dl class="compat-spec-list">
          <div v-for="spec in specChecks" :key="spec.label">
            <dt>{{ spec.label }}</dt>
            <dd>
              <strong>{{ spec.current }}</strong>
              <small>{{ spec.message }}</small>
            </dd>
            <span :class="['spec-badge', spec.status]">{{ spec.icon }}</span>
          </div>
        </dl>

        <div class="storage-spec-row">
          <div>
            <strong>저장공간</strong>
            <span>{{ storageSpec.current }}</span>
            <small>{{ storageSpec.message }}</small>
          </div>
          <span :class="['spec-badge', storageSpec.status]">{{ storageSpec.icon }}</span>
        </div>
        <div class="storage-meter">
          <span :style="{ width: `${storageUsage}%` }"></span>
        </div>
        <p class="storage-caption">C 드라이브 200GB / 2 TB</p>

        <div class="compat-actions">
          <RouterLink class="primary-button" to="/equipment">필요한 장비 구매하기</RouterLink>
          <RouterLink class="secondary-button" to="/profile/edit?tab=pc">내 장비 업데이트</RouterLink>
        </div>

        <section class="upgrade-section">
          <h3>추천 업그레이드</h3>
          <RouterLink v-for="item in upgrades" :key="item.id" class="upgrade-card" :to="`/equipment/${item.id}`">
            <span>{{ item.type }}</span>
            <strong>{{ item.name }}</strong>
            <small>{{ item.reason }}</small>
          </RouterLink>
        </section>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import api from "../../services/api";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const auth = useAuthStore();
const game = ref({});
const actionMessage = ref("");
const showPlatformPicker = ref(false);
const selectedPlatform = ref("Steam");
const reviewForm = reactive({
  recommend: true,
  body: "",
});
const localReviews = ref([]);

const platforms = [
  { label: "Steam", value: "Steam" },
  { label: "Epic games", value: "Epic games" },
  { label: "Ubisoft", value: "Ubisoft" },
  { label: "그 외", value: "Other" },
];

const detailByTitle = {
  "Civilization VII": {
    keywords: ["전략", "4X", "턴제", "시뮬레이션"],
    colors: ["#1d3557", "#2a9d8f", "#e9c46a"],
    publisher: "Firaxis Games",
    releaseDate: "2025년 예정",
    ageRating: "12세 이용가",
    developer: "Firaxis Games",
    officialUrl: "https://civilization.2k.com/",
    minimum: "Intel i5급 CPU, GTX 1060, 8GB RAM, 저장공간 50GB",
    recommended: "Ryzen 7 5800X, RTX 2060 이상, 16GB RAM, 저장공간 80GB",
    priceHistory: [62000, 59800, 56000, 54800, 49800, 42300],
  },
  "It Takes Two": {
    keywords: ["협동", "퍼즐", "액션", "어드벤처"],
    colors: ["#5f4bb6", "#86a8e7", "#f9c74f"],
    publisher: "Electronic Arts",
    releaseDate: "2021년 3월",
    ageRating: "12세 이용가",
    developer: "Hazelight Studios",
    officialUrl: "https://www.ea.com/games/it-takes-two",
    minimum: "Intel i3급 CPU, GTX 660, 8GB RAM, 저장공간 50GB",
    recommended: "Ryzen 5급 CPU, GTX 980 이상, 16GB RAM, 저장공간 50GB",
    priceHistory: [44000, 33000, 26000, 22000, 19800, 17600],
  },
  "Hades II": {
    keywords: ["액션", "로그라이트", "인디", "싱글플레이"],
    colors: ["#3a0ca3", "#f72585", "#ffb703"],
    publisher: "Supergiant Games",
    releaseDate: "얼리 액세스",
    ageRating: "15세 이용가",
    developer: "Supergiant Games",
    officialUrl: "https://www.supergiantgames.com/games/hades-ii/",
    minimum: "Dual Core CPU, GTX 950, 8GB RAM, 저장공간 10GB",
    recommended: "Quad Core CPU, GTX 1060 이상, 16GB RAM, 저장공간 10GB",
    priceHistory: [32000, 32000, 30400, 28800, 28800, 27200],
  },
};

const defaultDetail = {
  keywords: ["액션", "퍼즐", "인디"],
  colors: ["#14213d", "#17637d", "#8ad0c2"],
  publisher: "Game Studio",
  releaseDate: "출시일 미정",
  ageRating: "전체 이용가",
  developer: "Game Studio",
  officialUrl: "https://store.steampowered.com/",
  minimum: "GTX 1060, 8GB RAM, 저장공간 50GB",
  recommended: "RTX 2060, 16GB RAM, 저장공간 80GB",
  priceHistory: [48000, 46000, 43000, 41000, 39000, 36000],
};

const detail = computed(() => detailByTitle[game.value.title] || defaultDetail);
const gameKeywords = computed(() => detail.value.keywords);
const gameImage = computed(() => createGameArtwork(game.value.title || "GameFit", detail.value.keywords, detail.value.colors));
const isOwned = computed(() => Boolean(game.value.title && (auth.user?.owned_games || []).includes(game.value.title)));
const isInterested = computed(() => Boolean(game.value.title && (auth.user?.interested_games || []).includes(game.value.title)));
const isAlertEnabled = computed(() => {
  if (!game.value.title) return false;
  const alerts = auth.user?.interest_alerts || {};
  return alerts[game.value.title] ?? true;
});
const infoUrl = computed(() => detail.value.officialUrl);
const requirements = computed(() => ({
  minimum: detail.value.minimum,
  recommended: detail.value.recommended,
}));
const priceMarkets = computed(() => {
  const base = Number(game.value.price || 0) || 30000;
  return [
    {
      platform: "Steam",
      price: base,
      discount: Number(game.value.discount || 0),
      url: `https://store.steampowered.com/search/?term=${encodeURIComponent(game.value.title || "")}`,
    },
    {
      platform: "Epic games",
      price: Math.max(0, Math.floor(base * 0.92)),
      discount: Math.min(80, Number(game.value.discount || 0) + 8),
      url: `https://store.epicgames.com/ko/browse?q=${encodeURIComponent(game.value.title || "")}`,
    },
    {
      platform: "Ubisoft",
      price: Math.max(0, Math.floor(base * 0.98)),
      discount: Math.max(0, Number(game.value.discount || 0) - 5),
      url: "https://store.ubisoft.com/kr/home",
    },
  ].sort((a, b) => a.price - b.price);
});
const timingHeadline = computed(() => {
  if ((game.value.discount || 0) >= 50) return "지금 구매 추천";
  if ((game.value.discount || 0) >= 25) return "관심 등록 후 한 번 더 확인";
  return "다음 대형 세일까지 대기";
});
const timingMessage = computed(() => {
  if ((game.value.discount || 0) >= 50) return "최근 가격 흐름상 할인 폭이 충분히 커서 바로 구매해도 괜찮아요.";
  if ((game.value.discount || 0) >= 25) return "현재도 나쁘지 않지만 이전 최저가보다 높아서 관심게임에 넣고 알림을 보는 쪽이 좋아요.";
  return "할인율이 낮아서 여름/연말 세일 때 다시 확인하는 걸 추천해요.";
});
const gameInfo = computed(() => [
  { label: "제조사", value: detail.value.publisher },
  { label: "개발사", value: detail.value.developer },
  { label: "출시일", value: detail.value.releaseDate },
  { label: "권장연령", value: detail.value.ageRating },
]);
const priceHistoryPoints = computed(() => {
  const values = detail.value.priceHistory;
  const min = Math.min(...values);
  const max = Math.max(...values);
  return values.map((value, index) => {
    const ratio = max === min ? 0.5 : (value - min) / (max - min);
    return {
      label: `${index + 1}월`,
      x: 34 + index * 106,
      y: 150 - ratio * 118,
    };
  });
});
const priceChartPoints = computed(() => priceHistoryPoints.value.map((point) => `${point.x},${point.y}`).join(" "));

const specChecks = computed(() => [
  {
    label: "CPU",
    current: auth.user?.pc_specs?.cpu || "AMD Ryzen 7 5800X",
    message: "권장 사양 충족",
    status: "pass",
    icon: "v",
  },
  {
    label: "메모리",
    current: auth.user?.pc_specs?.memory || "64GB",
    message: "충분함",
    status: "pass",
    icon: "v",
  },
  {
    label: "GPU",
    current: auth.user?.pc_specs?.gpu || "NVIDIA RTX 3070 Ti",
    message: (game.value.title || "").includes("Civilization") ? "중상옵 안정권" : "쾌적",
    status: (game.value.title || "").includes("Civilization") ? "warn" : "pass",
    icon: (game.value.title || "").includes("Civilization") ? "△" : "v",
  },
  {
    label: "VR",
    current: auth.user?.pc_specs?.vr || "없음",
    message: "필수 아님",
    status: "empty",
    icon: "x",
  },
  {
    label: "콘솔",
    current: auth.user?.pc_specs?.console || "없음",
    message: "PC 플레이 가능",
    status: "empty",
    icon: "x",
  },
]);
const storageSpec = computed(() => ({
  current: auth.user?.pc_specs?.storage || "C: 200GB / 2TB",
  message: "설치 가능",
  status: "pass",
  icon: "v",
}));
const compatibilitySummary = computed(() =>
  specChecks.value.some((item) => item.status === "fail")
    ? "일부 핵심 부품 업그레이드가 필요해요."
    : "현재 장비로 플레이 가능해 보여요.",
);
const storageUsage = 72;
const upgrades = computed(() => [
  { id: 2, type: "GPU", name: "RTX 4070 SUPER", reason: "QHD 옵션 여유 확보" },
  { id: 1, type: "CPU", name: "Ryzen 7 7800X3D", reason: "전략/시뮬레이션 프레임 안정" },
  { id: 3, type: "VR", name: "Meta Quest 3", reason: "VR 지원 게임 대비" },
]);
const reviews = computed(() => [
  ...localReviews.value,
  {
    id: 1,
    username: "strategy_admin",
    avatar: "S",
    recommend: true,
    title: game.value.reviews || "최근 평가 매우 긍정적",
    body: "내 PC 기준으로 옵션만 조금 조절하면 충분히 플레이할 수 있어요.",
  },
  {
    id: 2,
    username: "sale_watcher",
    avatar: "W",
    recommend: false,
    title: "할인 타이밍은 조금 애매",
    body: "관심 등록해두면 다음 세일 때 비교하기 좋을 것 같아요.",
  },
  {
    id: 3,
    username: "coop_player",
    avatar: "C",
    recommend: true,
    title: "취향이 맞으면 추천",
    body: "협동이나 전략 태그가 맞는 유저에게 특히 잘 맞습니다.",
  },
]);

onMounted(async () => {
  const { data } = await api.get(`/catalog/games/${route.params.id}/`);
  game.value = data;
});

function handleOwnedClick() {
  if (isOwned.value) {
    removeOwned();
    return;
  }
  openPlatformPicker();
}

function openPlatformPicker() {
  showPlatformPicker.value = true;
  actionMessage.value = "";
}

async function confirmOwnedAdd() {
  await patchGameList("owned_games", selectedPlatform.value);
  showPlatformPicker.value = false;
}

async function handleInterestedClick() {
  if (isInterested.value) {
    await removeInterested();
    return;
  }
  await patchGameList("interested_games");
}

async function patchGameList(key, platform = null) {
  const title = game.value.title;
  if (!title) return;

  const current = auth.user?.[key] || [];
  const nextProfile = {
    ...auth.user,
    [key]: current.includes(title) ? current : [...current, title],
  };

  if (platform) {
    nextProfile.game_platforms = {
      ...(auth.user?.game_platforms || {}),
      [title]: platform,
    };
  }

  if (key === "interested_games") {
    nextProfile.interest_alerts = {
      ...(auth.user?.interest_alerts || {}),
      [title]: true,
    };
  }

  await auth.updateProfile(nextProfile);
  actionMessage.value = key === "owned_games" ? `${title}을(를) 내 게임에 추가했어요.` : `${title}을(를) 관심게임에 등록했어요.`;
}

async function removeOwned() {
  const title = game.value.title;
  if (!title) return;
  const nextPlatforms = { ...(auth.user?.game_platforms || {}) };
  delete nextPlatforms[title];
  await auth.updateProfile({
    ...auth.user,
    owned_games: (auth.user?.owned_games || []).filter((item) => item !== title),
    game_platforms: nextPlatforms,
  });
  actionMessage.value = `${title}을(를) 내 게임에서 제거했어요.`;
}

async function removeInterested() {
  const title = game.value.title;
  if (!title) return;
  const nextAlerts = { ...(auth.user?.interest_alerts || {}) };
  delete nextAlerts[title];
  await auth.updateProfile({
    ...auth.user,
    interested_games: (auth.user?.interested_games || []).filter((item) => item !== title),
    interest_alerts: nextAlerts,
  });
  actionMessage.value = `${title}을(를) 관심게임에서 삭제했어요.`;
}

async function toggleInterestAlert() {
  const title = game.value.title;
  if (!title) return;
  const nextValue = !isAlertEnabled.value;
  await auth.updateProfile({
    ...auth.user,
    interest_alerts: {
      ...(auth.user?.interest_alerts || {}),
      [title]: nextValue,
    },
  });
  actionMessage.value = nextValue ? `${title} 할인 알림을 켰어요.` : `${title} 할인 알림을 껐어요.`;
}

function submitReview() {
  const body = reviewForm.body.trim();
  if (!body) return;

  localReviews.value.unshift({
    id: Date.now(),
    username: auth.user?.nickname || auth.user?.username || "me",
    avatar: (auth.user?.nickname || auth.user?.username || "M").slice(0, 1).toUpperCase(),
    recommend: reviewForm.recommend,
    title: reviewForm.recommend ? "내 추천 의견" : "내 비추천 의견",
    body,
  });
  reviewForm.body = "";
  reviewForm.recommend = true;
}

function createGameArtwork(title, keywords, colors) {
  const [start, middle, end] = colors;
  const subtitle = keywords.slice(0, 3).join(" · ");
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="${start}" />
          <stop offset="58%" stop-color="${middle}" />
          <stop offset="100%" stop-color="${end}" />
        </linearGradient>
        <radialGradient id="glow" cx="76%" cy="24%" r="58%">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.36" />
          <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
        </radialGradient>
      </defs>
      <rect width="1200" height="420" fill="url(#bg)" />
      <rect width="1200" height="420" fill="url(#glow)" />
      <circle cx="930" cy="92" r="150" fill="#ffffff" opacity="0.12" />
      <circle cx="1014" cy="266" r="104" fill="#000000" opacity="0.16" />
      <path d="M0 330 C190 278 290 390 470 326 C650 262 752 288 920 240 C1058 201 1128 235 1200 202 L1200 420 L0 420Z" fill="#000000" opacity="0.24" />
      <text x="72" y="174" fill="#ffffff" font-family="Arial, sans-serif" font-size="54" font-weight="800">${escapeSvg(title)}</text>
      <text x="76" y="226" fill="#eaf6ff" font-family="Arial, sans-serif" font-size="24" font-weight="700">${escapeSvg(subtitle)}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function escapeSvg(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
</script>
