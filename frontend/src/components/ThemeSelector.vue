<template>
  <div class="theme-selector" role="group" aria-label="화면 스타일 모드 선택">
    <button
      v-for="mode in theme.modes"
      :key="mode.value"
      type="button"
      :class="{ active: theme.mode === mode.value }"
      :aria-pressed="theme.mode === mode.value"
      @click="theme.setMode(mode.value)"
    >
      <span class="theme-selector-dot" :class="`theme-selector-dot--${mode.value}`"></span>
      {{ mode.label }}
    </button>
  </div>
</template>

<script setup>
import { useThemeStore } from "../stores/theme";

const theme = useThemeStore();
</script>
