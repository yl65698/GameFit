<template>
  <section class="content-stack">
    <RouterLink class="back-link" :to="`/games/${route.params.id}`">게임 상세로 돌아가기</RouterLink>

    <header class="page-header community-header">
      <div>
        <p class="eyebrow">게임 커뮤니티</p>
        <h1>{{ gameTitle || '커뮤니티' }} 게시판</h1>
      </div>
      <div class="panel-actions">
        <button class="primary-button" @click="openComposer">글쓰기</button>
      </div>
    </header>

    <div class="community-layout">
      <main class="community-board">

        <!-- List View -->
        <section v-if="viewMode === 'list'" class="panel board-panel">
          <div class="board-toolbar">
            <div>
              <h2>{{ boardMode === 'popular' ? '인기글' : '게시글' }}</h2>
              <p>{{ boardMode === 'popular' ? '추천 수가 높은 글부터 보여줘요.' : '최근 올라온 글을 확인해요.' }}</p>
            </div>
            <div class="segmented-control">
              <button :class="{ active: boardMode === 'recent' }" @click="boardMode = 'recent'">최신순</button>
              <button :class="{ active: boardMode === 'popular' }" @click="boardMode = 'popular'">추천순</button>
            </div>
          </div>

          <div class="board-category-filter">
            <button class="category-chip" :class="{ active: categoryFilter === '' }" @click="categoryFilter = ''">전체</button>
            <button
              v-for="cat in CATEGORIES"
              :key="cat"
              class="category-chip"
              :class="{ active: categoryFilter === cat }"
              @click="categoryFilter = cat"
            >{{ cat }}</button>
          </div>

          <p v-if="postsLoading" class="subtle">불러오는 중...</p>
          <p v-else-if="visiblePosts.length === 0" class="subtle">아직 게시글이 없습니다. 첫 번째 글을 작성해보세요.</p>

          <article
            v-for="post in visiblePosts"
            :key="post.id"
            class="board-post-card"
            @click="openPost(post)"
          >
            <div class="post-vote-box">
              <button :class="['vote-btn', { liked: post.is_liked }]" @click.stop="toggleLike(post.id)">
                {{ post.is_liked ? '♥' : '♡' }}
              </button>
              <strong>{{ post.likes }}</strong>
            </div>
            <div>
              <div class="post-meta">
                <span :class="`post-category-badge cat-${post.category}`">{{ post.category }}</span>
                <span>{{ post.author }}</span>
                <span>{{ post.created_at }}</span>
                <span>댓글 {{ post.comment_count || 0 }}</span>
              </div>
              <h3>{{ post.title }}</h3>
              <p>{{ post.body }}</p>
            </div>
          </article>
        </section>

        <!-- Compose View -->
        <section v-if="viewMode === 'compose'" class="panel post-editor">
          <div class="board-toolbar">
            <div>
              <h2>게시글 작성</h2>
              <p>{{ gameTitle }} 게시판에 새 글을 남깁니다.</p>
            </div>
            <button class="secondary-button" @click="viewMode = 'list'">목록</button>
          </div>
          <label>
            말머리
            <select v-model="draft.category">
              <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </label>
          <label>
            제목
            <input v-model="draft.title" placeholder="게시글 제목" />
          </label>
          <label>
            내용
            <textarea v-model="draft.body" placeholder="내용을 입력하세요." />
          </label>
          <div class="button-row">
            <button class="primary-button" :disabled="submitting" @click="submitPost">게시글 등록</button>
            <button class="secondary-button" @click="viewMode = 'list'">취소</button>
          </div>
        </section>

        <!-- Detail View -->
        <section v-if="viewMode === 'detail' && selectedPost" class="panel post-detail">
          <button class="back-link post-back-button" @click="viewMode = 'list'">← 게시판으로 돌아가기</button>

          <div class="post-detail-heading">
            <span :class="`post-category-badge cat-${selectedPost.category}`">{{ selectedPost.category }}</span>
            <h2>{{ selectedPost.title }}</h2>
            <div class="post-author-row">
              <RouterLink :to="`/players/${selectedPost.author_username}`" class="post-author-avatar-link">
                <span class="user-avatar-sm">
                  <img v-if="selectedPost.author_avatar" :src="selectedPost.author_avatar" :alt="selectedPost.author" />
                  <template v-else>{{ (selectedPost.author || '?')[0] }}</template>
                </span>
              </RouterLink>
              <RouterLink :to="`/players/${selectedPost.author_username}`" class="post-author-name">{{ selectedPost.author }}</RouterLink>
              <span class="post-meta-sep">·</span>
              <span class="post-date">{{ selectedPost.created_at }}</span>
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
              class="secondary-button post-delete-btn"
              @click="deletePost(selectedPost.id)"
            >삭제</button>
          </div>

          <form v-if="auth.isAuthenticated" class="comment-writer" @submit.prevent="submitComment">
            <textarea v-model="commentText" placeholder="댓글을 입력하세요." />
            <button class="secondary-button" :disabled="submitting">댓글 쓰기</button>
          </form>
          <p v-else class="subtle">댓글을 작성하려면 로그인하세요.</p>

          <div class="comment-list">
            <p v-if="!selectedPost.comments?.length" class="subtle">아직 댓글이 없습니다.</p>
            <article v-for="comment in selectedPost.comments" :key="comment.id">
              <div class="comment-header">
                <RouterLink :to="`/players/${comment.author_username}`" class="comment-avatar-link">
                  <span class="user-avatar-sm">
                    <img v-if="comment.author_avatar" :src="comment.author_avatar" :alt="comment.author" />
                    <template v-else>{{ (comment.author || '?')[0] }}</template>
                  </span>
                </RouterLink>
                <RouterLink :to="`/players/${comment.author_username}`" class="comment-author-link">{{ comment.author }}</RouterLink>
                <span class="comment-time">{{ comment.created_at }}</span>
                <button v-if="comment.is_mine" class="comment-delete-btn" @click="deleteComment(comment.id)">삭제</button>
              </div>
              <p>{{ comment.body }}</p>
            </article>
          </div>
        </section>

      </main>

      <!-- Group Sidebar -->
      <aside class="panel group-panel">
        <section class="community-group-section">
          <h2>내가 참여중인 그룹</h2>
          <article
            v-for="group in myGroups"
            :key="group.id"
            class="group-card group-card-button joined"
            @click="openGroup(group)"
          >
            <button class="group-card-main" @click.stop="openGroup(group)">
              <strong>{{ group.name }}</strong>
              <span>{{ group.members }}/{{ group.capacity }}명</span>
              <small>{{ group.schedule || '일정 협의' }}</small>
            </button>
            <button class="secondary-button group-leave-button" @click.stop="leaveGroup(group.id)">그룹 나가기</button>
          </article>
          <p v-if="myGroups.length === 0" class="subtle">아직 참여중인 그룹이 없습니다.</p>
        </section>

        <section class="community-group-section">
          <div class="group-section-heading">
            <h2>그룹 탐색</h2>
            <button class="secondary-button" @click="showGroupCreator = !showGroupCreator">
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
            <input v-model="groupQuery" placeholder="그룹 검색" />
          </div>
          <p v-if="groupsLoading" class="subtle">불러오는 중...</p>
          <div class="group-list-grid group-list-grid--side">
            <p v-if="!groupsLoading && filteredGroups.length === 0" class="subtle">검색 결과가 없습니다.</p>
            <button
              v-for="group in filteredGroups"
              :key="group.id"
              class="group-result-card"
              @click="openGroup(group)"
            >
              <strong>{{ group.name }}</strong>
              <span>{{ group.members }}/{{ group.capacity }}명 참여중</span>
              <small>{{ group.schedule || '일정 협의' }}{{ group.style ? ' · ' + group.style : '' }}</small>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <!-- Group Detail Modal -->
    <div v-if="selectedGroup" class="modal-backdrop" @click.self="selectedGroup = null">
      <section class="group-detail-modal">
        <button class="modal-close" @click="selectedGroup = null">닫기</button>
        <p class="eyebrow">게임 그룹</p>
        <h2>{{ selectedGroup.name }}</h2>
        <p>{{ selectedGroup.description || '그룹 설명이 없습니다.' }}</p>
        <dl>
          <div>
            <dt>참여 인원</dt>
            <dd>{{ selectedGroup.members }}/{{ selectedGroup.capacity }}명</dd>
          </div>
          <div v-if="selectedGroup.schedule">
            <dt>일정</dt>
            <dd>{{ selectedGroup.schedule }}</dd>
          </div>
          <div v-if="selectedGroup.style">
            <dt>플레이 스타일</dt>
            <dd>{{ selectedGroup.style }}</dd>
          </div>
          <div v-if="selectedGroup.role">
            <dt>필요 역할</dt>
            <dd>{{ selectedGroup.role }}</dd>
          </div>
          <div>
            <dt>현재 구성원</dt>
            <dd>
              <RouterLink
                v-for="member in (selectedGroup.memberList || selectedGroup.memberNames.map(n => ({ name: n, username: n })))"
                :key="member.username"
                :to="`/players/${member.username}`"
                class="group-member-chip group-member-chip-link"
              >
                <span v-if="member.avatar" class="user-avatar-xs">
                  <img :src="member.avatar" :alt="member.name" />
                </span>
                {{ member.name }}
              </RouterLink>
            </dd>
          </div>
        </dl>
        <button v-if="!selectedGroup.joined" class="primary-button" @click="joinGroup(selectedGroup.id)">그룹 참여</button>
        <button v-else class="secondary-button" @click="leaveGroup(selectedGroup.id)">그룹 나가기</button>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
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

