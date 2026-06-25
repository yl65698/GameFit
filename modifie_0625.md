# 2026-06-25 변경 사항 정리

## 1. 성향 분석 3D Vector Map 개선

**`frontend/src/pages/analysis/TasteAnalysisView.vue`**

- 게임 장르를 하나의 성향 축에만 연결하던 구조를 수정했습니다.
- 게임 장르 후보 중 앞쪽 2개를 사용해 메인/서브 성향 축을 계산하도록 변경했습니다.
  - 예: `fps, 전략` → 메인 `액션형`, 서브 `공략가형`
- 게임 노드는 메인 축에 더 가깝게 배치되도록 `메인 68% + 서브 32%` 위치 계산을 적용했습니다.
- 메인 축 연결선은 진하게, 서브 축 연결선은 옅게 표시되도록 했습니다.
- `shooter`, `action`, `racing`, `souls`, `casual`, `coop`, `multiplayer` 등 추가 장르 키 매핑을 보강했습니다.
- 깨진 문자열 감지 함수 `looksBroken()`의 깨진 샘플 문자를 유니코드 escape 기반으로 정리했습니다.

---

## 2. 도트 원정대 미니게임 조작 개선

**`frontend/src/pages/analysis/TasteMiniGameView.vue`**

- 선택지 조작을 마우스 클릭뿐 아니라 키보드로도 가능하게 개선했습니다.
- 대화 선택지가 열린 상태에서 다음 입력을 지원합니다.
  - 방향키 / WASD: 선택지 이동
  - Space / Z: 현재 선택된 선택지 확정
  - 1 / 2 / 3: 해당 번호 선택지 즉시 선택
- 현재 선택된 선택지를 관리하는 `selectedChoiceIndex` 상태를 추가했습니다.
- 선택지 이동/확정 로직을 `moveChoice()`, `pickChoice()`로 분리했습니다.
- 시작 선택지에도 키보드 확정이 동작하도록 처리했습니다.
- 플레이어 기준으로 맵이 움직이는 카메라 구조를 추가했습니다.
  - 월드 폭 `WORLD_W` 추가
  - NPC 위치를 월드 오른쪽으로 이동
  - 플레이어가 이동하면 `cameraX` 기준으로 바닥, NPC, 캐릭터가 스크롤되도록 처리
  - 상호작용 판정은 기존 월드 좌표 기준을 유지

**`frontend/src/styles.css`**

- 선택된 미니게임 선택지에 `.bit-choice.selected` 하이라이트 스타일을 추가했습니다.

---

## 2-1. 도트 원정대 미니게임 스테이지별 게임 요소 추가

**`frontend/src/pages/analysis/TasteMiniGameView.vue`**

### HUD (항상 표시)
- 게임 화면 상단에 HP(하트)와 코인 수를 항상 표시하도록 HUD를 개선했습니다.
- `gameHp`(최대 5), `gameCoins` 상태를 추가했습니다.
- 피격 시 1500ms 무적 시간(`invincible`)이 적용되며, 무적 중 플레이어가 깜빡이는 시각 효과를 추가했습니다.

### Stage 1 — rival (경쟁자 구역): 투사체 피하기
- 화면 오른쪽에서 화염구가 날아오고, W 키 점프로 피해야 합니다.
- 화염구에 맞으면 HP가 1 감소합니다.
- 스폰 타이머(`spawnTimer`)로 일정 간격마다 화염구가 생성됩니다.

### Stage 2 — helper (협력 구역): 장애물 점프
- 길목에 뾰족한 장애물 6개가 배치됩니다.
- 장애물에 부딪히면 HP가 1 감소하며 튕겨납니다.
- 무적 시간 중에는 장애물을 통과할 수 있어 진행이 막히지 않습니다.

### Stage 3 — scenery (숲 구역): 반짝 보석 수집
- 배경을 반딧불이, 빛 기둥, 바닥 파티클, 캐노피 빛 번짐 등으로 대폭 개선했습니다.
- 기존에 화면을 따라다니던 떠 있는 섬을 월드 좌표계(`x=838`)로 고정해 NPC 근처에만 표시되도록 수정했습니다.
- 월드 곳곳에 초록 보석 7개를 배치했습니다.
  - 보석 y 위치를 `FLOOR-68 ~ FLOOR-76`으로 설정해 서 있는 상태에서는 수집 불가, 점프해야 수집 가능합니다.
  - 수집 시 `gameCoins`가 1 증가합니다.

### Stage 4 — ruin (폐허 구역): 몬스터 처치
- 작은 몬스터 3마리가 초기 배치되고, 이후 일정 간격으로 화면 오른쪽에서 추가 등장합니다.
- 몬스터는 플레이어 방향으로 걸어옵니다.
- Z / Space 키로 공격해 몬스터를 처치하면 `gameCoins`가 1 증가합니다.
- 공격 범위는 플레이어가 바라보는 방향 앞쪽 36px이며, 공격 애니메이션 280ms 중에는 재공격이 불가합니다.
- 몬스터에 닿으면 HP가 1 감소합니다.
- Z / Space 키는 NPC 근처에서는 대화 상호작용, 몬스터 구역에서는 공격으로 구분됩니다.

### Stage 5 — market (시장 구역): 코인 수집
- 길바닥에 금화 15개가 일정 간격으로 배치됩니다.
- 별도 조작 없이 걸어가면 자동으로 수집되며 `gameCoins`가 1 증가합니다.
- 장애물이나 적 없이 이동에만 집중할 수 있는 구간입니다.

