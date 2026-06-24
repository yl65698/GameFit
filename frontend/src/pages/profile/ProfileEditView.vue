<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">프로필 수정</p>
        <h1>{{ activeTitle }}</h1>
      </div>
      <button class="primary-button" :disabled="saving" @click="save">
        {{ saving ? "저장 중..." : "저장" }}
      </button>
    </header>
    <p v-if="saveError" class="save-error-msg">{{ saveError }}</p>

    <div class="settings-layout">
      <aside class="settings-menu">
        <button :class="{ active: activeTab === 'basic' }" @click="activeTab = 'basic'">기본 설정</button>
        <button :class="{ active: activeTab === 'pc' }" @click="activeTab = 'pc'">내 컴퓨터</button>
        <button :class="{ active: activeTab === 'games' }" @click="activeTab = 'games'">보유 및 관심 게임</button>
      </aside>

      <form class="panel edit-panel" @submit.prevent="save">

        <!-- ── 기본 설정 ── -->
        <template v-if="activeTab === 'basic'">
          <div class="basic-grid">

            <!-- 왼쪽: 사진 · 닉네임 · 비밀번호 -->
            <div class="basic-left">

              <!-- 프로필 사진 -->
              <div class="basic-section">
                <p class="section-label">프로필 사진</p>
                <div class="avatar-row">
                  <div class="avatar-preview">
                    <img v-if="avatarPreview" :src="avatarPreview" alt="프로필 사진 미리보기" />
                    <span v-else class="avatar-empty">사진 없음</span>
                  </div>
                  <div class="avatar-actions">
                    <label class="file-btn secondary-button">
                      사진 변경
                      <input type="file" accept="image/*" class="hidden-file" @change="handleAvatarChange" />
                    </label>
                    <button v-if="avatarPreview" type="button" class="text-btn danger" @click="clearAvatar">사진 지우기</button>
                  </div>
                </div>
              </div>

              <div class="divider" />

              <!-- 닉네임 -->
              <div class="basic-section">
                <p class="section-label">닉네임</p>
                <input class="field-input" v-model="draft.nickname" placeholder="닉네임 입력" />
              </div>

              <div class="divider" />

              <!-- 비밀번호 변경 -->
              <div class="basic-section">
                <p class="section-label">비밀번호 변경</p>
                <div class="field-stack">
                  <div class="field-row">
                    <span class="field-label">현재 비밀번호</span>
                    <input class="field-input" v-model="pwForm.current" type="password" autocomplete="current-password" placeholder="현재 비밀번호" />
                  </div>
                  <div class="field-row">
                    <span class="field-label">새 비밀번호 <em class="hint-text">8자 이상</em></span>
                    <input class="field-input" v-model="pwForm.next" type="password" autocomplete="new-password" placeholder="새 비밀번호" />
                  </div>
                  <div class="field-row">
                    <span class="field-label">새 비밀번호 확인</span>
                    <input class="field-input" v-model="pwForm.confirm" type="password" autocomplete="new-password" placeholder="새 비밀번호 확인" />
                  </div>
                </div>
                <p v-if="pwError" class="pw-error">{{ pwError }}</p>
                <p v-if="pwSuccess" class="pw-success">{{ pwSuccess }}</p>
                <button
                  type="button"
                  class="secondary-button"
                  :disabled="pwSaving || !pwForm.current || !pwForm.next"
                  @click="changePassword"
                >{{ pwSaving ? "변경 중..." : "비밀번호 변경" }}</button>
              </div>

            </div>

            <!-- 세로 구분선 -->
            <div class="vertical-divider" />

            <!-- 오른쪽: 해시태그 -->
            <div class="basic-right">
              <div class="basic-section">
                <p class="section-label">게임 성향 해시태그 <span class="hint-text">최대 10개</span></p>
                <div class="tag-chip-input-row" @click="focusTagInput">
                  <span v-for="tag in draft.hashtags" :key="tag" class="tag-chip">
                    #{{ tag }}
                    <button type="button" class="tag-chip-remove" @click.stop="removeTag(tag)">×</button>
                  </span>
                  <input
                    ref="tagInputRef"
                    v-model="tagInput"
                    class="tag-input"
                    placeholder="태그 입력 후 Enter"
                    :disabled="draft.hashtags.length >= 10"
                    @keydown="onTagKeydown"
                  />
                </div>
                <div class="tag-presets">
                  <button
                    v-for="preset in tagPresets"
                    :key="preset"
                    type="button"
                    :class="['tag-preset-btn', { active: draft.hashtags.includes(preset) }]"
                    @click="togglePreset(preset)"
                  >#{{ preset }}</button>
                </div>
              </div>
            </div>

          </div>
        </template>

        <!-- ── 내 컴퓨터 ── -->
        <template v-if="activeTab === 'pc'">

          <!-- 메모리: 다중 입력 -->
          <div class="hw-field">
            <label>메모리</label>
            <!-- 등록된 메모리 칩 목록 -->
            <div v-if="memoryList.length" class="memory-chip-row">
              <span v-for="(m, i) in memoryList" :key="i" class="memory-edit-chip">
                {{ m }}
                <button type="button" class="memory-chip-remove" @click="removeMemory(i)">×</button>
              </span>
            </div>
            <!-- 메모리 검색 추가 -->
            <div class="hw-input-wrap">
              <input
                id="hw-input-memory"
                v-model="memoryInput"
                autocomplete="off"
                placeholder="메모리 검색 또는 직접 입력 후 Enter"
                @input="onMemoryInput"
                @focus="onMemoryFocus"
                @blur="scheduleClose"
                @keydown.enter.prevent="addMemoryDirect"
              />
              <ul v-if="hwDropdown.field === 'memory'" class="hw-dropdown">
                <li v-if="hwDropdown.loading" class="hw-dropdown-hint">검색 중...</li>
                <li
                  v-for="item in hwDropdown.results"
                  :key="item.id"
                  class="hw-dropdown-item"
                  @mousedown.prevent="addMemoryFromSearch(item.name)"
                >
                  <span class="hw-item-name">{{ item.name }}</span>
                  <span class="hw-item-maker">{{ item.manufacturer }}</span>
                </li>
                <li v-if="!hwDropdown.loading && hwDropdown.results.length === 0 && hwDropdown.searched" class="hw-dropdown-hint">
                  검색 결과가 없습니다.
                </li>
                <li v-if="memoryInput.trim()" class="hw-dropdown-direct" @mousedown.prevent="addMemoryDirect">
                  ✏️ "{{ memoryInput.trim() }}" 직접 추가하기
                </li>
              </ul>
            </div>
          </div>

          <!-- 나머지 부품: 단일 입력 -->
          <div v-for="part in pcPartsExceptMemory" :key="part.key" class="hw-field">
            <label :for="`hw-input-${part.key}`">{{ part.label }}</label>
            <div class="hw-input-wrap">
              <input
                :id="`hw-input-${part.key}`"
                v-model="draft.pc_specs[part.key]"
                autocomplete="off"
                :placeholder="`${part.label} 검색 또는 직접 입력`"
                @input="onHwInput(part)"
                @focus="onHwFocus(part)"
                @blur="scheduleClose"
              />
              <ul v-if="hwDropdown.field === part.key" class="hw-dropdown">
                <li v-if="hwDropdown.loading" class="hw-dropdown-hint">검색 중...</li>
                <li
                  v-for="item in hwDropdown.results"
                  :key="item.id"
                  class="hw-dropdown-item"
                  @mousedown.prevent="selectHw(part.key, item.name)"
                >
                  <span class="hw-item-name">{{ item.name }}</span>
                  <span class="hw-item-maker">{{ item.manufacturer }}</span>
                </li>
                <li v-if="!hwDropdown.loading && hwDropdown.results.length === 0 && hwDropdown.searched" class="hw-dropdown-hint">
                  검색 결과가 없습니다.
                </li>
                <li class="hw-dropdown-direct" @mousedown.prevent="confirmDirect(part.key)">
                  ✏️ "{{ draft.pc_specs[part.key] }}" 직접 추가하기
                </li>
              </ul>
            </div>
            <button
              v-if="draft.pc_specs[part.key]"
              type="button"
              class="hw-clear-btn"
              @click="draft.pc_specs[part.key] = ''"
            >지우기</button>
          </div>
        </template>

        <!-- ── 보유 및 관심 게임 ── -->
        <template v-if="activeTab === 'games'">

          <!-- 보유 게임 플랫폼별 섹션 -->
          <section v-for="section in ownedGameSections" :key="section.platform" class="game-edit-section">
            <div class="section-title">
              <h2>{{ section.title }}</h2>
              <button type="button" class="secondary-button" @click="openGameSearch(section.platform, false)">
                게임 추가
              </button>
            </div>

            <!-- 게임 DB 검색 -->
            <div
              v-if="gameSearch.active && gameSearch.platform === section.platform && !gameSearch.forInterested"
              class="game-search-box"
            >
              <div class="game-search-input-wrap">
                <input
                  v-model="gameSearch.query"
                  class="game-search-input"
                  :placeholder="`${section.title}에 추가할 게임 검색`"
                  autocomplete="off"
                  @input="onGameInput"
                  @blur="scheduleGameClose"
                />
                <button type="button" class="game-search-close" @click="closeGameSearch">✕</button>
              </div>
              <ul v-if="gameSearch.query" class="game-dropdown">
                <li v-if="gameSearch.loading" class="game-dropdown-hint">검색 중...</li>
                <li
                  v-for="game in gameSearch.results"
                  :key="game.id"
                  class="game-dropdown-item"
                  @mousedown.prevent="selectGame(game)"
                >
                  <img v-if="game.image_url" :src="game.image_url" class="game-thumb" alt="" />
                  <span class="game-dropdown-title">{{ game.title }}</span>
                  <span class="game-dropdown-platform">{{ platformLabel[game.platform] || "기타" }}</span>
                </li>
                <li v-if="!gameSearch.loading && gameSearch.results.length === 0 && gameSearch.searched" class="game-dropdown-hint">
                  검색 결과가 없습니다.
                </li>
              </ul>
            </div>

            <div class="editable-list">
              <div v-for="game in section.games" :key="game" class="editable-row">
                <span>{{ game }}</span>
                <button type="button" class="remove-btn" @click="removeOwnedGame(game)">×</button>
              </div>
              <p v-if="section.games.length === 0" class="empty-hint">등록된 게임이 없습니다.</p>
            </div>
          </section>

          <!-- 관심 게임 섹션 -->
          <section class="game-edit-section">
            <div class="section-title">
              <h2>관심 게임</h2>
              <button type="button" class="secondary-button" @click="openGameSearch(null, true)">
                게임 추가
              </button>
            </div>

            <div v-if="gameSearch.active && gameSearch.forInterested" class="game-search-box">
              <div class="game-search-input-wrap">
                <input
                  v-model="gameSearch.query"
                  class="game-search-input"
                  placeholder="관심 게임 검색"
                  autocomplete="off"
                  @input="onGameInput"
                  @blur="scheduleGameClose"
                />
                <button type="button" class="game-search-close" @click="closeGameSearch">✕</button>
              </div>
              <ul v-if="gameSearch.query" class="game-dropdown">
                <li v-if="gameSearch.loading" class="game-dropdown-hint">검색 중...</li>
                <li
                  v-for="game in gameSearch.results"
                  :key="game.id"
                  class="game-dropdown-item"
                  @mousedown.prevent="selectGame(game)"
                >
                  <img v-if="game.image_url" :src="game.image_url" class="game-thumb" alt="" />
                  <span class="game-dropdown-title">{{ game.title }}</span>
                  <span class="game-dropdown-platform">{{ platformLabel[game.platform] || "기타" }}</span>
                </li>
                <li v-if="!gameSearch.loading && gameSearch.results.length === 0 && gameSearch.searched" class="game-dropdown-hint">
                  검색 결과가 없습니다.
                </li>
              </ul>
            </div>

            <div class="editable-list">
              <div v-for="game in draft.interested_games" :key="game" class="editable-row">
                <span>{{ game }}</span>
                <button type="button" class="remove-btn" @click="removeInterestedGame(game)">×</button>
              </div>
              <p v-if="draft.interested_games.length === 0" class="empty-hint">등록된 관심 게임이 없습니다.</p>
            </div>
          </section>

        </template>
      </form>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";
