import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: { default: "NutriMind – AI Nutrition Intelligence", template: "%s | NutriMind" },
  description:
    "Personalized AI-powered nutrition tracking with food image analysis, Gemini AI coaching, and intelligent health insights.",
  keywords: ["nutrition", "AI", "food tracking", "health", "diet", "calories", "Gemini AI"],
  authors: [{ name: "NutriMind" }],
  openGraph: {
    title: "NutriMind – Personalized Nutrition Intelligence",
    description: "Track nutrition with AI-powered food analysis and personalized coaching",
    type: "website",
    url: "https://nutrimind.app",
  },
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${outfit.variable} font-sans min-h-screen bg-background`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <QueryProvider>
            {children}
            <Toaster
              position="top-right"
              toastOptions={{
                style: {
                  background: "rgba(17,24,39,0.9)",
                  color: "#fff",
                  border: "1px solid rgba(255,255,255,0.1)",
                  backdropFilter: "blur(12px)",
                  borderRadius: "12px",
                },
                success: { iconTheme: { primary: "#10b981", secondary: "#fff" } },
                error: { iconTheme: { primary: "#ef4444", secondary: "#fff" } },
              }}
            />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
