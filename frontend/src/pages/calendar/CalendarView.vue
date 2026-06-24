<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">캘린더</p>
        <h1>게임 할인 및 출시 일정</h1>
      </div>
      <div class="panel-actions">
        <div class="segmented-control">
          <button :class="{ active: viewMode === 'schedule' }" @click="viewMode = 'schedule'">일정버전으로 보기</button>
          <button :class="{ active: viewMode === 'calendar' }" @click="viewMode = 'calendar'">캘린더로 보기</button>
        </div>
      </div>
    </header>

    <section class="panel calendar-filter-panel">
      <div class="filter-row">
        <button v-for="filter in filters" :key="filter.value" class="filter-chip" :class="{ active: activeFilter === filter.value }" @click="activeFilter = filter.value">
          {{ filter.label }}
        </button>
      </div>
      <label class="calendar-name-filter">
        검색
        <input v-model="searchQuery" placeholder="이름으로 필터링" />
      </label>
    </section>

    <section v-if="viewMode === 'schedule'" class="panel calendar-panel">
      <article v-for="event in filteredEvents" :key="`${event.date}-${event.title}`" :class="['calendar-card', `event-${event.type}`]">
        <time>{{ event.date }}</time>
        <div>
          <strong>{{ event.title }}</strong>
          <p>{{ event.description || eventLabel(event.type) }}</p>
        </div>
      </article>
      <p v-if="filteredEvents.length === 0" class="subtle">조건에 맞는 일정이 없습니다.</p>
    </section>

    <section v-else class="panel month-calendar">
      <div class="month-header">
        <div class="month-nav">
          <button class="secondary-button" @click="moveMonth(-1)">이전 달</button>
          <h2>{{ currentYear }}년 {{ currentMonth }}월</h2>
          <button class="secondary-button" @click="moveMonth(1)">다음 달</button>
        </div>
        <div class="calendar-legend">
          <span class="event-discount">할인</span>
          <span class="event-game_release">게임 출시</span>
          <span class="event-hardware_release">장비 출시</span>
        </div>
      </div>
      <div class="calendar-grid">
        <strong v-for="day in weekDays" :key="day">{{ day }}</strong>
        <div v-for="blank in leadingBlanks" :key="`blank-${blank}`" class="calendar-cell muted-cell"></div>
        <div v-for="day in daysInMonth" :key="day" class="calendar-cell">
          <span>{{ day }}</span>
          <p v-for="event in eventsByDay(day)" :key="event.title" :class="`event-${event.type}`">
            <strong>{{ eventLabel(event.type) }}</strong>
            {{ event.title }}
          </p>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import api from "../../services/api";

const events = ref([]);
const viewMode = ref("schedule");
const activeFilter = ref("all");
const searchQuery = ref("");
const currentYear = ref(new Date().getFullYear());
const currentMonth = ref(new Date().getMonth() + 1);
const weekDays = ["월", "화", "수", "목", "금", "토", "일"];
const filters = [
  { label: "전체", value: "all" },
  { label: "할인", value: "discount" },
  { label: "게임 출시", value: "game_release" },
  { label: "장비 출시", value: "hardware_release" },
];

onMounted(async () => {
  const { data } = await api.get("/catalog/calendar/");
  events.value = data;
});

const filteredEvents = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase();
  return events.value.filter((event) => {
    const matchesType = activeFilter.value === "all" || event.type === activeFilter.value;
    const matchesKeyword =
      !keyword ||
      [event.title, event.description].some((v) => String(v || "").toLowerCase().includes(keyword));
    return matchesType && matchesKeyword;
  });
});

const daysInMonth = computed(() => new Date(currentYear.value, currentMonth.value, 0).getDate());
const leadingBlanks = computed(() => {
  const day = new Date(currentYear.value, currentMonth.value - 1, 1).getDay();
  return day === 0 ? 6 : day - 1;
});

function eventLabel(type) {
  return { discount: "할인", game_release: "게임 출시", hardware_release: "장비 출시" }[type] || type;
}

function eventsByDay(day) {
  return filteredEvents.value.filter((event) => {
    const [year, month, date] = event.date.split("-").map(Number);
    return year === currentYear.value && month === currentMonth.value && date === day;
  });
}

function moveMonth(delta) {
  const next = new Date(currentYear.value, currentMonth.value - 1 + delta, 1);
  currentYear.value = next.getFullYear();
  currentMonth.value = next.getMonth() + 1;
}
</script>
