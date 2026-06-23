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
        <button v-for="type in searchTypes" :key="type.value" :class="{ active: selectedType === type.value }" @click="selectedType = type.value">
          {{ type.label }}
        </button>
      </div>

      <div class="equipment-search-row">
        <input v-model="query" placeholder="장비명, 용도, 게임명으로 검색" />
        <button class="secondary-button" @click="query = ''">초기화</button>
      </div>

      <form class="ai-equipment-search" @submit.prevent="runAiRecommendation">
        <label>
          LLM 장비 추천
          <textarea v-model="aiPrompt" placeholder="예: QHD에서 전략 게임이랑 협동 게임을 쾌적하게 하고 싶은데 GPU를 추천해줘" />
        </label>
        <button class="primary-button">추천 받기</button>
      </form>

      <p v-if="aiSummary" class="ai-summary">{{ aiSummary }}</p>
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

import api from "../../services/api";

const query = ref("");
const selectedType = ref("all");
const aiPrompt = ref("");
const aiSummary = ref("");
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
  const lower = prompt.toLowerCase();

  if (lower.includes("vr")) {
    selectedType.value = "VR";
    query.value = "quest";
    aiSummary.value = "VR 플레이가 목적이면 Meta Quest 3부터 확인하는 걸 추천해요.";
    return;
  }

  if (lower.includes("qhd") || lower.includes("gpu") || prompt.includes("그래픽")) {
    selectedType.value = "GPU";
    query.value = "4070";
    aiSummary.value = "QHD 기준이면 RTX 4070 SUPER급 GPU가 가장 먼저 볼 후보예요.";
    return;
  }

  if (lower.includes("cpu") || prompt.includes("전략") || prompt.includes("시뮬")) {
    selectedType.value = "CPU";
    query.value = "7800";
    aiSummary.value = "전략/시뮬레이션 게임은 Ryzen 7 7800X3D 같은 CPU 업그레이드가 체감이 커요.";
    return;
  }

  selectedType.value = "all";
  query.value = "";
  aiSummary.value = "조건이 넓어서 CPU, GPU, 저장장치 후보를 함께 비교해보는 걸 추천해요.";
}
</script>
