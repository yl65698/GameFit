<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <h1 class="page-title-large">게임 탐색</h1>
      </div>
    </header>

    <section class="panel search-hero">
      <div class="search-mode-tabs">
        <button :class="{ active: searchMode === 'title' }" @click="searchMode = 'title'">게임명 검색</button>
        <button :class="{ active: searchMode === 'ai' }" @click="searchMode = 'ai'">AI 자연어 검색</button>
      </div>
      <form class="large-search" @submit.prevent="runSearch">
        <div class="autocomplete-wrap">
          <input
            v-model="query"
            :placeholder="searchMode === 'title' ? '게임명을 입력하세요' : '예: 친구랑 같이 할 수 있는 공포 게임, 할인 많이 된 RPG, 혼자 편하게 즐길 수 있는 인디 게임'"
            @input="onQueryInput"
            @keydown.escape="clearAiResults"
          />
          <div v-if="showSuggestions" class="suggestion-list">
            <RouterLink
              v-for="game in titleSuggestions"
              :key="game.id"
              :to="`/games/${game.id}`"
              @click="clearSuggestions"
            >
              <strong>{{ game.title }}</strong>
              <span>{{ game.genre }} · {{ game.discount }}% 할인</span>
            </RouterLink>
          </div>
        </div>
        <button class="primary-button" :disabled="aiLoading">
          {{ aiLoading ? "AI 검색 중..." : "검색" }}
        </button>
      </form>

      <template v-if="isAiSearchActive">
        <div class="ai-result-meta">
          <span class="ai-badge">AI 검색</span>
          <span v-if="aiIntent" class="ai-intent">{{ aiIntent }}</span>
          <button class="link-button" @click="clearAiResults">필터로 돌아가기</button>
        </div>
        <p v-if="aiSummary" class="ai-summary">{{ aiSummary }}</p>
      </template>
      <p v-if="aiError" class="error-text">{{ aiError }}</p>
    </section>

    <div v-if="!isAiSearchActive" class="filter-row">
      <button
        v-for="chip in FILTER_CHIPS"
        :key="chip.key"
        class="filter-chip"
        :class="{ active: activeFilter === chip.key }"
        @click="setFilter(chip.key)"
      >
        {{ chip.label }}
      </button>
    </div>

    <section class="panel">
      <div class="panel-heading">
        <h2>{{ currentSectionTitle }}</h2>
        <span v-if="!filterLoading && !aiLoading">
          {{ isAiSearchActive ? aiGames.length : totalCount }}개
        </span>
      </div>

      <div v-if="filterLoading || aiLoading" class="loading-state">불러오는 중...</div>
      <div v-else-if="displayGames.length === 0" class="empty-state">
        <p v-if="isAiSearchActive">AI가 검색 결과를 찾지 못했습니다. 다른 표현으로 검색해보세요.</p>
        <p v-else-if="activeFilter === 'recommended'">프로필 설정 후 이용할 수 있습니다.</p>
        <p v-else-if="activeFilter === 'interest-genre'">관심 장르 데이터가 없습니다. 게임을 보유/관심 목록에 추가해보세요.</p>
        <p v-else>게임이 없습니다.</p>
      </div>
      <div v-else class="game-grid">
        <RouterLink
          v-for="game in displayGames"
          :key="game.id"
          class="game-card"
          :to="`/games/${game.id}`"
        >
          <div class="game-art" :style="imageBackground(game.image_url)">
            <span v-if="game.discount > 0">{{ game.discount }}%</span>
            <span v-else-if="isAiSearchActive" class="chip-ai">AI</span>
            <span v-else-if="activeFilter === 'new-release'" class="chip-new">NEW</span>
            <span v-else-if="activeFilter === 'popular'" class="chip-popular">인기</span>
          </div>
          <div>
            <h3>{{ game.title }}</h3>
            <p>{{ game.summary }}</p>
          </div>
          <footer>
            <span>{{ game.genre }}</span>
          </footer>
        </RouterLink>
      </div>

      <!-- 페이지네이션 (필터 모드에서만 표시) -->
      <div v-if="!isAiSearchActive && totalPages > 1" class="pagination">
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

