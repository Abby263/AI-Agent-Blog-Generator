import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { AppProvider } from "@/lib/context";
import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { ToastViewport } from "@/components/toast-viewport";

export const metadata: Metadata = {
  title: "Atlas — Editorial Agent for Long-Form Publishing",
  description:
    "Plan, draft, review, and approve technical books, blog series, reports, and research papers with a transparent multi-agent pipeline.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas text-ink-900">
        <AppProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 min-w-0 flex flex-col">
              <Topbar />
              <main className="flex-1 min-w-0">
                <div className="mx-auto w-full max-w-6xl px-5 py-8 md:px-8 md:py-10">
                  {children}
                </div>
              </main>
            </div>
          </div>
          <ToastViewport />
        </AppProvider>
      </body>
    </html>
  );
}
