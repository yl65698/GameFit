<template>
  <section class="content-stack">
    <RouterLink class="back-link" to="/games">← 게임 목록으로 돌아가기</RouterLink>

    <div v-if="loading" class="panel" style="text-align: center; padding: 2rem;">
      프로필을 불러오는 중...
    </div>

    <div v-else-if="error" class="panel" style="text-align: center; padding: 2rem;">
      {{ error }}
    </div>

    <template v-else-if="player">
      <article class="panel public-profile">
        <div class="avatar avatar--photo">
          <img v-if="player.avatar_url" :src="player.avatar_url" alt="프로필 사진" />
          <span v-else>{{ initial }}</span>
        </div>
        <div>
          <p class="eyebrow">플레이어 프로필</p>
          <h1>{{ player.nickname || player.username }}</h1>
          <div class="follow-summary">
            <button @click="showSocial('followers')">
              <strong>{{ followerCount.toLocaleString("ko-KR") }}</strong>
              <span>팔로워</span>
            </button>
            <button @click="showSocial('following')">
              <strong>{{ (player.following_list?.length ?? 0).toLocaleString("ko-KR") }}</strong>
              <span>팔로잉</span>
            </button>
          </div>
          <div v-if="player.hashtags?.length" class="hashtag-chips">
            <span v-for="tag in player.hashtags" :key="tag" class="hashtag-chip">#{{ tag }}</span>
          </div>
        </div>
        <button
          v-if="auth.isAuthenticated && player.id !== auth.user?.id"
          :class="isFollowing ? 'secondary-button' : 'primary-button'"
          :disabled="followLoading"
          @click="toggleFollow"
        >
          {{ isFollowing ? "팔로잉" : "팔로우" }}
        </button>
      </article>

      <div class="public-profile-grid">
        <section class="panel">
          <h2>보유 게임</h2>
          <div class="public-game-list">
            <div v-if="!player.owned_games?.length" class="subtle">등록된 보유 게임이 없습니다.</div>
            <RouterLink
              v-for="game in player.owned_games"
              :key="game.id"
              class="interest-item"
              :to="`/games/${game.id}`"
            >
              <strong>{{ game.title }}</strong>
              <span>{{ platformLabel[game.platform] || game.platform || "기타" }}</span>
            </RouterLink>
          </div>
        </section>

        <section class="panel">
          <h2>관심 게임</h2>
          <div class="public-game-list">
            <div v-if="!player.interested_games?.length" class="subtle">등록된 관심 게임이 없습니다.</div>
            <RouterLink
              v-for="game in player.interested_games"
              :key="game.id"
              class="interest-item"
              :to="`/games/${game.id}`"
            >
              <strong>{{ game.title }}</strong>
              <span>{{ platformLabel[game.platform] || game.platform || "기타" }}</span>
            </RouterLink>
          </div>
        </section>
      </div>

      <section class="panel">
        <h2>장비 정보</h2>
        <dl class="spec-grid">
          <template v-for="(value, key) in player.pc_specs" :key="key">
            <dt>{{ specLabel(key) }}</dt>
            <dd>
              <template v-if="specDisplayItems(value, key).length">
                <span class="spec-chip-list">
                  <span v-for="(item, i) in specDisplayItems(value, key)" :key="i" class="spec-chip">{{ item }}</span>
                </span>
              </template>
              <template v-else>
                <span class="spec-empty">미등록</span>
              </template>
            </dd>
          </template>
        </dl>
      </section>

      <div v-if="socialModal" class="modal-backdrop" @click.self="socialModal = ''">
        <section class="social-modal">
          <button class="modal-close" @click="socialModal = ''">닫기</button>
          <p class="eyebrow">{{ player.nickname || player.username }}</p>
          <h2>{{ socialModal === "followers" ? "팔로워" : "팔로잉" }}</h2>
          <div class="social-list">
            <RouterLink
              v-for="user in visibleSocialUsers"
              :key="user.id"
              :to="`/players/${user.username}`"
              @click="socialModal = ''"
            >
              <span class="avatar avatar--small">
                <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.nickname" />
                <template v-else>{{ (user.nickname || user.username).slice(0, 1).toUpperCase() }}</template>
              </span>
              <strong>{{ user.nickname || user.username }}</strong>
            </RouterLink>
            <p v-if="visibleSocialUsers.length === 0" class="subtle">아직 아무도 없습니다.</p>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const auth = useAuthStore();

