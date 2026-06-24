<template>
  <section class="equipment-detail-page">
    <RouterLink class="detail-back" to="/equipment">← 목록으로 돌아가기</RouterLink>

    <div class="equipment-detail-shell" v-if="item.id">
      <main class="equipment-detail-main">

        <!-- 헤로 영역 -->
        <section class="equip-hero" :style="heroStyle">
          <div class="equip-hero-content">
            <span class="equip-hero-category">{{ item.type }}</span>
            <h1>{{ item.name }}</h1>
            <p v-if="item.manufacturer" class="equip-hero-maker">{{ item.manufacturer }}</p>

            <!-- 벤치마크 바 -->
            <div v-if="item.benchmark_score > 0" class="equip-bench-block">
              <span class="equip-bench-label">벤치마크</span>
              <div class="equip-bench-bar">
                <div class="equip-bench-fill" :style="{ width: item.benchmark_score + '%' }"></div>
              </div>
              <span class="equip-bench-score">{{ item.benchmark_score }}점</span>
            </div>

            <!-- 가격 -->
            <div class="equip-hero-price-row">
              <strong class="equip-hero-price">{{ priceLabel }}</strong>
              <span v-if="item.discount_percent > 0" class="equip-hero-discount">
                -{{ item.discount_percent }}%
                <del>{{ Number(item.original_price).toLocaleString("ko-KR") }}원</del>
              </span>
            </div>

            <!-- 액션 버튼 -->
            <div class="equip-hero-actions">
              <button
                :class="isOwned ? 'secondary-button' : 'primary-button'"
                @click="handleOwned"
              >
                {{ isOwned ? "내 장비에서 제거" : "내 장비 추가" }}
              </button>
              <button
                :class="isInterested ? 'secondary-button danger-soft-button' : 'secondary-button'"
                @click="handleInterested"
              >
                {{ isInterested ? "관심 취소" : "관심 장비 등록" }}
              </button>
            </div>
            <p v-if="actionMessage" class="action-message">{{ actionMessage }}</p>
          </div>
        </section>

        <!-- 설명 -->
        <section v-if="item.description || item.specs" class="detail-panel equip-desc-panel">
          <h2>장비 설명</h2>
          <p class="equip-description">{{ item.description || item.specs }}</p>
        </section>

        <!-- 가격 변동 -->
        <section class="detail-panel price-trend-panel">
          <div class="panel-heading compact">
            <h2>가격 변동 추이</h2>
            <span>{{ chartHistory.length > 0 ? "실제 가격 이력" : "데이터 없음" }}</span>
          </div>

          <div v-if="chartHistory.length === 0" class="empty-state" style="padding: 20px 0;">
            <p>가격 변동 데이터가 아직 없습니다.</p>
          </div>
          <template v-else>
            <svg class="line-chart" viewBox="0 0 600 180" role="img">
              <polyline class="line-chart-grid" points="0,36 600,36" />
              <polyline class="line-chart-grid" points="0,90 600,90" />
              <polyline class="line-chart-grid" points="0,144 600,144" />
              <polyline class="line-chart-line equipment-line" :points="priceChartPoints" />
              <circle
                v-for="pt in priceHistoryPoints"
                :key="pt.label"
                class="line-chart-dot equipment-dot"
                :cx="pt.x"
                :cy="pt.y"
                r="5"
              />
            </svg>
            <div class="chart-labels">
              <span v-for="pt in priceHistoryPoints" :key="pt.label">{{ pt.label }}</span>
            </div>
          </template>
        </section>

        <!-- 정보 그리드 -->
        <div class="detail-info-grid">

          <!-- 가격 비교 -->
          <section class="detail-panel">
            <h2>가격 비교</h2>
            <div class="price-market-list">
              <article v-for="market in priceMarkets" :key="market.store">
                <strong>{{ market.store }}</strong>
                <span>{{ Number(market.price).toLocaleString("ko-KR") }}원</span>
                <em v-if="market.discount > 0">-{{ market.discount }}%</em>
                <a
                  class="price-link-button"
                  :href="`https://search.naver.com/search.naver?where=nexearch&query=${encodeURIComponent(item.name)}`"
                  target="_blank"
                  rel="noreferrer"
                >이동</a>
              </article>
              <p v-if="priceMarkets.length === 0" class="subtle">쇼핑몰 가격 정보가 없습니다.</p>
            </div>
          </section>

          <!-- 구매 타이밍 -->
          <section class="detail-panel">
            <h2>구매 추천 시점</h2>
            <strong class="buy-timing">{{ timingHeadline }}</strong>
            <p>{{ timingMessage }}</p>
          </section>

          <!-- 보유 게임 적합성 -->
          <section class="detail-panel equipment-fit-panel">
            <h2>보유 게임 사양 적합도</h2>
            <div v-if="ownedGameMatches.length === 0" class="subtle" style="padding: 8px 0;">
              보유 게임이 없거나 사양 데이터가 없습니다.
            </div>
            <article v-for="g in ownedGameMatches" :key="g.title">
              <strong>{{ g.title }}</strong>
              <span>{{ g.reason }}</span>
            </article>
          </section>

          <!-- 관심 게임 적합성 -->
          <section class="detail-panel equipment-fit-panel">
            <h2>관심 게임 사양 적합도</h2>
            <div v-if="interestedGameMatches.length === 0" class="subtle" style="padding: 8px 0;">
              관심 게임이 없거나 사양 데이터가 없습니다.
            </div>
            <article v-for="g in interestedGameMatches" :key="g.title">
              <strong>{{ g.title }}</strong>
              <span>{{ g.reason }}</span>
            </article>
          </section>
        </div>
      </main>

      <!-- 사이드바: 내 PC와 비교 -->
      <aside class="equipment-compare-sidebar">
        <h2>내 장비랑 비교하면?</h2>

        <dl class="compat-spec-list equipment-current-specs">
          <div
            v-for="spec in currentSpecs"
            :key="spec.label"
            :class="{ highlighted: spec.highlighted }"
          >
            <dt>{{ spec.label }}</dt>
            <dd>
              <strong>{{ spec.value }}</strong>
              <small>{{ spec.note }}</small>
            </dd>
          </div>
        </dl>

        <!-- 성능 비교 카드 (CPU/GPU만) -->
        <section v-if="benchComparison" class="equipment-judgement-card">
          <h3>성능 차이</h3>
          <p>{{ benchComparison.message }}</p>
          <div class="bench-comparison-row">
            <div class="bench-compare-item">
              <span class="bench-compare-label">현재</span>
              <div class="equip-bench-bar">
                <div class="equip-bench-fill" :style="{ width: benchComparison.currentScore + '%', background: '#4b5563' }"></div>
              </div>
              <span class="bench-score">{{ benchComparison.currentName }}</span>
            </div>
            <div class="bench-compare-item">
              <span class="bench-compare-label">이 장비</span>
              <div class="equip-bench-bar">
                <div class="equip-bench-fill" :style="{ width: item.benchmark_score + '%' }"></div>
              </div>
              <span class="bench-score">{{ item.benchmark_score }}점</span>
            </div>
          </div>
          <strong :class="['recommend-badge', benchComparison.recommend ? 'recommend-good' : 'recommend-neutral']">
            {{ benchComparison.verdict }}
          </strong>
        </section>

        <section v-else class="equipment-judgement-card">
          <h3>업그레이드 판단</h3>
          <p>{{ genericAdvice }}</p>
        </section>

        <div class="compat-actions" style="margin-top: 16px;">
          <RouterLink class="secondary-button" to="/profile/edit?tab=pc">내 장비 업데이트</RouterLink>
        </div>
      </aside>
    </div>

    <!-- 로딩 -->
    <div v-else class="loading-state">
      <p>장비 정보를 불러오는 중...</p>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import api from "../../services/api";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const auth = useAuthStore();
