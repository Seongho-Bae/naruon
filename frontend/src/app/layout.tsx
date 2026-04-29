import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Naruon | AI Email Workspace",
  description:
    "Naruon connects email, schedules, relationships, and decisions into one AI-powered execution workspace.",
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
