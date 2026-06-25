<template>
  <section class="content-stack">
    <RouterLink class="back-link" to="/games">← 게임 목록으로 돌아가기</RouterLink>

    <div v-if="loading" class="panel" style="text-align:center;padding:2rem">프로필을 불러오는 중...</div>
    <div v-else-if="error" class="panel" style="text-align:center;padding:2rem">{{ error }}</div>

    <template v-else-if="player">

      <!-- 플레이어 히어로 -->
      <article class="panel player-hero">
        <div class="avatar avatar--photo avatar--large">
          <img v-if="player.avatar_url" :src="player.avatar_url" alt="프로필 사진" />
          <span v-else>{{ initial }}</span>
        </div>
        <div class="player-identity">
          <h1>{{ player.nickname || player.username }}</h1>
          <p class="player-username">@{{ player.username }}</p>
          <div v-if="player.hashtags?.length" class="hashtag-chips">
            <span v-for="tag in player.hashtags" :key="tag" class="hashtag-chip">#{{ tag }}</span>
          </div>
        </div>
        <div class="player-hero-actions">
          <div class="player-social-row">
            <button class="player-stat-btn" @click="showSocial('followers')">
              <strong>{{ followerCount.toLocaleString("ko-KR") }}</strong>
              <span>팔로워</span>
            </button>
            <button class="player-stat-btn" @click="showSocial('following')">
              <strong>{{ (player.following_list?.length ?? 0).toLocaleString("ko-KR") }}</strong>
              <span>팔로잉</span>
            </button>
          </div>
          <button
            v-if="auth.isAuthenticated && player.id !== auth.user?.id"
            :class="isFollowing ? 'secondary-button' : 'primary-button'"
            :disabled="followLoading"
            class="player-follow-btn"
            @click="toggleFollow"
          >
            {{ isFollowing ? "✓ 팔로잉" : "+ 팔로우" }}
          </button>
        </div>
      </article>

      <!-- 남긴 의견 + 장비 정보 50/50 -->
      <div class="player-bottom-row">

        <!-- 남긴 의견 -->
        <div class="detail-panel">
          <div class="panel-heading">
            <h2>남긴 의견</h2>
          </div>
          <div v-if="reviewsLoading" class="subtle" style="padding:0.5rem 0">불러오는 중...</div>
          <div v-else-if="playerReviews.length === 0" class="subtle" style="padding:0.5rem 0">아직 남긴 의견이 없습니다.</div>
          <div v-else class="my-review-list">
            <div v-for="review in pagedReviews" :key="review.id" class="my-review-card">
              <div class="my-review-game">
                <img v-if="review.game_image_url" :src="review.game_image_url" class="my-review-thumb" alt="" />
                <div v-else class="my-review-thumb-placeholder" />
                <RouterLink class="my-review-game-title" :to="`/games/${review.game_id}`">{{ review.game_title }}</RouterLink>
                <span :class="['my-review-badge', review.recommend ? 'good' : 'bad']">{{ review.recommend ? "추천" : "비추천" }}</span>
              </div>
              <p class="my-review-content">{{ review.content }}</p>
              <time class="my-review-date">{{ formatDate(review.created_at) }}</time>
            </div>
          </div>
          <div v-if="reviewTotalPages > 1" class="pagination">
            <button v-for="p in reviewTotalPages" :key="p" :class="['page-btn', { active: p === reviewPage }]" @click="reviewPage = p">{{ p }}</button>
          </div>
        </div>

        <!-- 장비 정보 -->
        <div class="detail-panel">
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
        </div>
      </div>

      <!-- 보유 게임 -->
      <section class="panel">
        <div class="panel-heading">
          <h2>보유 게임 <span class="heading-count">{{ player.owned_games?.length ?? 0 }}</span></h2>
          <div class="segmented-control">
            <button :class="{ active: ownedView === 'card' }" @click="ownedView = 'card'">카드</button>
            <button :class="{ active: ownedView === 'list' }" @click="ownedView = 'list'">리스트</button>
          </div>
        </div>
        <div v-if="!ownedGames.length" class="subtle" style="padding:0.5rem 0">등록된 보유 게임이 없습니다.</div>
        <div :class="ownedView === 'card' ? 'game-strip' : 'profile-list'">
          <RouterLink
            v-for="game in pagedOwnedGames"
            :key="game.id"
            :class="ownedView === 'card' ? 'game-cover' : 'profile-list-item'"
            :to="`/games/${game.id}`"
          >
            <img v-if="game.image_url && ownedView === 'card'" :src="game.image_url" :alt="game.title" class="game-cover-img" />
            <span>{{ game.title }}</span>
            <small>{{ platformLabel[game.platform] || game.platform || "기타" }}</small>
          </RouterLink>
        </div>
        <div v-if="ownedTotalPages > 1" class="pagination">
          <button v-for="p in ownedTotalPages" :key="p" :class="['page-btn', { active: p === ownedPage }]" @click="ownedPage = p">{{ p }}</button>
        </div>
      </section>

      <!-- 관심 게임 -->
      <section class="panel">
        <div class="panel-heading">
          <h2>관심 게임 <span class="heading-count">{{ player.interested_games?.length ?? 0 }}</span></h2>
          <div class="segmented-control">
            <button :class="{ active: interestView === 'card' }" @click="interestView = 'card'">카드</button>
            <button :class="{ active: interestView === 'list' }" @click="interestView = 'list'">리스트</button>
          </div>
        </div>
        <div v-if="!interestedGames.length" class="subtle" style="padding:0.5rem 0">등록된 관심 게임이 없습니다.</div>
        <div :class="interestView === 'card' ? 'game-strip' : 'profile-list'">
          <RouterLink
            v-for="game in pagedInterestedGames"
            :key="game.id"
            :class="interestView === 'card' ? 'game-cover' : 'profile-list-item'"
            :to="`/games/${game.id}`"
          >
            <img v-if="game.image_url && interestView === 'card'" :src="game.image_url" :alt="game.title" class="game-cover-img" />
            <span>{{ game.title }}</span>
          </RouterLink>
        </div>
        <div v-if="interestTotalPages > 1" class="pagination">
          <button v-for="p in interestTotalPages" :key="p" :class="['page-btn', { active: p === interestPage }]" @click="interestPage = p">{{ p }}</button>
        </div>
      </section>

      <!-- 팔로워/팔로잉 모달 -->
      <div v-if="socialModal" class="modal-backdrop" @click.self="socialModal = ''">
        <section class="social-modal">
          <button class="modal-close" @click="socialModal = ''">닫기</button>
          <p class="eyebrow">{{ player?.nickname || player?.username }}</p>
          <h2>{{ socialModal === "followers" ? "팔로워" : "팔로잉" }}</h2>
          <div class="social-list">
            <RouterLink v-for="user in visibleSocialUsers" :key="user.id" :to="`/players/${user.username}`" @click="socialModal = ''">
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
import api from "../../services/api";

