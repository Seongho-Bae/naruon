import Link from 'next/link';
import { Database, FileArchive, FolderTree, ShieldCheck } from 'lucide-react';

const dataSections = [
  { title: 'WebDAV 파일', copy: '첨부파일과 산출물을 프로젝트/스레드/할 일 기준 폴더로 구조화합니다.' },
  { title: 'ZIP/메일 반입', copy: 'ZIP 반입과 포워딩 중복을 Message-ID, fingerprint, thread provenance로 정리합니다.' },
  { title: 'Naruon 산출물', copy: 'AI가 종합한 결과도 원본 계정의 파일/일정/업무 흐름으로 되돌릴 수 있게 추적합니다.' },
];

export default function DataPage() {
  return (
    <div className="h-full min-h-0 overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-card p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Knowledge and files</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">데이터와 파일</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            메일, 첨부파일, WebDAV 폴더, AI 종합 결과를 원본 시스템 추적이 가능한 지식 작업공간으로 묶습니다.
          </p>
          <Link href="/projects" className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            <FolderTree className="size-4" aria-hidden="true" />
            프로젝트 폴더 구조 보기
          </Link>
        </section>
        <section aria-label="데이터 작업 영역" className="grid gap-4 md:grid-cols-3">
          {dataSections.map(({ title, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <Database className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
        </section>
        <section aria-label="반입 중복 처리" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <FileArchive className="size-6 text-primary" aria-hidden="true" />
            <h2 className="text-xl font-black text-foreground">중복 반입과 thread 정리</h2>
          </div>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            포워딩으로 같은 메일이 여러 계정에 도착하거나 ZIP 파일에서 다시 반입돼도 unique email 후보를 계산해 canonical thread에 연결해야 합니다.
          </p>
          <p className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm font-semibold text-emerald-800">
            <ShieldCheck className="mr-2 inline size-4" aria-hidden="true" />
            원본 파일/메일 서버를 대체하지 않고 customer-owned source에 provenance를 남깁니다.
          </p>
        </section>
      </div>
    </div>
  );
}
