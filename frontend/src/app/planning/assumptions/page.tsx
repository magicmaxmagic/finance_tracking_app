'use client'

import { useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { AssumptionVersion } from '@/types'

const defaultForm = {
  name: '',
  income_growth_rate: '0',
  expense_inflation_rate: '0',
  investment_return_rate: '0',
  volatility: '0',
  risk_level: 'medium',
  notes: '',
}

export default function AssumptionsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: assumptions, loading, mutate } = useAPI<AssumptionVersion[]>(
    user ? '/api/assumptions' : null
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
      await apiClient.post('/api/assumptions', {
        name: form.name,
        income_growth_rate: Number(form.income_growth_rate),
        expense_inflation_rate: Number(form.expense_inflation_rate),
        investment_return_rate: Number(form.investment_return_rate),
        volatility: Number(form.volatility),
        risk_level: form.risk_level,
        notes: form.notes || null,
      })
      setForm(defaultForm)
      await mutate()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to save assumptions')
    } finally {
      setSubmitting(false)
    }
  }

  const activateAssumption = async (assumptionId: number) => {
    try {
      await apiClient.put(`/api/assumptions/${assumptionId}/activate`)
      await mutate()
    } catch (err) {
      setError('Unable to activate this version')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Assumptions"
        subtitle="Capture the hypothesis driving your financial projections."
      >
        <div className="surface p-6">
          <h2 className="text-lg font-semibold mb-4">Create a new assumption set</h2>
          <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleSubmit}>
            <input
              className="input-field"
              placeholder="Version name"
              value={form.name}
              onChange={(event) => updateField('name', event.target.value)}
              required
            />
            <select
              className="select-field"
              value={form.risk_level}
              onChange={(event) => updateField('risk_level', event.target.value)}
            >
              <option value="low">Low risk</option>
              <option value="medium">Medium risk</option>
              <option value="high">High risk</option>
            </select>
            <input
              className="input-field"
              type="number"
              step="0.01"
              placeholder="Income growth rate (%)"
              value={form.income_growth_rate}
              onChange={(event) => updateField('income_growth_rate', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.01"
              placeholder="Expense inflation rate (%)"
              value={form.expense_inflation_rate}
              onChange={(event) => updateField('expense_inflation_rate', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.01"
              placeholder="Investment return rate (%)"
              value={form.investment_return_rate}
              onChange={(event) => updateField('investment_return_rate', event.target.value)}
            />
            <input
              className="input-field"
              type="number"
              step="0.01"
              placeholder="Volatility (%)"
              value={form.volatility}
              onChange={(event) => updateField('volatility', event.target.value)}
            />
            <textarea
              className="input-field md:col-span-2"
              placeholder="Notes"
              value={form.notes}
              onChange={(event) => updateField('notes', event.target.value)}
            />
            <div className="md:col-span-2 flex items-center gap-3">
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : 'Save assumptions'}
              </button>
              {error ? <span className="text-sm text-red-600">{error}</span> : null}
            </div>
          </form>
        </div>

        <div className="surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Assumption history</h2>
            <span className="text-sm text-gray-500">{assumptions?.length || 0} versions</span>
          </div>
          {loading ? (
            <p className="text-sm text-gray-500">Loading assumption versions...</p>
          ) : assumptions && assumptions.length ? (
            <div className="space-y-3">
              {assumptions.map((assumption) => (
                <div key={assumption.id} className="surface-muted p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">{assumption.name}</h3>
                      <p className="text-sm text-gray-600">Version {assumption.version}</p>
                    </div>
                    {assumption.is_active && (
                      <span className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-700 mt-3">
                    <div>Income growth: {assumption.income_growth_rate}%</div>
                    <div>Expense inflation: {assumption.expense_inflation_rate}%</div>
                    <div>Return rate: {assumption.investment_return_rate}%</div>
                    <div>Volatility: {assumption.volatility}%</div>
                  </div>
                  {assumption.notes ? (
                    <p className="text-sm text-gray-500 mt-2">{assumption.notes}</p>
                  ) : null}
                  {!assumption.is_active && (
                    <div className="mt-3">
                      <button
                        className="btn-secondary"
                        type="button"
                        onClick={() => activateAssumption(assumption.id)}
                      >
                        Activate
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No assumptions yet. Create your first version.</p>
          )}
        </div>
      </AppShell>
    </AuthGate>
  )
}
