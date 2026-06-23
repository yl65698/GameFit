<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">게임 탐색</p>
        <h1>할인과 취향을 같이 보는 게임 목록</h1>
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
            :placeholder="searchMode === 'title' ? '게임명을 입력하세요' : '예: 친구랑 할 수 있고 할인 중인 협동 게임 찾아줘'"
          />
          <div v-if="showSuggestions" class="suggestion-list">
            <RouterLink v-for="game in titleSuggestions" :key="game.id" :to="`/games/${game.id}`">
              <strong>{{ game.title }}</strong>
              <span>{{ game.genre }} · {{ game.discount }}% 할인</span>
            </RouterLink>
          </div>
        </div>
        <button class="primary-button" :disabled="aiLoading">
          {{ searchMode === "ai" && aiLoading ? "AI 검색 중..." : "검색" }}
        </button>
      </form>
      <p v-if="aiSummary" class="ai-summary">{{ aiSummary }}</p>
      <p v-if="aiError" class="error-text">{{ aiError }}</p>
    </section>

    <div class="filter-row">
      <button class="filter-chip active">내 PC 구동 가능</button>
      <button class="filter-chip">최고 할인</button>
      <button class="filter-chip">관심 장르</button>
      <button class="filter-chip">신규 출시</button>
    </div>

    <section class="panel">
      <div class="panel-heading">
        <h2>최고 할인 게임</h2>
        <span>{{ discountedGames.length }}개</span>
      </div>
      <div class="game-grid">
        <RouterLink v-for="game in discountedGames" :key="game.id" class="game-card" :to="`/games/${game.id}`">
          <div class="game-art">
            <span>{{ game.discount }}%</span>
          </div>
          <div>
            <h3>{{ game.title }}</h3>
            <p>{{ game.summary }}</p>
          </div>
          <footer>
            <span>{{ game.genre }}</span>
            <strong>{{ game.buy_signal }}</strong>
          </footer>
        </RouterLink>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <h2>맞춤 추천 게임</h2>
        <RouterLink to="/taste">성향 분석 보기</RouterLink>
      </div>
      <div class="recommend-row">
        <RouterLink v-for="game in filteredGames" :key="`rec-${game.id}`" :to="`/games/${game.id}`">
          <strong>{{ game.title }}</strong>
          <span>{{ game.compatibility }}</span>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import aiApi from "../../services/aiApi";
import api from "../../services/api";

const query = ref("");
const games = ref([]);
const aiResults = ref([]);
const aiSummary = ref("");
const aiError = ref("");
const aiLoading = ref(false);
const searchMode = ref("title");

onMounted(async () => {
  const { data } = await api.get("/catalog/games/");
  games.value = data;
});

const filteredGames = computed(() => {
  if (searchMode.value === "ai" && aiResults.value.length) return aiResults.value;
  const keyword = query.value.trim().toLowerCase();
  if (!keyword) return games.value;
  return games.value.filter((game) => game.title.toLowerCase().includes(keyword));
});

const discountedGames = computed(() => [...filteredGames.value].sort((a, b) => b.discount - a.discount));
const titleSuggestions = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  if (searchMode.value !== "title" || keyword.length < 1) return [];
  return games.value.filter((game) => game.title.toLowerCase().includes(keyword)).slice(0, 8);
});
const showSuggestions = computed(() => titleSuggestions.value.length > 0);

async function runSearch() {
  aiError.value = "";
  aiSummary.value = "";

  if (searchMode.value === "title") {
    aiResults.value = [];
    return;
  }

  const prompt = query.value.trim();
  if (!prompt) {
    aiError.value = "자연어로 찾고 싶은 게임 조건을 입력해주세요.";
    return;
  }

  aiLoading.value = true;
  try {
    const { data } = await aiApi.post("/ai/search", {
      query: prompt,
      games: games.value,
    });
    aiResults.value = data.results;
    aiSummary.value = data.summary;
  } catch (error) {
    aiError.value = "AI 검색 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인해주세요.";
  } finally {
    aiLoading.value = false;
  }
}
</script>
