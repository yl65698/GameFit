<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow page-title-eyebrow">내 프로필</p>
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
          <div class="hashtag-chips card-hashtags">
            <span v-for="tag in (profile.hashtags?.length ? profile.hashtags : ['전략', '협동', '인디'])" :key="tag" class="hashtag-chip">#{{ tag }}</span>
          </div>
          <div class="stat-row">
            <button @click="openSocialModal('following')">
              <strong>{{ profile.following_count ?? followingUsers.length }}</strong>
              <span>팔로잉</span>
            </button>
            <button @click="openSocialModal('followers')">
              <strong>{{ (profile.followers_count ?? followerUsers.length).toLocaleString("ko-KR") }}</strong>
              <span>팔로워</span>
            </button>
            <button class="search-user-btn" title="유저 검색" @click="openSearchModal">
              <span class="search-icon">🔍</span>
              <span>유저 검색</span>
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
            <dd>
              <template v-if="Array.isArray(value) && value.length">
                <span v-for="(m, i) in value" :key="i" class="spec-chip">{{ m }}</span>
              </template>
              <template v-else-if="!Array.isArray(value) && value && value !== '없음'">
                <span class="spec-chip">{{ value }}</span>
              </template>
              <template v-else>
                <span class="spec-empty">미등록</span>
              </template>
            </dd>
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
      <div v-if="filteredOwnedGames.length === 0" class="subtle" style="padding: 0.5rem 0;">등록된 보유 게임이 없습니다.</div>
      <div :class="ownedView === 'card' ? 'game-strip' : 'profile-list'">
        <RouterLink
          v-for="game in pagedOwnedGames"
          :key="game.id"
          :class="ownedView === 'card' ? 'game-cover' : 'profile-list-item'"
          :to="gameDetailPath(game)"
        >
          <img v-if="game.image_url && ownedView === 'card'" :src="game.image_url" :alt="game.title" class="game-cover-img" />
          <span>{{ game.title }}</span>
          <small>{{ gamePlatform(game) }}</small>
        </RouterLink>
      </div>
      <div v-if="ownedTotalPages > 1" class="pagination">
        <button
          v-for="p in ownedTotalPages"
          :key="p"
          :class="['page-btn', { active: p === ownedPage }]"
          @click="ownedPage = p"
        >{{ p }}</button>
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
      <div v-if="interestedGames.length === 0" class="subtle" style="padding: 0.5rem 0;">등록된 관심 게임이 없습니다.</div>
      <div :class="interestView === 'card' ? 'game-strip' : 'profile-list'">
        <RouterLink
          v-for="game in pagedInterestedGames"
          :key="game.id"
          :class="interestView === 'card' ? 'game-cover' : 'profile-list-item'"
          :to="gameDetailPath(game)"
        >
          <img v-if="game.image_url && interestView === 'card'" :src="game.image_url" :alt="game.title" class="game-cover-img" />
          <span>{{ game.title }}</span>
        </RouterLink>
      </div>
      <div v-if="interestTotalPages > 1" class="pagination">
        <button
          v-for="p in interestTotalPages"
          :key="p"
          :class="['page-btn', { active: p === interestPage }]"
          @click="interestPage = p"
        >{{ p }}</button>
      </div>
    </section>

    <!-- 내가 남긴 의견 -->
    <section class="panel">
      <div class="panel-heading">
        <h2>내가 남긴 의견</h2>
      </div>
      <div v-if="myReviewsLoading" class="subtle" style="padding: 0.5rem 0;">불러오는 중...</div>
      <div v-else-if="myReviews.length === 0" class="subtle" style="padding: 0.5rem 0;">아직 남긴 의견이 없습니다.</div>
      <div v-else class="my-review-list">
        <div v-for="review in pagedMyReviews" :key="review.id" class="my-review-card">
          <div class="my-review-game">
            <img v-if="review.game_image_url" :src="review.game_image_url" class="my-review-thumb" alt="" />
            <div v-else class="my-review-thumb-placeholder" />
            <RouterLink class="my-review-game-title" :to="`/games/${review.game_id}`">
              {{ review.game_title }}
            </RouterLink>
            <span :class="['my-review-badge', review.recommend ? 'good' : 'bad']">
              {{ review.recommend ? "추천" : "비추천" }}
            </span>
            <button class="my-review-delete-btn" @click="deleteMyReview(review)">삭제</button>
          </div>
          <p class="my-review-content">{{ review.content }}</p>
          <time class="my-review-date">{{ formatDate(review.created_at) }}</time>
        </div>
      </div>
      <div v-if="myReviewTotalPages > 1" class="pagination">
        <button
          v-for="p in myReviewTotalPages"
          :key="p"
          :class="['page-btn', { active: p === myReviewPage }]"
          @click="myReviewPage = p"
        >{{ p }}</button>
      </div>
    </section>

    <!-- 팔로워/팔로잉 모달 -->
    <div v-if="socialModal" class="modal-backdrop" @click.self="socialModal = ''">
      <section class="social-modal">
        <button class="modal-close" @click="socialModal = ''">닫기</button>
        <p class="eyebrow">내 프로필</p>
        <h2>{{ socialModal === "followers" ? "팔로워" : "팔로잉" }}</h2>
        <div class="social-list">
          <RouterLink v-for="user in visibleSocialUsers" :key="user.id" :to="`/players/${user.username}`" @click="socialModal = ''">
            <span class="avatar avatar--small">
              <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.nickname" />
              <template v-else>{{ (user.nickname || user.username).slice(0, 1).toUpperCase() }}</template>
            </span>
            <strong>{{ user.nickname || user.username }}</strong>
          </RouterLink>
          <p v-if="visibleSocialUsers.length === 0" class="subtle" style="padding: 1rem 0;">아직 아무도 없습니다.</p>
        </div>
      </section>
    </div>

    <!-- 유저 검색 모달 -->
    <div v-if="searchModal" class="modal-backdrop" @click.self="closeSearchModal">
      <section class="social-modal user-search-modal">
        <button class="modal-close" @click="closeSearchModal">닫기</button>
        <p class="eyebrow">플레이어 찾기</p>
        <h2>유저 검색</h2>
        <div class="user-search-input-row">
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            class="user-search-input"
            placeholder="닉네임 또는 아이디로 검색"
            @input="onSearchInput"
          />
        </div>
        <div class="social-list user-search-results">
          <p v-if="searchLoading" class="subtle" style="padding: 1rem 0;">검색 중...</p>
          <p v-else-if="searchQuery && searchResults.length === 0" class="subtle" style="padding: 1rem 0;">검색 결과가 없습니다.</p>
          <p v-else-if="!searchQuery" class="subtle" style="padding: 1rem 0;">닉네임 또는 아이디를 입력하세요.</p>
          <div v-for="user in searchResults" :key="user.id" class="user-search-result-row">
            <RouterLink :to="`/players/${user.username}`" class="user-search-result-info" @click="closeSearchModal">
              <span class="avatar avatar--small">
                <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.nickname" />
                <template v-else>{{ (user.nickname || user.username).slice(0, 1).toUpperCase() }}</template>
              </span>
              <div class="user-search-result-text">
                <strong>{{ user.nickname || user.username }}</strong>
                <span class="subtle">@{{ user.username }}</span>
              </div>
            </RouterLink>
            <button
              :class="followStates[user.id] ? 'secondary-button' : 'primary-button'"
              :disabled="followLoadingStates[user.id]"
              class="user-search-follow-btn"
              @click="toggleSearchFollow(user)"
            >
              {{ followStates[user.id] ? "팔로잉" : "팔로우" }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "../../stores/auth";
import api from "../../services/api";

const auth = useAuthStore();
const ownedView = ref("card");
const interestView = ref("card");
const socialModal = ref("");
const searchModal = ref(false);
const searchQuery = ref("");
const searchResults = ref([]);
const searchLoading = ref(false);
const searchInputRef = ref(null);
const followStates = reactive({});
const followLoadingStates = reactive({});
let searchTimer = null;

const platforms = [
  { label: "Steam", value: "steam" },
  { label: "Epic Games", value: "epic" },
  { label: "Ubisoft", value: "ubisoft" },
  { label: "그 외", value: "other" },
];
const selectedPlatforms = ref(platforms.map((p) => p.value));
const profile = computed(() => auth.user || {});
const initial = computed(() => (profile.value.nickname || profile.value.username || "G").slice(0, 1));
const PAGE_SIZE = 21; // 7열 × 3행
const ownedPage = ref(1);
const interestPage = ref(1);

const ownedGames = computed(() => profile.value.owned_games || []);
const filteredOwnedGames = computed(() => {
  ownedPage.value = 1; // 필터 바뀌면 첫 페이지로
  return ownedGames.value.filter((game) => {
    const p = game.platform || "other";
    if (selectedPlatforms.value.includes(p)) return true;
    if (selectedPlatforms.value.includes("other") && !["steam", "epic", "ubisoft"].includes(p)) return true;
    return false;
  });
});
const ownedTotalPages = computed(() => Math.ceil(filteredOwnedGames.value.length / PAGE_SIZE));
const pagedOwnedGames = computed(() => {
  const start = (ownedPage.value - 1) * PAGE_SIZE;
  return filteredOwnedGames.value.slice(start, start + PAGE_SIZE);
});

const interestedGames = computed(() => profile.value.interested_games || []);
const interestTotalPages = computed(() => Math.ceil(interestedGames.value.length / PAGE_SIZE));
const pagedInterestedGames = computed(() => {
  const start = (interestPage.value - 1) * PAGE_SIZE;
  return interestedGames.value.slice(start, start + PAGE_SIZE);
});

const followerUsers = computed(() => profile.value.followers_list || []);
const followingUsers = computed(() => profile.value.following_list || []);
const visibleSocialUsers = computed(() =>
  socialModal.value === "followers" ? followerUsers.value : followingUsers.value,
);

const myReviews = ref([]);
const myReviewsLoading = ref(false);
const myReviewPage = ref(1);
const MY_REVIEW_PAGE_SIZE = 5;
const myReviewTotalPages = computed(() => Math.ceil(myReviews.value.length / MY_REVIEW_PAGE_SIZE));
const pagedMyReviews = computed(() => {
  const start = (myReviewPage.value - 1) * MY_REVIEW_PAGE_SIZE;
  return myReviews.value.slice(start, start + MY_REVIEW_PAGE_SIZE);
});

async function fetchMyReviews() {
  myReviewsLoading.value = true;
  try {
    const { data } = await api.get("/games/reviews/mine/");
    myReviews.value = data;
  } catch {
    myReviews.value = [];
  } finally {
    myReviewsLoading.value = false;
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("ko-KR", { year: "numeric", month: "short", day: "numeric" });
}

async function deleteMyReview(review) {
  try {
    await api.delete(`/games/${review.game_id}/reviews/delete/`);
    myReviews.value = myReviews.value.filter((r) => r.id !== review.id);
    if (myReviewPage.value > myReviewTotalPages.value && myReviewPage.value > 1) {
      myReviewPage.value--;
    }
  } catch {
    // 실패 시 조용히 무시
  }
}

onMounted(() => {
  auth.fetchProfile();
  fetchMyReviews();
});

function specLabel(key) {
  return {
    cpu: "CPU",
    memory: "메모리",
    gpu: "GPU",
    storage: "저장장치",
    vr: "VR",
    console: "콘솔",
  }[key] || key;
}

const platformLabel = {
  steam: "Steam",
  epic: "Epic Games",
  ubisoft: "Ubisoft",
  gog: "GOG",
  origin: "EA/Origin",
  battlenet: "Battle.net",
  other: "기타",
};

function gamePlatform(game) {
  return platformLabel[game.platform] || game.platform || "기타";
}

function gameDetailPath(game) {
  return `/games/${game.id}`;
}

function interestAlertLabel(game) {
  const alerts = profile.value.interest_alerts || {};
  const isOn = alerts[game.title] ?? true;
  return isOn ? "끄기" : "할인 알림 키기";
}

function openSocialModal(type) {
  socialModal.value = type;
}

async function openSearchModal() {
  searchModal.value = true;
  searchQuery.value = "";
  searchResults.value = [];
  await nextTick();
  searchInputRef.value?.focus();
}

function closeSearchModal() {
  searchModal.value = false;
  searchQuery.value = "";
  searchResults.value = [];
  clearTimeout(searchTimer);
}

function onSearchInput() {
  clearTimeout(searchTimer);
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  searchLoading.value = true;
  searchTimer = setTimeout(async () => {
    try {
      const results = await auth.searchUsers(searchQuery.value.trim());
      searchResults.value = results;
      const myFollowingIds = new Set((profile.value.following_list || []).map((u) => u.id));
      results.forEach((user) => {
        if (!(user.id in followStates)) {
          followStates[user.id] = user.is_following ?? myFollowingIds.has(user.id);
        }
      });
    } catch (e) {
      console.error("유저 검색 오류:", e);
    } finally {
      searchLoading.value = false;
    }
  }, 300);
}

async function toggleSearchFollow(user) {
  if (followLoadingStates[user.id]) return;
  followLoadingStates[user.id] = true;
  try {
    const result = await auth.followUser(user.id);
    followStates[user.id] = result.followed;
    await auth.fetchProfile();
  } catch (e) {
    console.error("팔로우 처리 오류:", e);
  } finally {
    followLoadingStates[user.id] = false;
  }
}
</script>

<style scoped>
.page-title-eyebrow {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.search-user-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.7rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 6px;
  background: transparent;
  color: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s;
}
.search-user-btn:hover {
  background: rgba(23, 99, 125, 0.07);
}
.search-icon {
  font-size: 0.9rem;
}

.user-search-modal {
  width: min(480px, 90vw);
}
.user-search-input-row {
  margin: 0.75rem 0;
}
.user-search-input {
  width: 100%;
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: #ffffff;
  color: #1c2430;
  font-size: 0.95rem;
  box-sizing: border-box;
}
.user-search-input::placeholder {
  color: var(--clr-text-muted, #5a6b7e);
}
.user-search-input:focus {
  outline: none;
  border-color: var(--clr-primary, #17637d);
  box-shadow: 0 0 0 2px rgba(23, 99, 125, 0.15);
}
.user-search-results {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 340px;
  overflow-y: auto;
}
.user-search-result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--clr-border, #d4dde8);
}
.user-search-result-row:last-child {
  border-bottom: none;
}
.user-search-result-info {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
  color: inherit;
  flex: 1;
  min-width: 0;
}
.user-search-result-info:hover strong {
  text-decoration: underline;
}
.user-search-result-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}
.user-search-result-text strong {
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-search-result-text .subtle {
  font-size: 0.8rem;
}
.user-search-follow-btn {
  flex-shrink: 0;
  padding: 0.3rem 0.8rem;
  font-size: 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--clr-primary, #17637d);
}

/* ── 스펙 칩 ── */
.spec-chip {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgba(23, 99, 125, 0.1);
  color: var(--clr-primary, #17637d);
  font-size: 0.82rem;
  font-weight: 600;
  margin: 0.1rem 0.2rem 0.1rem 0;
}

.spec-empty {
  font-size: 0.85rem;
  color: var(--clr-text-muted, #5a6b7e);
}

/* ── 내가 남긴 의견 ── */
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
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.14s, border-color 0.14s;
}

.my-review-card:hover {
  border-color: var(--clr-primary, #17637d);
  box-shadow: 0 3px 12px rgba(23, 99, 125, 0.1);
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

.my-review-badge.good {
  background: rgba(26, 122, 74, 0.12);
  color: #1a7a4a;
}

.my-review-badge.bad {
  background: rgba(192, 57, 43, 0.1);
  color: #c0392b;
}

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

.my-review-delete-btn {
  margin-left: auto;
  background: none;
  border: 1px solid #e0c0c0;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.78rem;
  color: #c0392b;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.12s;
}

.my-review-delete-btn:hover {
  background: #fdf0ef;
}

/* 게임 커버에 이미지가 있을 때 배경 덮어쓰기 */
.game-cover-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  opacity: 0.55;
}

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
