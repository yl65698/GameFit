<template>
  <section class="game-detail-page">
    <RouterLink class="detail-back" to="/games">← 목록으로 돌아가기</RouterLink>

    <div class="game-detail-shell">
      <main class="game-detail-main">
        <section class="game-hero-image" :style="{ backgroundImage: `linear-gradient(120deg, rgba(12, 18, 28, 0.2), rgba(12, 18, 28, 0.72)), url(${gameImage})` }">
          <RouterLink class="hero-community-btn" :to="`/games/${game.id}/community`">커뮤니티 →</RouterLink>
        </section>

        <section class="game-title-row">
          <div>
            <h1>{{ game.title || "게임이름" }}</h1>
            <p>{{ game.summary || "간단한 게임 설명" }}</p>
            <div class="genre-tag-row">
              <span v-for="g in gameGenres" :key="g.key" class="genre-tag">{{ g.name }}</span>
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
            <span>최근 기록</span>
          </div>
          <div v-if="!chartHistory.length" class="empty-state" style="padding: 20px 0;">
            <p>가격 변동 데이터가 없습니다.</p>
          </div>
          <template v-else>
            <svg class="line-chart" viewBox="0 0 660 180" role="img" aria-label="가격 변동 선 그래프">
              <text
                v-for="tick in yAxisLabels"
                :key="tick.y"
                :x="62"
                :y="tick.y + 4"
                class="chart-y-label"
                text-anchor="end"
              >{{ tick.label }}</text>
              <line
                v-for="tick in yAxisLabels"
                :key="'grid-' + tick.y"
                class="line-chart-grid"
                :x1="68"
                :y1="tick.y"
                :x2="648"
                :y2="tick.y"
              />
              <polyline
                class="line-chart-line"
                :points="priceChartPoints"
                :style="chartHistory.length >= 20 ? { strokeWidth: '2.5' } : {}"
              />
              <template v-if="chartHistory.length < 20">
                <circle v-for="point in priceHistoryPoints" :key="point.label" class="line-chart-dot" :cx="point.x" :cy="point.y" r="5" />
              </template>
            </svg>
            <div class="chart-labels">
              <span>{{ chartEdgeLabels[0] }}</span>
              <span>{{ chartEdgeLabels[1] }}</span>
            </div>
          </template>
        </section>

        <div class="detail-info-grid-2col">
          <section class="detail-panel">
            <h2>구매 추천 시점</h2>
            <strong class="buy-timing">{{ timingHeadline }}</strong>
            <p>{{ timingMessage }}</p>
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

        <section class="detail-panel live-prices-panel">
          <div class="panel-heading compact">
            <h2>실시간 가격 비교</h2>
            <span v-if="game.original_price" class="lp-original-price">
              정가 {{ game.original_price.toLocaleString('ko-KR') }}원
            </span>
          </div>

          <div v-if="livePricesLoading" class="loading-state" style="padding:16px 0">불러오는 중...</div>

          <template v-else-if="filteredDeals.length">
            <div class="live-price-list">
              <div
                v-for="deal in filteredDeals"
                :key="deal.shop + deal.price"
                class="live-price-row"
                :class="{ 'is-deal': deal.cut > 0, 'is-history-low': deal.is_history_low }"
              >
                <span class="lp-shop">{{ deal.shop }}</span>
                <div class="lp-price-group">
                  <span class="lp-cut" v-if="deal.cut > 0">-{{ deal.cut }}%</span>
                  <strong class="lp-price">{{ deal.price.toLocaleString('ko-KR') }}원</strong>
                </div>
                <a class="lp-goto" :href="deal.url" target="_blank" rel="noreferrer">샵으로 이동</a>
              </div>
            </div>
          </template>

          <div v-else-if="livePricesLoaded" class="empty-state" style="padding:16px 0">
            <p>현재 판매 중인 샵 정보가 없습니다.</p>
          </div>
        </section>

        <section class="review-section">
          <div class="review-heading">
            <h2>게임 의견 및 평가</h2>
            <RouterLink class="secondary-button" :to="`/games/${game.id}/community`">게임 커뮤니티</RouterLink>
          </div>

          <div v-if="reviews.length === 0" class="empty-state" style="padding: 20px 0;">
            <p>아직 작성된 리뷰가 없습니다. 첫 번째 리뷰를 남겨보세요.</p>
          </div>
          <article v-for="review in reviews" :key="review.id" class="review-card">
            <span class="review-avatar">{{ review.avatar }}</span>
            <div>
              <div class="review-meta">
                <span>{{ review.username }}</span>
                <span :class="['review-vote', review.recommend ? 'good' : 'bad']">
                  {{ review.recommend ? "추천" : "비추천" }}
                </span>
              </div>
              <p>{{ review.body }}</p>
            </div>
          </article>

          <div v-if="reviewTotalPages > 1" class="pagination" style="margin-top: 12px;">
            <button class="page-btn" :disabled="reviewPage === 1" @click="loadReviews(reviewPage - 1)">‹</button>
            <button
              v-for="p in reviewTotalPages"
              :key="p"
              class="page-btn"
              :class="{ active: p === reviewPage }"
              @click="loadReviews(p)"
            >{{ p }}</button>
            <button class="page-btn" :disabled="reviewPage === reviewTotalPages" @click="loadReviews(reviewPage + 1)">›</button>
          </div>

          <form v-if="auth.isAuthenticated" class="review-form" style="margin-top: 24px;" @submit.prevent="submitReview">
            <div class="recommend-toggle">
              <button type="button" :class="{ active: reviewForm.recommend === true }" @click="reviewForm.recommend = true">추천</button>
              <button type="button" :class="{ active: reviewForm.recommend === false }" @click="reviewForm.recommend = false">비추천</button>
            </div>
            <div class="review-form-right">
              <textarea v-model="reviewForm.body" placeholder="이 게임에 대한 의견을 남겨주세요." />
              <div class="review-form-footer">
                <p v-if="reviewError" class="error-text" style="margin:0;">{{ reviewError }}</p>
                <button class="primary-button">{{ myReview ? "의견 수정하기" : "의견 남기기" }}</button>
              </div>
            </div>
          </form>
          <p v-else class="empty-state" style="margin-top: 20px; text-align: center;">로그인 후 의견을 남길 수 있습니다.</p>
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

        <div class="compat-actions">
          <RouterLink class="primary-button" to="/equipment">필요한 장비 구매하기</RouterLink>
          <RouterLink class="secondary-button" to="/profile/edit?tab=pc">내 장비 업데이트</RouterLink>
        </div>

        <section v-if="upgrades.length" class="upgrade-section">
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
const selectedPlatform = ref("steam");
const reviewForm = reactive({ recommend: true, body: "" });
const reviews = ref([]);
const reviewError = ref("");
const reviewPage = ref(1);
const reviewTotalPages = ref(1);
const myReview = ref(null);
const upgrades = ref([]);

