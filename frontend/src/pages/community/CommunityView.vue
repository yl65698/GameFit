<template>
  <section class="content-stack">
    <RouterLink class="back-link" :to="`/games/${route.params.id}`">← 게임 상세로 돌아가기</RouterLink>

    <header class="community-hero panel">
      <div class="community-hero-info">
        <p class="eyebrow">게임 커뮤니티</p>
        <h1>{{ gameTitle || '커뮤니티' }}</h1>
      </div>
    </header>

    <div class="community-layout">
      <!-- 게시판 메인 -->
      <main class="community-main">

        <!-- 목록 뷰 -->
        <section v-if="viewMode === 'list'" class="panel board-panel">
          <div class="board-controls">
            <div class="board-category-filter">
              <button class="category-chip cat-all" :class="{ active: categoryFilter === '' }" @click="categoryFilter = ''">전체</button>
              <button
                v-for="cat in CATEGORIES"
                :key="cat"
                class="category-chip"
                :class="[categoryToneClass(cat), { active: categoryFilter === cat }]"
                @click="categoryFilter = cat"
              >{{ cat }}</button>
            </div>
            <div class="segmented-control">
              <button :class="{ active: boardMode === 'recent' }" @click="boardMode = 'recent'">최신순</button>
              <button :class="{ active: boardMode === 'popular' }" @click="boardMode = 'popular'">추천순</button>
            </div>
          </div>

          <p v-if="postsLoading" class="subtle board-empty">불러오는 중...</p>
          <p v-else-if="visiblePosts.length === 0" class="subtle board-empty">아직 게시글이 없습니다. 첫 번째 글을 작성해보세요.</p>

          <div v-else class="post-list">
            <article
              v-for="post in paginatedPosts"
              :key="post.id"
              class="post-card"
              @click="openPost(post)"
            >
              <div class="post-card-like">
                <button :class="['like-btn', { liked: post.is_liked }]" @click.stop="toggleLike(post.id)">
                  {{ post.is_liked ? '♥' : '♡' }}
                </button>
                <span class="like-count">{{ post.likes }}</span>
              </div>
              <div class="post-card-body">
                <div class="post-card-meta">
                  <span :class="['category-badge', categoryToneClass(post.category)]">{{ post.category }}</span>
                  <span class="post-author">{{ post.author }}</span>
                  <span class="post-dot">·</span>
                  <span class="post-time">{{ post.created_at }}</span>
                  <span class="post-dot">·</span>
                  <span class="post-comment-count">댓글 {{ post.comment_count || 0 }}</span>
                </div>
                <h3 class="post-card-title">{{ post.title }}</h3>
                <p class="post-card-preview">{{ post.body }}</p>
              </div>
            </article>
          </div>

          <div v-if="!postsLoading" class="board-footer">
            <div></div>
            <div class="board-pagination">
              <template v-if="totalPages > 1">
                <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--">‹</button>
                <button
                  v-for="n in totalPages"
                  :key="n"
                  class="page-btn"
                  :class="{ active: currentPage === n }"
                  @click="currentPage = n"
                >{{ n }}</button>
                <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">›</button>
              </template>
            </div>
            <div class="board-footer-end">
              <button class="primary-button" @click="openComposer">+ 글쓰기</button>
            </div>
          </div>
        </section>

        <!-- 작성 뷰 -->
        <section v-if="viewMode === 'compose'" class="panel post-editor">
          <div class="editor-header">
            <div>
              <h2>게시글 작성</h2>
              <p class="subtle">{{ gameTitle }} 게시판에 새 글을 남깁니다.</p>
            </div>
            <button class="secondary-button" @click="viewMode = 'list'">목록으로</button>
          </div>
          <div class="editor-fields">
            <label class="editor-label">
              말머리
              <select v-model="draft.category" class="editor-select">
                <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </label>
            <label class="editor-label editor-label--full">
              제목
              <input v-model="draft.title" placeholder="게시글 제목을 입력하세요." class="editor-input" />
            </label>
            <label class="editor-label editor-label--full">
              내용
              <textarea v-model="draft.body" placeholder="내용을 입력하세요." class="editor-textarea" />
            </label>
          </div>
          <div class="button-row">
            <button class="primary-button" :disabled="submitting" @click="submitPost">게시글 등록</button>
            <button class="secondary-button" @click="viewMode = 'list'">취소</button>
          </div>
        </section>

        <!-- 상세 뷰 -->
        <section v-if="viewMode === 'detail' && selectedPost" class="panel post-detail-panel">
          <button class="back-link post-back" @click="viewMode = 'list'">← 게시판으로 돌아가기</button>

          <div class="post-detail-head">
            <div class="post-title-row">
              <h2 class="post-detail-title">{{ selectedPost.title }}</h2>
              <span :class="['category-badge', categoryToneClass(selectedPost.category)]">{{ selectedPost.category }}</span>
            </div>
            <div class="post-author-row">
              <RouterLink :to="`/players/${selectedPost.author_username}`" class="post-author-avatar">
                <span class="user-avatar-sm">
                  <img v-if="selectedPost.author_avatar" :src="selectedPost.author_avatar" :alt="selectedPost.author" />
                  <template v-else>{{ (selectedPost.author || '?')[0] }}</template>
                </span>
              </RouterLink>
              <RouterLink :to="`/players/${selectedPost.author_username}`" class="post-author-name">{{ selectedPost.author }}</RouterLink>
              <span class="post-dot">·</span>
              <span class="post-time">{{ selectedPost.created_at }}</span>
            </div>
          </div>

          <p class="post-detail-body">{{ selectedPost.body }}</p>

          <div class="post-detail-actions">
            <button
              :class="['secondary-button', { 'like-active': selectedPost.is_liked }]"
              @click="toggleLike(selectedPost.id)"
            >
              {{ selectedPost.is_liked ? '♥ 추천 취소' : '♡ 추천' }} {{ selectedPost.likes }}
            </button>
            <button
              v-if="selectedPost.is_mine"
              class="secondary-button danger-soft-button"
              @click="deletePost(selectedPost.id)"
            >삭제</button>
          </div>

          <div class="comment-section">
            <h3 class="comment-section-title">댓글 {{ selectedPost.comments?.length || 0 }}</h3>
            <form v-if="auth.isAuthenticated" class="comment-writer" @submit.prevent="submitComment">
              <textarea v-model="commentText" placeholder="댓글을 입력하세요." class="comment-input" />
              <button class="secondary-button" :disabled="submitting">댓글 작성</button>
            </form>
            <p v-else class="subtle">댓글을 작성하려면 로그인하세요.</p>

            <div class="comment-list">
              <p v-if="!selectedPost.comments?.length" class="subtle">아직 댓글이 없습니다.</p>
              <article v-for="comment in paginatedComments" :key="comment.id" class="comment-item">
                <div class="comment-header">
                  <RouterLink :to="`/players/${comment.author_username}`">
                    <span class="user-avatar-sm">
                      <img v-if="comment.author_avatar" :src="comment.author_avatar" :alt="comment.author" />
                      <template v-else>{{ (comment.author || '?')[0] }}</template>
                    </span>
                  </RouterLink>
                  <RouterLink :to="`/players/${comment.author_username}`" class="comment-author">{{ comment.author }}</RouterLink>
                  <span class="comment-time">{{ comment.created_at }}</span>
                  <button v-if="comment.is_mine" class="comment-delete-btn" @click="deleteComment(comment.id)">삭제</button>
                </div>
                <p class="comment-body">{{ comment.body }}</p>
              </article>
            </div>

            <div v-if="commentTotalPages > 1" class="comment-pagination">
              <button class="page-btn" :disabled="commentPage <= 1" @click="commentPage--">‹</button>
              <button
                v-for="n in commentTotalPages"
                :key="n"
                class="page-btn"
                :class="{ active: commentPage === n }"
                @click="commentPage = n"
              >{{ n }}</button>
              <button class="page-btn" :disabled="commentPage >= commentTotalPages" @click="commentPage++">›</button>
            </div>
          </div>
        </section>
      </main>

      <!-- 그룹 사이드바 -->
      <aside class="community-sidebar">
        <section class="panel sidebar-section">
          <h2 class="sidebar-title">참여중인 그룹</h2>
          <div v-if="myGroups.length === 0" class="subtle sidebar-empty">아직 참여중인 그룹이 없습니다.</div>
          <div v-else class="my-group-list">
            <article
              v-for="group in myGroups"
              :key="group.id"
              class="my-group-card"
              @click="openGroup(group)"
            >
              <div class="my-group-info">
                <strong class="my-group-name">{{ group.name }}</strong>
                <span class="my-group-meta">{{ group.members }}/{{ group.capacity }}명 · {{ group.schedule || '일정 협의' }}</span>
              </div>
              <button class="secondary-button my-group-leave" @click.stop="leaveGroup(group.id)">나가기</button>
            </article>
          </div>
        </section>

        <section class="panel sidebar-section">
          <div class="sidebar-section-head">
            <h2 class="sidebar-title">그룹 탐색</h2>
            <button class="secondary-button sidebar-sm-btn" @click="showGroupCreator = !showGroupCreator">
              {{ showGroupCreator ? '닫기' : '그룹 만들기' }}
            </button>
          </div>

          <form v-if="showGroupCreator" class="group-create-form" @submit.prevent="createGroup">
            <input v-model="groupDraft.name" placeholder="그룹 이름 *" />
            <input v-model="groupDraft.schedule" placeholder="일정 예: 토 20:00" />
            <input v-model="groupDraft.style" placeholder="플레이 스타일" />
            <input v-model="groupDraft.role" placeholder="필요 역할" />
            <input v-model.number="groupDraft.capacity" type="number" min="2" max="20" placeholder="최대 인원" />
            <textarea v-model="groupDraft.description" placeholder="그룹 설명" />
            <button class="primary-button" :disabled="submitting">그룹 생성</button>
          </form>

          <div class="group-search-row">
            <input v-model="groupQuery" placeholder="그룹 검색..." />
          </div>

          <p v-if="groupsLoading" class="subtle sidebar-empty">불러오는 중...</p>
          <div class="group-search-list">
            <p v-if="!groupsLoading && filteredGroups.length === 0" class="subtle sidebar-empty">검색 결과가 없습니다.</p>
            <button
              v-for="group in filteredGroups"
              :key="group.id"
              class="group-result-item"
              @click="openGroup(group)"
            >
              <div class="group-result-head">
                <strong class="group-result-name">{{ group.name }}</strong>
                <span class="group-result-capacity">{{ group.members }}/{{ group.capacity }}명</span>
              </div>
              <span class="group-result-meta">{{ group.schedule || '일정 협의' }}{{ group.style ? ' · ' + group.style : '' }}</span>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <!-- 그룹 상세 모달 -->
    <div v-if="selectedGroup" class="modal-backdrop" @click.self="selectedGroup = null">
      <section class="group-detail-modal">
        <button class="modal-close" @click="selectedGroup = null">닫기</button>
        <p class="eyebrow">게임 그룹</p>
        <h2>{{ selectedGroup.name }}</h2>
        <p>{{ selectedGroup.description || '그룹 설명이 없습니다.' }}</p>
        <dl class="group-detail-dl">
          <div><dt>참여 인원</dt><dd>{{ selectedGroup.members }}/{{ selectedGroup.capacity }}명</dd></div>
          <div v-if="selectedGroup.schedule"><dt>일정</dt><dd>{{ selectedGroup.schedule }}</dd></div>
          <div v-if="selectedGroup.style"><dt>플레이 스타일</dt><dd>{{ selectedGroup.style }}</dd></div>
          <div v-if="selectedGroup.role"><dt>필요 역할</dt><dd>{{ selectedGroup.role }}</dd></div>
          <div>
            <dt>현재 구성원</dt>
            <dd class="group-member-chips">
              <RouterLink
                v-for="member in (selectedGroup.memberList || selectedGroup.memberNames.map(n => ({ name: n, username: n })))"
                :key="member.username"
                :to="`/players/${member.username}`"
                class="group-member-chip"
              >
                <span v-if="member.avatar" class="user-avatar-xs"><img :src="member.avatar" :alt="member.name" /></span>
                {{ member.name }}
              </RouterLink>
            </dd>
          </div>
        </dl>
        <div class="button-row">
          <button v-if="!selectedGroup.joined" class="primary-button" @click="joinGroup(selectedGroup.id)">그룹 참여</button>
          <button v-else class="secondary-button" @click="leaveGroup(selectedGroup.id)">그룹 나가기</button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import api from "../../services/api";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const auth = useAuthStore();

