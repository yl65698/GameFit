# 세션 변경 사항 정리

## 1. 커뮤니티 기능 전면 개편

### 백엔드

**`backend/games/models.py`**
- `Post` 모델에 `category` 필드 추가 (7가지 말머리: 공략/질문/구매상담/그룹모집/후기/잡담/기타)
- `GameGroup` 모델에 `schedule`, `play_style`, `required_role`, `capacity` 필드 추가

**`backend/games/migrations/0012_gamegroup_capacity_gamegroup_play_style_and_more.py`**
- 위 모델 변경에 대한 마이그레이션 파일 (적용 완료)

**`backend/catalog/community_views.py`** (신규 생성)
- 9개 API 뷰 클래스 구현:
  - `CommunityPostListView` — 게시글 목록 조회 / 작성
  - `CommunityPostDetailView` — 게시글 상세 조회 + 댓글 목록 / 게시글 삭제(본인만)
  - `CommunityPostLikeView` — 추천 토글 (계정별 M2M, 추천↔추천취소)
  - `CommunityCommentView` — 댓글 작성
  - `CommunityCommentDeleteView` — 댓글 삭제(본인만)
  - `CommunityGroupListView` — 그룹 목록 조회 / 그룹 생성
  - `CommunityGroupJoinView` — 그룹 참가 (인원 초과 체크)
  - `CommunityGroupLeaveView` — 그룹 탈퇴 (오너 양도, 빈 그룹 자동 삭제)
- 공통 헬퍼: `_avatar_url()`, `_post_to_dict()`, `_group_to_dict()`
- 모든 응답에 `author_username`, `author_avatar`, `memberList` 포함

**`backend/catalog/urls.py`**
- 커뮤니티 관련 URL 9개 추가:
  ```
  games/<id>/community/posts/
  games/<id>/community/posts/<id>/
  games/<id>/community/posts/<id>/like/
  games/<id>/community/posts/<id>/comments/
  games/<id>/community/comments/<id>/
  games/<id>/community/groups/
  games/<id>/community/groups/<id>/join/
  games/<id>/community/groups/<id>/leave/
  ```

### 프론트엔드

**`frontend/src/pages/community/CommunityView.vue`** (전면 재작성)
- `gameTitle` 하드코딩 제거 → `GET /catalog/games/{id}/` API 호출
- 부제목("게임 공략, 구매 타이밍...") 삭제
- 모든 게시글/댓글/그룹 동작이 실제 API 연동 (클라이언트 상태 조작 없음)
- 말머리 7종 필터 칩 추가
- 추천 버튼: `is_liked` 기반으로 추천↔추천취소 토글
- 댓글 타임스탬프 + 본인 댓글 삭제 버튼 추가

---

## 2. 프로필 사진 + 클릭 가능한 닉네임

### 게시글 상세 (CommunityView)
- 닉네임 좌측에 프로필 사진 표시 (없으면 이니셜)
- 닉네임 클릭 시 `/players/{username}` 프로필 페이지 이동

### 댓글 (CommunityView)
- 댓글 작성자 프로필 사진 + 닉네임 링크 추가

### 그룹 구성원 (CommunityView)
- 구성원 칩 → 각 유저 프로필 링크 (`/players/{username}`)
- `memberList` 배열(name, username, avatar)로 렌더링

### 게임 상세 의견 목록 (GameDetailView)

**`backend/games/serializers.py`**
- `GameReviewSerializer`에 `user_username`, `avatar`, `avatar_url` 필드 추가
- `get_avatar_url()`에서 `request.build_absolute_uri()` 사용해 절대 URL 반환

**`backend/games/views.py`**
- `game_reviews()` 뷰에서 `context={'request': request}` 시리얼라이저에 전달

**`frontend/src/pages/games/GameDetailView.vue`**
- 리뷰 카드에 프로필 사진 추가 (없으면 이니셜)
- 작성자 닉네임 클릭 시 `/players/{username}` 이동

---

## 3. 게임 탐색 카드 정리

**`frontend/src/pages/games/GameExploreView.vue`**
- 게임 카드 하단 "지금 구매 추천" (`buy_signal`) 텍스트 삭제
- 카드 footer에 장르만 표시

---

## 4. 캘린더 기능 개편

**`backend/games/models.py`**
- `CalendarEvent` 모델 신규 추가 (date, title, description, event_type, url)
- `event_type` choices: `discount` / `game_release` / `hardware_release`

**`backend/games/migrations/0011_calendar_event.py`** (신규 생성)
- `CalendarEvent` 모델 마이그레이션 (적용 완료)

**`backend/games/fixtures/calendar_events.json`** (신규 생성)
- 캘린더 초기 데이터 픽스처

**`backend/catalog/calendar_views.py`**
- 하드코딩된 `adapters.calendar_payload()` 호출 제거
- `CalendarEvent.objects.all()` DB 조회로 교체 (date, title, description, type, url 반환)
- `backend/catalog/adapters.py` 삭제 (calendar_payload 함수 제거)