import api from "../../services/api";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

// ── 기본 상태 ──
const avatarFile = ref(null);
const avatarPreview = ref("");
const saving = ref(false);
const saveError = ref("");
const activeTab = ref("basic");

// ── 비밀번호 변경 ──
const pwForm = reactive({ current: "", next: "", confirm: "" });
const pwSaving = ref(false);
const pwError = ref("");
const pwSuccess = ref("");

async function changePassword() {
  pwError.value = "";
  pwSuccess.value = "";
  if (pwForm.next.length < 8) {
    pwError.value = "새 비밀번호는 8자 이상이어야 합니다.";
    return;
  }
  if (pwForm.next !== pwForm.confirm) {
    pwError.value = "새 비밀번호가 일치하지 않습니다.";
    return;
  }
  pwSaving.value = true;
  try {
    await api.post("/accounts/password/change/", {
      current_password: pwForm.current,
      new_password: pwForm.next,
    });
    pwSuccess.value = "비밀번호가 변경되었습니다.";
    pwForm.current = "";
    pwForm.next = "";
    pwForm.confirm = "";
  } catch (e) {
    const data = e.response?.data;
    if (data?.current_password) pwError.value = data.current_password;
    else if (data?.new_password) pwError.value = data.new_password;
    else pwError.value = "비밀번호 변경에 실패했습니다.";
  } finally {
    pwSaving.value = false;
  }
}

