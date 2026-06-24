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

            <div v-if="item.benchmark_score > 0" class="equip-bench-block">
              <span class="equip-bench-label">벤치마크</span>
              <div class="equip-bench-bar">
                <div class="equip-bench-fill" :style="{ width: item.benchmark_score + '%' }"></div>
              </div>
              <span class="equip-bench-score">{{ item.benchmark_score }}점</span>
            </div>

            <div class="equip-hero-price-row">
              <strong class="equip-hero-price">{{ priceLabel }}</strong>
              <span v-if="item.discount_percent > 0" class="equip-hero-discount">
                -{{ item.discount_percent }}%
                <del>{{ Number(item.original_price).toLocaleString("ko-KR") }}원</del>
              </span>
            </div>

            <div class="equip-hero-actions">
              <button :class="isOwned ? 'secondary-button' : 'primary-button'" @click="handleOwned">
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

        <!-- 가격 비교 -->
        <section class="detail-panel equip-price-panel">
          <h2>가격 비교</h2>

          <div v-if="priceStats" class="price-stats-bar">
            <div class="price-stat-item">
              <span>현재가</span>
              <strong>{{ Number(item.price).toLocaleString("ko-KR") }}원</strong>
            </div>
            <div class="price-stat-item">
              <span>최저가</span>
              <strong class="price-low">{{ Number(priceStats.min).toLocaleString("ko-KR") }}원</strong>
            </div>
            <div class="price-stat-item">
              <span>최고가</span>
              <strong class="price-high">{{ Number(priceStats.max).toLocaleString("ko-KR") }}원</strong>
            </div>
            <span :class="['price-trend-badge', `trend-${priceStats.trend}`]">
              {{ { up: "↑ 상승 중", down: "↓ 하락 중", stable: "→ 안정세" }[priceStats.trend] }}
            </span>
          </div>

          <div class="price-market-list">
            <article v-for="market in priceMarkets" :key="market.store">
              <strong>{{ market.store }}</strong>
              <span>{{ Number(market.price).toLocaleString("ko-KR") }}원</span>
              <em v-if="market.discount > 0">-{{ market.discount }}%</em>
            </article>
            <p v-if="priceMarkets.length === 0" class="subtle">등록된 쇼핑몰 가격 정보가 없습니다.</p>
          </div>

          <div class="price-search-links">
            <a
              :href="`https://search.shopping.naver.com/search/all?query=${encodeURIComponent(item.name)}`"
              target="_blank" rel="noreferrer" class="price-link-button"
            >네이버 쇼핑</a>
            <a
              :href="`https://search.danawa.com/dsearch.php?query=${encodeURIComponent(item.name)}`"
              target="_blank" rel="noreferrer" class="price-link-button"
            >다나와</a>
          </div>
        </section>

        <!-- 게임 적합도 그리드 -->
        <div class="fit-panels-grid">

          <!-- 보유 게임 적합도 -->
          <section class="detail-panel equipment-fit-panel">
            <h2>보유 게임 사양 적합도</h2>

            <div v-if="suitabilityLoading" class="fit-loading">
              <div class="timing-spinner"></div>
              <span>AI 분석 중...</span>
            </div>
            <template v-else-if="suitability.owned.length > 0">
              <article v-for="g in suitability.owned" :key="g.title" class="game-fit-card">
                <div class="game-fit-header">
                  <strong>{{ g.title }}</strong>
                  <span :class="['fit-badge', `fit-${g.status}`]">{{ fitLabel(g.status) }}</span>
                </div>
                <p class="game-fit-detail">{{ g.detail }}</p>
              </article>
            </template>
            <p v-else class="subtle" style="padding: 8px 0;">
              {{ auth.isAuthenticated ? "보유 게임이 없거나 사양 정보가 없습니다." : "로그인 후 이용 가능합니다." }}
            </p>
          </section>

          <!-- 관심 게임 적합도 -->
          <section class="detail-panel equipment-fit-panel">
            <h2>관심 게임 사양 적합도</h2>

            <div v-if="suitabilityLoading" class="fit-loading">
              <div class="timing-spinner"></div>
              <span>AI 분석 중...</span>
            </div>
            <template v-else-if="suitability.interested.length > 0">
              <article v-for="g in suitability.interested" :key="g.title" class="game-fit-card">
                <div class="game-fit-header">
                  <strong>{{ g.title }}</strong>
                  <span :class="['fit-badge', `fit-${g.status}`]">{{ fitLabel(g.status) }}</span>
                </div>
                <p class="game-fit-detail">{{ g.detail }}</p>
              </article>
            </template>
            <p v-else class="subtle" style="padding: 8px 0;">
              {{ auth.isAuthenticated ? "관심 게임이 없거나 사양 정보가 없습니다." : "로그인 후 이용 가능합니다." }}
            </p>
          </section>

        </div>
      </main>

      <!-- 사이드바: 내 장비랑 비교 -->
      <aside class="equipment-compare-sidebar">
        <h2>내 장비랑 비교하면?</h2>

        <dl class="compat-spec-list equipment-current-specs">
          <div v-for="spec in currentSpecs" :key="spec.label" :class="{ highlighted: spec.highlighted }">
            <dt>{{ spec.label }}</dt>
            <dd>
              <strong>{{ spec.value }}</strong>
              <small>{{ spec.note }}</small>
            </dd>
          </div>
        </dl>

        <!-- AI 업그레이드 분석 카드 -->
        <section class="equipment-judgement-card">
          <h3>업그레이드 분석</h3>

          <div v-if="pcCompareLoading" class="fit-loading">
            <div class="timing-spinner"></div>
            <span>AI 분석 중...</span>
          </div>

          <template v-else-if="pcCompare">
            <div class="compare-current-new">
              <div class="compare-spec-box">
                <span class="compare-label">현재</span>
                <strong>{{ pcCompare.current_spec }}</strong>
              </div>
              <span class="compare-arrow">→</span>
              <div class="compare-spec-box compare-spec-new">
                <span class="compare-label">신규</span>
                <strong>{{ item.name }}</strong>
              </div>
            </div>
            <p class="compare-diff-summary">{{ pcCompare.diff_summary }}</p>
            <ul v-if="pcCompare.points && pcCompare.points.length" class="compare-points">
              <li v-for="pt in pcCompare.points" :key="pt">{{ pt }}</li>
            </ul>
            <span :class="['upgrade-verdict-badge', `upgrade-${pcCompare.upgrade_value}`]">
              {{ pcCompare.verdict }}
            </span>
          </template>

          <p v-else-if="!auth.isAuthenticated" class="subtle">로그인 후 이용 가능합니다.</p>
          <p v-else class="subtle">{{ genericAdvice }}</p>
        </section>

        <div class="compat-actions" style="margin-top: 16px;">
          <RouterLink class="secondary-button" to="/profile/edit?tab=pc">내 장비 업데이트</RouterLink>
        </div>
      </aside>
    </div>

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