### 공통 구조 변경
- `initStage(sceneId)` 함수를 추가해 스테이지 전환 시 투사체·장애물·아이템·몬스터·코인 배열을 초기화하고 해당 스테이지 요소를 세팅합니다.
- `hitPlayer()` 함수를 추가해 피격 처리(HP 감소, 무적 발동, 피격음)를 통합했습니다.
- `handleAttack()` 함수를 추가해 공격 범위 내 몬스터를 처치하는 로직을 분리했습니다.
- 스테이지별 힌트 문구(`gameHint`)를 조작 방법에 맞게 변경했습니다.
- 스테이지 진입·리셋 시 HP와 코인이 올바르게 초기화되도록 했습니다.

**`frontend/src/styles.css`**

- HUD 관련 스타일을 추가했습니다.
  - `.bit-hud-left`, `.bit-hud-right`: 좌우 영역 세로 정렬
  - `.bit-hud-hp`, `.hp-heart`, `.hp-full`, `.hp-empty`: HP 하트 표시
  - `.bit-hud-coins`: 금화 수 표시 (금색)

---

## 3. 할인 캘린더 기본 보기 변경

**`frontend/src/pages/calendar/CalendarView.vue`**

- 보기 전환 버튼 순서를 변경했습니다.
  - 기존: `일정버전으로 보기 / 캘린더로 보기`
  - 변경: `캘린더로 보기 / 일정버전으로 보기`
- 기본 보기 모드를 `schedule`에서 `calendar`로 변경했습니다.

---

## 4. 전체 화면 스타일 모드 시스템 추가

**`frontend/src/stores/theme.js`** 신규 생성

- 전역 테마 상태를 관리하는 Pinia store를 추가했습니다.
- 선택한 테마를 `localStorage`에 저장하도록 했습니다.
- 앱 전체에 `document.documentElement.dataset.theme` 값으로 테마를 적용합니다.
- 현재 지원 모드는 `pixel`, `neon`입니다.
- 기본 테마는 `pixel`입니다.

**`frontend/src/components/ThemeSelector.vue`** 신규 생성

- 공통 테마 선택 UI를 추가했습니다.
- `Pixel / Neon` 버튼을 통해 전체 화면 스타일 모드를 변경할 수 있습니다.

**`frontend/src/App.vue`**

- 로그인 후 보이는 상단 네비게이션 바에 `ThemeSelector`를 추가했습니다.
- 앱 mounted 시 저장된 테마가 적용되도록 `theme.init()`을 호출합니다.

**`frontend/src/pages/welcome/WelcomeView.vue`**

- 메인 화면 우측 계정정보 영역 옆에 `ThemeSelector`를 추가했습니다.
- 로그인하지 않은 상태에서도 메인 화면에서 테마를 선택할 수 있게 했습니다.

**`frontend/src/styles.css`**

- 테마별 확장을 위해 CSS 변수 구조를 정리했습니다.
- 공통 토큰을 추가했습니다.
  - 폰트: `--theme-font-body`, `--theme-font-display`, `--theme-font-ui`
  - 모양: `--theme-card-radius`, `--theme-control-radius`, `--theme-pill-radius`
  - 색상: `--clr-page`, `--clr-surface`, `--clr-surface-soft`, `--clr-text`, `--clr-heading`, `--clr-border`
  - 상단바: `--topbar-bg`, `--topbar-text`, `--topbar-border`
- `pixel`과 `neon`이 서로 다른 색, 폰트, radius, shadow를 가질 수 있도록 분리했습니다.
- 기존 `light/dark` 명칭은 제거하고 `pixel/neon` 기준으로 정리했습니다.
- CSS minify 경고를 만들던 깨진 한글 카테고리 클래스 선택자 블록을 제거했습니다.

---

## 5. 다른 유저 프로필 PC 사양 표시 개선

**`frontend/src/pages/profile/PlayerProfileView.vue`**

- 다른 유저 프로필(`/players/:username`)에서 PC 사양 값이 배열이면 제품별로 줄을 나눠 표시하도록 변경했습니다.
- 메모리 값이 배열이 아니라 붙어 있는 문자열로 내려오는 경우도 분리하도록 표시용 헬퍼를 추가했습니다.
  - `specDisplayItems()`
  - `normalizeSpecText()`
  - `parseArrayText()`
  - `splitMemoryText()`
- 예시처럼 붙어서 내려오는 메모리 문자열을 제품별로 분리합니다.
  - `CORSAIR ... BlackG 트라이던트 ...`
  - `CORSAIR ... Black`
  - `G 트라이던트 ...`
- `PlayerProfileView.vue` 내부에 scoped 스타일을 추가해 다른 유저 프로필에서도 제품이 세로 목록으로 표시되도록 했습니다.

**`frontend/src/pages/profile/ProfileView.vue`**

- 내 프로필의 배열형 PC 사양도 `spec-chip-list`로 감싸 세로 표시가 가능하도록 맞췄습니다.

---

## 6. 검증

다음 명령으로 프론트엔드 빌드를 여러 차례 확인했습니다.

```bash
npm.cmd run build
```

- Vite production build 통과
- CSS 문법 경고 제거 확인
- chunk size 경고는 기존 번들 크기 관련 경고로 남아 있음

