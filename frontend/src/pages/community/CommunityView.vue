<template>
  <section class="content-stack">
    <RouterLink class="back-link" :to="`/games/${route.params.id}`">게임 상세로 돌아가기</RouterLink>

    <header class="page-header community-header">
      <div>
        <p class="eyebrow">게임 커뮤니티</p>
        <h1>{{ gameTitle }} 게시판</h1>
        <p class="subtle">게임 공략, 구매 타이밍, 같이 할 그룹을 한 곳에서 확인합니다.</p>
      </div>
      <div class="panel-actions">
        <button class="primary-button" @click="openComposer">글쓰기</button>
      </div>
    </header>

    <div class="community-layout">
      <main class="community-board">
        <section v-if="viewMode === 'list'" class="panel board-panel">
          <div class="board-toolbar">
            <div>
              <h2>{{ boardMode === "popular" ? "인기글" : "게시글" }}</h2>
              <p>{{ boardMode === "popular" ? "추천 수가 높은 글부터 보여줘요." : "최근 올라온 글을 확인해요." }}</p>
            </div>
            <div class="segmented-control">
              <button :class="{ active: boardMode === 'recent' }" @click="boardMode = 'recent'">최신순</button>
              <button :class="{ active: boardMode === 'popular' }" @click="boardMode = 'popular'">추천순</button>
            </div>
          </div>

          <article v-for="post in visiblePosts" :key="post.id" class="board-post-card" @click="openPost(post)">
            <div class="post-vote-box">
              <button @click.stop="recommendPost(post.id)">추천</button>
              <strong>{{ post.recommendations }}</strong>
            </div>
            <div>
              <div class="post-meta">
                <span>{{ post.category }}</span>
                <span>{{ post.author }}</span>
                <span>{{ post.createdAt }}</span>
              </div>
              <h3>{{ post.title }}</h3>
              <p>{{ post.body }}</p>
            </div>
          </article>
        </section>

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
              <option>공략</option>
              <option>질문</option>
              <option>구매상담</option>
              <option>그룹모집</option>
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
            <button class="primary-button" @click="submitPost">게시글 등록</button>
            <button class="secondary-button" @click="viewMode = 'list'">취소</button>
          </div>
        </section>

        <section v-if="viewMode === 'detail' && selectedPost" class="panel post-detail">
          <button class="back-link post-back-button" @click="viewMode = 'list'">← 게시판으로 돌아가기</button>
          <div class="post-detail-heading">
            <span>{{ selectedPost.category }}</span>
            <h2>{{ selectedPost.title }}</h2>
            <p>{{ selectedPost.author }} · {{ selectedPost.createdAt }}</p>
          </div>
          <p class="post-detail-body">{{ selectedPost.body }}</p>
          <button class="primary-button" @click="recommendPost(selectedPost.id)">
            추천 {{ selectedPost.recommendations }}
          </button>

          <form class="comment-writer" @submit.prevent="submitComment">
            <textarea v-model="commentText" placeholder="댓글을 입력하세요." />
            <button class="secondary-button">댓글 쓰기</button>
          </form>

          <div class="comment-list">
            <article v-for="comment in selectedPost.comments" :key="comment.id">
              <strong>{{ comment.author }}</strong>
              <p>{{ comment.body }}</p>
            </article>
          </div>
        </section>

      </main>

      <aside class="panel group-panel">
        <section class="community-group-section">
          <h2>내가 참여중인 그룹</h2>
          <article v-for="group in myGroups" :key="group.id" class="group-card group-card-button joined" @click="openGroup(group)">
            <button class="group-card-main" @click="openGroup(group)">
              <strong>{{ group.name }}</strong>
              <span>{{ group.members }}/{{ group.capacity }}명</span>
              <small>{{ group.schedule }}</small>
            </button>
            <button class="secondary-button group-leave-button" @click.stop="leaveGroup(group.id)">그룹 나가기</button>
          </article>
          <p v-if="myGroups.length === 0" class="subtle">아직 참여중인 그룹이 없습니다.</p>
        </section>

        <section class="community-group-section">
          <div class="group-section-heading">
            <h2>그룹 탐색</h2>
            <button class="secondary-button" @click="showGroupCreator = !showGroupCreator">
              {{ showGroupCreator ? "닫기" : "그룹 만들기" }}
            </button>
          </div>
          <form v-if="showGroupCreator" class="group-create-form" @submit.prevent="createGroup">
            <input v-model="groupDraft.name" placeholder="그룹 이름" />
            <input v-model="groupDraft.schedule" placeholder="일정 예: 토 20:00" />
            <input v-model="groupDraft.style" placeholder="플레이 스타일" />
            <input v-model="groupDraft.role" placeholder="필요 역할" />
            <input v-model.number="groupDraft.capacity" type="number" min="2" max="12" placeholder="최대 인원" />
            <textarea v-model="groupDraft.description" placeholder="그룹 설명" />
            <button class="primary-button">그룹 생성</button>
          </form>
          <div class="group-search-row">
            <input v-model="groupQuery" placeholder="그룹 검색" />
            <button class="secondary-button">검색</button>
          </div>
          <div class="group-list-grid group-list-grid--side">
            <button v-for="group in filteredGroups" :key="group.id" class="group-result-card" @click="openGroup(group)">
              <strong>{{ group.name }}</strong>
              <span>{{ group.members }}/{{ group.capacity }}명 참여중</span>
              <small>{{ group.schedule }} · {{ group.style }}</small>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="selectedGroup" class="modal-backdrop" @click.self="selectedGroup = null">
      <section class="group-detail-modal">
        <button class="modal-close" @click="selectedGroup = null">닫기</button>
        <p class="eyebrow">게임 그룹</p>
        <h2>{{ selectedGroup.name }}</h2>
        <p>{{ selectedGroup.description }}</p>
        <dl>
          <div>
            <dt>참여 인원</dt>
            <dd>{{ selectedGroup.members }}/{{ selectedGroup.capacity }}명</dd>
          </div>
          <div>
            <dt>일정</dt>
            <dd>{{ selectedGroup.schedule }}</dd>
          </div>
          <div>
            <dt>플레이 스타일</dt>
            <dd>{{ selectedGroup.style }}</dd>
          </div>
          <div>
            <dt>필요 역할</dt>
            <dd>{{ selectedGroup.role }}</dd>
          </div>
          <div>
            <dt>현재 구성원</dt>
            <dd>
              <span v-for="member in selectedGroup.memberNames" :key="member" class="group-member-chip">{{ member }}</span>
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
const viewMode = ref("list");
const boardMode = ref("recent");
const posts = ref([]);
const selectedPostId = ref(null);
const selectedGroup = ref(null);
const groupQuery = ref("");
const commentText = ref("");
const showGroupCreator = ref(false);
const draft = reactive({
  category: "질문",
  title: "",
  body: "",
});
const groupDraft = reactive({
  name: "",
  schedule: "",
  style: "",
  role: "",
  capacity: 4,
  description: "",
});

