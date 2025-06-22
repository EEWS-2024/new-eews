import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/modules/common/components/Navbar";
import {GlobalProvider} from "@/modules/common/components/GlobalProvider";
import {Toaster} from "react-hot-toast";
import {Suspense} from "react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Guncang",
  description: "Integrated Earthquake Early Warning System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
      <Suspense fallback={<p>Loading...</p>}>
        <GlobalProvider>
          <div className={'bg-gray-900'}>
            <Navbar/>
            <div className={'p-2'}>
              {children}
            </div>
          </div>
          <Toaster/>
        </GlobalProvider>
      </Suspense>
      </body>
    </html>
  );
}
