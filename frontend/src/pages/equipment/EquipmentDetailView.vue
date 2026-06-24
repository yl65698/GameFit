<template>
  <section class="equipment-detail-page">
    <RouterLink class="detail-back" to="/equipment">← 목록으로 돌아가기</RouterLink>

    <header class="detail-header">
      <div class="detail-art equipment-art" :style="imageBackground(item.image_url)">
        <span>{{ item.type }}</span>
      </div>
      <div>
        <p class="eyebrow">장비 상세</p>
        <h1>{{ item.name }}</h1>
        <p>{{ item.fit }}</p>
        <div class="button-row">
          <button class="primary-button">내 장비 추가</button>
          <button class="secondary-button">관심장비 등록</button>
        </div>
      </div>
      <aside class="buy-signal">
        <span>내 장비랑 비교</span>
        <strong>추천</strong>
        <p>{{ price }}원</p>
      </aside>
    </header>

          <div class="equipment-title-block">
            <h1>{{ item.name || "장비 이름" }}</h1>
            <dl>
              <div>
                <dt>제조사</dt>
                <dd>{{ maker }}</dd>
              </div>
              <div>
                <dt>가격</dt>
                <dd>{{ price }}원</dd>
              </div>
              <div>
                <dt>용도</dt>
                <dd>{{ item.fit || "게임 플레이 환경 개선" }}</dd>
              </div>
            </dl>
          </div>

          <div class="detail-action-stack">
            <button :class="isOwned ? 'secondary-button' : 'primary-button'" @click="toggleOwned">
              {{ isOwned ? "내 장비에서 제거" : "내 장비 추가" }}
            </button>
          </div>
        </section>

        <p v-if="actionMessage" class="action-message">{{ actionMessage }}</p>

        <section class="detail-panel price-trend-panel">
          <div class="panel-heading compact">
            <h2>가격 변동 추이</h2>
            <span>최근 6개월</span>
          </div>
          <svg class="line-chart" viewBox="0 0 600 180" role="img" aria-label="장비 가격 변동 선 그래프">
            <polyline class="line-chart-grid" points="0,36 600,36" />
            <polyline class="line-chart-grid" points="0,90 600,90" />
            <polyline class="line-chart-grid" points="0,144 600,144" />
            <polyline class="line-chart-line equipment-line" :points="priceChartPoints" />
            <circle v-for="point in priceHistoryPoints" :key="point.label" class="line-chart-dot equipment-dot" :cx="point.x" :cy="point.y" r="5" />
          </svg>
          <div class="chart-labels">
            <span v-for="point in priceHistoryPoints" :key="point.label">{{ point.label }}</span>
          </div>
        </section>

        <div class="detail-info-grid">
          <section class="detail-panel">
            <h2>가격 비교</h2>
            <div class="price-market-list">
              <article v-for="market in markets" :key="market.store">
                <strong>{{ market.store }}</strong>
                <span>{{ market.price.toLocaleString("ko-KR") }}원</span>
                <em>{{ market.badge }}</em>
                <a class="price-link-button" :href="market.url" target="_blank" rel="noreferrer">이동</a>
              </article>
            </div>
          </section>

          <section class="detail-panel">
            <h2>가격 예측 및 구매 타이밍 추천</h2>
            <strong class="buy-timing">{{ timingHeadline }}</strong>
            <p>{{ timingMessage }}</p>
          </section>

          <section class="detail-panel equipment-fit-panel">
            <h2>보유 게임 적합 장비</h2>
            <article v-for="game in ownedGameMatches" :key="game.title">
              <strong>{{ game.title }}</strong>
              <span>{{ game.reason }}</span>
            </article>
          </section>

          <section class="detail-panel equipment-fit-panel">
            <h2>관심 게임 적합 장비</h2>
            <article v-for="game in interestedGameMatches" :key="game.title">
              <strong>{{ game.title }}</strong>
              <span>{{ game.reason }}</span>
            </article>
          </section>
        </div>
      </main>

      <aside class="equipment-compare-sidebar">
        <h2>내 장비랑 비교하면?</h2>

        <dl class="compat-spec-list equipment-current-specs">
          <div v-for="spec in currentSpecs" :key="spec.label" :class="{ highlighted: spec.highlighted }">
            <dt>{{ spec.label }}</dt>
            <dd>
              <strong>{{ spec.value }}</strong>
              <small>{{ spec.note }}</small>
            </dd>
          </div>
        </dl>

        <div class="equipment-storage-row">
          <strong>저장공간</strong>
          <span>C 드라이브 200GB / 2 TB</span>
        </div>
        <div class="storage-meter">
          <span style="width: 62%"></span>
        </div>

        <section class="equipment-judgement-card">
          <h3>장비 비교해서 어떤게 좋은지</h3>
          <p>{{ comparisonMessage }}</p>
          <strong :class="recommendation === '추천' ? 'recommend-good' : 'recommend-bad'">{{ recommendation }}</strong>
        </section>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import api from "../../services/api";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const auth = useAuthStore();
