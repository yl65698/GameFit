import { defineStore } from "pinia";

const STORAGE_KEY = "gamefitTheme";
const TONE_STORAGE_KEY = "gamefitThemeTone";
const LEGACY_THEME_MAP = {
  pixel: { family: "pixel", tone: "day" },
  neon: { family: "neon", tone: "night" },
};
const DEFAULT_FAMILY = "pixel";
const DEFAULT_TONE = "day";
const THEME_FAMILIES = [
  { value: "pixel", label: "Pixel" },
  { value: "neon", label: "Neon" },
];
const THEME_TONES = [
  { value: "day", label: "Day" },
  { value: "night", label: "Night" },
];
const VALID_FAMILIES = THEME_FAMILIES.map((theme) => theme.value);
const VALID_TONES = THEME_TONES.map((tone) => tone.value);

export const useThemeStore = defineStore("theme", {
  state: () => ({
    family: readStoredFamily(),
    tone: readStoredTone(),
    families: THEME_FAMILIES,
    tones: THEME_TONES,
  }),
  getters: {
    mode: (state) => `${state.family}-${state.tone}`,
  },
  actions: {
    init() {
      this.applyTheme();
    },
    setFamily(family) {
      this.family = VALID_FAMILIES.includes(family) ? family : DEFAULT_FAMILY;
      this.persistTheme();
      this.applyTheme();
    },
    setTone(tone) {
      this.tone = VALID_TONES.includes(tone) ? tone : DEFAULT_TONE;
      this.persistTheme();
      this.applyTheme();
    },
    setMode(mode) {
      const [family, tone] = String(mode).split("-");
      this.family = VALID_FAMILIES.includes(family) ? family : DEFAULT_FAMILY;
      this.tone = VALID_TONES.includes(tone) ? tone : DEFAULT_TONE;
      this.persistTheme();
      this.applyTheme();
    },
    toggleFamily() {
      const currentIndex = VALID_FAMILIES.indexOf(this.family);
      this.setFamily(VALID_FAMILIES[(currentIndex + 1) % VALID_FAMILIES.length]);
    },
    toggleTone() {
      const currentIndex = VALID_TONES.indexOf(this.tone);
      this.setTone(VALID_TONES[(currentIndex + 1) % VALID_TONES.length]);
    },
    persistTheme() {
      localStorage.setItem(STORAGE_KEY, this.family);
      localStorage.setItem(TONE_STORAGE_KEY, this.tone);
    },
    applyTheme() {
      document.documentElement.dataset.theme = this.family;
      document.documentElement.dataset.themeTone = this.tone;
      document.documentElement.dataset.themeMode = this.mode;
      document.documentElement.style.colorScheme = this.tone === "night" ? "dark" : "light";
    },
  },
});

function readStoredFamily() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (VALID_FAMILIES.includes(stored)) {
    return stored;
  }

  if (stored && LEGACY_THEME_MAP[stored]) {
    return LEGACY_THEME_MAP[stored].family;
  }

  return DEFAULT_FAMILY;
}

function readStoredTone() {
  const storedTone = localStorage.getItem(TONE_STORAGE_KEY);
  if (VALID_TONES.includes(storedTone)) {
    return storedTone;
  }

  const storedTheme = localStorage.getItem(STORAGE_KEY);
  if (storedTheme && LEGACY_THEME_MAP[storedTheme]) {
    return LEGACY_THEME_MAP[storedTheme].tone;
  }

  return DEFAULT_TONE;
}