**`frontend/src/pages/calendar/CalendarView.vue`**
- 페이지 제목 변경: "찜한 게임의 할인과 출시 일정" → "게임 할인 및 출시 일정"
- 이벤트 타입 키 통일: `sale`/`game`/`release` → `discount`/`game_release`/`hardware_release`
- 하드코딩된 더미 이벤트 3건 제거, API 응답만 사용
- 필터 레이블 업데이트: 할인 / 게임 출시 / 장비 출시
- 현재 연월을 `new Date()`로 초기화 (기존 하드코딩 2026/6 제거)
- 검색 변수명 `gameQuery` → `searchQuery`, 검색 대상에 `description` 포함
- 이벤트 카드에 `event.game` 대신 `event.title` / `event.description` 표시

---

## 5. 장비 상세 페이지 기능 추가

**`backend/catalog/equipment_ai_view.py`** (신규 생성)
- `EquipmentGameSuitabilityView` — `GET /catalog/equipment/{id}/suitability/`
  - 로그인한 유저의 보유/관심 게임(각 5개) 대상 AI 게임 적합도 분석
  - CPU/GPU/RAM 카테고리는 GMS AI 배치 분석, 나머지(모니터/마우스 등)는 범용 개선 메시지 반환
- `EquipmentPCCompareView` — `GET /catalog/equipment/{id}/pc-compare/`
  - 유저의 현재 PC 스펙(`PCSpec`)과 해당 장비 비교
  - GMS AI로 업그레이드 가치 분석: `high`/`medium`/`low`/`downgrade`/`na`
  - 현재 스펙 vs 신규 장비 차이 요약, 변화 포인트 3개 반환

**`frontend/src/pages/equipment/EquipmentDetailView.vue`** (대폭 수정)
- **가격 비교 섹션** 추가:
  - 현재가 / 최저가 / 최고가 통계 바
  - 가격 추세 배지 (↑ 상승 중 / ↓ 하락 중 / → 안정세)
  - 쇼핑몰별 가격 목록
  - 네이버 쇼핑 / 다나와 외부 링크
- **게임 적합도 그리드** 추가:
  - 보유 게임 / 관심 게임 각각 AI 분석 결과 카드
  - `pass`/`warn`/`fail`/`unknown`/`info` 배지 표시
- **사이드바: 내 PC와 비교 + AI 업그레이드 분석** 추가:
  - 현재 보유 스펙 vs 검토 중인 장비 비교 표시
  - 업그레이드 가치 등급, diff 요약, 변화 포인트 목록

---

## 6. 게임 상세 페이지 기능 추가

**`backend/catalog/buy_timing.py`** (신규 생성)
- ITAD API 연동으로 가격 이력 분석
- 할인율/역대 최저가 대비/할인 빈도/최근 할인 시점 기반 점수 산출
- 구매 권장 등급 반환: `buy_now` / `good` / `watch` / `wait`

**`backend/catalog/buy_timing_view.py`** (신규 생성)
- `GET /catalog/games/{id}/buy-timing/` 엔드포인트
- 캐싱 적용 (반복 API 호출 방지)

**`backend/catalog/compat_view.py`** (신규 생성)
- `GameCompatView` — `GET /catalog/games/{id}/compat/?cpu=&gpu=&ram=`
- 게임 요구사양과 유저 PC 스펙을 GMS AI로 비교 분석
- CPU/GPU/RAM 각각 `pass`/`warn`/`fail`/`unknown` 판정 + 한 줄 요약 반환

**`frontend/src/pages/games/GameDetailView.vue`** (수정)
- **구매 타이밍 분석 섹션** 추가:
  - 점수 프로그레스 바 + 신호 배지 (지금 구매 / 좋은 가격 / 지켜보기 / 대기 추천)
  - 판단 요인 목록 (긍정 ▲ / 부정 ▼ 아이콘)
  - 역대/1년/3개월 최저가 표시
- **PC 호환성 체크 섹션** 추가:
  - 유저 PC 스펙 기반 CPU/GPU/RAM 호환성 AI 분석 결과 표시

---

## 7. 피처 파일

**`backend/fixtures/initial_data.json`** (신규 생성)
- `accounts`, `games`, `hardware` 앱 전체 데이터 단일 파일로 덤프
- 기존 분리된 `accounts.json`, `games.json`, `hardware.json` 통합 후 삭제
- Windows cp949 인코딩 문제 → `PYTHONUTF8=1` 환경변수로 해결

---

## 8. 스타일 추가

**`frontend/src/styles.css`**
- 말머리 필터 칩: `.board-category-filter`, `.category-chip`, `.category-chip.active`
- 말머리 배지 색상: `.cat-공략` ~ `.cat-기타` (7종 color-coded)
- 추천 토글 버튼: `.vote-btn`, `.vote-btn.liked`
- 게시글 상세 액션: `.post-detail-actions`, `.post-delete-btn`
- 댓글 헤더: `.comment-header`, `.comment-time`, `.comment-delete-btn`
- 아바타: `.user-avatar-sm` (28px), `.user-avatar-xs` (20px) + img 스타일
- 리뷰 아바타: `.review-avatar-link`, `.review-avatar img`
- 게시글/댓글 작성자 행: `.post-author-row`, `.post-author-name`, `.comment-author-link`
- 그룹 구성원 칩 링크: `.group-member-chip-link`
