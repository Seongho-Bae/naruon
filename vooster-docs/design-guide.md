# Naruon Design Guide

## Visual Direction
Naruon is a Korean-first enterprise AI email workspace. The visual language is clean, calm, precise, and execution-oriented: white and slate surfaces, deep navy text, blue/indigo AI accents, green action success, rounded cards, subtle borders, and low-shadow elevation.

## Canonical Repository References
Use the current repository files below as the design source of truth:
- `docs/ui-ux/naruon-ui-ux-mapping.md`
- `docs/ui-ux/mockups/mockup_01.png` through `docs/ui-ux/mockups/mockup_41.png`
- `frontend/branding/naruon-ux-mockup-1.png` through `frontend/branding/naruon-ux-mockup-10.png`
- `frontend/public/brand/naruon-logo.svg`
- `frontend/public/brand/naruon-symbol.svg`
- `frontend/public/brand/naruon-app-icon.svg`

Do not cite stale asset paths such as `brand_assets/*`, `uiux/*`, `branding/naruon_branding.png`, or root-level `naruon-rebrand-dashboard*.png` unless those files are restored in the repository.

## Product UX Contract
Naruon is an Evidence-based AI Email Workspace. The UI must synthesize email, attachments, images, calendars, relations, and project contexts based on evidence to assist judgment and execution.

Core principles:
1. Do not just shorten emails. Connect the context.
2. AI does not just state conclusions. It presents evidence and confidence.
3. Judgments must lead to execution.

Home must include today's decision points, pending tasks, calendar coordination/conflict evidence, and recent email. These surfaces must be source-backed. Avoid fixed fixture metrics or static operational claims such as fake calendar counts, fake project counts, fake progress percentages, or hardcoded conflict rows. When a source integration is not available, show a designed empty/loading/pending state rather than pretending data exists.

## Brand Tokens
Recommended palette:
- Ink/Navy: `#0B132B` / `#0B1220`
- Primary Blue: `#2563EB`
- Indigo: `#4F46E5`
- AI Purple: `#7C3AED`
- Action Green: `#22C55E`
- Info Sky: `#38BDF8`
- Slate Text: `#475569`, `#64748B`
- Border: `#E5E7EB`
- App Background: `#F8FAFC`
- Surface: `#FFFFFF`
- Success: `#16A34A`
- Warning: `#F59E0B`
- Danger: `#EF4444`
- Info: `#0EA5E9`

## Typography
- Korean-first: Pretendard preferred. SUIT or Noto Sans KR acceptable fallback.
- English/numbers: Inter acceptable if bundled locally or system fallback if external fonts are not allowed.
- Avoid default Create Next App / Geist identity.
- Use clear hierarchy:
  - H1 32-40px
  - H2 24-28px
  - H3 18-20px
  - Body 14-16px
  - Caption 12px
  - Button/label 13-14px

## Layout
Desktop workspace target:
- Left navigation/sidebar: 220-260px
- Email/search list: 320-380px
- Main thread detail: flexible center
- Right insight/context panel: 300-360px
- 8px spacing grid, with 16/24/32px primary rhythm
- Cards use 12-16px radius, 1px border, soft shadow

Responsive:
- Desktop `>=1024px`: 3-pane workspace
- Tablet `768-1024px`: collapse right panel or use drawer
- Phone `<768px`: mobile app bar, bottom navigation, stacked email list/detail

## Navigation And Terminology
The application is organized into 10 main GNB areas: 홈, 메일, 일정, 작업, 프로젝트, 맥락 검색, 데이터, AI 허브, 보안, 설정.

Use Korean-first terminology from `docs/ui-ux/naruon-ui-ux-mapping.md`:
- AI Summary -> 맥락 종합
- Summary -> 종합 / 핵심 맥락
- Insight -> 판단 포인트
- Todo -> 실행 항목
- Smart Reply -> 답장 초안
- Search -> 맥락 검색
- Network Graph -> 관계 맥락
- Calendar Sync -> 일정 반영
- AI Assistant -> 판단 보조

## Components
### Email Row
Must support selected, unread, thread count, sender avatar, subject, snippet, tags, attachment indicator, and date. Selected state should use blue border/background and clear ARIA state.

### Email Detail
Show subject, sender, recipients, date, thread history, body, attachments, reply actions, and AI insight cards. Empty, loading, and error states must feel designed, not default text blocks.

### AI Insight Card
Use blue/purple accents with an `AI` or `AI Generated` chip. Must include source/provenance when available, confidence/limitation copy when needed, and explicit actions such as `작업 만들기`, `캘린더 반영`, `답장 초안`, `다시 생성`.

### Provider Settings
Admin-only. Secret fields never echo saved values. Use `연결됨`, `마지막 업데이트`, and fingerprint/status metadata instead of masked fake secrets as primary contract.

### Network Graph
Use Naruon colors, clear empty/error/loading states, and a text fallback summary. Graph should not look like an unstyled third-party embed.

## Accessibility
- WCAG AA contrast for text and controls.
- Visible Naruon blue focus ring.
- Icon-only buttons require accessible labels.
- Minimum mobile touch target 44px.
- Resizable panels need keyboard-friendly fallback or usable collapsed layout.
- AI output must be distinguishable from verified facts.

## Copy Tone
Korean-first enterprise tone: concise, calm, and action-oriented. Avoid overclaiming AI certainty. Use labels like `요약`, `실행 항목`, `답장 초안`, `관계 맥락`, `모델 설정`, `연결 상태`, `다시 시도`.