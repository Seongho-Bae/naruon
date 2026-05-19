import { CalendarDays, FileText, Mail, Network, Search, UserRound } from 'lucide-react';

const searchScopes = [
  { title: '메일', detail: '받은편지함, 보낸 메일 답변 추적, thread 중복 정리', icon: Mail },
  { title: '일정', detail: 'CalDAV 원본 계정별 일정 후보와 충돌', icon: CalendarDays },
  { title: '문서', detail: 'WebDAV 첨부 파일, 종합 산출물, 프로젝트 폴더', icon: FileText },
  { title: '사람', detail: '발신자 DAG, 관계 맥락, 다음 액션 힌트', icon: UserRound },
];

export default function SearchPage() {
  return (
    <div className="min-h-full overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-card p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Context Search</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">맥락 검색</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            메일, 일정, 첨부 파일, 사람 관계를 하나의 검색 흐름으로 묶고 결과 상세에서 관계 그래프와 타임라인으로 이동합니다.
          </p>
          <label className="mt-5 flex min-h-12 items-center gap-3 rounded-2xl border border-border bg-background px-4 text-sm shadow-inner">
            <Search className="size-5 text-primary" aria-hidden="true" />
            <span className="sr-only">맥락 검색어</span>
            <input className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted-foreground" type="search" placeholder="메일, 사람, 파일, 일정, 의사결정 로그 검색" />
          </label>
        </section>

        <section aria-label="검색 범위" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {searchScopes.map(({ title, detail, icon: Icon }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" aria-hidden="true" /></span>
                <h2 className="text-lg font-black text-foreground">{title}</h2>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{detail}</p>
            </article>
          ))}
        </section>

        <section aria-label="관계 그래프와 타임라인" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-2xl bg-emerald-500/10 text-emerald-700"><Network className="size-5" aria-hidden="true" /></span>
            <div>
              <h2 className="text-xl font-black text-foreground">관계 그래프와 타임라인</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                검색 결과는 발신자 DAG, 프로젝트, 일정 writeback provenance와 연결되어 사용자가 다음 액션을 검증할 수 있게 합니다.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