// ── 해시태그 ──
const tagInput = ref("");
const tagInputRef = ref(null);
const tagPresets = ["전략", "협동", "인디", "액션", "로그라이트", "공포", "시뮬레이션", "RPG", "어드벤처", "스포츠", "퍼즐", "멀티플레이"];

// ── PC 부품 ──
const pcParts = [
  { key: "cpu",     label: "CPU",     category: "cpu"     },
  { key: "gpu",     label: "GPU",     category: "gpu"     },
  { key: "memory",  label: "메모리",   category: "ram"     },
  { key: "storage", label: "저장장치", category: "storage" },
  { key: "vr",      label: "VR",      category: "vr"      },
  { key: "console", label: "콘솔",    category: "console" },
];
const pcPartsExceptMemory = pcParts.filter((p) => p.key !== "memory");
const memoryPart = pcParts.find((p) => p.key === "memory");

// 메모리 배열 (draft.pc_specs.memory 와 동기)
const memoryInput = ref("");
const memoryList = computed({
  get: () => {
    const v = draft.pc_specs.memory;
    if (Array.isArray(v)) return v;
    if (typeof v === "string" && v.trim()) return v.split(",").map((s) => s.trim()).filter(Boolean);
    return [];
  },
  set: (arr) => { draft.pc_specs.memory = arr; },
});

