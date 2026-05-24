import type { Metadata } from "next";
import { DashboardLayout } from "@/components/DashboardLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Naruon | AI Email Workspace",
  description: "AI Email Workspace",
  icons: {
    icon: "/brand/naruon-app-icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <DashboardLayout>{children}</DashboardLayout>
      </body>
    </html>
  );
}