const platforms = [
  { label: "Steam", value: "steam" },
  { label: "Epic Games", value: "epic" },
  { label: "Ubisoft", value: "ubisoft" },
  { label: "그 외", value: "other" },
];

// ── 보유/관심 상태 (API 응답 기준) ──
const isOwned = computed(() => game.value.is_owned ?? false);
const isInterested = computed(() => game.value.is_interested ?? false);
const isAlertEnabled = computed(() => {
  if (!game.value.title) return false;
  return (auth.user?.interest_alerts || {})[game.value.title] ?? true;
});

// ── 장르 태그 (GameGenre 기반) ──
const gameGenres = computed(() => game.value.genres || []);

// ── 이미지 (장르명을 SVG 서브타이틀로 활용) ──
const gameImage = computed(() => {
  const genreNames = gameGenres.value.slice(0, 3).map((g) => g.name);
  return (
    game.value.image_url ||
    createGameArtwork(game.value.title || "GameFit", genreNames, ["#14213d", "#17637d", "#8ad0c2"])
  );
});

// ── 사양 정보 ──
const requirements = computed(() => {
  const g = game.value;
  const minParts = [g.min_cpu, g.min_gpu, g.min_ram].filter(Boolean);
  const recParts = [g.rec_cpu, g.rec_gpu, g.rec_ram].filter(Boolean);
  return {
    minimum: minParts.length ? minParts.join(" / ") : "정보 없음",
    recommended: recParts.length ? recParts.join(" / ") : "정보 없음",
  };
});

