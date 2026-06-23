<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">프로필 수정</p>
        <h1>{{ activeTitle }}</h1>
      </div>
      <button class="primary-button" @click="save">저장</button>
    </header>

    <div class="settings-layout">
      <aside class="settings-menu">
        <button :class="{ active: activeTab === 'basic' }" @click="activeTab = 'basic'">기본 설정</button>
        <button :class="{ active: activeTab === 'pc' }" @click="activeTab = 'pc'">내 컴퓨터</button>
        <button :class="{ active: activeTab === 'games' }" @click="activeTab = 'games'">보유 및 관심 게임</button>
      </aside>

      <form class="panel edit-panel" @submit.prevent="save">
        <template v-if="activeTab === 'basic'">
          <label class="avatar-setting">
            프로필 사진
            <div class="avatar-preview">
              <img v-if="draft.avatar_url" :src="draft.avatar_url" alt="프로필 사진 미리보기" />
              <span v-else>빈 사진</span>
            </div>
            <input type="file" accept="image/*" @change="handleAvatarChange" />
            <button v-if="draft.avatar_url" class="secondary-button" type="button" @click="clearAvatar">사진 지우기</button>
          </label>
          <label>
            닉네임
            <input v-model="draft.nickname" />
          </label>
          <fieldset class="tag-checkboxes">
            <legend>게임 성향 해시태그</legend>
            <label v-for="tag in tasteTagOptions" :key="tag">
              <input v-model="draft.hashtags" type="checkbox" :value="tag" />
              #{{ tag }}
            </label>
          </fieldset>
          <label>
            새 비밀번호
            <input type="password" placeholder="백엔드 연동 예정" disabled />
          </label>
        </template>

        <template v-if="activeTab === 'pc'">
          <label v-for="part in pcParts" :key="part.key" class="part-search">
            {{ part.label }}
            <input v-model="draft.pc_specs[part.key]" :list="`${part.key}-options`" :placeholder="`${part.label} 검색`" />
            <datalist :id="`${part.key}-options`">
              <option v-for="option in part.options" :key="option" :value="option" />
            </datalist>
          </label>
        </template>

        <template v-if="activeTab === 'games'">
          <section v-for="section in ownedGameSections" :key="section.platform" class="game-edit-section">
            <div class="section-title">
              <h2>{{ section.title }}</h2>
              <div class="button-row">
                <button v-if="section.platform === 'Steam'" type="button" class="secondary-button">Steam 연동</button>
                <button type="button" class="secondary-button" @click="openOwnedAdd(section.platform)">직접추가</button>
              </div>
            </div>
            <div v-if="addForms.owned[section.platform]" class="inline-add-row">
              <input
                v-model="addForms.ownedTitle[section.platform]"
                :placeholder="`${section.title}에 추가할 게임명`"
                @keyup.enter="confirmOwnedAdd(section.platform)"
              />
              <button type="button" class="primary-button" @click="confirmOwnedAdd(section.platform)">추가</button>
              <button type="button" class="secondary-button" @click="closeOwnedAdd(section.platform)">취소</button>
            </div>
            <div class="editable-list">
              <div v-for="game in section.games" :key="game" class="editable-row">
                <span>{{ game }}</span>
                <button type="button" @click="removeOwnedGame(game)">x</button>
              </div>
              <p v-if="section.games.length === 0">등록된 게임이 없습니다.</p>
            </div>
          </section>

          <section class="game-edit-section">
            <div class="section-title">
              <h2>관심게임</h2>
              <button type="button" class="secondary-button" @click="addForms.interested = true">직접추가</button>
            </div>
            <div v-if="addForms.interested" class="inline-add-row">
              <input
                v-model="addForms.interestedTitle"
                placeholder="관심게임에 추가할 게임명"
                @keyup.enter="confirmInterestedAdd"
              />
              <button type="button" class="primary-button" @click="confirmInterestedAdd">추가</button>
              <button type="button" class="secondary-button" @click="closeInterestedAdd">취소</button>
            </div>
            <div class="editable-list">
              <div v-for="game in draft.interested_games" :key="game" class="editable-row">
                <span>{{ game }}</span>
                <button type="button" @click="removeInterestedGame(game)">x</button>
              </div>
              <p v-if="draft.interested_games.length === 0">등록된 관심게임이 없습니다.</p>
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

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const activeTab = ref("basic");
const tasteTagOptions = ["전략", "협동", "인디", "액션", "로그라이트", "공포", "시뮬레이션"];
const addForms = reactive({
  owned: {},
  ownedTitle: {},
  interested: false,
  interestedTitle: "",
});
const pcParts = [
  {
    key: "cpu",
    label: "CPU",
    options: ["AMD Ryzen 7 5800X", "AMD Ryzen 7 7800X3D", "Intel Core i5-13600K", "Intel Core i7-14700K"],
  },
  {
    key: "gpu",
    label: "GPU",
    options: ["NVIDIA RTX 3070 Ti", "NVIDIA RTX 4070 SUPER", "NVIDIA RTX 4060", "AMD Radeon RX 7800 XT"],
  },
  {
    key: "memory",
    label: "메모리",
    options: ["16GB DDR4", "32GB DDR4", "32GB DDR5", "64GB DDR5"],
  },
  {
    key: "storage",
    label: "저장공간",
    options: ["C: 200GB / 2TB", "1TB NVMe SSD", "2TB NVMe SSD", "512GB SSD + 2TB HDD"],
  },
  {
    key: "vr",
    label: "VR",
    options: ["없음", "Meta Quest 3", "Valve Index", "HTC Vive"],
  },
  {
    key: "console",
    label: "콘솔",
    options: ["없음", "PlayStation 5", "Xbox Series X", "Nintendo Switch 2"],
  },
];
const ownedPlatformSections = [
  { platform: "Steam", title: "Steam 게임 리스트" },
  { platform: "Epic games", title: "epic game 리스트" },
  { platform: "Ubisoft", title: "ubi soft game 리스트" },
  { platform: "Other", title: "그 외 게임 리스트" },
];
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
    if (["basic", "pc", "games"].includes(tab)) {
      activeTab.value = tab;
    }
  },
  { immediate: true },
);

