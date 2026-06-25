import { defineStore } from "pinia";

const STORAGE_KEY = "gamefitTheme";
const DEFAULT_THEME = "pixel";
const THEME_MODES = [
  { value: "pixel", label: "Pixel" },
  { value: "neon", label: "Neon" },
];
const VALID_THEMES = THEME_MODES.map((theme) => theme.value);

export const useThemeStore = defineStore("theme", {
  state: () => ({
    mode: readStoredTheme(),
    modes: THEME_MODES,
  }),
  actions: {
    init() {
      this.applyTheme();
    },
    setMode(mode) {
      this.mode = VALID_THEMES.includes(mode) ? mode : DEFAULT_THEME;
      localStorage.setItem(STORAGE_KEY, this.mode);
      this.applyTheme();
    },
    toggle() {
      const currentIndex = VALID_THEMES.indexOf(this.mode);
      this.setMode(VALID_THEMES[(currentIndex + 1) % VALID_THEMES.length]);
    },
    applyTheme() {
      document.documentElement.dataset.theme = this.mode;
      document.documentElement.style.colorScheme = this.mode === "neon" ? "dark" : "light";
    },
  },
});

function readStoredTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  return VALID_THEMES.includes(stored) ? stored : DEFAULT_THEME;
}
