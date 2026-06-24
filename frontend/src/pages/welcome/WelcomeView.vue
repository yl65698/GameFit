<template>
  <section class="welcome-screen">
    <Transition name="bg-fade">
      <div class="welcome-bg" :key="currentIndex" :style="currentBgStyle" />
    </Transition>
    <div class="welcome-overlay" />

    <header v-if="auth.isAuthenticated" class="welcome-session">
      <RouterLink class="session-profile" to="/profile">
        <span class="session-avatar">{{ initial }}</span>
        <span>{{ auth.user?.nickname || auth.user?.username }}</span>
      </RouterLink>
      <button class="session-logout" @click="handleLogout">로그아웃</button>
    </header>

    <div class="welcome-hero">
      <div class="welcome-media">
        <div class="media-grid">
          <div class="media-card is-large media-card--info">
            <Transition name="card-fade" mode="out-in">
              <div :key="currentIndex" class="media-card-content">
                <strong class="media-game-title">{{ currentGame?.title || 'GameFit' }}</strong>
                <p class="media-game-desc">{{ currentGame?.description || '지금 가장 인기 있는 할인 게임들을 소개합니다.' }}</p>
              </div>
            </Transition>
          </div>
          <div class="media-card">
            <span>할인</span>
            <Transition name="card-fade" mode="out-in">
              <strong :key="currentIndex">{{ currentGame ? currentGame.discount_percent + '%' : '—' }}</strong>
            </Transition>
          </div>
          <div class="media-card">
            <span>장르</span>
            <Transition name="card-fade" mode="out-in">
              <strong :key="currentIndex">{{ currentGenreLabel }}</strong>
            </Transition>
          </div>
        </div>
      </div>

      <div class="welcome-copy">
        <p class="eyebrow">GameFit</p>
        <h1>내 PC와 취향에 맞춰 게임 구매를 판단하세요</h1>
        <p>
          보유 게임과 PC 사양을 기준으로 구동 가능 여부, 할인 타이밍, 취향 추천을 한 번에 확인합니다.
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
    </div>

    <div v-if="featuredGames.length > 1" class="slideshow-dots">
      <button
        v-for="(g, i) in featuredGames"
        :key="g.id"
        class="dot"
        :class="{ active: i === currentIndex }"
        @click="goTo(i)"
      />
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../../services/api";
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

// Slideshow
const featuredGames = ref([]);
const currentIndex = ref(0);
let timer = null;

const genreMap = {
  rpg: "RPG",
  fps: "FPS",
  strategy: "전략",
  simulation: "시뮬레이션",
  adventure: "어드벤처",
  sports: "스포츠",
  horror: "공포",
  indie: "인디",
  other: "기타",
};

const currentGame = computed(() => featuredGames.value[currentIndex.value] || null);

const currentGenreLabel = computed(() =>
  currentGame.value ? (genreMap[currentGame.value.genre] || currentGame.value.genre) : "—"
);

const currentBgStyle = computed(() =>
  currentGame.value?.image_url
    ? { backgroundImage: `url(${currentGame.value.image_url})` }
    : {}
);

function startTimer() {
  clearInterval(timer);
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % featuredGames.value.length;
  }, 5000);
}

function goTo(i) {
  currentIndex.value = i;
  startTimer();
}

onMounted(async () => {
  try {
    const { data } = await api.get("/games/featured/");
    featuredGames.value = data;
    if (featuredGames.value.length > 1) startTimer();
  } catch {
    // API 응답 없으면 기본 배경 유지
  }
});

onBeforeUnmount(() => clearInterval(timer));

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
