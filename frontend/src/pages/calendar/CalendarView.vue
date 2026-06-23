<template>
  <section class="content-stack">
    <header class="page-header">
      <div>
        <p class="eyebrow">캘린더</p>
        <h1>찜한 게임의 할인과 출시 일정</h1>
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
        게임 이름
        <input v-model="gameQuery" placeholder="게임 이름으로 필터링" />
      </label>
    </section>

    <section v-if="viewMode === 'schedule'" class="panel calendar-panel">
      <article v-for="event in filteredEvents" :key="`${event.date}-${event.title}`" :class="['calendar-card', `event-${event.type}`]">
        <time>{{ event.date }}</time>
        <div>
          <strong>{{ event.title }}</strong>
          <p>{{ event.game }} · {{ eventLabel(event.type) }}</p>
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
          <span class="event-sale">할인</span>
          <span class="event-game">게임</span>
          <span class="event-release">출시</span>
        </div>
      </div>
      <div class="calendar-grid">
        <strong v-for="day in weekDays" :key="day">{{ day }}</strong>
        <div v-for="blank in leadingBlanks" :key="`blank-${blank}`" class="calendar-cell muted-cell"></div>
        <div v-for="day in daysInMonth" :key="day" class="calendar-cell">
          <span>{{ day }}</span>
          <p v-for="event in eventsByDay(day)" :key="event.title" :class="`event-${event.type}`">
            <strong>{{ eventLabel(event.type) }}</strong>
            {{ event.game }}
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
const gameQuery = ref("");
const currentYear = ref(2026);
const currentMonth = ref(6);
const weekDays = ["월", "화", "수", "목", "금", "토", "일"];
const filters = [
  { label: "전체", value: "all" },
  { label: "할인", value: "sale" },
  { label: "게임", value: "game" },
  { label: "출시", value: "release" },
];
const fallbackGames = {
  "Steam 여름 할인 시작": "Steam 전체",
  "It Takes Two 할인 종료": "It Takes Two",
  "관심 게임 출시 예정": "Civilization VII",
};

onMounted(async () => {
  const { data } = await api.get("/catalog/calendar/");
  events.value = [
    ...data.map((event) => ({
      ...event,
      game: fallbackGames[event.title] || event.title,
      type: event.type === "alert" ? "game" : event.type,
    })),
    { date: "2026-06-12", title: "Hades II 패치 업데이트", game: "Hades II", type: "game" },
    { date: "2026-06-18", title: "Civilization VII 예약 할인", game: "Civilization VII", type: "sale" },
    { date: "2026-06-30", title: "인디 신작 출시", game: "신규 인디 게임", type: "release" },
  ];
});

const filteredEvents = computed(() => {
  const keyword = gameQuery.value.trim().toLowerCase();
  return events.value.filter((event) => {
    const matchesType = activeFilter.value === "all" || event.type === activeFilter.value;
    const matchesKeyword =
      !keyword ||
      [event.game, event.title].some((value) => String(value).toLowerCase().includes(keyword));
    return matchesType && matchesKeyword;
  });
});
const daysInMonth = computed(() => new Date(currentYear.value, currentMonth.value, 0).getDate());
const leadingBlanks = computed(() => {
  const day = new Date(currentYear.value, currentMonth.value - 1, 1).getDay();
  return day === 0 ? 6 : day - 1;
});

function eventLabel(type) {
  return { sale: "할인", game: "게임", release: "출시" }[type] || type;
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
