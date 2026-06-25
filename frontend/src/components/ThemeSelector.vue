<template>
  <div class="theme-selector" role="group" aria-label="Theme mode selector">
    <div class="theme-selector-segment" aria-label="Theme style">
      <button
        v-for="family in theme.families"
        :key="family.value"
        type="button"
        :class="{ active: theme.family === family.value }"
        :aria-pressed="theme.family === family.value"
        @click="theme.setFamily(family.value)"
      >
        <span class="theme-selector-dot" :class="`theme-selector-dot--${family.value}`"></span>
        {{ family.label }}
      </button>
    </div>
    <span class="theme-selector-divider" aria-hidden="true"></span>
    <div class="theme-selector-segment" aria-label="Theme brightness">
      <button
        v-for="tone in theme.tones"
        :key="tone.value"
        type="button"
        :class="{ active: theme.tone === tone.value }"
        :aria-pressed="theme.tone === tone.value"
        @click="theme.setTone(tone.value)"
      >
        {{ tone.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useThemeStore } from "../stores/theme";

const theme = useThemeStore();
</script>
