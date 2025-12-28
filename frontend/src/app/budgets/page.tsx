// Budgets page
'use client'

import React from 'react'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'

export default function BudgetsPage() {
  const { user, logout } = useAuth()

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Finance Tracker</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">{user.email}</span>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-4">
          <Link href="/dashboard" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Dashboard
          </Link>
          <Link href="/transactions" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Transactions
          </Link>
          <Link href="/budgets" className="px-3 py-4 border-b-2 border-blue-500 text-blue-600 font-bold">
            Budgets
          </Link>
          <Link href="/net-worth" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Net Worth
          </Link>
          <Link href="/accounts" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Accounts
          </Link>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-xl font-bold mb-4">Budgets</h2>
        <p className="text-gray-600">Budget management feature coming soon...</p>
      </main>
    </div>
  )
}