const item = ref({});
const actionMessage = ref("");
const userGames = ref([]);

// ── 보유/관심 상태 (API 기반) ──
const isOwned = computed(() => item.value.is_owned ?? false);
const isInterested = computed(() => item.value.is_interested ?? false);

// ── 히어로 이미지 ──
const CATEGORY_COLORS = {
  cpu: "linear-gradient(135deg,#182a4d 0%,#1e3a8a 60%,#3b82f6 100%)",
  gpu: "linear-gradient(135deg,#14213d 0%,#166534 60%,#4ade80 100%)",
  ram: "linear-gradient(135deg,#1e1b4b 0%,#5b21b6 60%,#a78bfa 100%)",
  storage: "linear-gradient(135deg,#1c1917 0%,#44403c 60%,#a8a29e 100%)",
  monitor: "linear-gradient(135deg,#0f172a 0%,#0369a1 60%,#38bdf8 100%)",
  mouse: "linear-gradient(135deg,#1a1a2e 0%,#b91c1c 60%,#fca5a5 100%)",
  keyboard: "linear-gradient(135deg,#0d1117 0%,#15803d 60%,#86efac 100%)",
  headset: "linear-gradient(135deg,#1e293b 0%,#b45309 60%,#fde68a 100%)",
  vr: "linear-gradient(135deg,#33165f 0%,#7c3aed 60%,#c4b5fd 100%)",
  power: "linear-gradient(135deg,#1c1c1c 0%,#9f1239 60%,#fda4af 100%)",
  default: "linear-gradient(135deg,#263238 0%,#17637d 60%,#8ad0c2 100%)",
};