// ── 게임 정보 ──
const gameInfo = computed(() => [
  { label: "제조사", value: game.value.publisher || "—" },
  { label: "개발사", value: game.value.developer || "—" },
  { label: "출시일", value: game.value.release_date || "—" },
  { label: "권장연령", value: game.value.age_rating || "—" },
]);

const infoUrl = computed(() =>
  `https://store.steampowered.com/search/?term=${encodeURIComponent(game.value.title || "")}`
);

// ── 가격 그래프: 백엔드 price_history + 현재 딜 최저가를 마지막 포인트로 주입 ──
const chartHistory = computed(() => {
  const history = [...(game.value.price_history || [])];
  if (livePricesLoaded.value && livePrices.value.deals?.length) {
    const bestDeal = livePrices.value.deals[0]; // 가격 오름차순 정렬된 첫 번째 = 최저가
    const todayIso = new Date().toISOString();
    if (history.length > 0) {
      const last = { ...history[history.length - 1] };
      last.price = bestDeal.price;
      last.shop_name = bestDeal.shop;
      last.recorded_at = todayIso;
      history[history.length - 1] = last;
    } else {
      history.push({ price: bestDeal.price, shop_name: bestDeal.shop, recorded_at: todayIso });
    }
  }
  return history;
});

const priceHistoryPoints = computed(() => {
  const entries = chartHistory.value;
  if (!entries.length) return [];
  const values = entries.map((e) => e.price);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const xStep = entries.length === 1 ? 0 : 580 / (entries.length - 1);
  return entries.map((entry, i) => ({
    label: new Date(entry.recorded_at).toLocaleDateString("ko-KR", { year: "numeric", month: "short", day: "numeric" }),
    x: entries.length === 1 ? 358 : 68 + i * xStep,
    y: 150 - (max === min ? 0.5 : (entry.price - min) / (max - min)) * 118,
  }));
});

function formatYTick(price) {
  if (price % 10000 === 0) return `${price / 10000}만`;
  if (price >= 10000) return `${(price / 10000).toFixed(1)}만`;
  return price.toLocaleString();
}

const TICK_COUNT = 5;

const yAxisLabels = computed(() => {
  const entries = chartHistory.value;
  if (!entries.length) return [];
  const values = entries.map((e) => e.price);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);

  if (maxVal === minVal) {
    return [{ label: formatYTick(minVal), y: 91 }];
  }

  return Array.from({ length: TICK_COUNT }, (_, i) => {
    const price = minVal + (i / (TICK_COUNT - 1)) * (maxVal - minVal);
    const y = 150 - (i / (TICK_COUNT - 1)) * 118;
    return { label: formatYTick(Math.round(price)), y };
  });
});

const chartEdgeLabels = computed(() => {
  const pts = priceHistoryPoints.value;
  if (!pts.length) return ["", ""];
  return [pts[0].label, pts[pts.length - 1].label];
});

const priceChartPoints = computed(() =>
  priceHistoryPoints.value.map((p) => `${p.x},${p.y}`).join(" ")
);

// ── 실시간 가격 비교 (ITAD API) ──
const livePrices = ref({ deals: [], history_low_all: null, history_low_1y: null, history_low_3m: null });
const livePricesLoading = ref(false);
const livePricesLoaded = ref(false);

const filteredDeals = computed(() => {
  const deals = livePrices.value.deals || [];
  const basePrice = game.value.original_price || Infinity;
  return deals.filter((d) => d.cut > 0 && d.price < basePrice);
});