const visiblePosts = computed(() => {
  let list = posts.value;
  if (categoryFilter.value) {
    list = list.filter((p) => p.category === categoryFilter.value);
  }
  if (boardMode.value === "popular") {
    return [...list].sort((a, b) => b.likes - a.likes);
  }
  return list;
});

const myGroups = computed(() => groups.value.filter((g) => g.joined));
const filteredGroups = computed(() => {
  const q = groupQuery.value.trim().toLowerCase();
  const available = groups.value.filter((g) => !g.joined);
  if (!q) return available;
  return available.filter((g) =>
    [g.name, g.style, g.schedule, g.role].some((v) => (v || "").toLowerCase().includes(q)),
  );
});

async function loadGame() {
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/`);
    gameTitle.value = data.title || "";
  } catch {
    gameTitle.value = "";
  }
}

async function loadPosts() {
  postsLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/posts/`);
    posts.value = data;
  } catch {
    posts.value = [];
  } finally {
    postsLoading.value = false;
  }
}

async function loadGroups() {
  groupsLoading.value = true;
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/groups/`);
    groups.value = data;
  } catch {
    groups.value = [];
  } finally {
    groupsLoading.value = false;
  }
}

function openComposer() {
  if (!auth.isAuthenticated) {
    alert("로그인이 필요합니다.");
    return;
  }
  viewMode.value = "compose";
  selectedPost.value = null;
}

async function openPost(post) {
  viewMode.value = "detail";
  selectedPost.value = { ...post, comments: [] };
  try {
    const { data } = await api.get(`/catalog/games/${gameId.value}/community/posts/${post.id}/`);
    selectedPost.value = data;
  } catch {
    // keep partial data
  }
}

async function submitPost() {
  const title = draft.title.trim();
  const body = draft.body.trim();
  if (!title || !body || submitting.value) return;
  submitting.value = true;
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/posts/`, {
      category: draft.category,
      title,
      body,
    });
    posts.value.unshift(data);
    draft.title = "";
    draft.body = "";
    selectedPost.value = { ...data, comments: [] };
    viewMode.value = "detail";
  } catch {
    alert("게시글 등록에 실패했습니다.");
  } finally {
    submitting.value = false;
  }
}