const item = ref({});
const ownedEquipment = ref(JSON.parse(localStorage.getItem("ownedEquipment") || "[]"));
const actionMessage = ref("");
const price = computed(() => Number(item.value.price || 0).toLocaleString("ko-KR"));
const detail = computed(() => equipmentDetails[item.value.type] || equipmentDetails.default);
const maker = computed(() => detail.value.maker(item.value.name || ""));
const equipmentImage = computed(() => createEquipmentArtwork(item.value.name || "GameFit Gear", item.value.type || "GEAR", detail.value.colors));
const isOwned = computed(() => ownedEquipment.value.includes(item.value.name));
const recommendation = computed(() => {
  if (item.value.type === "VR" && (auth.user?.pc_specs?.vr || "없음") !== "없음") return "비추천";
  return "추천";
});
const comparisonMessage = computed(() => {
  if (item.value.type === "GPU") return "현재 GPU보다 QHD/AAA 게임 여유가 커져서 업그레이드 체감이 큽니다.";
  if (item.value.type === "CPU") return "전략, 시뮬레이션, 대규모 연산 게임에서 프레임 안정성이 좋아집니다.";
  if (item.value.type === "VR") return "VR 게임을 새로 시작하려는 경우에만 우선순위가 높습니다.";
  return "현재 플레이 스타일에 맞춰 선택할 만한 장비입니다.";
});
const timingHeadline = computed(() => {
  if ((item.value.price || 0) > 700000) return "할인 알림 후 구매 추천";
  return "가격 안정권, 필요하면 구매";
});
const timingMessage = computed(() => {
  if ((item.value.price || 0) > 700000) return "고가 장비라 바로 구매보다 카드/특가 할인 시점을 기다리는 편이 좋아요.";
  return "최근 가격이 크게 흔들리지 않아서 필요성이 명확하면 지금 구매해도 무난합니다.";
});
const markets = computed(() => {
  const base = Number(item.value.price || 0) || 100000;
  return [
    { store: "제조사몰", price: base, badge: "정가", url: "https://www.google.com/search?q=" + encodeURIComponent(item.value.name || "") },
    { store: "오픈마켓", price: Math.floor(base * 0.94), badge: "-6%", url: "https://www.google.com/search?q=" + encodeURIComponent(`${item.value.name || ""} 최저가`) },
    { store: "중고/리퍼", price: Math.floor(base * 0.82), badge: "-18%", url: "https://www.google.com/search?q=" + encodeURIComponent(`${item.value.name || ""} 중고`) },
  ].sort((a, b) => a.price - b.price);
});
const priceHistory = computed(() => {
  const base = Number(item.value.price || 0) || 100000;
  return [1.08, 1.03, 1.0, 0.96, 0.98, 0.94].map((ratio) => Math.floor(base * ratio));
});
const priceHistoryPoints = computed(() => {
  const values = priceHistory.value;
  const min = Math.min(...values);
  const max = Math.max(...values);
  return values.map((value, index) => {
    const ratio = max === min ? 0.5 : (value - min) / (max - min);
    return {
      label: `${index + 1}월`,
      x: 34 + index * 106,
      y: 150 - ratio * 118,
    };
  });
});
const priceChartPoints = computed(() => priceHistoryPoints.value.map((point) => `${point.x},${point.y}`).join(" "));
const currentSpecs = computed(() => [
  { label: "CPU", value: auth.user?.pc_specs?.cpu || "AMD 5800X", note: item.value.type === "CPU" ? "비교 대상" : "충분함", highlighted: item.value.type === "CPU" },
  { label: "메모리", value: auth.user?.pc_specs?.memory || "64GB", note: "충분함" },
  { label: "GPU", value: auth.user?.pc_specs?.gpu || "NVIDIA 3070Ti", note: item.value.type === "GPU" ? "업그레이드 후보" : "현재 장비", highlighted: item.value.type === "GPU" },
  { label: "VR", value: auth.user?.pc_specs?.vr || "없음", note: item.value.type === "VR" ? "새 장비 후보" : "필수 아님", highlighted: item.value.type === "VR" },
  { label: "콘솔", value: auth.user?.pc_specs?.console || "없음", note: "PC 기준 비교" },
]);
const ownedGameMatches = computed(() => {
  const games = auth.user?.owned_games?.length ? auth.user.owned_games : ["Civilization VI", "Dead by Daylight"];
  return games.slice(0, 3).map((title) => ({
    title,
    reason: item.value.type === "CPU" ? "시뮬레이션/전략 처리 안정화" : item.value.type === "GPU" ? "그래픽 옵션 여유 확보" : "플레이 경험 확장",
  }));
});
const interestedGameMatches = computed(() => {
  const games = auth.user?.interested_games?.length ? auth.user.interested_games : ["It Takes Two", "Hades II"];
  return games.slice(0, 3).map((title) => ({
    title,
    reason: item.value.type === "VR" ? "VR 지원 여부 확인 추천" : "권장 사양 대비 여유 확보",
  }));
});