function addMemoryFromSearch(name) {
  if (!name || memoryList.value.includes(name)) return;
  draft.pc_specs.memory = [...memoryList.value, name];
  memoryInput.value = "";
  hwDropdown.field = null;
  hwDropdown.results = [];
}

function addMemoryDirect() {
  const name = memoryInput.value.trim();
  if (!name || memoryList.value.includes(name)) return;
  draft.pc_specs.memory = [...memoryList.value, name];
  memoryInput.value = "";
  hwDropdown.field = null;
  hwDropdown.results = [];
}

function removeMemory(index) {
  const arr = [...memoryList.value];
  arr.splice(index, 1);
  draft.pc_specs.memory = arr;
}

function onMemoryInput() {
  clearTimeout(hwTimer);
  hwDropdown.field = "memory";
  hwDropdown.searched = false;
  const q = memoryInput.value.trim();
  if (!q) { hwDropdown.results = []; return; }
  hwDropdown.loading = true;
  hwTimer = setTimeout(() => searchHardware(memoryPart, q), 280);
}

function onMemoryFocus() {
  clearTimeout(closeTimer);
  hwDropdown.field = "memory";
  if (!hwDropdown.results.length && memoryInput.value) {
    searchHardware(memoryPart, memoryInput.value);
  }
}

