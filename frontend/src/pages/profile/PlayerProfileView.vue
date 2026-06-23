<template>
  <section class="content-stack">
    <RouterLink class="back-link" to="/games">← 게임 목록으로 돌아가기</RouterLink>

    <article class="panel public-profile">
      <div class="avatar">{{ initial }}</div>
      <div>
        <p class="eyebrow">플레이어 프로필</p>
        <h1>{{ player.nickname }}</h1>
        <div class="follow-summary">
          <button @click="showSocial('followers')">
            <strong>{{ followerCount.toLocaleString("ko-KR") }}</strong>
            <span>팔로워</span>
          </button>
          <button @click="showSocial('following')">
            <strong>{{ player.following.length.toLocaleString("ko-KR") }}</strong>
            <span>팔로잉</span>
          </button>
        </div>
        <p class="taste-summary">
          <span v-for="tag in player.hashtags" :key="tag">#{{ tag }}</span>
        </p>
        <p class="subtle">{{ player.bio }}</p>
      </div>
      <button :class="isFollowing ? 'secondary-button' : 'primary-button'" @click="toggleFollow">
        {{ isFollowing ? "팔로잉" : "팔로우" }}
      </button>
    </article>

    <div class="public-profile-grid">
      <section class="panel">
        <h2>보유 게임</h2>
        <div class="public-game-list">
          <RouterLink v-for="game in player.ownedGames" :key="game.title" class="interest-item" :to="`/games/${game.id}`">
            <strong>{{ game.title }}</strong>
            <span>{{ game.platform }} · {{ game.playtime }}</span>
          </RouterLink>
        </div>
      </section>

      <section class="panel">
        <h2>관심 게임</h2>
        <div class="public-game-list">
          <RouterLink v-for="game in player.interestedGames" :key="game.title" class="interest-item" :to="`/games/${game.id}`">
            <strong>{{ game.title }}</strong>
            <span>{{ game.reason }}</span>
          </RouterLink>
        </div>
      </section>
    </div>

    <section class="panel">
      <h2>장비 정보</h2>
      <dl class="public-equipment-list">
        <div v-for="part in player.equipment" :key="part.label">
          <dt>{{ part.label }}</dt>
          <dd>
            <strong>{{ part.value }}</strong>
            <span>{{ part.note }}</span>
          </dd>
        </div>
      </dl>
    </section>

    <section class="panel">
      <h2>최근 남긴 의견</h2>
      <div class="profile-list">
        <RouterLink v-for="opinion in player.recentOpinions" :key="opinion.id" class="profile-list-item public-opinion-item" :to="opinion.to">
          <div>
            <span>{{ opinion.game }}</span>
            <strong>{{ opinion.postTitle }}</strong>
            <p>{{ opinion.body }}</p>
          </div>
          <small>{{ opinion.type }} · {{ opinion.createdAt }}</small>
        </RouterLink>
      </div>
    </section>

    <div v-if="socialModal" class="modal-backdrop" @click.self="socialModal = ''">
      <section class="social-modal">
        <button class="modal-close" @click="socialModal = ''">닫기</button>
        <p class="eyebrow">{{ player.nickname }}</p>
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
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const username = computed(() => route.params.username || "player");
const player = computed(() => playerProfiles[username.value] || createDefaultProfile(username.value));
const initial = computed(() => player.value.nickname.slice(0, 1).toUpperCase());
const followedPlayers = ref(JSON.parse(localStorage.getItem("followedPlayers") || "[]"));
const socialModal = ref("");
const isFollowing = computed(() => followedPlayers.value.includes(player.value.nickname));
const followerCount = computed(() => player.value.followers.length + (isFollowing.value ? 1 : 0));
const visibleSocialUsers = computed(() => {
  if (socialModal.value === "followers") {
    return isFollowing.value ? ["admin", ...player.value.followers] : player.value.followers;
  }
  return player.value.following;
});

