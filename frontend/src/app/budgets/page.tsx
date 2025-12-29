// Budgets page
'use client'

import React, { useMemo } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import Link from 'next/link'
import { Budget } from '@/types'
import { formatCurrency } from '@/lib/utils'

export default function BudgetsPage() {
  const { user, logout } = useAuth()
  const currentMonth = useMemo(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  }, [])
  const { data: budgets, loading } = useAPI<Budget[]>(
    `/api/budgets/month/${currentMonth}`
  )

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
        {loading ? (
          <p className="text-gray-600">Loading budgets...</p>
        ) : budgets && budgets.length > 0 ? (
          <div className="grid gap-4">
            {budgets.map((budget) => (
              <div key={budget.id} className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">{budget.category_name}</h3>
                    <p className="text-sm text-gray-500">Month: {budget.month}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Budget</p>
                    <p className="text-lg font-bold">{formatCurrency(budget.amount)}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Spent</span>
                    <span>{formatCurrency(budget.spent)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Remaining: {formatCurrency(budget.remaining)}</span>
                    <span>{budget.percentage_used.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No budgets for this month.</p>
        )}
      </main>
    </div>
  )
}
