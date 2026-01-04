'use client'

import { useEffect, useMemo, useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { Account, AssumptionVersion, DashboardData, FinancialGoal } from '@/types'
import { formatCurrency } from '@/lib/utils'

const riskDefaults: Record<string, number> = {
  low: 2,
  medium: 4,
  high: 6,
}

const presets = {
  Conservative: { income_growth_rate: 1, expense_inflation_rate: 3, investment_return_rate: 3, risk_level: 'low' },
  Balanced: { income_growth_rate: 2, expense_inflation_rate: 3, investment_return_rate: 6, risk_level: 'medium' },
  Aggressive: { income_growth_rate: 3, expense_inflation_rate: 3.5, investment_return_rate: 8, risk_level: 'high' },
}

export default function WorkspacePage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: dashboard, mutate: mutateDashboard } = useAPI<DashboardData>(
    user ? '/api/dashboard' : null
  )
  const { data: accounts, mutate: mutateAccounts } = useAPI<Account[]>(
    user ? '/api/accounts' : null
  )
  const { data: activeGoal, mutate: mutateGoals } = useAPI<FinancialGoal | null>(
    user ? '/api/goals/active' : null
  )
  const { data: activeAssumption, mutate: mutateAssumptions } = useAPI<AssumptionVersion | null>(
    user ? '/api/assumptions/active' : null
  )

  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvPreview, setCsvPreview] = useState<any | null>(null)
  const [csvLoading, setCsvLoading] = useState(false)
  const [csvError, setCsvError] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)
  const [importAccountId, setImportAccountId] = useState('')

  const [goalForm, setGoalForm] = useState({ target_value: '', target_date: '' })
  const [assumptionForm, setAssumptionForm] = useState({
    income_growth_rate: '0',
    expense_inflation_rate: '0',
    investment_return_rate: '0',
    risk_level: 'medium',
  })
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [savingGoal, setSavingGoal] = useState(false)
  const [savingAssumptions, setSavingAssumptions] = useState(false)

  const activeAccount = useMemo(() => {
    if (!accounts?.length) return null
    const selected = accounts.find((account) => String(account.id) === importAccountId)
    return selected || accounts[0]
  }, [accounts, importAccountId])

  useEffect(() => {
    if (accounts?.length && !importAccountId) {
      setImportAccountId(String(accounts[0].id))
    }
  }, [accounts, importAccountId])

  useEffect(() => {
    if (activeGoal) {
      setGoalForm({
        target_value: String(activeGoal.target_value),
        target_date: activeGoal.target_date,
      })
    }
  }, [activeGoal])

  useEffect(() => {
    if (activeAssumption) {
      setAssumptionForm({
        income_growth_rate: String(activeAssumption.income_growth_rate ?? 0),
        expense_inflation_rate: String(activeAssumption.expense_inflation_rate ?? 0),
        investment_return_rate: String(activeAssumption.investment_return_rate ?? 0),
        risk_level: activeAssumption.risk_level || 'medium',
      })
    }
  }, [activeAssumption])


  useEffect(() => {
    if (!csvFile) {
      setCsvPreview(null)
      setCsvError(null)
      return
    }
    const preview = async () => {
      setCsvLoading(true)
      setCsvError(null)
      try {
        const formData = new FormData()
        formData.append('file', csvFile)
        const response = await apiClient.post('/api/transactions/import/preview', formData)
        setCsvPreview(response.data)
      } catch (err: any) {
        setCsvError(err?.response?.data?.detail || 'Unable to analyze the CSV file.')
      } finally {
        setCsvLoading(false)
      }
    }
    preview()
  }, [csvFile])

  const ensureAccount = async () => {
    if (activeAccount) return activeAccount.id
    const name = csvFile?.name ? csvFile.name.replace(/\.[^/.]+$/, '') : 'Main account'
    const response = await apiClient.post('/api/accounts', {
      name,
      account_type: 'checking',
      currency: 'USD',
      balance: 0,
    })
    await mutateAccounts()
    const created = response.data
    setImportAccountId(String(created.id))
    return created.id
  }

  const handleImport = async () => {
    if (!csvFile) return
    setImporting(true)
    setCsvError(null)
    try {
      const accountId = await ensureAccount()
      const formData = new FormData()
      formData.append('file', csvFile)
      await apiClient.post(`/api/transactions/import/csv?account_id=${accountId}`, formData)
      setCsvFile(null)
      setCsvPreview(null)
      await mutateDashboard()
    } catch (err: any) {
      setCsvError(err?.response?.data?.detail || 'Import failed. Please verify the CSV format.')
    } finally {
      setImporting(false)
    }
  }

  const saveGoal = async () => {
    if (!goalForm.target_value || !goalForm.target_date) {
      setSettingsError('Enter a target value and date for the goal.')
      return
    }
    setSavingGoal(true)
    setSettingsError(null)
    try {
      if (activeGoal) {
        await apiClient.put(`/api/goals/${activeGoal.id}`, {
          target_value: Number(goalForm.target_value),
          target_date: goalForm.target_date,
        })
      } else {
        await apiClient.post('/api/goals', {
          name: 'Primary goal',
          target_type: 'net_worth',
          target_value: Number(goalForm.target_value),
          target_date: goalForm.target_date,
        })
      }
      await mutateGoals()
    } catch (err: any) {
      setSettingsError(err?.response?.data?.detail || 'Unable to save goal.')
    } finally {
      setSavingGoal(false)
    }
  }

  const saveAssumptions = async () => {
    setSavingAssumptions(true)
    setSettingsError(null)
    try {
      const riskLevel = assumptionForm.risk_level
      const volatility = riskDefaults[riskLevel] ?? 4
      await apiClient.post('/api/assumptions', {
        name: `Strategy ${new Date().toISOString().slice(0, 10)}`,
        income_growth_rate: Number(assumptionForm.income_growth_rate),
        expense_inflation_rate: Number(assumptionForm.expense_inflation_rate),
        investment_return_rate: Number(assumptionForm.investment_return_rate),
        volatility,
        risk_level: riskLevel,
      })
      await mutateAssumptions()
    } catch (err: any) {
      setSettingsError(err?.response?.data?.detail || 'Unable to save assumptions.')
    } finally {
      setSavingAssumptions(false)
    }
  }

  const applyPreset = (presetKey: keyof typeof presets) => {
    const preset = presets[presetKey]
    setAssumptionForm({
      income_growth_rate: String(preset.income_growth_rate),
      expense_inflation_rate: String(preset.expense_inflation_rate),
      investment_return_rate: String(preset.investment_return_rate),
      risk_level: preset.risk_level,
    })
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Workspace"
        subtitle="Upload a statement and let the engine auto-build your insights."
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-2">1. Drop your CSV</h2>
              <p className="text-sm text-gray-600 mb-4">
                We auto-detect columns and split income vs expenses for you.
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={(event) => setCsvFile(event.target.files?.[0] || null)}
                className="text-sm"
              />
              {csvLoading && <p className="text-sm text-gray-500 mt-3">Analyzing...</p>}
              {csvError && (
                <div className="surface p-3 text-red-700 border border-red-200 bg-red-50/70 mt-3">
                  {csvError}
                </div>
              )}
              {csvPreview && (
                <div className="mt-4 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="stat-tile">
                      <p className="text-xs uppercase text-gray-500">Income</p>
                      <p className="text-lg font-semibold text-emerald-600">
                        {formatCurrency(csvPreview.income_total)}
                      </p>
                    </div>
                    <div className="stat-tile">
                      <p className="text-xs uppercase text-gray-500">Expenses</p>
                      <p className="text-lg font-semibold text-red-600">
                        {formatCurrency(csvPreview.expense_total)}
                      </p>
                    </div>
                    <div className="stat-tile">
                      <p className="text-xs uppercase text-gray-500">Net</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(csvPreview.net_total)}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">
                    Rows analyzed: {csvPreview.rows} · Errors: {csvPreview.errors}
                  </p>
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-3 items-center">
                {accounts && accounts.length > 1 ? (
                  <select
                    className="select-field"
                    value={importAccountId}
                    onChange={(event) => setImportAccountId(event.target.value)}
                  >
                    {accounts.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="text-sm text-gray-500">
                    Importing into {activeAccount?.name || 'Main account'}
                  </span>
                )}
                <button
                  className="btn-primary"
                  type="button"
                  onClick={handleImport}
                  disabled={!csvFile || importing}
                >
                  {importing ? 'Importing...' : 'Import & update'}
                </button>
              </div>
            </div>

            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-3">2. Set your goal</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  type="number"
                  step="0.01"
                  placeholder="Target net worth"
                  value={goalForm.target_value}
                  onChange={(event) => setGoalForm({ ...goalForm, target_value: event.target.value })}
                />
                <input
                  className="input-field"
                  type="date"
                  value={goalForm.target_date}
                  onChange={(event) => setGoalForm({ ...goalForm, target_date: event.target.value })}
                />
              </div>
              <div className="mt-3 flex items-center gap-3">
                <button className="btn-secondary" type="button" onClick={saveGoal} disabled={savingGoal}>
                  {savingGoal ? 'Saving...' : activeGoal ? 'Update goal' : 'Save goal'}
                </button>
                {activeGoal && (
                  <span className="text-xs text-gray-500">Active goal: {activeGoal.name}</span>
                )}
              </div>
            </div>

            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-3">3. Strategy settings</h2>
              <div className="flex flex-wrap gap-2 mb-3">
                {Object.keys(presets).map((presetKey) => (
                  <button
                    key={presetKey}
                    className="btn-secondary"
                    type="button"
                    onClick={() => applyPreset(presetKey as keyof typeof presets)}
                  >
                    {presetKey}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  className="input-field"
                  type="number"
                  step="0.1"
                  placeholder="Income growth (%)"
                  value={assumptionForm.income_growth_rate}
                  onChange={(event) =>
                    setAssumptionForm({ ...assumptionForm, income_growth_rate: event.target.value })
                  }
                />
                <input
                  className="input-field"
                  type="number"
                  step="0.1"
                  placeholder="Expense inflation (%)"
                  value={assumptionForm.expense_inflation_rate}
                  onChange={(event) =>
                    setAssumptionForm({ ...assumptionForm, expense_inflation_rate: event.target.value })
                  }
                />
                <input
                  className="input-field"
                  type="number"
                  step="0.1"
                  placeholder="Return rate (%)"
                  value={assumptionForm.investment_return_rate}
                  onChange={(event) =>
                    setAssumptionForm({ ...assumptionForm, investment_return_rate: event.target.value })
                  }
                />
                <select
                  className="select-field"
                  value={assumptionForm.risk_level}
                  onChange={(event) =>
                    setAssumptionForm({ ...assumptionForm, risk_level: event.target.value })
                  }
                >
                  <option value="low">Low risk</option>
                  <option value="medium">Medium risk</option>
                  <option value="high">High risk</option>
                </select>
              </div>
              <div className="mt-3 flex items-center gap-3">
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={saveAssumptions}
                  disabled={savingAssumptions}
                >
                  {savingAssumptions ? 'Saving...' : 'Save settings'}
                </button>
                {activeAssumption && (
                  <span className="text-xs text-gray-500">Active: {activeAssumption.name}</span>
                )}
              </div>
            </div>

            {settingsError && (
              <div className="surface p-3 text-red-700 border border-red-200 bg-red-50/70">
                {settingsError}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h2 className="text-lg font-semibold mb-3">Live snapshot</h2>
              {dashboard ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="stat-tile">
                    <p className="text-xs uppercase text-gray-500">Monthly net</p>
                    <p className="text-lg font-semibold">
                      {formatCurrency(dashboard.kpi.monthly_net)}
                    </p>
                  </div>
                  <div className="stat-tile">
                    <p className="text-xs uppercase text-gray-500">Savings rate</p>
                    <p className="text-lg font-semibold">
                      {dashboard.kpi.savings_rate.toFixed(1)}%
                    </p>
                  </div>
                  <div className="stat-tile">
                    <p className="text-xs uppercase text-gray-500">Net worth</p>
                    <p className="text-lg font-semibold">
                      {formatCurrency(dashboard.kpi.current_net_worth)}
                    </p>
                  </div>
                  <div className="stat-tile">
                    <p className="text-xs uppercase text-gray-500">Monthly expenses</p>
                    <p className="text-lg font-semibold">
                      {formatCurrency(dashboard.kpi.monthly_expenses)}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Import a CSV to see your snapshot.</p>
              )}
            </div>

            {activeGoal && dashboard && (
              <div className="surface p-6">
                <h2 className="text-lg font-semibold mb-3">Goal progress</h2>
                <p className="text-sm text-gray-600">{activeGoal.name}</p>
                <div className="mt-3">
                  <div className="progress-track">
                    <div
                      className="progress-bar"
                      style={{
                        width: `${Math.min(
                          100,
                          (dashboard.kpi.current_net_worth / Number(activeGoal.target_value)) * 100
                        ).toFixed(0)}%`,
                        background: 'linear-gradient(90deg, #0f766e, #38bdf8)',
                      }}
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {formatCurrency(dashboard.kpi.current_net_worth)} /{' '}
                    {formatCurrency(activeGoal.target_value)} by {activeGoal.target_date}
                  </div>
                </div>
              </div>
            )}

            {dashboard?.kpi.time_to_goal_months && (
              <div className="surface p-6">
                <h2 className="text-lg font-semibold mb-2">Autopilot insight</h2>
                <p className="text-sm text-gray-600">
                  At your current trajectory, you reach the goal in about{' '}
                  <span className="font-semibold">{dashboard.kpi.time_to_goal_months} months</span>.
                </p>
              </div>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
