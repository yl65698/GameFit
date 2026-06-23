<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">내 프로필</p>
        <h1>{{ profile.nickname || profile.username }}</h1>
        <p class="subtle">{{ tags }}</p>
      </div>
      <RouterLink class="secondary-button" to="/profile/edit">프로필 수정</RouterLink>
    </header>

    <div class="profile-layout">
      <article class="panel profile-card">
        <div class="avatar avatar--photo">
          <img v-if="profile.avatar_url" :src="profile.avatar_url" alt="프로필 사진" />
          <span v-else>{{ initial }}</span>
        </div>
        <div>
          <strong>{{ profile.nickname || "플레이어" }}</strong>
          <p class="taste-summary">{{ tasteKeywords }}</p>
          <div class="stat-row">
            <button @click="openSocialModal('following')">
              <strong>{{ followingUsers.length }}</strong>
              <span>팔로잉</span>
            </button>
            <button @click="openSocialModal('followers')">
              <strong>{{ followerUsers.length.toLocaleString("ko-KR") }}</strong>
              <span>팔로워</span>
            </button>
          </div>
          <RouterLink class="text-link taste-link" to="/taste">게임 성향 더보기</RouterLink>
        </div>
      </article>

      <article class="panel pc-card">
        <div class="panel-heading">
          <h2>내 PC 정보</h2>
          <RouterLink to="/equipment">장비 보기</RouterLink>
        </div>
        <dl class="spec-grid">
          <template v-for="(value, key) in profile.pc_specs" :key="key">
            <dt>{{ specLabel(key) }}</dt>
            <dd>{{ value }}</dd>
          </template>
        </dl>
      </article>
    </div>

    <section class="panel">
      <div class="panel-heading">
        <h2>보유 게임 목록</h2>
        <div class="panel-actions">
          <RouterLink to="/games">게임 찾아보기</RouterLink>
          <div class="segmented-control">
            <button :class="{ active: ownedView === 'card' }" @click="ownedView = 'card'">카드</button>
            <button :class="{ active: ownedView === 'list' }" @click="ownedView = 'list'">리스트</button>
          </div>
        </div>
      </div>
      <div class="platform-filter">
        <label v-for="platform in platforms" :key="platform.value">
          <input v-model="selectedPlatforms" type="checkbox" :value="platform.value" />
          {{ platform.label }}
        </label>
      </div>
      <div :class="ownedView === 'card' ? 'game-strip' : 'profile-list'">
        <RouterLink v-for="game in filteredOwnedGames" :key="game" :class="ownedView === 'card' ? 'game-cover' : 'profile-list-item'" :to="gameDetailPath(game)">
          <span>{{ game }}</span>
          <small>{{ gamePlatform(game) }}</small>
        </RouterLink>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <h2>관심 등록 게임</h2>
        <div class="panel-actions">
          <RouterLink to="/calendar">할인 일정 보기</RouterLink>
          <div class="segmented-control">
            <button :class="{ active: interestView === 'card' }" @click="interestView = 'card'">카드</button>
            <button :class="{ active: interestView === 'list' }" @click="interestView = 'list'">리스트</button>
          </div>
        </div>
      </div>
      <div :class="interestView === 'card' ? 'game-strip' : 'profile-list'">
        <RouterLink v-for="game in interestedGames" :key="game" :class="interestView === 'card' ? 'game-cover' : 'profile-list-item'" :to="gameDetailPath(game)">
          <span>{{ game }}</span>
          <small>{{ interestAlertLabel(game) }} · {{ gamePlatform(game) }}</small>
        </RouterLink>
      </div>
    </section>

    <div v-if="socialModal" class="modal-backdrop" @click.self="socialModal = ''">
      <section class="social-modal">
        <button class="modal-close" @click="socialModal = ''">닫기</button>
        <p class="eyebrow">내 프로필</p>
        <h2>{{ socialModal === "followers" ? "팔로워" : "팔로잉" }}</h2>
        <div class="social-list">
          <RouterLink v-for="name in visibleSocialUsers" :key="name" :to="`/players/${name}`" @click="socialModal = ''">
            <span class="avatar avatar--small">{{ name.slice(0, 1).toUpperCase() }}</span>
            <strong>{{ name }}</strong>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();
const ownedView = ref("card");
const interestView = ref("card");
const socialModal = ref("");
const platforms = [
  { label: "Steam", value: "Steam" },
  { label: "Epic games", value: "Epic games" },
  { label: "Ubisoft", value: "Ubisoft" },
  { label: "그 외", value: "Other" },
];
const selectedPlatforms = ref(platforms.map((platform) => platform.value));
const profile = computed(() => auth.user || {});
const initial = computed(() => (profile.value.nickname || profile.value.username || "G").slice(0, 1));
const tags = computed(() => (profile.value.hashtags || []).map((tag) => `#${tag}`).join(" "));
const tasteKeywords = computed(() => {
  const keywords = profile.value.hashtags?.length ? profile.value.hashtags : ["전략", "협동", "인디"];
  return keywords.map((keyword) => `#${keyword}`).join(" ");
});
const ownedGames = computed(() => profile.value.owned_games || []);
const filteredOwnedGames = computed(() =>
  ownedGames.value.filter((game) => selectedPlatforms.value.includes(gamePlatform(game))),
);
const interestedGames = computed(() => profile.value.interested_games || []);
const followedPlayers = computed(() => {
  try {
    return JSON.parse(localStorage.getItem("followedPlayers") || "[]");
  } catch {
    return [];
  }
});
const followerUsers = computed(() => ["strategy_admin", "sale_watcher", "coop_player", "party_maker"]);
const followingUsers = computed(() => {
  const saved = followedPlayers.value;
  return saved.length ? saved : ["strategy_admin"];
});
const visibleSocialUsers = computed(() =>
  socialModal.value === "followers" ? followerUsers.value : followingUsers.value,
);

const platformByGame = {
  "Civilization VI": "Steam",
  "Civilization V": "Steam",
  "Dead by Daylight": "Steam",
  "Stardew Valley": "Steam",
  "It Takes Two": "Epic games",
  "The Last of Us": "Epic games",
  "Hades II": "Steam",
  Fortnite: "Epic games",
  "Battlefield V": "Epic games",
  "Assassin's Creed Origin": "Ubisoft",
  "Assassin’s Creed Origin": "Ubisoft",
  "Assasin’s Creed I": "Ubisoft",
};

onMounted(() => auth.fetchProfile());

function specLabel(key) {
  return {
    cpu: "CPU",
    memory: "메모리",
    gpu: "GPU",
    storage: "저장공간",
    vr: "VR",
    console: "콘솔",
  }[key] || key;
}

function gamePlatform(game) {
  return profile.value.game_platforms?.[game] || platformByGame[game] || "Other";
}

const gameIds = {
  "Civilization VII": 1,
  "Civilization VI": 1,
  "Civilization V": 1,
  "It Takes Two": 2,
  "Hades II": 3,
};

function gameDetailPath(game) {
  return `/games/${gameIds[game] || 1}`;
}

function interestAlertLabel(game) {
  const alerts = profile.value.interest_alerts || {};
  return alerts[game] ?? true ? "할인 알림 켜짐" : "할인 알림 꺼짐";
}

function openSocialModal(type) {
  socialModal.value = type;
}
</script>