const suitability = ref({ owned: [], interested: [] });
const suitabilityLoading = ref(false);
const pcCompare = ref(null);
const pcCompareLoading = ref(false);

const isOwned = computed(() => item.value.is_owned ?? false);
const isInterested = computed(() => item.value.is_interested ?? false);

// ── 히어로 배경 ──
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

const priceLabel = computed(() =>
  item.value.price ? `${Number(item.value.price).toLocaleString("ko-KR")}원` : "가격 정보 없음"
);

// ── 가격 비교 ──
const priceMarkets = computed(() => {
  const hist = item.value.price_history || [];
  const latestByShop = {};
  for (const h of [...hist].sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))) {
    if (!latestByShop[h.shop_name]) latestByShop[h.shop_name] = h;
  }
  return Object.values(latestByShop)
    .map((h) => ({ store: h.shop_name, price: h.price, discount: h.discount_percent }))
    .sort((a, b) => a.price - b.price)
    .slice(0, 5);
});

const priceStats = computed(() => {
  const hist = item.value.price_history || [];
  if (hist.length < 2) return null;
  const sorted = [...hist].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at));
  const prices = sorted.map((h) => h.price);
  const oldest = prices[0];
  const newest = prices[prices.length - 1];
  return {
    min: Math.min(...prices),
    max: Math.max(...prices),
    trend: newest > oldest ? "up" : newest < oldest ? "down" : "stable",
  };
});

// ── 사이드바: 현재 PC 사양 ──
const currentSpecs = computed(() => {
  const specs = auth.user?.pc_specs || {};
  const cat = item.value.category;
  return [
    { label: "CPU", value: specs.cpu || "정보 없음", note: cat === "cpu" ? "비교 대상" : "", highlighted: cat === "cpu" },
    { label: "GPU", value: specs.gpu || "정보 없음", note: cat === "gpu" ? "비교 대상" : "", highlighted: cat === "gpu" },
    { label: "메모리", value: (specs.memory || []).join(", ") || specs.ram || "정보 없음", note: cat === "ram" ? "비교 대상" : "", highlighted: cat === "ram" },
    { label: "저장장치", value: specs.storage || "정보 없음", note: cat === "storage" ? "비교 대상" : "", highlighted: cat === "storage" },
  ];
});

const genericAdvice = computed(() => {
  const cat = item.value.category;
  const map = {
    ram: "메모리가 부족하거나 멀티태스킹 시 렉이 잦다면 업그레이드를 고려하세요.",
    storage: "NVMe SSD 교체로 게임 로딩 시간을 크게 단축할 수 있습니다.",
    monitor: "고주사율·저지연 모니터는 FPS 게임에서 특히 큰 차이를 만듭니다.",
    mouse: "경량 마우스로 FPS 조준 정확도를 높일 수 있습니다.",
    keyboard: "기계식 키보드는 입력 반응속도와 내구성 모두 뛰어납니다.",
    headset: "공간 음향 지원 헤드셋은 게임 몰입감과 팀 커뮤니케이션을 향상시킵니다.",
    power: "안정적인 파워 서플라이는 고사양 빌드의 필수 요소입니다.",
  };
  return map[cat] || "현재 플레이 스타일에 맞춰 선택할 만한 장비입니다.";
});

// ── 유틸 ──
function fitLabel(status) {
  return { pass: "권장사양 충족", warn: "최소사양 충족", fail: "사양 부족", unknown: "분석 불가", info: "간접 개선" }[status] || status;
}

// ── API 로드 ──
async function loadSuitability(id) {
  suitabilityLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/equipment/${id}/game-suitability/`);
    suitability.value = data;
  } catch {
    suitability.value = { owned: [], interested: [] };
  } finally {
    suitabilityLoading.value = false;
  }
}

async function loadPCCompare(id) {
  pcCompareLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/equipment/${id}/pc-compare/`);
    pcCompare.value = data;
  } catch {
    pcCompare.value = null;
  } finally {
    pcCompareLoading.value = false;
  }
}

// ── 액션: 내 장비 추가/제거 ──
async function handleOwned() {
  if (!auth.isAuthenticated) { actionMessage.value = "로그인이 필요합니다."; return; }
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
  if (!auth.isAuthenticated) { actionMessage.value = "로그인이 필요합니다."; return; }
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
    loadSuitability(data.id);
    loadPCCompare(data.id);
  }
});
</script>