watchEffect(() => {
  if (!auth.user) return;
  Object.assign(draft, JSON.parse(JSON.stringify(auth.user)));
  draft.pc_specs ||= {};
  draft.game_platforms ||= {};
});

const ownedGameSections = computed(() =>
  ownedPlatformSections.map((section) => ({
    ...section,
    games: (draft.owned_games || []).filter((game) => gamePlatform(game) === section.platform),
  })),
);

async function save() {
  await auth.updateProfile(draft);
  router.push("/profile");
}

function handleAvatarChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    draft.avatar_url = reader.result;
  };
  reader.readAsDataURL(file);
}

function clearAvatar() {
  draft.avatar_url = "";
}

function openOwnedAdd(platform) {
  addForms.owned[platform] = true;
  addForms.ownedTitle[platform] ||= "";
}

function closeOwnedAdd(platform) {
  addForms.owned[platform] = false;
  addForms.ownedTitle[platform] = "";
}

function confirmOwnedAdd(platform) {
  const title = addForms.ownedTitle[platform];
  if (addToList("owned_games", title)) {
    draft.game_platforms[title.trim()] = platform;
    closeOwnedAdd(platform);
  }
}

function removeOwnedGame(game) {
  removeFromList("owned_games", game);
  delete draft.game_platforms[game];
}

function confirmInterestedAdd() {
  if (addToList("interested_games", addForms.interestedTitle)) {
    closeInterestedAdd();
  }
}

function closeInterestedAdd() {
  addForms.interested = false;
  addForms.interestedTitle = "";
}

function removeInterestedGame(game) {
  removeFromList("interested_games", game);
}

function addToList(key, title) {
  const normalized = title?.trim();
  if (!normalized || draft[key].includes(normalized)) return false;
  draft[key].push(normalized);
  return true;
}

function removeFromList(key, game) {
  draft[key] = draft[key].filter((item) => item !== game);
}

const platformByGame = {
  "Civilization VI": "Steam",
  "Civilization V": "Steam",
  "Dead by Daylight": "Steam",
  "Stardew Valley": "Steam",
  "Hades II": "Steam",
  "It Takes Two": "Epic games",
  "The Last of Us": "Epic games",
  Fortnite: "Epic games",
  "Battlefield V": "Epic games",
  "Assassin's Creed Origin": "Ubisoft",
  "Assassin’s Creed Origin": "Ubisoft",
  "Assasin’s Creed I": "Ubisoft",
};

function gamePlatform(game) {
  return draft.game_platforms?.[game] || platformByGame[game] || "Other";
}
</script>
