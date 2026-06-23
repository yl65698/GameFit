<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">게임 성향 분석</p>
        <h1>보유/관심 게임 기반 취향 리포트</h1>
      </div>
      <button class="primary-button">설문 / 미니 게임 시작</button>
    </header>

    <div class="analysis-layout">
      <section class="panel report-card">
        <h2>AI 기반 분석 결과 리포트</h2>
        <p>{{ report.report }}</p>
        <div class="tag-row">
          <span v-for="tag in report.taste_tags" :key="tag">#{{ tag }}</span>
        </div>
      </section>

      <section class="panel vector-card">
        <h2>game genre vector map</h2>
        <div class="vector-list">
          <div v-for="item in report.vector_map" :key="item.genre">
            <span>{{ item.genre }}</span>
            <div class="meter"><i :style="{ width: `${item.score}%` }"></i></div>
            <strong>{{ item.score }}</strong>
          </div>
        </div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-heading">
        <h2>추천 게임</h2>
        <RouterLink to="/games">더 보기</RouterLink>
      </div>
      <div class="recommend-row">
        <RouterLink v-for="game in report.games" :key="game.id" :to="`/games/${game.id}`">
          <strong>{{ game.title }}</strong>
          <span>{{ game.buy_signal }}</span>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";

import api from "../../services/api";

const report = ref({ taste_tags: [], vector_map: [], games: [] });

onMounted(async () => {
  const { data } = await api.get("/catalog/recommendations/");
  report.value = data;
});
</script>
