<template>
  <section class="welcome-screen">
    <header v-if="auth.isAuthenticated" class="welcome-session">
      <RouterLink class="session-profile" to="/profile">
        <span class="session-avatar">{{ initial }}</span>
        <span>{{ auth.user?.nickname || auth.user?.username }}</span>
      </RouterLink>
      <button class="session-logout" @click="handleLogout">로그아웃</button>
    </header>

    <div class="welcome-media">
      <div class="media-grid">
        <div class="media-card is-large">
          <span>내 PC로 구동 가능</span>
          <strong>RTX 3070 Ti</strong>
        </div>
        <div class="media-card">
          <span>최대 할인</span>
          <strong>75%</strong>
        </div>
        <div class="media-card">
          <span>AI 취향 분석</span>
          <strong>전략 · 협동</strong>
        </div>
      </div>
    </div>

    <div class="welcome-copy">
      <p class="eyebrow">GameFit — AI 게임 플랫폼</p>
      <h1>내 PC와 취향에 딱 맞는 게임을 찾아드립니다</h1>
      <p>
        PC 사양 기반 구동 가능 여부, 할인 타이밍 알림, AI 맞춤 추천까지 — 게임 구매 결정을 한 번에.
      </p>
      <div class="welcome-actions">
        <template v-if="auth.isAuthenticated">
          <RouterLink class="primary-button" to="/profile">찾아보러가기</RouterLink>
        </template>
        <template v-else>
          <button class="primary-button" @click="openModal('login')">로그인</button>
          <button class="secondary-button" @click="openModal('signup')">회원가입</button>
        </template>
      </div>
    </div>

    <div v-if="mode" class="modal-backdrop" @click.self="closeModal">
      <form class="auth-modal" @submit.prevent="submit">
        <button class="modal-close" type="button" @click="closeModal">닫기</button>
        <p class="eyebrow">{{ mode === "signup" ? "새 계정" : "돌아온 플레이어" }}</p>
        <h2>{{ mode === "signup" ? "회원가입" : "로그인" }}</h2>

        <label>
          아이디
          <input v-model="form.username" required autocomplete="username" />
        </label>
        <label v-if="mode === 'signup'">
          이메일
          <input v-model="form.email" type="email" autocomplete="email" />
        </label>
        <label v-if="mode === 'signup'">
          닉네임
          <input v-model="form.nickname" autocomplete="nickname" />
        </label>
        <label>
          비밀번호
          <input v-model="form.password" type="password" required :autocomplete="passwordAutocomplete" />
        </label>
        <label v-if="mode === 'signup'">
          비밀번호 확인
          <input v-model="form.password2" type="password" required autocomplete="new-password" />
        </label>

        <p v-if="auth.error" class="error-text">{{ auth.error }}</p>
        <button class="primary-button full-button" :disabled="auth.loading">{{ submitLabel }}</button>
        <button class="link-button" type="button" @click="toggleMode">
          {{ mode === "signup" ? "이미 계정이 있어요" : "계정 만들기" }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const mode = ref("");
const form = reactive({
  username: "",
  email: "",
  nickname: "",
  password: "",
  password2: "",
});

const passwordAutocomplete = computed(() => (mode.value === "signup" ? "new-password" : "current-password"));
const initial = computed(() => (auth.user?.nickname || auth.user?.username || "G").slice(0, 1));
const submitLabel = computed(() => {
  if (auth.loading) return mode.value === "signup" ? "가입 중..." : "로그인 중...";
  return mode.value === "signup" ? "가입하고 시작" : "로그인";
});

watch(
  () => route.query.auth,
  (authMode) => {
    if (authMode === "login" || authMode === "signup") openModal(authMode);
  },
  { immediate: true },
);

function openModal(nextMode) {
  mode.value = nextMode;
  auth.error = "";
}

function closeModal() {
  mode.value = "";
  auth.error = "";
  if (route.query.auth) router.replace({ name: "welcome" });
}

function toggleMode() {
  openModal(mode.value === "signup" ? "login" : "signup");
}

async function submit() {
  if (mode.value === "signup") {
    await auth.signup(form);
  } else {
    await auth.login({ username: form.username, password: form.password });
  }
  mode.value = "";
  router.push("/");
}

async function handleLogout() {
  await auth.logout();
  closeModal();
}
</script>