const gameId = computed(() => Number(route.params.id));
const gameTitle = ref("");
const postsLoading = ref(false);
const posts = ref([]);
const groups = ref([]);
const groupsLoading = ref(false);

const viewMode = ref("list");
const boardMode = ref("recent");
const categoryFilter = ref("");
const selectedPost = ref(null);
const selectedGroup = ref(null);
const groupQuery = ref("");
const commentText = ref("");
const showGroupCreator = ref(false);
const submitting = ref(false);

const draft = reactive({ category: "질문", title: "", body: "" });
const groupDraft = reactive({ name: "", schedule: "", style: "", role: "", capacity: 4, description: "" });

const CATEGORIES = ["공략", "질문", "구매상담", "그룹모집", "후기", "잡담", "기타"];
const CATEGORY_TONES = ["guide", "question", "purchase", "group", "review", "chat", "etc"];

const PAGE_SIZE = 10;
const currentPage = ref(1);

const COMMENT_PAGE_SIZE = 10;
const commentPage = ref(1);

const visiblePosts = computed(() => {
  let list = posts.value;
  if (categoryFilter.value) list = list.filter((p) => p.category === categoryFilter.value);
  if (boardMode.value === "popular") return [...list].sort((a, b) => b.likes - a.likes);
  return list;
});

