// Dashboard page
'use client'

import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import { formatCurrency } from '@/lib/utils'
import Link from 'next/link'
import { DashboardData, Transaction } from '@/types'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const { data: dashboard, loading } = useAPI<DashboardData>('/api/dashboard')
  const { data: notifications } = useAPI<any[]>('/api/notifications')

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
          <Link href="/dashboard" className="px-3 py-4 border-b-2 border-blue-500 text-blue-600 font-bold">
            Dashboard
          </Link>
          <Link href="/transactions" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Transactions
          </Link>
          <Link href="/budgets" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
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
        {loading ? (
          <div>Loading dashboard...</div>
        ) : dashboard ? (
          <>
            {/* Onboarding */}
            {dashboard.onboarding?.some(step => !step.completed) && (
              <div className="bg-white p-6 rounded-lg shadow mb-8">
                <h2 className="text-xl font-bold mb-4">Quick start</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {dashboard.onboarding.map(step => (
                    <div
                      key={step.key}
                      className={`flex items-center justify-between border rounded p-3 ${
                        step.completed ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'
                      }`}
                    >
                      <span className="text-sm font-medium">{step.label}</span>
                      <span className="text-xs font-bold">
                        {step.completed ? 'Done' : 'Next'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-gray-600 text-sm font-medium">Monthly Expenses</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {formatCurrency(dashboard.kpi.monthly_expenses)}
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-gray-600 text-sm font-medium">Daily Burn Rate</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {formatCurrency(dashboard.kpi.burn_rate)}
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-gray-600 text-sm font-medium">Net Worth</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {formatCurrency(dashboard.kpi.current_net_worth)}
                </p>
              </div>
            </div>

            {/* Recent Transactions */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Recent transactions</h2>
              <div className="space-y-2">
                {dashboard?.recent_transactions?.slice(0, 5).map((tx: Transaction) => (
                  <div key={tx.id} className="flex justify-between items-center py-2 border-b">
                    <span>{tx.description}</span>
                    <span className="font-bold">{formatCurrency(tx.amount)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Notifications */}
            {notifications && notifications.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow mt-6">
                <h2 className="text-xl font-bold mb-4">Notifications</h2>
                <div className="space-y-2">
                  {notifications.slice(0, 5).map((note) => (
                    <div key={note.id} className="flex items-start justify-between border-b pb-2">
                      <div>
                        <p className="font-semibold">{note.title}</p>
                        <p className="text-sm text-gray-600">{note.message}</p>
                      </div>
                      <span className="text-xs text-gray-500">{note.notification_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}
      </main>
    </div>
  )
}
