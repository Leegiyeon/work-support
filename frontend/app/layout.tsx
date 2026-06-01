import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "work-support",
  description: "Personal work automation and career assetization platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
