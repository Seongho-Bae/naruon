import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('..', import.meta.url)));

const read = (path) => readFileSync(join(root, path), 'utf8');

const files = {
  layout: read('src/components/DashboardLayout.tsx'),
  page: read('src/app/page.tsx'),
  detail: read('src/components/EmailDetail.tsx'),
  list: read('src/components/EmailList.tsx'),
};

const checks = [
  {
    name: 'desktop shell exposes Naruon global navigation labels',
    pass: () => ['홈', '대시보드', '메일', '일정', '프로젝트', '데이터', 'AI 허브', '보안', '설정'].every((label) => files.layout.includes(label)),
  },
  {
    name: 'mail workspace has a folder rail separate from global navigation',
    pass: () => ['받은편지함', '중요', 'AI 종합', '첨부', '내 폴더'].every((label) => files.layout.includes(label)),
  },
  {
    name: 'relationship graph is opened by an explicit selected-thread action',
    pass: () => files.page.includes('relationshipPanelOpen')
      && files.detail.includes('onOpenRelationshipContext')
      && files.detail.includes('관계 그래프 보기'),
  },
  {
    name: 'relationship graph is not mounted as an always-visible third pane',
    pass: () => files.page.includes('role="dialog"') && !files.page.includes('defaultSize={25}'),
  },
  {
    name: 'detail action bar includes mail, calendar, task, archive, and context actions',
    pass: () => ['답장', '전체답장', '전달', '일정 만들기', '작업 만들기', '보관', '관계 그래프 보기'].every((label) => files.detail.includes(label)),
  },
  {
    name: 'email list includes dense enterprise filters and Korean empty subject copy',
    pass: () => ['전체', '읽지 않음', '중요', '고객', '첨부', 'AI 추천', '(제목 없음)'].every((label) => files.list.includes(label)),
  },
  {
    name: 'mobile detail has a sticky bottom action bar',
    pass: () => files.detail.includes('md:hidden') && files.detail.includes('sticky bottom-0'),
  },
  {
    name: 'AI output includes provenance and limitation copy',
    pass: () => files.detail.includes('AI 요약은 원문을 기준으로 생성') && files.detail.includes('중요한 결정 전 원문을 확인'),
  },
  {
    name: 'async status and failure states are announced to assistive technology',
    pass: () => files.detail.includes('aria-live="polite"')
      && files.detail.includes('role="status"')
      && files.detail.includes('role="alert"')
      && files.detail.includes('스레드 전체를 불러오지 못해 선택한 메일만 표시합니다.'),
  },
  {
    name: 'relationship drawer manages keyboard focus and Escape close',
    pass: () => files.page.includes('relationshipOpenerRef')
      && files.page.includes('relationshipPanelRef')
      && files.page.includes("event.key === 'Escape'")
      && files.page.includes("event.key === 'Tab'"),
  },
];

const failures = checks.filter((check) => !check.pass());

if (failures.length > 0) {
  console.error('Naruon workspace UI contract failed:');
  for (const failure of failures) {
    console.error(`- ${failure.name}`);
  }
  process.exit(1);
}

console.log(`Naruon workspace UI contract passed (${checks.length} checks).`);