async function toggleLike(postId) {
  if (!auth.isAuthenticated) {
    alert("로그인이 필요합니다.");
    return;
  }
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/posts/${postId}/like/`);
    const p = posts.value.find((p) => p.id === postId);
    if (p) {
      p.likes = data.likes;
      p.is_liked = data.is_liked;
    }
    if (selectedPost.value?.id === postId) {
      selectedPost.value = { ...selectedPost.value, likes: data.likes, is_liked: data.is_liked };
    }
  } catch {
    // silently fail
  }
}

async function deletePost(postId) {
  if (!confirm("게시글을 삭제하시겠습니까?")) return;
  try {
    await api.delete(`/catalog/games/${gameId.value}/community/posts/${postId}/`);
    posts.value = posts.value.filter((p) => p.id !== postId);
    viewMode.value = "list";
    selectedPost.value = null;
  } catch {
    alert("게시글 삭제에 실패했습니다.");
  }
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
  } catch {
    alert("댓글 등록에 실패했습니다.");
  } finally {
    submitting.value = false;
  }
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
  } catch {
    alert("댓글 삭제에 실패했습니다.");
  }
}

function openGroup(group) {
  selectedGroup.value = group;
}

async function createGroup() {
  const name = groupDraft.name.trim();
  if (!name || submitting.value) return;
  if (!auth.isAuthenticated) {
    alert("로그인이 필요합니다.");
    return;
  }
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
  } catch {
    alert("그룹 생성에 실패했습니다.");
  } finally {
    submitting.value = false;
  }
}

async function joinGroup(groupId) {
  if (!auth.isAuthenticated) {
    alert("로그인이 필요합니다.");
    return;
  }
  try {
    const { data } = await api.post(`/catalog/games/${gameId.value}/community/groups/${groupId}/join/`);
    const idx = groups.value.findIndex((g) => g.id === groupId);
    if (idx !== -1) groups.value[idx] = data;
    selectedGroup.value = data;
  } catch (err) {
    const msg = err?.response?.data?.detail || "그룹 참여에 실패했습니다.";
    alert(msg);
  }
}

async function leaveGroup(groupId) {
  try {
    await api.delete(`/catalog/games/${gameId.value}/community/groups/${groupId}/leave/`);
    await loadGroups();
    selectedGroup.value = null;
  } catch {
    alert("그룹 나가기에 실패했습니다.");
  }
}

onMounted(() => {
  loadGame();
  loadPosts();
  loadGroups();
});
</script>
