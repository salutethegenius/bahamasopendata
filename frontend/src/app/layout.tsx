import type { Metadata } from "next";
import { Sora, DM_Mono } from "next/font/google";
import "./globals.css";
import ConditionalNavigation from "@/components/ConditionalNavigation";
import ConditionalFooter from "@/components/ConditionalFooter";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  display: "swap",
});

const dmMono = DM_Mono({
  variable: "--font-dm-mono",
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Bahamas Open Data | Civic Finance Dashboard",
  description: "The national dashboard for Bahamas public finance - budget, spending, revenue, and debt made clear and accessible.",
  keywords: ["Bahamas", "budget", "government", "finance", "spending", "revenue", "debt", "civic", "open data"],
  authors: [{ name: "Bahamas Open Data" }],
  openGraph: {
    title: "Bahamas Open Data | Civic Finance Dashboard",
    description: "The national dashboard for Bahamas public finance - budget, spending, revenue, and debt made clear and accessible.",
    type: "website",
    locale: "en_BS",
    url: "https://bahamasopendata.com",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${sora.variable} ${dmMono.variable} antialiased bg-gray-50`}
      >
        <ConditionalNavigation />
        <main className="min-h-screen">
          {children}
        </main>
        <ConditionalFooter />
      </body>
    </html>
  );
}