const playerProfiles = {
  strategy_admin: {
    nickname: "strategy_admin",
    followers: ["sale_watcher", "coop_player", "spec_checker", "turn_master"],
    following: ["sale_watcher", "party_maker"],
    hashtags: ["전략", "턴제", "사양체크"],
    bio: "전략 게임 위주로 플레이하고, 권장 사양과 장기 플레이 안정성을 꼼꼼히 보는 플레이어입니다.",
    ownedGames: [
      { id: 1, title: "Civilization VII", platform: "Steam", playtime: "128시간" },
      { id: 3, title: "Hades II", platform: "Steam", playtime: "42시간" },
    ],
    interestedGames: [
      { id: 2, title: "It Takes Two", reason: "협동 플레이용으로 관심" },
    ],
    equipment: [
      { label: "CPU", value: "AMD Ryzen 7 7800X3D", note: "전략/시뮬레이션 최적화" },
      { label: "메모리", value: "64GB", note: "대형 맵 플레이 여유" },
      { label: "GPU", value: "NVIDIA RTX 4070 SUPER", note: "QHD 중상옵 안정권" },
      { label: "저장공간", value: "NVMe 2TB", note: "게임 전용 드라이브" },
      { label: "VR", value: "없음", note: "PC 플레이 중심" },
    ],
    recentOpinions: [
      {
        id: 1,
        game: "Civilization VII",
        postTitle: "권장 사양 기준으로 CPU 여유가 중요해요",
        body: "후반 턴 로딩과 AI 처리 때문에 CPU를 먼저 보는 편이 좋아요.",
        type: "추천 의견",
        createdAt: "오늘",
        to: "/games/1/community",
      },
      {
        id: 2,
        game: "Hades II",
        postTitle: "그래픽보다 입력 지연이 체감에 더 큽니다",
        body: "프레임은 충분하고 컨트롤러 세팅을 먼저 맞추는 걸 추천합니다.",
        type: "댓글",
        createdAt: "어제",
        to: "/games/3/community",
      },
    ],
  },
  sale_watcher: {
    nickname: "sale_watcher",
    followers: ["strategy_admin", "deal_hunter", "coop_player"],
    following: ["strategy_admin", "discount_bot", "wish_master"],
    hashtags: ["할인탐색", "최저가", "위시리스트"],
    bio: "할인율, 최저가, 구매 타이밍을 중심으로 게임을 고르는 플레이어입니다.",
    ownedGames: [
      { id: 2, title: "It Takes Two", platform: "Epic games", playtime: "18시간" },
      { id: 3, title: "Hades II", platform: "Steam", playtime: "35시간" },
    ],
    interestedGames: [
      { id: 1, title: "Civilization VII", reason: "출시 할인 추적 중" },
    ],
    equipment: [
      { label: "CPU", value: "AMD Ryzen 5 5600", note: "대부분 게임 무난" },
      { label: "메모리", value: "32GB", note: "멀티태스킹 가능" },
      { label: "GPU", value: "NVIDIA RTX 3060 Ti", note: "FHD/QHD 혼합" },
      { label: "저장공간", value: "SSD 1TB", note: "여유 보통" },
      { label: "VR", value: "없음", note: "관심 낮음" },
    ],
    recentOpinions: [
      {
        id: 1,
        game: "It Takes Two",
        postTitle: "역대가보다 높으면 조금 기다려도 됩니다",
        body: "협동 게임은 세일 주기가 자주 와서 관심 등록 후 기다리는 편이 좋아요.",
        type: "구매 타이밍",
        createdAt: "오늘",
        to: "/games/2/community",
      },
      {
        id: 2,
        game: "Civilization VII",
        postTitle: "출시 초반에는 할인보다 번들 구성을 봐야 해요",
        body: "DLC가 많은 게임이라 에디션 구성을 비교하는 게 중요합니다.",
        type: "댓글",
        createdAt: "3일 전",
        to: "/games/1/community",
      },
    ],
  },
  coop_player: {
    nickname: "coop_player",
    followers: ["strategy_admin", "sale_watcher"],
    following: ["story_mate", "party_maker", "strategy_admin"],
    hashtags: ["협동", "스토리", "친목"],
    bio: "친구와 같이 하는 협동 게임과 스토리 중심 게임을 선호합니다.",
    ownedGames: [
      { id: 2, title: "It Takes Two", platform: "Ubisoft", playtime: "24시간" },
    ],
    interestedGames: [
      { id: 3, title: "Hades II", reason: "액션 로그라이트 입문 예정" },
      { id: 1, title: "Civilization VII", reason: "멀티 그룹 플레이 관심" },
    ],
    equipment: [
      { label: "CPU", value: "Intel i5-12400F", note: "협동 게임 충분" },
      { label: "메모리", value: "16GB", note: "보통 수준" },
      { label: "GPU", value: "NVIDIA RTX 3060", note: "FHD 쾌적" },
      { label: "저장공간", value: "SSD 512GB", note: "정리 필요" },
      { label: "콘솔", value: "Nintendo Switch", note: "파티 게임용" },
    ],
    recentOpinions: [
      {
        id: 1,
        game: "It Takes Two",
        postTitle: "처음 하는 사람과 같이 해도 괜찮아요",
        body: "퍼즐 난이도는 적당하고 같이 이야기하면서 풀기 좋아요.",
        type: "추천 의견",
        createdAt: "오늘",
        to: "/games/2/community",
      },
    ],
  },
};

function createDefaultProfile(name) {
  return {
    nickname: name,
    followers: ["strategy_admin", "sale_watcher"],
    following: ["coop_player"],
    hashtags: ["게임탐색", "PC사양", "커뮤니티"],
    bio: "공개 프로필 정보가 적어서 기본 정보만 보여주고 있습니다.",
    ownedGames: [
      { id: 1, title: "Civilization VII", platform: "Steam", playtime: "플레이 중" },
      { id: 2, title: "It Takes Two", platform: "Epic games", playtime: "보유" },
    ],
    interestedGames: [
      { id: 3, title: "Hades II", reason: "관심 등록" },
    ],
    equipment: [
      { label: "CPU", value: "AMD Ryzen 7 5800X", note: "공개 장비" },
      { label: "메모리", value: "32GB", note: "공개 장비" },
      { label: "GPU", value: "NVIDIA RTX 3070 Ti", note: "공개 장비" },
      { label: "저장공간", value: "SSD 1TB", note: "공개 장비" },
    ],
    recentOpinions: [
      {
        id: 1,
        game: "Civilization VII",
        postTitle: "게임 사양은 충분한지 먼저 확인하는 편이에요",
        body: "권장 사양을 확인하고 할인 타이밍을 같이 보는 편입니다.",
        type: "댓글",
        createdAt: "최근",
        to: "/games/1/community",
      },
    ],
  };
}

function toggleFollow() {
  const name = player.value.nickname;
  if (isFollowing.value) {
    followedPlayers.value = followedPlayers.value.filter((item) => item !== name);
  } else {
    followedPlayers.value = [...followedPlayers.value, name];
  }
  localStorage.setItem("followedPlayers", JSON.stringify(followedPlayers.value));
}

function showSocial(type) {
  socialModal.value = type;
}
</script>
