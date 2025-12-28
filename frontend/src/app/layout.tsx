// Root layout
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Finance Tracker',
  description: 'Personal finance management SaaS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
