"use client";

/**
 * AI 天氣助手頁面
 */

import Link from "next/link";
import { AIChatCard } from "@/components";

export default function ChatPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-100 to-white">
      {/* 頁首 */}
      <header className="py-6 text-center">
        <Link href="/" className="inline-block">
          <h1 className="text-3xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
            好日子
          </h1>
        </Link>
        <p className="text-gray-600 mt-1">AI 天氣助手</p>
      </header>

      {/* 主內容 */}
      <div className="container mx-auto px-4 pb-12">
        <AIChatCard />
      </div>

      {/* 返回首頁 */}
      <div className="text-center pb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-500 hover:text-blue-600 transition-colors"
        >
          <span>←</span>
          <span>返回首頁</span>
        </Link>
      </div>

      {/* 頁尾 */}
      <footer className="py-6 text-center text-gray-400 text-xs border-t border-gray-200">
        <p>好日子 Auspicious &copy; 2024</p>
        <p className="mt-1">資料來源：中央氣象署歷史觀測資料</p>
      </footer>
    </main>
  );
}
