<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">장비 탐색</p>
        <h1>장비 검색 및 추천</h1>
        <p class="subtle">CPU, GPU, VR, 주변 장치를 분류별로 찾거나 원하는 조건을 자연어로 입력해 추천받습니다.</p>
      </div>
    </header>

    <section class="panel equipment-search-panel">
      <div class="search-mode-tabs equipment-type-tabs">
        <button v-for="type in searchTypes" :key="type.value" :class="{ active: selectedType === type.value }" @click="chooseType(type.value)">
          {{ type.label }}
        </button>
      </div>

      <div class="equipment-search-row">
        <input v-model="query" placeholder="장비명, 용도, 게임명으로 검색" @input="clearAiResults" />
        <button class="secondary-button" @click="resetSearch">초기화</button>
      </div>

      <form class="ai-equipment-search" @submit.prevent="runAiRecommendation">
        <label>
          LLM 장비 추천
          <textarea v-model="aiPrompt" placeholder="예: QHD에서 전략 게임이랑 협동 게임을 쾌적하게 하고 싶은데 GPU를 추천해줘" />
        </label>
        <button class="primary-button" :disabled="aiLoading">
          {{ aiLoading ? "추천 중..." : "추천 받기" }}
        </button>
      </form>

      <p v-if="aiSummary" class="ai-summary">{{ aiSummary }}</p>
      <p v-if="aiError" class="error-text">{{ aiError }}</p>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <h2>{{ activeTitle }}</h2>
        <span>{{ filtered.length }}개</span>
      </div>
      <div class="equipment-grid">
        <RouterLink v-for="item in filtered" :key="item.id" class="equipment-card" :to="`/equipment/${item.id}`">
          <div class="equipment-thumb" :style="imageBackground(item.image_url)">
            <span>{{ item.type }}</span>
          </div>
          <span>{{ item.type }}</span>
          <strong>{{ item.name }}</strong>
          <p>{{ item.fit }}</p>
          <em>{{ Number(item.price).toLocaleString("ko-KR") }}원</em>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import aiApi from "../../services/aiApi";
import api from "../../services/api";

const query = ref("");
const selectedType = ref("all");
const aiPrompt = ref("");
const aiSummary = ref("");
const aiError = ref("");
const aiLoading = ref(false);
const aiResults = ref([]);
const equipment = ref([]);
const extraEquipment = [
  { id: 101, name: "Logitech G Pro X Superlight", type: "주변장치", price: 169000, fit: "FPS와 빠른 클릭 중심 플레이용 경량 마우스" },
  { id: 102, name: "SteelSeries Arctis Nova 7", type: "주변장치", price: 249000, fit: "협동 게임 음성 채팅과 공간감 추천" },
  { id: 103, name: "32GB DDR5 6000MHz", type: "메모리", price: 148000, fit: "전략/시뮬레이션 멀티태스킹 안정화" },
  { id: 104, name: "2TB NVMe SSD", type: "저장장치", price: 189000, fit: "대용량 AAA 게임 설치 공간 확보" },
];
const searchTypes = [
  { label: "통합", value: "all" },
  { label: "CPU", value: "CPU" },
  { label: "GPU", value: "GPU" },
  { label: "VR", value: "VR" },
  { label: "주변장치", value: "주변장치" },
];

onMounted(async () => {
  const { data } = await api.get("/catalog/equipment/");
  equipment.value = [...data, ...extraEquipment];
});

const activeTitle = computed(() => searchTypes.find((type) => type.value === selectedType.value)?.label || "통합");
const filtered = computed(() => {
  if (aiResults.value.length) return aiResults.value;
  const keyword = query.value.trim().toLowerCase();
  return equipment.value.filter((item) => {
    const matchesType = selectedType.value === "all" || item.type === selectedType.value;
    const matchesKeyword =
      !keyword ||
      [item.name, item.type, item.fit].some((value) => String(value).toLowerCase().includes(keyword));
    return matchesType && matchesKeyword;
  });
});

function imageBackground(url) {
  if (!url) return {};
  return {
    backgroundImage: `linear-gradient(180deg, rgba(248, 250, 252, 0.05), rgba(15, 23, 42, 0.52)), url("${url}")`,
  };
}

function runAiRecommendation() {
  const prompt = aiPrompt.value.trim();
  if (!prompt) return;
  aiError.value = "";
  aiSummary.value = "";
  aiLoading.value = true;

  try {
    const { data } = await aiApi.post("/ai/equipment-search", {
      query: prompt,
      equipment: equipment.value,
    });
    aiResults.value = data.results;
    aiSummary.value = data.summary;
    selectedType.value = "all";
    query.value = "";
  } catch (error) {
    aiError.value = "AI 장비 추천 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인해주세요.";
  } finally {
    aiLoading.value = false;
  }
}

function chooseType(type) {
  selectedType.value = type;
  clearAiResults();
}

function resetSearch() {
  query.value = "";
  aiPrompt.value = "";
  aiSummary.value = "";
  aiError.value = "";
  clearAiResults();
}

function clearAiResults() {
  aiResults.value = [];
}
</script>
