<template>
  <section class="content-stack">
    <RouterLink class="back-link" to="/equipment">목록으로 돌아가기</RouterLink>

    <header class="detail-header">
      <div class="detail-art equipment-art">
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

    <div class="detail-layout">
      <section class="panel price-panel">
        <h2>가격 변동 추이</h2>
        <div class="bar-chart">
          <i style="height: 50%"></i>
          <i style="height: 64%"></i>
          <i style="height: 45%"></i>
          <i style="height: 38%"></i>
          <i style="height: 54%"></i>
        </div>
      </section>
      <aside class="panel compatibility-card">
        <h2>장비 비교</h2>
        <strong>추천 / 비추천</strong>
        <p>현재 장비 대비 성능과 가격 효율을 비교합니다.</p>
      </aside>
      <section class="panel">
        <h2>가격 비교</h2>
        <p>제조사 가격 {{ price }}원</p>
      </section>
      <section class="panel">
        <h2>구매 타이밍 추천</h2>
        <p>가격 안정 구간. 급하지 않으면 할인 알림 등록을 추천합니다.</p>
      </section>
      <section class="panel">
        <h2>보유 게임 적합 장비</h2>
        <p>{{ item.fit }}</p>
      </section>
      <section class="panel">
        <h2>관심 게임 적합 장비</h2>
        <p>AAA 게임 권장 사양에 여유가 있습니다.</p>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import api from "../../services/api";

const route = useRoute();
const item = ref({});
const price = computed(() => Number(item.value.price || 0).toLocaleString("ko-KR"));

onMounted(async () => {
  const { data } = await api.get(`/catalog/equipment/${route.params.id}/`);
  item.value = data;
});
</script>
