'use client'

import { useEffect, useMemo, useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { DecisionOverview, TrajectoryResponse } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function DecisionsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: overview } = useAPI<DecisionOverview>(user ? '/api/strategy/decisions' : null)
  const [incomeDelta, setIncomeDelta] = useState(0)
  const [expenseDelta, setExpenseDelta] = useState(0)
  const [investmentDelta, setInvestmentDelta] = useState(0)
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const previewData = useMemo(() => {
    if (!trajectory) return []
    return trajectory.trajectory.map((point) => ({
      month: point.date,
      netWorth: Number(point.net_worth),
    }))
  }, [trajectory])

  const buildActions = () => {
    const actions: Array<{ action_type: string; value: number; start_date: string }> = []
    const startDate = new Date().toISOString().slice(0, 10)
    if (incomeDelta !== 0) {
      actions.push({
        action_type: 'income_delta',
        value: incomeDelta,
        start_date: startDate,
      })
    }
    if (expenseDelta !== 0) {
      actions.push({
        action_type: 'expense_delta',
        value: expenseDelta,
        start_date: startDate,
      })
    }
    if (investmentDelta !== 0) {
      actions.push({
        action_type: 'investment_delta',
        value: investmentDelta,
        start_date: startDate,
      })
    }
    return actions
  }

  const runPreview = async () => {
    setLoadingPreview(true)
    setError(null)
    try {
      const response = await apiClient.post<TrajectoryResponse>('/api/strategy/trajectory', {
        actions: buildActions(),
      })
      setTrajectory(response.data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to run preview')
    } finally {
      setLoadingPreview(false)
    }
  }

  useEffect(() => {
    if (user) {
      runPreview()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Decision Lab"
        subtitle="Preview the impact of your next financial move before you commit."
      >
        <div className="surface p-6">
          <h2 className="text-lg font-semibold mb-4">Decision impact preview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm font-semibold">Income change (monthly)</p>
              <input
                className="w-full"
                type="range"
                min={-1000}
                max={2000}
                step={50}
                value={incomeDelta}
                onChange={(event) => setIncomeDelta(Number(event.target.value))}
              />
              <p className="text-sm text-gray-600">{formatCurrency(incomeDelta)}</p>
            </div>
            <div>
              <p className="text-sm font-semibold">Expense change (monthly)</p>
              <input
                className="w-full"
                type="range"
                min={-1000}
                max={1000}
                step={50}
                value={expenseDelta}
                onChange={(event) => setExpenseDelta(Number(event.target.value))}
              />
              <p className="text-sm text-gray-600">{formatCurrency(expenseDelta)}</p>
            </div>
            <div>
              <p className="text-sm font-semibold">Investment change (monthly)</p>
              <input
                className="w-full"
                type="range"
                min={0}
                max={2000}
                step={50}
                value={investmentDelta}
                onChange={(event) => setInvestmentDelta(Number(event.target.value))}
              />
              <p className="text-sm text-gray-600">{formatCurrency(investmentDelta)}</p>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button className="btn-primary" type="button" onClick={runPreview} disabled={loadingPreview}>
              {loadingPreview ? 'Running...' : 'Preview impact'}
            </button>
            {error ? <span className="text-sm text-red-600">{error}</span> : null}
          </div>
        </div>

        <div className="surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Trajectory timeline</h2>
            {trajectory?.time_to_goal_months ? (
              <span className="text-sm text-gray-500">
                {trajectory.time_to_goal_months} months to goal
              </span>
            ) : null}
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={previewData}>
                <XAxis dataKey="month" hide />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Line type="monotone" dataKey="netWorth" stroke="#0f172a" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="surface p-6">
            <h2 className="text-lg font-semibold mb-4">Opportunity ranking</h2>
            {overview?.opportunities?.length ? (
              <div className="space-y-3">
                {overview.opportunities.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-semibold">{item.name}</p>
                      <p className="text-xs text-gray-500">{item.action_type}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatCurrency(item.monthly_delta)}</p>
                      <p className="text-xs text-gray-500">
                        {item.months_saved ? `${item.months_saved} months saved` : 'No goal linked'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No decision insights yet.</p>
            )}
          </div>
          <div className="surface p-6">
            <h2 className="text-lg font-semibold mb-4">Recommendations</h2>
            {overview?.recommendations?.length ? (
              <div className="space-y-3">
                {overview.recommendations.map((rec, index) => (
                  <div key={`${rec.headline}-${index}`}>
                    <p className="font-semibold">{rec.headline}</p>
                    <p className="text-sm text-gray-600">{rec.detail}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No recommendations yet.</p>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
