// Auth gate to handle loading and signed-out states
'use client'

import Link from 'next/link'
import React from 'react'

type AuthGateProps = {
  loading: boolean
  user: { email?: string } | null
  children: React.ReactNode
  title?: string
  subtitle?: string
}

export function AuthGate({
  loading,
  user,
  children,
  title = 'Sign in required',
  subtitle = 'Sign in to access your workspace.',
}: AuthGateProps) {
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="surface p-6 text-center text-gray-600">Loading your workspace...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="surface p-6 text-center space-y-3">
          <p className="text-lg font-semibold">{title}</p>
          <p className="text-sm text-gray-600">{subtitle}</p>
          <Link href="/login" className="btn-primary inline-flex justify-center">
            Sign in
          </Link>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