const heroStyle = computed(() => {
  if (item.value.image_url) {
    return {
      backgroundImage: `linear-gradient(120deg, rgba(12,18,28,0.55) 0%, rgba(12,18,28,0.25) 100%), url(${item.value.image_url})`,
      backgroundSize: "cover",
      backgroundPosition: "center",
    };
  }
  return { background: CATEGORY_COLORS[item.value.category] || CATEGORY_COLORS.default };
});

// ── 가격 표시 ──
const priceLabel = computed(() =>
  item.value.price ? `${Number(item.value.price).toLocaleString("ko-KR")}원` : "가격 정보 없음"
);

// ── 가격 변동 (실제 price_history) ──
const chartHistory = computed(() => {
  const hist = item.value.price_history || [];
  if (!hist.length) return [];
  const byShop = {};
  for (const h of [...hist].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))) {
    if (!byShop[h.shop_name]) byShop[h.shop_name] = [];
    byShop[h.shop_name].push(h);
  }
  const mainShop = Object.values(byShop).sort((a, b) => b.length - a.length)[0] || [];
  return mainShop.slice(-8);
});

const priceHistoryPoints = computed(() => {
  const entries = chartHistory.value;
  if (!entries.length) return [];
  const values = entries.map((e) => e.price);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const xStep = entries.length === 1 ? 0 : 532 / (entries.length - 1);
  return entries.map((e, i) => ({
    label: new Date(e.recorded_at).toLocaleDateString("ko-KR", { month: "short", day: "numeric" }),
    x: entries.length === 1 ? 300 : 34 + i * xStep,
    y: 150 - (max === min ? 0.5 : (e.price - min) / (max - min)) * 118,
  }));
});

const priceChartPoints = computed(() =>
  priceHistoryPoints.value.map((p) => `${p.x},${p.y}`).join(" ")
);

// ── 가격 비교 (price_history shop별 최신값) ──
const priceMarkets = computed(() => {
  const hist = item.value.price_history || [];
  const latestByShop = {};
  for (const h of [...hist].sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))) {
    if (!latestByShop[h.shop_name]) latestByShop[h.shop_name] = h;
  }
  return Object.values(latestByShop)
    .map((h) => ({ store: h.shop_name, price: h.price, discount: h.discount }))
    .sort((a, b) => a.price - b.price)
    .slice(0, 5);
});

// ── 구매 타이밍 ──
const timingHeadline = computed(() => {
  const d = item.value.discount_percent || 0;
  const p = item.value.price || 0;
  if (d >= 20) return "할인 중, 지금이 적기";
  if (p > 700000) return "할인 알림 후 구매 추천";
  return "가격 안정권, 필요하면 구매";
});
const timingMessage = computed(() => {
  const d = item.value.discount_percent || 0;
  const p = item.value.price || 0;
  if (d >= 20) return `현재 ${d}% 할인 중으로 구매 적기입니다.`;
  if (p > 700000) return "고가 장비는 카드/행사 할인 시점을 기다리는 편이 좋습니다.";
  return "최근 가격 변동이 크지 않아 필요성이 명확하다면 지금 구매해도 무난합니다.";
});

// ── 게임 적합성 ──
function gameReason(game, cat) {
  const reasons = {
    gpu: `${game.title} 그래픽 옵션 여유 확보`,
    cpu: `${game.title} 시뮬레이션/AI 처리 안정화`,
    ram: `${game.title} 멀티태스킹 & 로딩 개선`,
    storage: `${game.title} 빠른 로딩 및 설치 공간`,
    vr: `${game.title} VR 지원 시 체험 가능`,
    monitor: `${game.title} 화질 및 응답속도 향상`,
    default: `${game.title} 전반적인 플레이 환경 개선`,
  };
  return reasons[cat] || reasons.default;
}

const ownedGameMatches = computed(() => {
  const cat = item.value.category || "default";
  return userGames.value
    .filter((g) => g.status === "owned")
    .slice(0, 3)
    .map((g) => ({ title: g.game?.title || g.title, reason: gameReason(g.game || g, cat) }));
});

const interestedGameMatches = computed(() => {
  const cat = item.value.category || "default";
  return userGames.value
    .filter((g) => g.status === "interested")
    .slice(0, 3)
    .map((g) => ({ title: g.game?.title || g.title, reason: gameReason(g.game || g, cat) }));
});

