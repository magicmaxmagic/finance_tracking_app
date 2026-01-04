'use client'

import { useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { FinancialGoal } from '@/types'
import { formatCurrency } from '@/lib/utils'

const defaultForm = {
  name: '',
  target_type: 'net_worth',
  target_value: '',
  target_date: '',
}

export default function GoalsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: goals, loading, mutate } = useAPI<FinancialGoal[]>(
    user ? '/api/goals' : null
  )
  const [form, setForm] = useState(defaultForm)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateField = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await apiClient.post('/api/goals', {
        name: form.name,
        target_type: form.target_type,
        target_value: Number(form.target_value),
        target_date: form.target_date,
      })
      setForm(defaultForm)
      await mutate()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to create goal')
    } finally {
      setSubmitting(false)
    }
  }

  const updateStatus = async (goalId: number, status: string) => {
    try {
      await apiClient.put(`/api/goals/${goalId}`, { status })
      await mutate()
    } catch (err) {
      setError('Unable to update goal')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Goals"
        subtitle="Define the target that anchors your financial strategy."
      >
        <div className="surface p-6">
          <h2 className="text-lg font-semibold mb-4">Create a new goal</h2>
          <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleSubmit}>
            <input
              className="input-field"
              placeholder="Goal name"
              value={form.name}
              onChange={(event) => updateField('name', event.target.value)}
              required
            />
            <select
              className="select-field"
              value={form.target_type}
              onChange={(event) => updateField('target_type', event.target.value)}
            >
              <option value="net_worth">Net worth</option>
              <option value="liquid_assets">Liquid assets</option>
            </select>
            <input
              className="input-field"
              type="number"
              step="0.01"
              min="0"
              placeholder="Target value"
              value={form.target_value}
              onChange={(event) => updateField('target_value', event.target.value)}
              required
            />
            <input
              className="input-field"
              type="date"
              value={form.target_date}
              onChange={(event) => updateField('target_date', event.target.value)}
              required
            />
            <div className="md:col-span-2 flex items-center gap-3">
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : 'Save goal'}
              </button>
              {error ? <span className="text-sm text-red-600">{error}</span> : null}
            </div>
          </form>
        </div>

        <div className="surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Your goals</h2>
            <span className="text-sm text-gray-500">{goals?.length || 0} total</span>
          </div>
          {loading ? (
            <p className="text-sm text-gray-500">Loading goals...</p>
          ) : goals && goals.length ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {goals.map((goal) => (
                <div key={goal.id} className="surface-muted p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">{goal.name}</h3>
                      <p className="text-sm text-gray-600">
                        Target {formatCurrency(goal.target_value)} by {goal.target_date}
                      </p>
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                      {goal.status}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {goal.status !== 'active' && (
                      <button
                        className="btn-secondary"
                        type="button"
                        onClick={() => updateStatus(goal.id, 'active')}
                      >
                        Set active
                      </button>
                    )}
                    {goal.status !== 'archived' && (
                      <button
                        className="btn-secondary"
                        type="button"
                        onClick={() => updateStatus(goal.id, 'archived')}
                      >
                        Archive
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No goals yet. Create one to unlock strategy views.</p>
          )}
        </div>
      </AppShell>
    </AuthGate>
  )
}