async function loadLivePrices(gameId) {
  livePricesLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/${gameId}/live-prices/`);
    livePrices.value = data;
  } catch {
    livePrices.value = { deals: [], history_low_all: null, history_low_1y: null, history_low_3m: null };
  } finally {
    livePricesLoading.value = false;
    livePricesLoaded.value = true;
  }
}

// ── 구매 추천 시점 ──
const timingHeadline = computed(() => {
  const d = game.value.discount || 0;
  if (d >= 50) return "지금 구매 추천";
  if (d >= 25) return "관심 등록 후 한 번 더 확인";
  return "다음 대형 세일까지 대기";
});
const timingMessage = computed(() => {
  const d = game.value.discount || 0;
  if (d >= 50) return "최근 가격 흐름상 할인 폭이 충분히 커서 바로 구매해도 괜찮아요.";
  if (d >= 25) return "현재도 나쁘지 않지만 이전 최저가보다 높아서 관심게임에 넣고 알림을 보는 쪽이 좋아요.";
  return "할인율이 낮아서 여름/연말 세일 때 다시 확인하는 걸 추천해요.";
});

// ── PC 호환성 체크 ──
function parseGB(str) {
  const m = String(str || "").match(/(\d+)/);
  return m ? parseInt(m[1]) : 0;
}

function ramStatus(userRam, minRam, recRam) {
  const userGB = parseGB(userRam);
  const minGB = parseGB(minRam);
  const recGB = parseGB(recRam);
  if (!userGB) return { status: "none", message: "정보 없음" };
  if (!minGB) return { status: "pass", message: "요구사양 없음" };
  if (recGB && userGB >= recGB) return { status: "pass", message: "권장 사양 충족" };
  if (userGB >= minGB) return { status: "pass", message: "최소 사양 충족" };
  return { status: "fail", message: `최소 ${minGB}GB 필요` };
}

function cpuGpuStatus(userVal, minVal) {
  if (!userVal) return { status: "none", message: "정보 없음" };
  if (!minVal) return { status: "pass", message: "요구사양 없음" };
  return { status: "pass", message: `최소: ${minVal}` };
}

function iconFor(status) {
  return status === "pass" ? "v" : status === "fail" ? "✕" : "—";
}

const specChecks = computed(() => {
  const specs = auth.user?.pc_specs || {};
  const g = game.value;
  const ramRes = ramStatus(specs.memory || specs.ram, g.min_ram, g.rec_ram);
  const cpuRes = cpuGpuStatus(specs.cpu, g.min_cpu);
  const gpuRes = cpuGpuStatus(specs.gpu, g.min_gpu);
  return [
    { label: "CPU", current: specs.cpu || "정보 없음", message: cpuRes.message, status: cpuRes.status, icon: iconFor(cpuRes.status) },
    { label: "메모리", current: specs.memory || specs.ram || "정보 없음", message: ramRes.message, status: ramRes.status, icon: iconFor(ramRes.status) },
    { label: "GPU", current: specs.gpu || "정보 없음", message: gpuRes.message, status: gpuRes.status, icon: iconFor(gpuRes.status) },
    { label: "VR", current: specs.vr || "없음", message: "게임 지원 여부 확인", status: "empty", icon: "—" },
    { label: "콘솔", current: specs.console || "없음", message: "PC 플레이 가능", status: "empty", icon: "—" },
  ];
});

const storageSpec = computed(() => {
  const storage = auth.user?.pc_specs?.storage || "";
  return {
    current: storage || "정보 없음",
    message: storage ? "설치 가능 여부 확인" : "장비를 등록해주세요",
    status: storage ? "pass" : "none",
    icon: storage ? "v" : "—",
  };
});

const compatibilitySummary = computed(() => {
  const specs = auth.user?.pc_specs || {};
  if (!specs.cpu && !specs.gpu) return "내 장비 정보를 먼저 등록해주세요.";
  if (specChecks.value.some((s) => s.status === "fail")) return "일부 핵심 부품 업그레이드가 필요해요.";
  return "현재 장비로 플레이 가능해 보여요.";
});

// ── 액션: 내 게임 추가/삭제 (UserGame API 사용) ──
function handleOwnedClick() {
  isOwned.value ? removeUserGame() : openPlatformPicker();
}

function openPlatformPicker() {
  showPlatformPicker.value = true;
  actionMessage.value = "";
}

async function confirmOwnedAdd() {
  try {
    await api.post("/games/add/", { game_id: game.value.id, status: "owned", platform: selectedPlatform.value });
    game.value = { ...game.value, is_owned: true };
    actionMessage.value = `${game.value.title}을(를) 내 게임에 추가했어요.`;
    showPlatformPicker.value = false;
    await auth.fetchProfile();
  } catch {
    actionMessage.value = "추가 중 오류가 발생했습니다.";
  }
}

async function handleInterestedClick() {
  if (isInterested.value) {
    await removeUserGame();
    actionMessage.value = `${game.value.title}을(를) 관심게임에서 삭제했어요.`;
  } else {
    try {
      await api.post("/games/add/", { game_id: game.value.id, status: "interested" });
      game.value = { ...game.value, is_interested: true };
      actionMessage.value = `${game.value.title}을(를) 관심게임에 등록했어요.`;
      await auth.fetchProfile();
    } catch {
      actionMessage.value = "등록 중 오류가 발생했습니다.";
    }
  }
}

async function removeUserGame() {
  try {
    await api.delete(`/games/${game.value.id}/remove/`);
    game.value = { ...game.value, is_owned: false, is_interested: false };
    await auth.fetchProfile();
  } catch {
    actionMessage.value = "삭제 중 오류가 발생했습니다.";
  }
}

async function toggleInterestAlert() {
  const title = game.value.title;
  if (!title) return;
  const nextValue = !isAlertEnabled.value;
  await auth.updateProfile({
    ...auth.user,
    interest_alerts: { ...(auth.user?.interest_alerts || {}), [title]: nextValue },
  });
  actionMessage.value = nextValue ? `${title} 할인 알림을 켰어요.` : `${title} 할인 알림을 껐어요.`;
}

// ── 리뷰: API 연동 ──
async function loadReviews(page = 1) {
  try {
    const { data } = await api.get(`/games/${game.value.id}/reviews/?page=${page}`);
    reviews.value = data.results.map((r) => ({
      id: r.id,
      username: r.username,
      avatar: r.avatar,
      recommend: r.recommend ?? r.rating >= 4,
      body: r.content,
    }));
    reviewPage.value = data.page;
    reviewTotalPages.value = data.total_pages;
  } catch {
    reviews.value = [];
  }
}

async function loadMyReview(gameId) {
  if (!auth.isAuthenticated) return;
  try {
    const { data } = await api.get(`/games/${gameId}/reviews/my/`);
    if (data) {
      myReview.value = data;
      reviewForm.body = data.content;
      reviewForm.recommend = data.recommend;
    }
  } catch {
    myReview.value = null;
  }
}

async function submitReview() {
  const body = reviewForm.body.trim();
  if (!body) return;
  reviewError.value = "";
  try {
    if (myReview.value) {
      await api.put(`/games/${game.value.id}/reviews/update/`, {
        content: body,
        rating: reviewForm.recommend ? 5 : 1,
        recommend: reviewForm.recommend,
      });
    } else {
      await api.post(`/games/${game.value.id}/reviews/create/`, {
        content: body,
        rating: reviewForm.recommend ? 5 : 1,
        recommend: reviewForm.recommend,
      });
    }
    await loadMyReview(game.value.id);
    await loadReviews(reviewPage.value);
  } catch (err) {
    reviewError.value = err.response?.data?.non_field_errors?.[0] || "오류가 발생했습니다.";
  }
}

onMounted(async () => {
  const id = route.params.id;
  const { data } = await api.get(`/catalog/games/${id}/`);
  game.value = data;

  loadLivePrices(id);
  loadReviews(1);
  loadMyReview(id);
});

// ── SVG 아트워크 폴백 ──
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