// ── 하드웨어 드롭다운 ──
const hwDropdown = reactive({ field: null, results: [], loading: false, searched: false });
let hwTimer = null;
let closeTimer = null;

function onHwFocus(part) {
  clearTimeout(closeTimer);
  hwDropdown.field = part.key;
  if (!hwDropdown.results.length && draft.pc_specs[part.key]) {
    searchHardware(part, draft.pc_specs[part.key]);
  }
}

function onHwInput(part) {
  clearTimeout(hwTimer);
  hwDropdown.field = part.key;
  hwDropdown.searched = false;
  const q = draft.pc_specs[part.key]?.trim();
  if (!q) { hwDropdown.results = []; return; }
  hwDropdown.loading = true;
  hwTimer = setTimeout(() => searchHardware(part, q), 280);
}

async function searchHardware(part, q) {
  hwDropdown.loading = true;
  try {
    const { data } = await api.get("/hardware/", { params: { category: part.category, q, page: 1 } });
    hwDropdown.results = data.results || [];
    hwDropdown.searched = true;
  } catch {
    hwDropdown.results = [];
  } finally {
    hwDropdown.loading = false;
  }
}

function selectHw(key, name) {
  draft.pc_specs[key] = name;
  hwDropdown.field = null;
  hwDropdown.results = [];
}

function confirmDirect(key) {
  hwDropdown.field = null;
  hwDropdown.results = [];
}

function scheduleClose() {
  closeTimer = setTimeout(() => { hwDropdown.field = null; }, 150);
}

// ── 플랫폼 라벨 ──
const platformLabel = {
  steam: "Steam",
  epic: "Epic Games",
  ubisoft: "Ubisoft",
  other: "기타",
};

const ownedPlatformSections = [
  { platform: "steam",   title: "Steam 게임 리스트" },
  { platform: "epic",    title: "Epic Games 리스트" },
  { platform: "ubisoft", title: "Ubisoft 게임 리스트" },
  { platform: "other",   title: "그 외 게임 리스트" },
];

// ── 게임 DB 검색 ──
const gameSearch = reactive({
  active: false,
  platform: null,
  forInterested: false,
  query: "",
  results: [],
  loading: false,
  searched: false,
});
let gameTimer = null;
let gameCloseTimer = null;

function openGameSearch(platform, forInterested) {
  gameSearch.active = true;
  gameSearch.platform = platform;
  gameSearch.forInterested = forInterested;
  gameSearch.query = "";
  gameSearch.results = [];
  gameSearch.searched = false;
}

function closeGameSearch() {
  gameSearch.active = false;
  gameSearch.query = "";
  gameSearch.results = [];
}

function scheduleGameClose() {
  gameCloseTimer = setTimeout(() => { gameSearch.active = false; }, 150);
}

function onGameInput() {
  clearTimeout(gameTimer);
  clearTimeout(gameCloseTimer);
  gameSearch.searched = false;
  const q = gameSearch.query.trim();
  if (!q) { gameSearch.results = []; return; }
  gameSearch.loading = true;
  gameTimer = setTimeout(() => searchGames(q), 280);
}

async function searchGames(q) {
  gameSearch.loading = true;
  try {
    const { data } = await api.get("/games/", { params: { q, page: 1 } });
    gameSearch.results = data.results || [];
    gameSearch.searched = true;
  } catch {
    gameSearch.results = [];
  } finally {
    gameSearch.loading = false;
  }
}

function selectGame(game) {
  const title = game.title;
  if (gameSearch.forInterested) {
    if (!draft.interested_games.includes(title)) {
      draft.interested_games.push(title);
      draft.game_platforms[title] = game.platform || "other";
    }
  } else {
    if (!draft.owned_games.includes(title)) {
      draft.owned_games.push(title);
      draft.game_platforms[title] = gameSearch.platform || game.platform || "other";
    }
  }
  closeGameSearch();
}