const platformLabel = {
  steam: "Steam",
  epic: "Epic Games",
  ubisoft: "Ubisoft",
  gog: "GOG",
  origin: "EA/Origin",
  battlenet: "Battle.net",
  other: "기타",
};

const player = ref(null);
const loading = ref(false);
const error = ref("");
const socialModal = ref("");
const followLoading = ref(false);

const username = computed(() => route.params.username);
const initial = computed(() => (player.value?.nickname || player.value?.username || "?").slice(0, 1).toUpperCase());
const isFollowing = computed(() => player.value?.is_following ?? false);
const followerCount = ref(0);

const visibleSocialUsers = computed(() => {
  if (!player.value) return [];
  return socialModal.value === "followers"
    ? (player.value.followers_list || [])
    : (player.value.following_list || []);
});

async function loadPlayer() {
  if (!username.value) return;
  loading.value = true;
  error.value = "";
  try {
    player.value = await auth.fetchUserByUsername(username.value);
    followerCount.value = player.value.followers_count ?? 0;
  } catch (e) {
    error.value = e.response?.status === 404
      ? "플레이어를 찾을 수 없습니다."
      : "프로필을 불러오는 중 오류가 발생했습니다.";
  } finally {
    loading.value = false;
  }
}

async function toggleFollow() {
  if (!player.value || followLoading.value) return;
  followLoading.value = true;
  try {
    const result = await auth.followUser(player.value.id);
    player.value = { ...player.value, is_following: result.followed };
    followerCount.value = result.followers_count;
  } catch (e) {
    console.error("팔로우 처리 중 오류:", e);
  } finally {
    followLoading.value = false;
  }
}

function showSocial(type) {
  socialModal.value = type;
}

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

function specDisplayItems(value, key) {
  if (Array.isArray(value)) return value.map(normalizeSpecText).filter(Boolean);
  const text = normalizeSpecText(value);
  if (!text || text === "없음") return [];

  const parsed = parseArrayText(text);
  if (parsed.length) return parsed;

  if (key === "memory") return splitMemoryText(text);
  return [text];
}

function normalizeSpecText(value) {
  return String(value ?? "")
    .trim()
    .replace(/^\[\s*/, "")
    .replace(/\s*\]$/, "")
    .replace(/^["']|["']$/g, "")
    .trim();
}

function parseArrayText(text) {
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed.map(normalizeSpecText).filter(Boolean);
  } catch {
    // Some saved specs are already flattened strings, so fall back to heuristics.
  }

  const quotedItems = [...text.matchAll(/["']([^"']+)["']/g)].map((match) => normalizeSpecText(match[1]));
  return quotedItems.filter(Boolean);
}

function splitMemoryText(text) {
  const source = normalizeSpecText(text);
  const items = source
    .split(/(?=(?:G\s*\uD2B8\uB77C\uC774\uB358\uD2B8|G\.SKILL|CORSAIR|Samsung|SK\s*\uD558\uC774\uB2C9\uC2A4|Kingston|Crucial|TeamGroup|T-FORCE|ADATA|PNY|GeIL))/)
    .map((item) => item.trim())
    .filter(Boolean);
  return items.length > 1 ? items : [source];
}

onMounted(loadPlayer);
watch(username, loadPlayer);
</script>

<style scoped>
.spec-chip-list {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
}

.spec-chip {
  display: block;
  width: fit-content;
  max-width: 100%;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgba(23, 99, 125, 0.1);
  color: var(--clr-primary, #17637d);
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.45;
}

.spec-empty {
  font-size: 0.85rem;
  color: var(--clr-text-muted, #5a6b7e);
}
</style>
