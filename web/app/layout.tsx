import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Project Builder | Studio",
  description: "Turn an AI idea into a researched, reviewed project plan.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><head><meta name="theme-color" content="#f1f0ee" /></head><body>{children}</body></html>;
}
