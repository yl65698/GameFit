<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <h1 class="page-title-large">장비 탐색</h1>
      </div>
    </header>

    <!-- 검색 패널 (게임 탐색과 동일 구조) -->
    <section class="panel search-hero">
      <div class="search-mode-tabs">
        <button :class="{ active: searchMode === 'name' }" @click="setSearchMode('name')">장비명 검색</button>
        <button :class="{ active: searchMode === 'ai' }" @click="setSearchMode('ai')">AI 자연어 추천</button>
      </div>

      <form class="large-search" @submit.prevent="runSearch">
        <input
          v-model="query"
          :placeholder="searchMode === 'name'
            ? '장비명을 입력하세요 (예: RTX 4070, 게이밍 마우스)'
            : '예: QHD에서 FPS를 쾌적하게 즐기고 싶어. 예산 100만원 이하 GPU 추천해줘'"
          @input="onQueryInput"
        />
        <button class="primary-button" :disabled="loading || aiLoading">
          {{ aiLoading ? "AI 분석 중..." : "검색" }}
        </button>
      </form>

      <template v-if="isAiActive">
        <div class="ai-result-meta">
          <span class="ai-badge">AI 추천</span>
          <span v-if="aiIntent" class="ai-intent">{{ aiIntent }}</span>
          <button class="link-button" @click="clearAi">필터로 돌아가기</button>
        </div>
        <p v-if="aiSummary" class="ai-summary">{{ aiSummary }}</p>
      </template>
      <p v-if="aiError" class="error-text">{{ aiError }}</p>
    </section>

    <!-- 카테고리 필터 칩 + 정렬 (AI 모드 제외) -->
    <div v-if="!isAiActive" class="equip-filter-bar">
      <div class="filter-row">
        <button
          v-for="cat in CATEGORIES"
          :key="cat.value"
          :class="['filter-chip', activeCategory === cat.value && 'active']"
          @click="setCategory(cat.value)"
        >
          {{ cat.label }}
        </button>
      </div>
      <select v-model="sortMode" class="equip-sort-select" @change="loadEquipment(1)">
        <option value="benchmark">벤치마크 높은순</option>
        <option value="discount">할인율 높은순</option>
        <option value="price_asc">가격 낮은순</option>
        <option value="price_desc">가격 높은순</option>
      </select>
    </div>

    <!-- 장비 목록 -->
    <section class="panel">
      <div class="panel-heading">
        <h2>{{ isAiActive ? "AI 추천 결과" : activeCategoryLabel }}</h2>
        <span v-if="!loading && !aiLoading">
          {{ isAiActive ? aiEquipment.length : totalCount }}개
        </span>
      </div>

      <div v-if="loading || aiLoading" class="loading-state">불러오는 중...</div>

      <div v-else-if="displayList.length === 0" class="empty-state">
        <p v-if="isAiActive">AI 추천 결과가 없습니다. 다른 표현으로 검색해보세요.</p>
        <p v-else>해당 카테고리의 장비가 없습니다.</p>
      </div>

      <div v-else class="game-grid">
        <RouterLink
          v-for="item in displayList"
          :key="item.id"
          class="game-card"
          :to="`/equipment/${item.id}`"
        >
          <div class="game-art" :style="artStyle(item)">
            <span v-if="item.discount_percent > 0">{{ item.discount_percent }}%</span>
            <span v-else-if="isAiActive" class="chip-ai">AI</span>
            <span v-else>{{ item.type }}</span>
          </div>
          <div>
            <h3>{{ item.name }}</h3>
            <p>{{ item.specs || item.fit || "사양 정보 없음" }}</p>
          </div>
          <footer>
            <span>{{ item.benchmark_score > 0 ? "벤치 " + item.benchmark_score + "점" : item.type }}</span>
            <strong>{{ Number(item.price).toLocaleString("ko-KR") }}원</strong>
          </footer>
        </RouterLink>
      </div>

      <!-- 페이지네이션 (AI 모드 제외) -->
      <div v-if="!isAiActive && totalPages > 1" class="pagination">
        <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">‹</button>
        <template v-for="p in pageNumbers" :key="p">
          <span v-if="p === '...'" class="page-ellipsis">…</span>
          <button
            v-else
            class="page-btn"
            :class="{ active: p === currentPage }"
            @click="goToPage(p)"
          >{{ p }}</button>
        </template>
        <button class="page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">›</button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import api from "../../services/api";

const CATEGORIES = [
  { label: "전체", value: "" },
  { label: "CPU", value: "cpu" },
  { label: "GPU", value: "gpu" },
  { label: "RAM", value: "ram" },
  { label: "저장장치", value: "storage" },
  { label: "모니터", value: "monitor" },
  { label: "마우스", value: "mouse" },
  { label: "키보드", value: "keyboard" },
  { label: "헤드셋", value: "headset" },
  { label: "파워", value: "power" },
  { label: "VR", value: "vr" },
  { label: "기타", value: "other" },
];