const totalPages = computed(() => Math.max(1, Math.ceil(visiblePosts.value.length / PAGE_SIZE)));
const paginatedPosts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE;
  return visiblePosts.value.slice(start, start + PAGE_SIZE);
});

const paginatedComments = computed(() => {
  const comments = selectedPost.value?.comments ?? [];
  const start = (commentPage.value - 1) * COMMENT_PAGE_SIZE;
  return comments.slice(start, start + COMMENT_PAGE_SIZE);
});
const commentTotalPages = computed(() =>
  Math.max(1, Math.ceil((selectedPost.value?.comments?.length ?? 0) / COMMENT_PAGE_SIZE))
);

watch([categoryFilter, boardMode], () => { currentPage.value = 1; });

function categoryToneClass(category) {
  const index = CATEGORIES.indexOf(category);
  return `cat-${CATEGORY_TONES[index] || "etc"}`;
}

const myGroups = computed(() => groups.value.filter((g) => g.joined).slice(0, 5));
const filteredGroups = computed(() => {
  const q = groupQuery.value.trim().toLowerCase();
  const available = groups.value.filter((g) => !g.joined);
  const result = q
    ? available.filter((g) => [g.name, g.style, g.schedule, g.role].some((v) => (v || "").toLowerCase().includes(q)))
    : available;
  return result.slice(0, 10);
});

