'use client'

import { useMemo, useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import {
  Scenario,
  ScenarioComparisonResponse,
  FinancialGoal,
  AssumptionVersion,
} from '@/types'
import {
  BarChart,
  Bar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const defaultScenario = {
  name: '',
  description: '',
  goal_id: '',
  assumption_id: '',
  is_baseline: false,
}

type ActionForm = {
  action_type: 'income_delta' | 'expense_delta' | 'investment_delta' | 'one_time_investment'
  value: string
  start_date: string
  end_date: string
}

const emptyAction = (): ActionForm => ({
  action_type: 'income_delta',
  value: '0',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
})

export default function ScenariosPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: scenarios, mutate } = useAPI<Scenario[]>(user ? '/api/scenarios' : null)
  const { data: goals } = useAPI<FinancialGoal[]>(user ? '/api/goals' : null)
  const { data: assumptions } = useAPI<AssumptionVersion[]>(user ? '/api/assumptions' : null)

  const [form, setForm] = useState(defaultScenario)
  const [actions, setActions] = useState<ActionForm[]>([emptyAction()])
  const [selected, setSelected] = useState<number[]>([])
  const [comparison, setComparison] = useState<ScenarioComparisonResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingComparison, setLoadingComparison] = useState(false)

  const updateForm = (key: string, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const updateAction = <K extends keyof ActionForm>(index: number, key: K, value: ActionForm[K]) => {
    setActions((prev) =>
      prev.map((action, actionIndex) =>
        actionIndex === index ? { ...action, [key]: value } : action
      )
    )
  }

  const addAction = () => setActions((prev) => [...prev, emptyAction()])

  const removeAction = (index: number) => {
    setActions((prev) => prev.filter((_, actionIndex) => actionIndex !== index))
  }

  const handleCreateScenario = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      await apiClient.post('/api/scenarios', {
        name: form.name,
        description: form.description || null,
        goal_id: form.goal_id ? Number(form.goal_id) : null,
        assumption_id: form.assumption_id ? Number(form.assumption_id) : null,
        is_baseline: form.is_baseline,
        actions: actions
          .filter((action) => Number(action.value) !== 0)
          .map((action) => ({
            action_type: action.action_type,
            value: Number(action.value),
            start_date: action.start_date,
            end_date: action.end_date || null,
          })),
      })
      setForm(defaultScenario)
      setActions([emptyAction()])
      await mutate()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to create scenario')
    }
  }

  const handleCompare = async () => {
    if (selected.length < 2) {
      setError('Select at least two scenarios to compare.')
      return
    }
    setLoadingComparison(true)
    setError(null)
    try {
      const response = await apiClient.post<ScenarioComparisonResponse>(
        '/api/strategy/scenarios/compare',
        {
          scenario_ids: selected,
        }
      )
      setComparison(response.data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to compare scenarios')
    } finally {
      setLoadingComparison(false)
    }
  }

  const comparisonChart = useMemo(() => {
    if (!comparison) return []
    return comparison.comparisons.map((item) => ({
      name: item.name,
      netWorth: Number(item.final_net_worth),
    }))
  }, [comparison])

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Scenarios"
        subtitle="Model alternative futures and compare the delta toward your goals."
      >
        <div className="surface p-6">
          <h2 className="text-lg font-semibold mb-4">Build a scenario</h2>
          <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleCreateScenario}>
            <input
              className="input-field"
              placeholder="Scenario name"
              value={form.name}
              onChange={(event) => updateForm('name', event.target.value)}
              required
            />
            <input
              className="input-field"
              placeholder="Description"
              value={form.description}
              onChange={(event) => updateForm('description', event.target.value)}
            />
            <select
              className="select-field"
              value={form.goal_id}
              onChange={(event) => updateForm('goal_id', event.target.value)}
            >
              <option value="">Link to goal (optional)</option>
              {goals?.map((goal) => (
                <option key={goal.id} value={goal.id}>
                  {goal.name}
                </option>
              ))}
            </select>
            <select
              className="select-field"
              value={form.assumption_id}
              onChange={(event) => updateForm('assumption_id', event.target.value)}
            >
              <option value="">Link to assumptions (optional)</option>
              {assumptions?.map((assumption) => (
                <option key={assumption.id} value={assumption.id}>
                  {assumption.name} (v{assumption.version})
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_baseline}
                onChange={(event) => updateForm('is_baseline', event.target.checked)}
              />
              Mark as baseline
            </label>
            <div className="md:col-span-2">
              <h3 className="text-sm font-semibold mb-2">Actions</h3>
              <div className="space-y-3">
                {actions.map((action, index) => (
                  <div key={`${action.action_type}-${index}`} className="grid grid-cols-1 md:grid-cols-5 gap-2">
                    <select
                      className="select-field"
                      value={action.action_type}
                      onChange={(event) =>
                        updateAction(index, 'action_type', event.target.value as ActionForm['action_type'])
                      }
                    >
                      <option value="income_delta">Income delta</option>
                      <option value="expense_delta">Expense delta</option>
                      <option value="investment_delta">Investment delta</option>
                      <option value="one_time_investment">One-time investment</option>
                    </select>
                    <input
                      className="input-field"
                      type="number"
                      step="0.01"
                      value={action.value}
                      onChange={(event) => updateAction(index, 'value', event.target.value)}
                    />
                    <input
                      className="input-field"
                      type="date"
                      value={action.start_date}
                      onChange={(event) => updateAction(index, 'start_date', event.target.value)}
                    />
                    <input
                      className="input-field"
                      type="date"
                      value={action.end_date}
                      onChange={(event) => updateAction(index, 'end_date', event.target.value)}
                    />
                    <button
                      className="btn-ghost"
                      type="button"
                      onClick={() => removeAction(index)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              <button className="btn-secondary mt-3" type="button" onClick={addAction}>
                Add action
              </button>
            </div>
            <div className="md:col-span-2 flex items-center gap-3">
              <button className="btn-primary" type="submit">
                Save scenario
              </button>
              {error ? <span className="text-sm text-red-600">{error}</span> : null}
            </div>
          </form>
        </div>

        <div className="surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Scenario library</h2>
            <button className="btn-secondary" type="button" onClick={handleCompare}>
              {loadingComparison ? 'Comparing...' : 'Compare selected'}
            </button>
          </div>
          {scenarios && scenarios.length ? (
            <div className="space-y-3">
              {scenarios.map((scenario) => (
                <label
                  key={scenario.id}
                  className="surface-muted p-4 flex items-start gap-3 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(scenario.id)}
                    onChange={() => {
                      setSelected((prev) =>
                        prev.includes(scenario.id)
                          ? prev.filter((id) => id !== scenario.id)
                          : [...prev, scenario.id]
                      )
                    }}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">{scenario.name}</h3>
                      {scenario.is_baseline && (
                        <span className="text-xs uppercase text-emerald-600 font-semibold">Baseline</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{scenario.description || 'No description'}</p>
                    <p className="text-xs text-gray-500 mt-1">Actions: {scenario.actions?.length || 0}</p>
                  </div>
                </label>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No scenarios yet. Create one above.</p>
          )}
        </div>

        {comparison ? (
          <div className="surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Scenario comparison</h2>
              <span className="text-sm text-gray-500">
                Baseline ID: {comparison.baseline_scenario_id}
              </span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonChart}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="netWorth" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-6 space-y-2">
              {comparison.comparisons.map((item) => (
                <div key={item.scenario_id} className="flex items-center justify-between text-sm">
                  <span>{item.name}</span>
                  <span className="text-gray-600">
                    Δ net worth {item.delta_net_worth.toFixed(2)} | Δ months {item.delta_months ?? 'n/a'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </AppShell>
    </AuthGate>
  )
}