const query = ref("");
const games = ref([]);
const searchMode = ref("title");

// 필터 칩
const activeFilter = ref("top-discount");
const filterGames = ref([]);
const filterLoading = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const totalCount = ref(0);

// AI 검색
const isAiSearchActive = ref(false);
const aiGames = ref([]);
const aiSummary = ref("");
const aiIntent = ref("");
const aiError = ref("");
const aiLoading = ref(false);


const FILTER_CHIPS = [
  { key: "top-discount",   label: "최고 할인" },
  { key: "popular",        label: "최고 인기" },
  { key: "interest-genre", label: "관심 장르" },
  { key: "new-release",    label: "신규 출시" },
  { key: "recommended",    label: "맞춤 추천" },
];

const FILTER_TITLES = {
  "top-discount":   "최고 할인 게임",
  "popular":        "최고 인기 게임",
  "interest-genre": "관심 장르 게임",
  "new-release":    "신규 출시 게임",
  "recommended":    "맞춤 추천 게임",
};

const displayGames = computed(() => isAiSearchActive.value ? aiGames.value : filterGames.value);
const currentSectionTitle = computed(() =>
  isAiSearchActive.value ? "AI 검색 결과" : FILTER_TITLES[activeFilter.value]
);

// 페이지 번호 목록 (최대 7개 표시, 양끝 + 현재 주변)
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

onMounted(() => {
  // 필터 그리드와 자동완성 목록을 병렬로 로드
  loadFilterGames("top-discount", 1);
  api.get("/catalog/games/autocomplete/").then(res => {
    games.value = res.data;
  });
});

async function loadFilterGames(filterType, page = 1) {
  filterLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/filter/?type=${filterType}&page=${page}`);
    filterGames.value = data.results;
    totalPages.value = data.total_pages;
    totalCount.value = data.total;
    currentPage.value = data.page;
  } catch {
    filterGames.value = [];
    totalPages.value = 1;
    totalCount.value = 0;
  } finally {
    filterLoading.value = false;
  }
}

async function setFilter(filterType) {
  clearAiResults();
  activeFilter.value = filterType;
  await loadFilterGames(filterType, 1);
}

async function goToPage(page) {
  if (page < 1 || page > totalPages.value) return;
  await loadFilterGames(activeFilter.value, page);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// 타이틀 검색 자동완성
const titleSuggestions = computed(() => {
  if (searchMode.value !== "title") return [];
  const keyword = query.value.trim().toLowerCase();
  if (keyword.length < 1) return [];
  return games.value.filter((g) => g.title.toLowerCase().includes(keyword)).slice(0, 8);
});
const showSuggestions = computed(() => titleSuggestions.value.length > 0);

function onQueryInput() {
  if (isAiSearchActive.value) clearAiResults();
}

function clearSuggestions() {
  query.value = "";
}

function clearAiResults() {
  isAiSearchActive.value = false;
  aiGames.value = [];
  aiSummary.value = "";
  aiIntent.value = "";
  aiError.value = "";
}

function imageBackground(url) {
  if (!url) return {};
  return {
    backgroundImage: `linear-gradient(180deg, rgba(12, 18, 28, 0.05), rgba(12, 18, 28, 0.72)), url("${url}")`,
  };
}

async function runSearch() {
  aiError.value = "";

  if (searchMode.value === "title") {
    clearAiResults();
    return;
  }

  const prompt = query.value.trim();
  if (!prompt) {
    aiError.value = "자연어로 찾고 싶은 게임 조건을 입력해주세요.";
    return;
  }

  aiLoading.value = true;
  clearAiResults();

  try {
    const { data } = await api.post("/catalog/ai-search/", { query: prompt });
    aiGames.value = data.results || [];
    aiSummary.value = data.summary || "";
    aiIntent.value = data.intent || "";
    isAiSearchActive.value = true;
  } catch (err) {
    aiError.value = err.response?.data?.detail || "AI 검색 중 오류가 발생했습니다.";
  } finally {
    aiLoading.value = false;
  }
}
</script>
