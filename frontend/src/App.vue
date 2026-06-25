<template>
  <div class="app-shell">
    <div class="neon-gradient-bg" :class="{ 'is-welcome': isWelcome }" aria-hidden="true"></div>
    <header v-if="showServiceNav" class="topbar">
      <RouterLink class="brand" to="/">
        <span>Game<span class="brand-accent">Fit</span></span>
        <small>AI 기반 게임 가격 비교 · 추천</small>
      </RouterLink>
      <nav class="topnav">
        <RouterLink to="/profile">프로필</RouterLink>
        <RouterLink to="/taste">성향 분석</RouterLink>
        <RouterLink to="/games">게임 탐색</RouterLink>
        <RouterLink to="/equipment">장비 탐색</RouterLink>
        <RouterLink to="/calendar">할인 캘린더</RouterLink>
      </nav>
      <div class="topbar-actions">
        <ThemeSelector />
        <button class="icon-text-button" @click="handleLogout">로그아웃</button>
      </div>
    </header>

    <main :class="['page', { 'page--guest': route.name === 'welcome' }]">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import ThemeSelector from "./components/ThemeSelector.vue";
import { useAuthStore } from "./stores/auth";
import { useThemeStore } from "./stores/theme";

const auth = useAuthStore();
const theme = useThemeStore();
const router = useRouter();
const route = useRoute();
const showServiceNav = computed(() => auth.isAuthenticated && route.name !== "welcome");
const isWelcome = computed(() => route.name === "welcome");

onMounted(() => {
  theme.init();
});

async function handleLogout() {
  await auth.logout();
  router.push("/");
}
</script>
