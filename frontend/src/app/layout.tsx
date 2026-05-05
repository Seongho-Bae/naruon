import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Naruon | AI Email Workspace",
  description: "메일의 흐름을 건너 더 나은 판단과 실행으로 연결하는 AI 이메일 워크스페이스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
