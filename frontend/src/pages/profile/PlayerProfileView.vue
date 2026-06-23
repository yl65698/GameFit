<template>
  <section class="content-stack">
    <RouterLink class="back-link" to="/games">← 게임 목록으로 돌아가기</RouterLink>

    <article class="panel public-profile">
      <div class="avatar">{{ initial }}</div>
      <div>
        <p class="eyebrow">플레이어 프로필</p>
        <h1>{{ displayName }}</h1>
        <p class="taste-summary">#전략 #협동 #할인탐색</p>
        <p class="subtle">공개된 보유 게임과 게임 의견을 확인하는 임시 프로필 화면입니다.</p>
      </div>
    </article>

    <section class="panel">
      <h2>최근 남긴 의견</h2>
      <div class="profile-list">
        <div class="profile-list-item">
          <strong>게임 사양은 충분한지 먼저 확인하는 편이에요.</strong>
          <span>추천 의견</span>
        </div>
        <div class="profile-list-item">
          <strong>최저가 기록보다 높으면 관심게임에 넣고 기다립니다.</strong>
          <span>구매 타이밍</span>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const displayName = computed(() => route.params.username || "player");
const initial = computed(() => displayName.value.slice(0, 1).toUpperCase());
</script>