async function loadGame() {
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/`);
    gameTitle.value = data.title || "";
  } catch { gameTitle.value = ""; }
}

async function loadPosts() {
  postsLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/posts/`);
    posts.value = data;
  } catch { posts.value = []; }
  finally { postsLoading.value = false; }
}

async function loadGroups() {
  groupsLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/groups/`);
    groups.value = data;
  } catch { groups.value = []; }
  finally { groupsLoading.value = false; }
}

function openComposer() {
  if (!auth.isAuthenticated) { alert("로그인이 필요합니다."); return; }
  viewMode.value = "compose";
  selectedPost.value = null;
}

async function openPost(post) {
  commentPage.value = 1;
  viewMode.value = "detail";
  selectedPost.value = { ...post, comments: [] };
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/posts/${post.id}/`);
    selectedPost.value = data;
  } catch {}
}

async function submitPost() {
  const title = draft.title.trim();
  const body = draft.body.trim();
  if (!title || !body || submitting.value) return;
  submitting.value = true;
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/posts/`, {
      category: draft.category, title, body,
    });
    posts.value.unshift(data);
    draft.title = "";
    draft.body = "";
    selectedPost.value = { ...data, comments: [] };
    viewMode.value = "detail";
  } catch { alert("게시글 등록에 실패했습니다."); }
  finally { submitting.value = false; }
}

async function toggleLike(postId) {
  if (!auth.isAuthenticated) { alert("로그인이 필요합니다."); return; }
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/posts/${postId}/like/`);
    const p = posts.value.find((p) => p.id === postId);
    if (p) { p.likes = data.likes; p.is_liked = data.is_liked; }
    if (selectedPost.value?.id === postId) {
      selectedPost.value = { ...selectedPost.value, likes: data.likes, is_liked: data.is_liked };
    }
  } catch {}
}

