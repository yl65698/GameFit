import { createRouter, createWebHistory } from "vue-router";

import TasteAnalysisView from "../pages/analysis/TasteAnalysisView.vue";
import CalendarView from "../pages/calendar/CalendarView.vue";
import CommunityView from "../pages/community/CommunityView.vue";
import EquipmentDetailView from "../pages/equipment/EquipmentDetailView.vue";
import EquipmentExploreView from "../pages/equipment/EquipmentExploreView.vue";
import GameDetailView from "../pages/games/GameDetailView.vue";
import GameExploreView from "../pages/games/GameExploreView.vue";
import ProfileEditView from "../pages/profile/ProfileEditView.vue";
import PlayerProfileView from "../pages/profile/PlayerProfileView.vue";
import ProfileView from "../pages/profile/ProfileView.vue";
import WelcomeView from "../pages/welcome/WelcomeView.vue";
import { useAuthStore } from "../stores/auth";

const routes = [
  { path: "/", name: "welcome", component: WelcomeView },
  { path: "/profile", name: "profile", component: ProfileView, meta: { requiresAuth: true } },
  { path: "/profile/edit", name: "profile-edit", component: ProfileEditView, meta: { requiresAuth: true } },
  { path: "/players/:username", name: "player-profile", component: PlayerProfileView, meta: { requiresAuth: true } },
  { path: "/games", name: "games", component: GameExploreView, meta: { requiresAuth: true } },
  { path: "/games/:id", name: "game-detail", component: GameDetailView, meta: { requiresAuth: true } },
  { path: "/games/:id/community", name: "community", component: CommunityView, meta: { requiresAuth: true } },
  { path: "/equipment", name: "equipment", component: EquipmentExploreView, meta: { requiresAuth: true } },
  { path: "/equipment/:id", name: "equipment-detail", component: EquipmentDetailView, meta: { requiresAuth: true } },
  { path: "/taste", name: "taste", component: TasteAnalysisView, meta: { requiresAuth: true } },
  { path: "/calendar", name: "calendar", component: CalendarView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: "welcome", query: { auth: "login", next: to.fullPath } };
  }
  return true;
});

export default router;