const gameTitles = {
  1: "Civilization VII",
  2: "It Takes Two",
  3: "Hades II",
};
const gameTitle = computed(() => gameTitles[route.params.id] || "GameFit");
const selectedPost = computed(() => posts.value.find((post) => post.id === selectedPostId.value));
const visiblePosts = computed(() => {
  const sorted = [...posts.value];
  if (boardMode.value === "popular") {
    return sorted.sort((a, b) => b.recommendations - a.recommendations);
  }
  return sorted.sort((a, b) => b.id - a.id);
});
const gameGroups = computed(() => groups.value.filter((group) => group.gameId === Number(route.params.id)));
const myGroups = computed(() => gameGroups.value.filter((group) => group.joined));
const filteredGroups = computed(() => {
  const query = groupQuery.value.trim().toLowerCase();
  const availableGroups = gameGroups.value.filter((group) => !group.joined);
  if (!query) return availableGroups;
  return availableGroups.filter((group) =>
    [group.name, group.style, group.schedule, group.role].some((value) => value.toLowerCase().includes(query)),
  );
});

const groups = ref([
  {
    id: 1,
    gameId: 1,
    name: "평일 밤 전략 테이블",
    members: 3,
    capacity: 5,
    joined: true,
    schedule: "화/목 22:00",
    style: "느긋한 전략 플레이",
    role: "외교 담당 1명",
    description: "초보도 참여 가능한 장기 전략 그룹입니다. 한 판을 여러 번 나눠서 진행합니다.",
    memberNames: ["admin", "strategy_admin", "turn_master"],
  },
  {
    id: 2,
    gameId: 1,
    name: "빠른 정복전 파티",
    members: 2,
    capacity: 4,
    joined: false,
    schedule: "토 20:00",
    style: "공격적인 진행",
    role: "초반 러시 가능 유저",
    description: "짧은 시간 안에 승부를 보는 정복전 위주 그룹입니다.",
    memberNames: ["rush_leader", "early_push"],
  },
  {
    id: 3,
    gameId: 2,
    name: "주말 협동 클리어",
    members: 1,
    capacity: 2,
    joined: true,
    schedule: "일 15:00",
    style: "스토리 몰입",
    role: "파트너 1명",
    description: "처음부터 엔딩까지 같이 진행할 협동 플레이어를 찾습니다.",
    memberNames: ["admin"],
  },
  {
    id: 4,
    gameId: 3,
    name: "보스 패턴 연구방",
    members: 6,
    capacity: 8,
    joined: false,
    schedule: "상시",
    style: "공략 공유",
    role: "빌드 추천 가능 유저",
    description: "무기 조합과 보스 패턴을 공유하는 공략 중심 그룹입니다.",
    memberNames: ["build_note", "boss_reader", "dash_main", "nyx_route", "weapon_lab", "mirror_pick"],
  },
]);