const equipmentDetails = {
  CPU: {
    colors: ["#182a4d", "#2563eb", "#8ecae6"],
    maker: (name) => (name.includes("Ryzen") ? "AMD" : name.includes("Intel") ? "Intel" : "CPU 제조사"),
  },
  GPU: {
    colors: ["#14213d", "#16a34a", "#94d2bd"],
    maker: (name) => (name.includes("RTX") || name.includes("NVIDIA") ? "NVIDIA" : name.includes("Radeon") ? "AMD" : "GPU 제조사"),
  },
  VR: {
    colors: ["#33165f", "#7c3aed", "#c4b5fd"],
    maker: (name) => (name.includes("Quest") ? "Meta" : "VR 제조사"),
  },
  default: {
    colors: ["#263238", "#17637d", "#8ad0c2"],
    maker: () => "장비 제조사",
  },
};

function imageBackground(url) {
  if (!url) return {};
  return {
    backgroundImage: `linear-gradient(180deg, rgba(20, 30, 46, 0.08), rgba(20, 30, 46, 0.72)), url("${url}")`,
  };
}

onMounted(async () => {
  const { data } = await api.get(`/catalog/equipment/${route.params.id}/`);
  item.value = data;
});

function toggleOwned() {
  toggleList(ownedEquipment, "ownedEquipment", item.value.name, isOwned.value ? "내 장비에서 제거했어요." : "내 장비에 추가했어요.");
}

function toggleList(listRef, storageKey, name, message) {
  if (!name) return;
  if (listRef.value.includes(name)) {
    listRef.value = listRef.value.filter((itemName) => itemName !== name);
  } else {
    listRef.value = [...listRef.value, name];
  }
  localStorage.setItem(storageKey, JSON.stringify(listRef.value));
  actionMessage.value = `${name}을(를) ${message}`;
}

function createEquipmentArtwork(title, type, colors) {
  const [start, middle, end] = colors;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="520" height="360" viewBox="0 0 520 360">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="${start}" />
          <stop offset="62%" stop-color="${middle}" />
          <stop offset="100%" stop-color="${end}" />
        </linearGradient>
      </defs>
      <rect width="520" height="360" rx="18" fill="url(#bg)" />
      <circle cx="390" cy="72" r="96" fill="#ffffff" opacity="0.16" />
      <rect x="80" y="88" width="180" height="180" rx="24" fill="#ffffff" opacity="0.18" />
      <rect x="118" y="126" width="104" height="104" rx="14" fill="#000000" opacity="0.25" />
      <text x="48" y="304" fill="#ffffff" font-family="Arial, sans-serif" font-size="24" font-weight="800">${escapeSvg(type)}</text>
      <text x="48" y="332" fill="#eaf6ff" font-family="Arial, sans-serif" font-size="16" font-weight="700">${escapeSvg(title)}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function escapeSvg(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
</script>
