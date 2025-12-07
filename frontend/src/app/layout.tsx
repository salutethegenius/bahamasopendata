import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50`}
      >
        <Navigation />
        <main className="min-h-screen">
          {children}
        </main>
        <footer className="bg-white border-t border-gray-200 py-8 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-center md:text-left">
                <p className="font-bold text-gray-900">
                  Bahamas<span className="text-turquoise">OpenData</span>
                </p>
                <p className="text-sm text-gray-500">
                  Making Bahamas public finance clear and accessible
                </p>
              </div>
              <div className="text-sm text-gray-500 text-center md:text-right">
                <p>Data sourced from official government documents</p>
                <p>© 2025 Registered. Development by Kemis Group of Companies Inc.</p>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