// 카테고리별 game-art 그라데이션 (game-card nth-child 패턴과 유사)
const CATEGORY_GRADIENTS = {
  cpu:      "linear-gradient(145deg,#182a4d,#1e3a8a 55%,#3b82f6)",
  gpu:      "linear-gradient(145deg,#14213d,#166534 55%,#4ade80)",
  ram:      "linear-gradient(145deg,#1e1b4b,#5b21b6 55%,#a78bfa)",
  storage:  "linear-gradient(145deg,#1c1917,#44403c 55%,#a8a29e)",
  monitor:  "linear-gradient(145deg,#0f172a,#0369a1 55%,#38bdf8)",
  mouse:    "linear-gradient(145deg,#1a1a2e,#b91c1c 55%,#fca5a5)",
  keyboard: "linear-gradient(145deg,#0d1117,#15803d 55%,#86efac)",
  headset:  "linear-gradient(145deg,#1e293b,#b45309 55%,#fde68a)",
  vr:       "linear-gradient(145deg,#33165f,#7c3aed 55%,#c4b5fd)",
  power:    "linear-gradient(145deg,#1c1c1c,#9f1239 55%,#fda4af)",
  console:  "linear-gradient(145deg,#0f1923,#1a56db 55%,#93c5fd)",
  other:    "linear-gradient(145deg,#263238,#17637d 55%,#8ad0c2)",
};

const query = ref("");
const searchMode = ref("name");
const activeCategory = ref("");
const sortMode = ref("benchmark");
const equipment = ref([]);
const currentPage = ref(1);
const totalPages = ref(1);
const totalCount = ref(0);
const loading = ref(false);

const isAiActive = ref(false);
const aiEquipment = ref([]);
const aiSummary = ref("");
const aiIntent = ref("");
const aiError = ref("");
const aiLoading = ref(false);

let searchDebounce = null;

const activeCategoryLabel = computed(
  () => CATEGORIES.find((c) => c.value === activeCategory.value)?.label || "전체"
);
const displayList = computed(() => (isAiActive.value ? aiEquipment.value : equipment.value));

const pageNumbers = computed(() => {
  const total = totalPages.value;
  const cur = currentPage.value;
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = new Set([1, total, cur]);
  for (let i = cur - 1; i <= cur + 1; i++) {
    if (i >= 1 && i <= total) pages.add(i);
  }
  const sorted = [...pages].sort((a, b) => a - b);
  const result = [];
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) result.push("...");
    result.push(sorted[i]);
  }
  return result;
});

async function loadEquipment(page = 1) {
  loading.value = true;
  try {
    const params = new URLSearchParams({ page, sort: sortMode.value });
    if (activeCategory.value) params.set("category", activeCategory.value);
    if (query.value.trim() && searchMode.value === "name") params.set("q", query.value.trim());
    const { data } = await api.get(`/catalog/equipment/?${params}`);
    equipment.value = data.results;
    currentPage.value = data.page;
    totalPages.value = data.total_pages;
    totalCount.value = data.total;
  } catch {
    equipment.value = [];
  } finally {
    loading.value = false;
  }
}

function setCategory(cat) {
  activeCategory.value = cat;
  clearAi();
  loadEquipment(1);
}

function setSearchMode(mode) {
  searchMode.value = mode;
  query.value = "";
  clearAi();
}

function onQueryInput() {
  if (searchMode.value !== "name") return;
  clearAi();
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => loadEquipment(1), 350);
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return;
  loadEquipment(page);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearAi() {
  isAiActive.value = false;
  aiEquipment.value = [];
  aiSummary.value = "";
  aiIntent.value = "";
  aiError.value = "";
}

async function runSearch() {
  aiError.value = "";

  if (searchMode.value === "name") {
    clearAi();
    loadEquipment(1);
    return;
  }

  const prompt = query.value.trim();
  if (!prompt) {
    aiError.value = "원하는 장비 조건을 자연어로 입력해주세요.";
    return;
  }

  aiLoading.value = true;
  clearAi();

  try {
    const { data } = await api.post("/catalog/ai-equipment-search/", {
      query: prompt,
      category: activeCategory.value || "",
    });
    aiEquipment.value = data.results || [];
    aiSummary.value = data.summary || "";
    aiIntent.value = data.intent || "";
    isAiActive.value = true;
  } catch (err) {
    aiError.value = err.response?.data?.detail || "AI 추천 중 오류가 발생했습니다.";
  } finally {
    aiLoading.value = false;
  }
}

function artStyle(item) {
  if (item.image_url) {
    return {
      backgroundImage: `linear-gradient(180deg, rgba(12,18,28,0.05), rgba(12,18,28,0.72)), url("${item.image_url}")`,
      backgroundSize: "cover",
      backgroundPosition: "center",
    };
  }
  return { background: CATEGORY_GRADIENTS[item.category] || CATEGORY_GRADIENTS.other };
}

onMounted(() => loadEquipment(1));
</script>
