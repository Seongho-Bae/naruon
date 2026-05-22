import Link from 'next/link';
import { KeyRound, LockKeyhole, Route, ShieldCheck, Users } from 'lucide-react';

const securityCards = [
  { title: 'Universal RBAC', icon: Users, copy: 'SaaS 공급자, 기업 계열/사업부/팀, 개인/SOHO 역할을 한 vocabulary로 표현합니다.' },
  { title: 'ABAC deny precedence', icon: ShieldCheck, copy: '지역, 동의, source capability, customer policy deny가 broad role allow보다 우선합니다.' },
  { title: 'Keycloak/Casdoor', icon: KeyRound, copy: '자체 로그인과 enterprise OIDC/SAML/LDAP 연동을 모두 수용하는 인증/키 관리 후보입니다.' },
  { title: 'Traefik edge', icon: Route, copy: 'ForwardAuth, route policy, rate limit, trusted forwarded header 검증을 edge에서 분리합니다.' },
];

const governanceScreens = [
  { title: '보안 대시보드', copy: 'SSO 상태, 커넥터 권한, source별 실패율, 정책 거부 이벤트를 한 화면에서 봅니다.' },
  { title: '접근 권한', copy: 'SaaS 공급자, 기업, 그룹, 사업부, 팀, 개인/SOHO 역할을 RBAC/ABAC 조합으로 관리합니다.' },
  { title: '감사 로그', copy: '메일, CalDAV, WebDAV read와 writeback intent, 관리자 조회, 정책 거부를 불변 이벤트로 추적합니다.' },
  { title: '외부 공유', copy: '프로젝트 산출물 공유는 data-region, consent, source capability, customer policy deny를 먼저 통과해야 합니다.' },
  { title: '정책', copy: 'deny 우선 규칙, legal hold, source-of-truth, connector scope를 배포 전 검증합니다.' },
];

export default function SecurityPage() {
  return (
    <div className="h-full min-h-0 overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-card p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Security and admin</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">보안과 관리자</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            Naruon은 고객의 메일/일정/파일 원본을 대신 보관하는 서비스가 아니므로, 권한과 감사는 source 단위까지 내려가야 합니다.
          </p>
          <Link href="/settings" className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            <LockKeyhole className="size-4" aria-hidden="true" />
            인증/커넥터 설정 열기
          </Link>
        </section>

        <section aria-label="보안 운영 화면" className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {governanceScreens.map(({ title, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
        </section>

        <section aria-label="보안 설계 카드" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {securityCards.map(({ title, icon: Icon, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <Icon className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
        </section>

        <section aria-label="관리자 경계" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <h2 className="text-xl font-black text-foreground">관리자 경계</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            platform_admin은 플랫폼 운영을 위해 조직/리소스 경계를 넘을 수 있어도 data-region, consent, source capability, legal hold, customer policy deny를 우회하지 않습니다.
          </p>
        </section>
      </div>
    </div>
  );
}