const route = useRoute();
const auth = useAuthStore();

const platformLabel = {
  steam: "Steam", epic: "Epic Games", ubisoft: "Ubisoft",
  gog: "GOG", origin: "EA/Origin", battlenet: "Battle.net", other: "기타",
};

const player = ref(null);
const loading = ref(false);
const error = ref("");
const socialModal = ref("");
const followLoading = ref(false);

const ownedView = ref("card");
const interestView = ref("card");

const username = computed(() => route.params.username);
const initial = computed(() => (player.value?.nickname || player.value?.username || "?").slice(0, 1).toUpperCase());
const isFollowing = computed(() => player.value?.is_following ?? false);
const followerCount = ref(0);

const PAGE_SIZE = 14;
const ownedPage = ref(1);
const interestPage = ref(1);

const ownedGames = computed(() => player.value?.owned_games || []);
const interestedGames = computed(() => player.value?.interested_games || []);

const ownedTotalPages = computed(() => Math.max(1, Math.ceil(ownedGames.value.length / PAGE_SIZE)));
const pagedOwnedGames = computed(() => {
  const start = (ownedPage.value - 1) * PAGE_SIZE;
  return ownedGames.value.slice(start, start + PAGE_SIZE);
});

const interestTotalPages = computed(() => Math.max(1, Math.ceil(interestedGames.value.length / PAGE_SIZE)));
const pagedInterestedGames = computed(() => {
  const start = (interestPage.value - 1) * PAGE_SIZE;
  return interestedGames.value.slice(start, start + PAGE_SIZE);
});

const visibleSocialUsers = computed(() => {
  if (!player.value) return [];
  return socialModal.value === "followers"
    ? (player.value.followers_list || [])
    : (player.value.following_list || []);
});

// 리뷰
const playerReviews = ref([]);
const reviewsLoading = ref(false);
const reviewPage = ref(1);
const REVIEW_PAGE_SIZE = 3;
const reviewTotalPages = computed(() => Math.max(1, Math.ceil(playerReviews.value.length / REVIEW_PAGE_SIZE)));
const pagedReviews = computed(() => {
  const start = (reviewPage.value - 1) * REVIEW_PAGE_SIZE;
  return playerReviews.value.slice(start, start + REVIEW_PAGE_SIZE);
});

