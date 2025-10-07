import './globals.css'
import type { Metadata } from 'next'
import VastStatus from '@/components/VastStatus'

export const metadata: Metadata = {
  title: 'Video Cutter Task Manager',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <main style={{ padding: 24, fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif', background: '#0b0f17', color: '#e6eaf2' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h1 style={{ margin: 0, fontSize: 20, letterSpacing: 0.5 }}>Aporto Studio</h1>
              <nav style={{ display: 'flex', alignItems: 'center', gap: 12, opacity: 0.9, fontSize: 13 }}>
                <span>AI Video Tools</span>
                <VastStatus />
              </nav>
            </header>
            {children}
          </div>
        </main>
      </body>
    </html>
  )
}