onMounted(async () => {
  const { data } = await api.get(`/catalog/games/${route.params.id}/community/`);
  posts.value = [
    ...data.map((post, index) => ({
      ...post,
      category: index % 2 === 0 ? "후기" : "구매상담",
      author: index % 2 === 0 ? "spec_checker" : "sale_watcher",
      createdAt: index % 2 === 0 ? "오늘" : "어제",
      recommendations: 12 - index * 3,
      comments: [
        { id: `${post.id}-1`, author: "admin", body: "좋은 정보 고마워요." },
      ],
    })),
    {
      id: 900 + Number(route.params.id),
      game_id: Number(route.params.id),
      category: "그룹모집",
      title: `${gameTitle.value} 같이 할 사람 구해요`,
      body: "이번 주말에 같이 플레이할 그룹원을 찾고 있어요. 부담 없이 들어오면 됩니다.",
      author: "party_maker",
      createdAt: "방금",
      recommendations: 18,
      comments: [],
    },
  ];
});

function openComposer() {
  viewMode.value = "compose";
  selectedPostId.value = null;
}

function openPost(post) {
  selectedPostId.value = post.id;
  viewMode.value = "detail";
}

function submitPost() {
  const title = draft.title.trim();
  const body = draft.body.trim();
  if (!title || !body) return;
  const post = {
    id: Date.now(),
    game_id: Number(route.params.id),
    category: draft.category,
    title,
    body,
    author: auth.user?.nickname || auth.user?.username || "me",
    createdAt: "방금",
    recommendations: 0,
    comments: [],
  };
  posts.value.unshift(post);
  draft.title = "";
  draft.body = "";
  viewMode.value = "detail";
  selectedPostId.value = post.id;
}

function recommendPost(postId) {
  const post = posts.value.find((item) => item.id === postId);
  if (!post) return;
  post.recommendations += 1;
}

function submitComment() {
  const body = commentText.value.trim();
  if (!body || !selectedPost.value) return;
  selectedPost.value.comments.push({
    id: Date.now(),
    author: auth.user?.nickname || auth.user?.username || "me",
    body,
  });
  commentText.value = "";
}

function openGroup(group) {
  selectedGroup.value = group;
}

function currentMemberName() {
  return auth.user?.nickname || auth.user?.username || "admin";
}

function joinGroup(groupId) {
  const group = groups.value.find((item) => item.id === groupId);
  if (!group || group.joined || group.members >= group.capacity) return;
  const memberName = currentMemberName();
  group.joined = true;
  if (!group.memberNames.includes(memberName)) {
    group.memberNames = [...group.memberNames, memberName];
  }
  group.members = group.memberNames.length;
  selectedGroup.value = null;
}

function leaveGroup(groupId) {
  const group = groups.value.find((item) => item.id === groupId);
  if (!group) return;
  group.joined = false;
  group.memberNames = group.memberNames.filter((member) => member !== currentMemberName());
  group.members = Math.max(0, group.memberNames.length || group.members - 1);
  if (group.members === 0) {
    groups.value = groups.value.filter((item) => item.id !== groupId);
  }
  if (selectedGroup.value?.id === groupId) {
    selectedGroup.value = null;
  }
}

function createGroup() {
  const name = groupDraft.name.trim();
  if (!name) return;
  const memberName = currentMemberName();
  groups.value.unshift({
    id: Date.now(),
    gameId: Number(route.params.id),
    name,
    members: 1,
    capacity: Number(groupDraft.capacity) || 4,
    joined: true,
    schedule: groupDraft.schedule.trim() || "일정 협의",
    style: groupDraft.style.trim() || "자유 플레이",
    role: groupDraft.role.trim() || "함께할 플레이어",
    description: groupDraft.description.trim() || "새로 만들어진 게임 그룹입니다.",
    memberNames: [memberName],
  });
  groupDraft.name = "";
  groupDraft.schedule = "";
  groupDraft.style = "";
  groupDraft.role = "";
  groupDraft.capacity = 4;
  groupDraft.description = "";
  showGroupCreator.value = false;
}
</script>
