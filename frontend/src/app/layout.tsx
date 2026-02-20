import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '쉽게 보는 사주, 사주 고!',
  description: 'AI 사주 분석 서비스 - 사주고',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="dark">
      <body className={`${inter.className} bg-background-light dark:bg-background-dark min-h-screen flex justify-center text-slate-900 dark:text-slate-100`}>
        <main className="w-full max-w-[430px] min-h-screen bg-background-light dark:bg-background-dark relative flex flex-col shadow-2xl overflow-hidden border-x border-primary/10">
            {children}
        </main>
      </body>
    </html>
  )
}