async function fetchPlayerReviews() {
  if (!player.value?.id) return;
  reviewsLoading.value = true;
  try {
    const { data } = await api.get(`/games/reviews/user/${player.value.id}/`);
    playerReviews.value = data;
  } catch {
    playerReviews.value = [];
  } finally {
    reviewsLoading.value = false;
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("ko-KR", { year: "numeric", month: "short", day: "numeric" });
}

async function loadPlayer() {
  if (!username.value) return;
  loading.value = true;
  error.value = "";
  try {
    player.value = await auth.fetchUserByUsername(username.value);
    followerCount.value = player.value.followers_count ?? 0;
    fetchPlayerReviews();
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

function showSocial(type) { socialModal.value = type; }

function specLabel(key) {
  return { cpu: "CPU", memory: "메모리", gpu: "GPU", storage: "저장공간", vr: "VR", console: "콘솔" }[key] || key;
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
  return String(value ?? "").trim()
    .replace(/^\[\s*/, "").replace(/\s*\]$/, "")
    .replace(/^["']|["']$/g, "").trim();
}

function parseArrayText(text) {
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed.map(normalizeSpecText).filter(Boolean);
  } catch {}
  const quotedItems = [...text.matchAll(/["']([^"']+)["']/g)].map((m) => normalizeSpecText(m[1]));
  return quotedItems.filter(Boolean);
}

function splitMemoryText(text) {
  const source = normalizeSpecText(text);
  const items = source
    .split(/(?=(?:G\s*트라이던트|G\.SKILL|CORSAIR|Samsung|SK\s*하이닉스|Kingston|Crucial|TeamGroup|T-FORCE|ADATA|PNY|GeIL))/)
    .map((item) => item.trim()).filter(Boolean);
  return items.length > 1 ? items : [source];
}

onMounted(loadPlayer);
watch(username, loadPlayer);
</script>

<style scoped>
/* 히어로 */
.player-hero {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 20px 28px;
  align-items: start;
}

.player-identity {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 4px;
}

.player-identity h1 { margin: 0; font-size: 28px; letter-spacing: -0.02em; }

.player-username {
  margin: 0;
  font-size: 14px;
  color: var(--clr-text-muted, #5a6b7e);
}

.player-hero-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
  min-width: 180px;
}

.player-social-row {
  display: flex;
  gap: 8px;
}

.player-stat-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 10px 18px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 12px;
  background: var(--clr-surface-soft, #f8fafc);
  cursor: pointer;
  transition: border-color 0.13s, background 0.13s;
  min-width: 76px;
}

.player-stat-btn:hover {
  border-color: var(--clr-primary, #17637d);
  background: rgba(23, 99, 125, 0.06);
}

.player-stat-btn strong {
  font-size: 18px;
  font-weight: 800;
  color: var(--clr-heading, #0f1923);
  line-height: 1;
}

.player-stat-btn span {
  font-size: 11px;
  font-weight: 600;
  color: var(--clr-text-muted, #5a6b7e);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.player-follow-btn {
  width: 100%;
  font-size: 14px;
}

/* 히어로 아바타 */
.avatar--large {
  width: 130px;
  height: 130px;
  min-width: 130px;
  flex: 0 0 130px;
  font-size: 50px;
  align-self: start;
}

/* 의견 + 장비 50/50 */
.player-bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

/* 게임 개수 배지 */
.heading-count {
  font-size: 12px;
  font-weight: 700;
  color: var(--clr-primary, #17637d);
  background: rgba(23, 99, 125, 0.1);
  padding: 2px 8px;
  border-radius: 999px;
  vertical-align: middle;
}

/* 게임 7열 */
.game-strip {
  grid-template-columns: repeat(7, 1fr);
}

/* 스펙 칩 */
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

/* 리뷰 카드 */
.my-review-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.my-review-card {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 10px;
}

.my-review-game {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.my-review-thumb {
  width: 36px;
  height: 36px;
  border-radius: 5px;
  object-fit: cover;
  flex-shrink: 0;
}

.my-review-thumb-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 5px;
  background: var(--clr-border, #d4dde8);
  flex-shrink: 0;
}

.my-review-game-title {
  font-size: 0.95rem;
  font-weight: 700;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.my-review-badge {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.my-review-badge.good { background: rgba(26, 122, 74, 0.12); color: #1a7a4a; }
.my-review-badge.bad  { background: rgba(192, 57, 43, 0.1);  color: #c0392b; }

.my-review-content {
  font-size: 0.875rem;
  color: #3a4a5e;
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.my-review-date {
  font-size: 0.78rem;
  color: var(--clr-text-muted, #5a6b7e);
}

/* 게임 커버 이미지 */
.game-cover-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  opacity: 0.55;
}

/* 페이지네이션 */
.pagination {
  display: flex;
  gap: 0.4rem;
  justify-content: center;
  margin-top: 1.25rem;
  flex-wrap: wrap;
}

.page-btn {
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.5rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 6px;
  background: transparent;
  color: var(--clr-text-muted, #5a6b7e);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}

.page-btn:hover {
  background: rgba(23, 99, 125, 0.07);
  border-color: var(--clr-primary, #17637d);
  color: var(--clr-primary, #17637d);
}

.page-btn.active {
  background: var(--clr-primary, #17637d);
  border-color: var(--clr-primary, #17637d);
  color: #fff;
  font-weight: 600;
}
</style>
