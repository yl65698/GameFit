<template>
  <div class="app-shell">
    <header v-if="showServiceNav" class="topbar">
      <RouterLink class="brand" to="/">
        <span>GameFit</span>
        <small>PC 사양 기반 게임 판단</small>
      </RouterLink>
      <nav class="topnav">
        <RouterLink to="/profile">프로필</RouterLink>
        <RouterLink to="/taste">게임성향분석</RouterLink>
        <RouterLink to="/games">게임탐색</RouterLink>
        <RouterLink to="/equipment">장비 탐색</RouterLink>
        <RouterLink to="/calendar">할인 켈린더</RouterLink>
      </nav>
      <button class="icon-text-button" @click="handleLogout">로그아웃</button>
    </header>

    <main :class="['page', { 'page--guest': route.name === 'welcome' }]">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "./stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const showServiceNav = computed(() => auth.isAuthenticated && route.name !== "welcome");

async function handleLogout() {
  await auth.logout();
  router.push("/");
}
</script>