// ── 드래프트 ──
const draft = reactive({
  nickname: "",
  avatar_url: "",
  show_hashtags: true,
  hashtags: [],
  pc_specs: {},
  owned_games: [],
  interested_games: [],
  game_platforms: {},
});

const activeTitle = computed(
  () => ({ basic: "기본 설정", pc: "내 컴퓨터", games: "보유 및 관심 게임" })[activeTab.value],
);

watch(
  () => route.query.tab,
  (tab) => {
    if (["basic", "pc", "games"].includes(tab)) activeTab.value = tab;
  },
  { immediate: true },
);

watchEffect(() => {
  if (!auth.user) return;
  const user = JSON.parse(JSON.stringify(auth.user));

  const gamePlatforms = {};
  if (Array.isArray(user.owned_games)) {
    user.owned_games = user.owned_games.map((g) => {
      if (typeof g === "object") { gamePlatforms[g.title] = g.platform; return g.title; }
      return g;
    });
  }
  if (Array.isArray(user.interested_games)) {
    user.interested_games = user.interested_games.map((g) => {
      if (typeof g === "object") { gamePlatforms[g.title] = g.platform; return g.title; }
      return g;
    });
  }
  user.game_platforms = { ...gamePlatforms, ...(user.game_platforms || {}) };

  Object.assign(draft, user);
  draft.pc_specs ||= {};
  draft.game_platforms ||= {};
  if (!avatarPreview.value && auth.user.avatar_url) {
    avatarPreview.value = auth.user.avatar_url;
  }
});

const ownedGameSections = computed(() =>
  ownedPlatformSections.map((section) => ({
    ...section,
    games: (draft.owned_games || []).filter((game) => gamePlatform(game) === section.platform),
  })),
);

// ── 해시태그 함수 ──
function addTag() {
  const tag = tagInput.value.trim().replace(/^#+/, "").replace(/[,\s]+$/, "");
  if (!tag || draft.hashtags.includes(tag) || draft.hashtags.length >= 10) return;
  draft.hashtags.push(tag);
  tagInput.value = "";
}

function removeTag(tag) {
  draft.hashtags = draft.hashtags.filter((t) => t !== tag);
}

function togglePreset(preset) {
  if (draft.hashtags.includes(preset)) removeTag(preset);
  else if (draft.hashtags.length < 10) draft.hashtags.push(preset);
}

function onTagKeydown(e) {
  if (e.key === "Enter" || e.key === "," || e.key === " ") {
    e.preventDefault();
    addTag();
  } else if (e.key === "Backspace" && !tagInput.value && draft.hashtags.length) {
    draft.hashtags.pop();
  }
}

function focusTagInput() {
  tagInputRef.value?.focus();
}

// ── 저장 ──
async function save() {
  saving.value = true;
  saveError.value = "";
  try {
    if (avatarFile.value) {
      await auth.uploadProfileImage(avatarFile.value);
      avatarFile.value = null;
    }
    const { avatar_url, profile_image, ...profileData } = draft;
    await auth.updateProfile(profileData);
    router.push("/profile");
  } catch (e) {
    const data = e.response?.data;
    if (data && typeof data === "object") {
      saveError.value = Object.values(data).flat().join(" ");
    } else {
      saveError.value = "저장 중 오류가 발생했습니다.";
    }
  } finally {
    saving.value = false;
  }
}

function handleAvatarChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  avatarFile.value = file;
  avatarPreview.value = URL.createObjectURL(file);
}

function clearAvatar() {
  avatarFile.value = null;
  avatarPreview.value = "";
}

// ── 게임 리스트 조작 ──
function removeOwnedGame(game) {
  draft.owned_games = draft.owned_games.filter((g) => g !== game);
  delete draft.game_platforms[game];
}

function removeInterestedGame(game) {
  draft.interested_games = draft.interested_games.filter((g) => g !== game);
}

function gamePlatform(game) {
  return draft.game_platforms?.[game] || "other";
}
</script>

<style scoped>
.save-error-msg {
  color: #c0392b;
  background: #fdf0ef;
  border: 1px solid #f5c6c2;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
}

