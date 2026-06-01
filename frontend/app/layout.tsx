import type { Metadata } from "next";
import { AppLogo } from "./components/AppLogo";
import "./globals.css";

export const metadata: Metadata = {
  title: "work-support",
  description: "Personal work automation and career assetization platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <div className="app-frame">
          <header className="app-header" aria-label="전역 이동">
            <AppLogo />
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
