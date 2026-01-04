// Dashboard page
'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import { formatCurrency } from '@/lib/utils'
import { DashboardData, OnboardingProfile, Transaction } from '@/types'
import {
  ResponsiveContainer,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ComposedChart,
} from 'recharts'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { OnboardingModal } from '@/components/OnboardingModal'

export default function DashboardPage() {
  const { user, logout, loading: authLoading, onboardingComplete, refreshOnboardingStatus } = useAuth()
  const router = useRouter()
  const { data: dashboard, loading, mutate: mutateDashboard } = useAPI<DashboardData>(
    user ? '/api/dashboard' : null,
    {
      revalidateOnFocus: true,
      refreshInterval: 20000,
    }
  )
  const { data: notifications } = useAPI<any[]>(user ? '/api/notifications' : null)
  const { data: onboardingProfile } = useAPI<OnboardingProfile | null>(
    user ? '/api/onboarding' : null
  )
  const [showOnboarding, setShowOnboarding] = useState(false)

  const formatDelta = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
  const deltaClass = (value: number) => (value >= 0 ? 'text-emerald-600' : 'text-red-600')

  useEffect(() => {
    if (onboardingComplete) {
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('ft_onboarding_dismissed')
      }
      setShowOnboarding(false)
      mutateDashboard()
      return
    }
    if (onboardingComplete !== false) return
    if (typeof window === 'undefined') return
    const dismissed = window.localStorage.getItem('ft_onboarding_dismissed')
    if (dismissed === 'true') return
    setShowOnboarding(true)
  }, [onboardingComplete, mutateDashboard])

  const handleOnboardingClose = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('ft_onboarding_dismissed', 'true')
    }
    setShowOnboarding(false)
  }

  const handleOnboardingComplete = async () => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('ft_onboarding_dismissed')
    }
    await refreshOnboardingStatus()
    mutateDashboard()
    setShowOnboarding(false)
  }

  const handleQuickStartAction = (stepKey: string) => {
    switch (stepKey) {
      case 'complete_onboarding':
        setShowOnboarding(true)
        break
      case 'add_account':
        router.push('/accounts')
        break
      case 'add_category':
      case 'add_transaction':
        router.push('/transactions')
        break
      case 'set_budget':
        router.push('/budgets')
        break
      default:
        break
    }
  }

  const quickStartSteps = dashboard?.onboarding ?? []
  const quickStartCompleted = quickStartSteps.filter((step) => step.completed).length
  const quickStartProgress =
    quickStartSteps.length > 0 ? Math.round((quickStartCompleted / quickStartSteps.length) * 100) : 0
  const nextStep = quickStartSteps.find((step) => !step.completed)

  const quickStartActionLabel = (stepKey: string) => {
    switch (stepKey) {
      case 'complete_onboarding':
        return 'Launch onboarding'
      case 'add_account':
        return 'Add account'
      case 'add_category':
        return 'Create category'
      case 'add_transaction':
        return 'Add transaction'
      case 'set_budget':
        return 'Create budget'
      default:
        return 'Start'
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Dashboard"
        subtitle="Your monthly momentum, alerts, and key signals in one place."
      >
        <OnboardingModal
          isOpen={showOnboarding}
          onClose={handleOnboardingClose}
          onComplete={handleOnboardingComplete}
        />
        {loading ? (
          <div className="surface p-6">Loading dashboard...</div>
        ) : dashboard ? (
          <>
          {quickStartSteps.length ? (
            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Quick start checklist</h2>
                <span className="text-sm text-gray-500">
                  {quickStartCompleted}/{quickStartSteps.length} completed
                </span>
              </div>
              <div className="mb-4 space-y-2">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>Progress</span>
                  <span>{quickStartProgress}%</span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${quickStartProgress}%`,
                      background: 'linear-gradient(120deg, #0f172a, #38bdf8)',
                    }}
                  />
                </div>
                {nextStep ? (
                  <p className="text-xs text-gray-500">
                    Next up: <span className="font-semibold text-gray-700">{nextStep.label}</span>
                  </p>
                ) : (
                  <p className="text-xs text-emerald-600">All set. You are ready to scale.</p>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {quickStartSteps.map((step) => (
                  <button
                    type="button"
                    key={step.key}
                    onClick={() => handleQuickStartAction(step.key)}
                    className={`rounded-xl border p-4 text-left transition hover:shadow-sm ${
                      step.completed
                        ? 'bg-emerald-50 border-emerald-200'
                        : 'bg-amber-50 border-amber-200'
                    }`}
                    disabled={step.completed}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{step.label}</span>
                      <span className="text-xs font-bold">
                        {step.completed ? 'Done' : quickStartActionLabel(step.key)}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4 stagger">
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Monthly income</p>
              <p className="text-2xl font-semibold text-emerald-600">
                {formatCurrency(dashboard.kpi.monthly_income)}
              </p>
              <p className={`text-xs mt-2 ${deltaClass(dashboard.kpi.income_change_pct)}`}>
                {formatDelta(dashboard.kpi.income_change_pct)} vs last month
              </p>
              <p className="text-xs text-gray-500">Avg 6 mo: {formatCurrency(dashboard.kpi.avg_monthly_income)}</p>
            </div>
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Monthly expenses</p>
              <p className="text-2xl font-semibold text-red-600">
                {formatCurrency(dashboard.kpi.monthly_expenses)}
              </p>
              <p className={`text-xs mt-2 ${deltaClass(dashboard.kpi.expense_change_pct)}`}>
                {formatDelta(dashboard.kpi.expense_change_pct)} vs last month
              </p>
              <p className="text-xs text-gray-500">Avg 6 mo: {formatCurrency(dashboard.kpi.avg_monthly_expenses)}</p>
            </div>
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Monthly net</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(dashboard.kpi.monthly_net)}
              </p>
              <p className={`text-xs mt-2 ${deltaClass(dashboard.kpi.net_change_pct)}`}>
                {formatDelta(dashboard.kpi.net_change_pct)} vs last month
              </p>
            </div>
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Savings rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboard.kpi.savings_rate.toFixed(1)}%
              </p>
            </div>
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Daily burn rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(dashboard.kpi.burn_rate)}
              </p>
            </div>
            <div className="stat-tile">
              <p className="text-xs uppercase text-gray-500">Net worth</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(dashboard.kpi.current_net_worth)}
              </p>
            </div>
          </div>

          <div className="surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Investor profile snapshot</h2>
              <span className="text-sm text-gray-500">Onboarding data</span>
            </div>
            {onboardingProfile ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-sm">
                <div>
                  <p className="text-gray-500">Target net worth</p>
                  <p className="text-lg font-semibold">
                    {formatCurrency(onboardingProfile.goal_value)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Target horizon</p>
                  <p className="text-lg font-semibold">
                    {onboardingProfile.goal_horizon_years} years ·{' '}
                    {new Date(onboardingProfile.target_date).toLocaleDateString('en-US', {
                      month: 'short',
                      year: 'numeric',
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Risk appetite</p>
                  <p className="text-lg font-semibold capitalize">
                    {onboardingProfile.risk_appetite}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Investor profile</p>
                  <p className="text-lg font-semibold capitalize">
                    {onboardingProfile.investor_profile}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Asset allocation</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {onboardingProfile.asset_allocation.map((item) => (
                      <span key={item} className="tag-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-gray-500">Investment interests</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {onboardingProfile.investment_interests.map((item) => (
                      <span key={item} className="tag-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
                {onboardingProfile.vision ? (
                  <div className="md:col-span-2">
                    <p className="text-gray-500">Vision (5-10 years)</p>
                    <p className="mt-2 text-gray-700">{onboardingProfile.vision}</p>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="flex flex-col gap-3 text-sm text-gray-600">
                <p>Complete onboarding to show your investor profile and strategy inputs here.</p>
                <Link href="/workspace" className="btn-secondary w-fit">
                  Complete onboarding
                </Link>
              </div>
            )}
          </div>

          {(dashboard.kpi.time_to_goal_months ||
            dashboard.kpi.required_savings_rate ||
            dashboard.kpi.required_investment_rate ||
            dashboard.kpi.decision_impact_score != null) && (
            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Strategy KPIs</h2>
                <span className="text-sm text-gray-500">Decision engine</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Time to goal</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboard.kpi.time_to_goal_months != null
                      ? `${dashboard.kpi.time_to_goal_months} mo`
                      : 'Not reachable'}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Required savings</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboard.kpi.required_savings_rate?.toFixed(1) ?? 'n/a'}%
                  </p>
                  <p className="text-xs text-gray-500">
                    Actual: {dashboard.kpi.savings_rate.toFixed(1)}%
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Required investing</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboard.kpi.required_investment_rate?.toFixed(1) ?? 'n/a'}%
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Decision impact</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboard.kpi.decision_impact_score != null
                      ? dashboard.kpi.decision_impact_score.toFixed(0)
                      : '0'}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Cashflow analysis</h2>
              <span className="text-sm text-gray-500">Last 6 months</span>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={dashboard.cashflow}>
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Bar dataKey="income" name="Income" fill="#10b981" />
                  <Bar dataKey="expenses" name="Expenses" fill="#ef4444" />
                  <Line type="monotone" dataKey="net" name="Net" stroke="#111827" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {dashboard.assets_by_category?.length ? (
            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Asset allocation</h2>
                <span className="text-sm text-gray-500">Accounts + investments</span>
              </div>
              <div className="space-y-3">
                {dashboard.assets_by_category.slice(0, 8).map((item) => (
                  <div key={item.key} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{item.label}</span>
                      <span className="text-gray-600">
                        {formatCurrency(item.amount)} · {item.percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="progress-track">
                      <div
                        className="progress-bar"
                        style={{
                          width: `${Math.min(item.percentage, 100).toFixed(1)}%`,
                          background: 'linear-gradient(120deg, #10b981, #38bdf8)',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-4">Top expense sources</h2>
              <div className="space-y-3">
                {dashboard.top_expense_merchants?.length ? (
                  dashboard.top_expense_merchants.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{item.name}</p>
                        <p className="text-xs text-gray-500">{item.count} transactions</p>
                      </div>
                      <p className="font-semibold text-red-600">{formatCurrency(item.amount)}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No expense data yet.</p>
                )}
              </div>
            </div>
            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-4">Top income sources</h2>
              <div className="space-y-3">
                {dashboard.top_income_merchants?.length ? (
                  dashboard.top_income_merchants.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{item.name}</p>
                        <p className="text-xs text-gray-500">{item.count} transactions</p>
                      </div>
                      <p className="font-semibold text-emerald-600">{formatCurrency(item.amount)}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No income data yet.</p>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {dashboard.expenses_by_label?.length ? (
              <div className="surface p-6">
                <h2 className="text-lg font-semibold mb-4">Spending by label</h2>
                <div className="space-y-3">
                  {dashboard.expenses_by_label.slice(0, 8).map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.label}</span>
                      <div className="text-right">
                        <p className="font-semibold">{formatCurrency(item.amount)}</p>
                        <p className="text-xs text-gray-500">{item.percentage.toFixed(1)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {dashboard.income_by_label?.length ? (
              <div className="surface p-6">
                <h2 className="text-lg font-semibold mb-4">Earnings by label</h2>
                <div className="space-y-3">
                  {dashboard.income_by_label.slice(0, 8).map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.label}</span>
                      <div className="text-right">
                        <p className="font-semibold">{formatCurrency(item.amount)}</p>
                        <p className="text-xs text-gray-500">{item.percentage.toFixed(1)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="surface p-6">
            <h2 className="text-lg font-semibold mb-4">Recent transactions</h2>
            <div className="space-y-2">
              {dashboard.recent_transactions?.slice(0, 5).map((tx: Transaction) => (
                <div key={tx.id} className="flex justify-between items-center border-b border-gray-100 py-2">
                  <span>{tx.description}</span>
                  <span className="font-bold">{formatCurrency(tx.amount)}</span>
                </div>
              ))}
            </div>
          </div>

          {notifications && notifications.length > 0 && (
            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-4">Notifications</h2>
              <div className="space-y-2">
                {notifications.slice(0, 5).map((note) => (
                  <div key={note.id} className="flex items-start justify-between border-b border-gray-100 pb-2">
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
        ) : (
          <div className="surface p-6 text-gray-600">No data yet. Import a CSV or add a transaction.</div>
        )}
      </AppShell>
    </AuthGate>
  )
}