/* ── 기본 설정 2컬럼 그리드 ── */
.basic-grid {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  column-gap: 2rem;
  align-items: start;
  grid-column: 1 / -1;
}

.basic-left {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.basic-right {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.vertical-divider {
  width: 1px;
  background: var(--clr-border, #d4dde8);
  align-self: stretch;
}

/* ── 기본 설정 공통 ── */
.basic-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--clr-text-muted, #5a6b7e);
  margin: 0;
}

.hint-text {
  font-size: 0.78rem;
  font-weight: 400;
  font-style: normal;
  color: var(--clr-text-muted, #5a6b7e);
  margin-left: 0.3rem;
}

.divider {
  height: 1px;
  background: var(--clr-border, #d4dde8);
}

.field-input {
  width: 100%;
  padding: 0.55rem 0.85rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: #fff;
  color: #1c2430;
  font-size: 0.95rem;
  box-sizing: border-box;
  font-family: inherit;
}

.field-input:focus {
  outline: none;
  border-color: var(--clr-primary, #17637d);
  box-shadow: 0 0 0 2px rgba(23, 99, 125, 0.13);
}

/* 프로필 사진 */
.avatar-row {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--clr-border, #d4dde8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid var(--clr-border, #d4dde8);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-empty {
  font-size: 0.75rem;
  color: var(--clr-text-muted, #5a6b7e);
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}

.file-btn {
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.hidden-file {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  font-size: 0;
}

.text-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.82rem;
  cursor: pointer;
  text-decoration: underline;
}

.text-btn.danger {
  color: #c0392b;
}

/* 비밀번호 필드 */
.field-stack {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field-label {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--clr-text-muted, #5a6b7e);
}

.pw-error {
  margin: 0;
  font-size: 0.85rem;
  color: #c0392b;
}

.pw-success {
  margin: 0;
  font-size: 0.85rem;
  color: #1a7a4a;
}

/* ── 메모리 다중 입력 ── */
.memory-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}

.memory-edit-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: rgba(23, 99, 125, 0.12);
  color: var(--clr-primary, #17637d);
  font-size: 0.82rem;
  font-weight: 600;
}

.memory-chip-remove {
  background: none;
  border: none;
  color: var(--clr-primary, #17637d);
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  cursor: pointer;
  opacity: 0.6;
}

.memory-chip-remove:hover {
  opacity: 1;
}

/* ── PC 부품 검색 ── */
.hw-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.hw-field > label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--clr-text-muted, #5a6b7e);
}

.hw-input-wrap {
  position: relative;
}

.hw-input-wrap input {
  width: 100%;
  padding: 0.55rem 0.85rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: #fff;
  color: #1c2430;
  font-size: 0.95rem;
  box-sizing: border-box;
}

.hw-input-wrap input:focus {
  outline: none;
  border-color: var(--clr-primary, #17637d);
  box-shadow: 0 0 0 2px rgba(23, 99, 125, 0.13);
}

.hw-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(20, 40, 70, 0.13);
  z-index: 100;
  max-height: 260px;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: 0.3rem 0;
}

.hw-dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  cursor: pointer;
  gap: 0.5rem;
}

.hw-dropdown-item:hover {
  background: rgba(23, 99, 125, 0.07);
}

.hw-item-name {
  font-size: 0.9rem;
  color: #1c2430;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hw-item-maker {
  font-size: 0.78rem;
  color: var(--clr-text-muted, #5a6b7e);
  flex-shrink: 0;
}

.hw-dropdown-hint {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  color: var(--clr-text-muted, #5a6b7e);
  cursor: default;
}

.hw-dropdown-direct {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  color: var(--clr-primary, #17637d);
  cursor: pointer;
  border-top: 1px solid var(--clr-border, #d4dde8);
  margin-top: 0.2rem;
}

.hw-dropdown-direct:hover {
  background: rgba(23, 99, 125, 0.07);
}

.hw-clear-btn {
  align-self: flex-start;
  padding: 0.25rem 0.65rem;
  font-size: 0.8rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 6px;
  background: transparent;
  color: var(--clr-text-muted, #5a6b7e);
  cursor: pointer;
}

.hw-clear-btn:hover {
  border-color: #c0392b;
  color: #c0392b;
}

/* ── 해시태그 편집 ── */
.tag-editor {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.tag-editor-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--clr-text-muted, #5a6b7e);
  margin: 0;
}

.tag-count {
  font-weight: 400;
  font-size: 0.8rem;
}

.tag-chip-input-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: #fff;
  cursor: text;
  min-height: 2.6rem;
}

.tag-chip-input-row:focus-within {
  border-color: var(--clr-primary, #17637d);
  box-shadow: 0 0 0 2px rgba(23, 99, 125, 0.13);
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  background: rgba(23, 99, 125, 0.12);
  color: var(--clr-primary, #17637d);
  font-size: 0.82rem;
  font-weight: 600;
}

.tag-chip-remove {
  background: none;
  border: none;
  color: var(--clr-primary, #17637d);
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  cursor: pointer;
  opacity: 0.6;
}

.tag-chip-remove:hover {
  opacity: 1;
}

.tag-input {
  border: none;
  outline: none;
  font: inherit;
  font-size: 0.9rem;
  color: #1c2430;
  flex: 1;
  min-width: 120px;
  background: transparent;
}

.tag-input:disabled {
  cursor: not-allowed;
  color: var(--clr-text-muted, #5a6b7e);
}

.tag-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.tag-preset-btn {
  padding: 0.22rem 0.65rem;
  border-radius: 999px;
  border: 1px solid var(--clr-border, #d4dde8);
  background: transparent;
  color: var(--clr-text-muted, #5a6b7e);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.12s;
}

.tag-preset-btn:hover {
  border-color: var(--clr-primary, #17637d);
  color: var(--clr-primary, #17637d);
  background: rgba(23, 99, 125, 0.06);
}

.tag-preset-btn.active {
  border-color: var(--clr-primary, #17637d);
  background: rgba(23, 99, 125, 0.12);
  color: var(--clr-primary, #17637d);
  font-weight: 600;
}

/* ── 게임 편집 ── */
.game-edit-section {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.section-title h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.game-search-box {
  position: relative;
}

.game-search-input-wrap {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.game-search-input {
  flex: 1;
  padding: 0.5rem 0.85rem;
  border: 1px solid var(--clr-primary, #17637d);
  border-radius: 8px;
  background: #fff;
  color: #1c2430;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.game-search-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(23, 99, 125, 0.13);
}

.game-search-close {
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  background: transparent;
  color: var(--clr-text-muted, #5a6b7e);
  cursor: pointer;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.game-search-close:hover {
  border-color: #c0392b;
  color: #c0392b;
}

.game-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid var(--clr-border, #d4dde8);
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(20, 40, 70, 0.13);
  z-index: 100;
  max-height: 280px;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: 0.3rem 0;
}

.game-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.game-dropdown-item:hover {
  background: rgba(23, 99, 125, 0.07);
}

.game-thumb {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
  background: var(--clr-border, #d4dde8);
}

.game-dropdown-title {
  flex: 1;
  font-size: 0.9rem;
  color: #1c2430;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-dropdown-platform {
  font-size: 0.78rem;
  color: var(--clr-text-muted, #5a6b7e);
  flex-shrink: 0;
}

.game-dropdown-hint {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  color: var(--clr-text-muted, #5a6b7e);
  cursor: default;
}

.editable-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.editable-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.45rem 0.75rem;
  background: var(--surface-alt, #f5f7fa);
  border-radius: 6px;
  font-size: 0.9rem;
  color: #1c2430;
}

.remove-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  line-height: 1;
  color: var(--clr-text-muted, #5a6b7e);
  cursor: pointer;
  padding: 0 0.2rem;
  flex-shrink: 0;
}

.remove-btn:hover {
  color: #c0392b;
}

.empty-hint {
  font-size: 0.85rem;
  color: var(--clr-text-muted, #5a6b7e);
  margin: 0;
  padding: 0.3rem 0;
}
</style>