async function deletePost(postId) {
  if (!confirm("게시글을 삭제하시겠습니까?")) return;
  try {
    await api.delete(`/catalog/games/${gameId.value}/community/posts/${postId}/`);
    posts.value = posts.value.filter((p) => p.id !== postId);
    viewMode.value = "list";
    selectedPost.value = null;
  } catch { alert("게시글 삭제에 실패했습니다."); }
}

async function submitComment() {
  const body = commentText.value.trim();
  if (!body || !selectedPost.value || submitting.value) return;
  submitting.value = true;
  try {
    const { data } = await api.post(
      `/catalog/games/${gameId.value}/community/posts/${selectedPost.value.id}/comments/`,
      { body },
    );
    const postId = selectedPost.value.id;
    selectedPost.value = {
      ...selectedPost.value,
      comments: [...(selectedPost.value.comments || []), data],
      comment_count: (selectedPost.value.comment_count || 0) + 1,
    };
    const p = posts.value.find((p) => p.id === postId);
    if (p) p.comment_count = (p.comment_count || 0) + 1;
    commentText.value = "";
  } catch { alert("댓글 등록에 실패했습니다."); }
  finally { submitting.value = false; }
}

async function deleteComment(commentId) {
  if (!selectedPost.value) return;
  try {
    await api.delete(`/catalog/games/${gameId.value}/community/comments/${commentId}/`);
    const postId = selectedPost.value.id;
    selectedPost.value = {
      ...selectedPost.value,
      comments: selectedPost.value.comments.filter((c) => c.id !== commentId),
      comment_count: Math.max(0, (selectedPost.value.comment_count || 1) - 1),
    };
    const p = posts.value.find((p) => p.id === postId);
    if (p) p.comment_count = Math.max(0, (p.comment_count || 1) - 1);
  } catch { alert("댓글 삭제에 실패했습니다."); }
}

function openGroup(group) { selectedGroup.value = group; }

async function createGroup() {
  const name = groupDraft.name.trim();
  if (!name || submitting.value) return;
  if (!auth.isAuthenticated) { alert("로그인이 필요합니다."); return; }
  submitting.value = true;
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/groups/`, {
      name,
      description: groupDraft.description.trim(),
      schedule: groupDraft.schedule.trim(),
      style: groupDraft.style.trim(),
      role: groupDraft.role.trim(),
      capacity: Number(groupDraft.capacity) || 4,
    });
    groups.value.unshift(data);
    Object.assign(groupDraft, { name: "", schedule: "", style: "", role: "", capacity: 4, description: "" });
    showGroupCreator.value = false;
  } catch { alert("그룹 생성에 실패했습니다."); }
  finally { submitting.value = false; }
}

async function joinGroup(groupId) {
  if (!auth.isAuthenticated) { alert("로그인이 필요합니다."); return; }
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/groups/${groupId}/join/`);
    const idx = groups.value.findIndex((g) => g.id === groupId);
    if (idx !== -1) groups.value[idx] = data;
    selectedGroup.value = data;
  } catch (err) { alert(err?.response?.data?.detail || "그룹 참여에 실패했습니다."); }
}

async function leaveGroup(groupId) {
  try {
    await api.delete(`/catalog/games/${gameId.value}/community/groups/${groupId}/leave/`);
    await loadGroups();
    selectedGroup.value = null;
  } catch { alert("그룹 나가기에 실패했습니다."); }
}

onMounted(() => {
  loadGame();
  loadPosts();
  loadGroups();
});
</script>

<style scoped>
/* 히어로 헤더 */
.community-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.community-hero-info p {
  margin: 0 0 6px;
  font-size: 15px;
  letter-spacing: 0.03em;
}

.community-hero-info h1 {
  margin: 0;
  font-size: 24px;
  letter-spacing: -0.02em;
}

/* 레이아웃 */
.community-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: start;
}

.community-main { display: grid; gap: 0; }

.community-sidebar {
  display: grid;
  gap: 16px;
  position: sticky;
  top: 74px;
}

/* 게시판 패널 */
.board-panel {
  padding: 0;
  overflow: hidden;
  gap: 0;
  display: block;
}

.board-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--clr-border, #d4dde8);
  flex-wrap: wrap;
}