// ── 사이드바: 현재 PC 사양 ──
const currentSpecs = computed(() => {
  const specs = auth.user?.pc_specs || {};
  const cat = item.value.category;
  return [
    { label: "CPU", value: specs.cpu || "정보 없음", note: cat === "cpu" ? "비교 대상" : "현재 장비", highlighted: cat === "cpu" },
    { label: "메모리", value: specs.memory || specs.ram || "정보 없음", note: cat === "ram" ? "비교 대상" : "현재 장비", highlighted: cat === "ram" },
    { label: "GPU", value: specs.gpu || "정보 없음", note: cat === "gpu" ? "업그레이드 후보" : "현재 장비", highlighted: cat === "gpu" },
    { label: "저장장치", value: specs.storage || "정보 없음", note: cat === "storage" ? "비교 대상" : "현재 장비", highlighted: cat === "storage" },
    { label: "VR", value: specs.vr || "없음", note: cat === "vr" ? "내 장비 후보" : "현재 장비", highlighted: cat === "vr" },
  ];
});

// ── 벤치마크 비교 (CPU/GPU만) ──
const benchComparison = computed(() => {
  const cat = item.value.category;
  if (!["cpu", "gpu"].includes(cat)) return null;
  const specs = auth.user?.pc_specs || {};
  const currentName = cat === "cpu" ? specs.cpu : specs.gpu;
  if (!currentName) return null;
  const thisBench = item.value.benchmark_score || 0;
  if (!thisBench) return null;
  const diff = thisBench;
  return {
    currentName,
    currentScore: Math.max(10, thisBench - 20),
    message:
      cat === "gpu"
        ? "현재 GPU와 성능 차이입니다. 수치가 클수록 업그레이드 체감이 큽니다."
        : "현재 CPU와 성능 차이입니다. 전략·시뮬레이션 게임에서 차이가 납니다.",
    recommend: diff > 10,
    verdict: diff > 20 ? "업그레이드 강력 추천" : diff > 10 ? "업그레이드 추천" : "현재 장비도 충분",
  };
});

const genericAdvice = computed(() => {
  const cat = item.value.category;
  const map = {
    ram: "메모리 용량이 부족하거나 게임 렉이 잦다면 업그레이드를 고려해보세요.",
    storage: "NVMe SSD 교체로 게임 로딩 시간을 크게 줄일 수 있습니다.",
    monitor: "주사율과 해상도 향상으로 게임 몰입감이 크게 올라갑니다.",
    mouse: "경량 마우스로 FPS 게임 조준 정확도를 높일 수 있습니다.",
    keyboard: "기계식 키보드는 입력 반응속도와 내구성이 뛰어납니다.",
    headset: "공간감 있는 사운드로 게임 몰입감과 팀 커뮤니케이션이 향상됩니다.",
    power: "안정적인 파워 서플라이는 고사양 빌드의 필수 요소입니다.",
  };
  return map[cat] || "현재 플레이 스타일에 맞춰 선택할 만한 장비입니다.";
});

// ── 액션: 내 장비 추가/제거 ──
async function handleOwned() {
  if (!auth.isAuthenticated) {
    actionMessage.value = "로그인이 필요합니다.";
    return;
  }
  try {
    if (isOwned.value) {
      await api.delete(`/hardware/${item.value.id}/remove/`);
      item.value = { ...item.value, is_owned: false, is_interested: false };
      actionMessage.value = `${item.value.name}을(를) 내 장비에서 제거했습니다.`;
    } else {
      await api.post("/hardware/add/", { hardware_id: item.value.id, status: "owned" });
      item.value = { ...item.value, is_owned: true };
      actionMessage.value = `${item.value.name}을(를) 내 장비에 추가했습니다.`;
    }
    await auth.fetchProfile();
  } catch {
    actionMessage.value = "처리 중 오류가 발생했습니다.";
  }
}

async function handleInterested() {
  if (!auth.isAuthenticated) {
    actionMessage.value = "로그인이 필요합니다.";
    return;
  }
  try {
    if (isInterested.value) {
      await api.delete(`/hardware/${item.value.id}/remove/`);
      item.value = { ...item.value, is_owned: false, is_interested: false };
      actionMessage.value = `${item.value.name}을(를) 관심 장비에서 제거했습니다.`;
    } else {
      await api.post("/hardware/add/", { hardware_id: item.value.id, status: "interested" });
      item.value = { ...item.value, is_interested: true };
      actionMessage.value = `${item.value.name}을(를) 관심 장비에 등록했습니다.`;
    }
  } catch {
    actionMessage.value = "처리 중 오류가 발생했습니다.";
  }
}

onMounted(async () => {
  const { data } = await api.get(`/catalog/equipment/${route.params.id}/`);
  item.value = data;

  if (auth.isAuthenticated) {
    try {
      const { data: gamesData } = await api.get("/games/my/");
      userGames.value = Array.isArray(gamesData) ? gamesData : gamesData.results || [];
    } catch {
      userGames.value = [];
    }
  }
});
</script>
