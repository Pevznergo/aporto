import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Video Cutter Task Manager',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <main style={{ padding: 24, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif' }}>
          {children}
        </main>
      </body>
    </html>
  )
}