.board-category-filter {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.category-chip {
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 999px;
  background: transparent;
  color: var(--clr-text-muted, #5a6b7e);
  padding: 5px 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.13s, color 0.13s, border-color 0.13s;
}

.category-chip:hover {
  border-color: var(--clr-primary, #17637d);
  color: var(--clr-primary, #17637d);
}

.category-chip.active {
  background: var(--clr-primary, #17637d);
  border-color: var(--clr-primary, #17637d);
  color: #fff;
}

.board-empty { padding: 2rem 20px; }

/* 게시글 카드 */
.post-list { display: grid; gap: 0; }

.post-card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--clr-border, #d4dde8);
  cursor: pointer;
  transition: background 0.12s;
}

.post-card:last-child { border-bottom: none; }
.post-card:hover { background: var(--clr-surface-soft, #f8fafc); }

.post-card-like {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 36px;
  padding-top: 2px;
}

.like-btn {
  border: none;
  background: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--clr-text-muted, #5a6b7e);
  padding: 0;
  transition: color 0.12s, transform 0.12s;
}

.like-btn:hover { transform: scale(1.2); }
.like-btn.liked { color: #c0392b; }

.like-count {
  font-size: 13px;
  font-weight: 700;
  color: var(--clr-text-muted, #5a6b7e);
}

.post-card-body { flex: 1; min-width: 0; }

.post-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.post-author { font-size: 13px; font-weight: 700; color: var(--clr-text, #1c2430); }
.post-time, .post-comment-count { font-size: 12px; color: var(--clr-text-muted, #5a6b7e); }
.post-dot { color: var(--clr-border, #d4dde8); font-size: 12px; }

.post-card-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: var(--clr-heading, #0f1923);
  line-height: 1.3;
}

.post-card-preview {
  margin: 0;
  font-size: 13px;
  color: var(--clr-text-muted, #5a6b7e);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 카테고리 배지 */
.category-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--clr-control, #e4eaf3);
  color: var(--clr-text-muted, #5a6b7e);
}

/* 게시판 하단 (페이지네이션 + 글쓰기) */
.board-footer {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 14px 20px;
  border-top: 1px solid var(--clr-border, #d4dde8);
}

.board-footer-end {
  display: flex;
  justify-content: flex-end;
}

.board-pagination {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
}

.page-btn {
  min-width: 34px;
  height: 34px;
  padding: 0 8px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 6px;
  background: transparent;
  color: var(--clr-text, #1c2430);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s, color 0.12s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--clr-primary, #17637d);
  color: var(--clr-primary, #17637d);
}

.page-btn.active {
  background: var(--clr-primary, #17637d);
  border-color: var(--clr-primary, #17637d);
  color: #fff;
}

.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 작성 폼 */
.post-editor { display: grid; gap: 20px; }

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
}

.editor-header h2 { margin: 0 0 4px; }

.editor-fields {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 14px;
}

.editor-label {
  display: grid;
  gap: 6px;
  font-weight: 700;
  font-size: 13px;
  color: var(--clr-text-muted, #5a6b7e);
}

.editor-label--full { grid-column: 1 / -1; }

.editor-select {
  padding: 10px 12px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: var(--clr-surface, #fff);
  color: var(--clr-text, #1c2430);
  font: inherit;
}

.editor-input { width: 100%; }
.editor-textarea { min-height: 160px; resize: vertical; }

/* 게시글 상세 */
.post-detail-panel { display: grid; gap: 20px; }

.post-back { background: none; border: none; padding: 0; }

.post-detail-head { display: grid; gap: 10px; }

.post-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.post-detail-title {
  margin: 0;
  font-size: 28px;
  letter-spacing: -0.02em;
}

.post-author-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-author-avatar, .post-author-name { text-decoration: none; color: inherit; }
.post-author-name { font-weight: 700; font-size: 14px; }
.post-author-name:hover { text-decoration: underline; }

.post-detail-body {
  font-size: 15px;
  line-height: 1.7;
  color: var(--clr-text, #1c2430);
  white-space: pre-wrap;
  margin: 0;
  border-top: 1px solid var(--clr-border, #d4dde8);
  border-bottom: 1px solid var(--clr-border, #d4dde8);
  padding: 20px 0;
}

.post-detail-actions { display: flex; gap: 8px; }
.like-active { color: #c0392b !important; }

/* 댓글 */
.comment-section { display: grid; gap: 14px; }

.comment-section-title {
  margin: 0;
  font-size: 15px;
  border-bottom: 1px solid var(--clr-border, #d4dde8);
  padding-bottom: 10px;
}

.comment-writer { display: grid; gap: 8px; }
.comment-input { min-height: 80px; resize: vertical; }

.comment-list { display: grid; gap: 8px; }

.comment-item {
  padding: 14px 16px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: transparent;
}

.comment-item:last-child { border-bottom: 1px solid var(--clr-border, #d4dde8); }

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.comment-author { font-weight: 700; font-size: 14px; text-decoration: none; color: inherit; }
.comment-author:hover { text-decoration: underline; }

.comment-time {
  font-size: 12px;
  color: var(--clr-text-muted, #5a6b7e);
  margin-left: auto;
}

.comment-delete-btn {
  border: 1px solid #e0c0c0;
  border-radius: 6px;
  background: none;
  padding: 2px 8px;
  font-size: 12px;
  color: #c0392b;
  cursor: pointer;
}

.comment-body {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--clr-text, #1c2430);
}

.comment-pagination {
  display: flex;
  gap: 4px;
  justify-content: center;
  padding-top: 12px;
}

/* 사이드바 */
.sidebar-section { padding: 16px; }
.sidebar-title { margin: 0; font-size: 15px; }
.sidebar-empty { padding: 8px 0; font-size: 13px; }

.sidebar-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sidebar-sm-btn { padding: 6px 10px; font-size: 12px; min-height: 32px; }

/* 내 그룹 */
.my-group-list { display: grid; gap: 8px; margin-top: 10px; }

.my-group-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: var(--theme-card-radius, 10px);
  cursor: pointer;
  transition: border-color 0.13s;
}

.my-group-card:hover { border-color: var(--clr-primary, #17637d); }
.my-group-info { display: grid; gap: 3px; flex: 1; min-width: 0; }
.my-group-name { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.my-group-meta { font-size: 12px; color: var(--clr-text-muted, #5a6b7e); }
.my-group-leave { padding: 4px 8px; font-size: 12px; min-height: 28px; flex-shrink: 0; }

/* 그룹 검색 */
.group-search-row { margin: 10px 0 8px; }
.group-search-list { display: grid; gap: 6px; }

.group-result-item {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: var(--theme-card-radius, 10px);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.13s, background 0.12s;
}

.group-result-item:hover {
  border-color: var(--clr-primary, #17637d);
  background: var(--clr-surface-soft, #f8fafc);
}

.group-result-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.group-result-name { font-size: 14px; font-weight: 700; }
.group-result-capacity { font-size: 12px; font-weight: 700; color: var(--clr-primary, #17637d); flex-shrink: 0; }
.group-result-meta { font-size: 12px; color: var(--clr-text-muted, #5a6b7e); }

/* 그룹 생성 폼 */
.group-create-form {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
  padding: 12px;
  background: var(--clr-surface-soft, #f8fafc);
  border-radius: var(--theme-card-radius, 10px);
  border: 1px solid var(--clr-border, #d4dde8);
}

.group-create-form input,
.group-create-form textarea { font-size: 13px; padding: 8px 10px; }
.group-create-form textarea { min-height: 60px; }

/* 그룹 상세 모달 */
.group-detail-dl { display: grid; gap: 10px; margin: 0 0 16px; }

.group-detail-dl > div {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 6px;
  align-items: start;
}

.group-detail-dl dt { font-weight: 700; font-size: 13px; color: var(--clr-text-muted, #5a6b7e); }
.group-detail-dl dd { margin: 0; font-size: 14px; }

.group-member-chips { display: flex; flex-wrap: wrap; gap: 6px; }

.group-member-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 999px;
  font-size: 13px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.13s;
}

.group-member-chip:hover { border-color: var(--clr-primary, #17637d); }

/* 아바타 */
.user-avatar-sm {
  width: 28px;
  height: 28px;
  min-width: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #17637d, #5cb8b2);
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  display: grid;
  place-items: center;
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar-sm img { width: 100%; height: 100%; object-fit: cover; }

.user-avatar-xs {
  width: 20px;
  height: 20px;
  min-width: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #17637d, #5cb8b2);
  color: #fff;
  font-size: 10px;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.user-avatar-xs img { width: 100%; height: 100%; object-fit: cover; }
</style>
