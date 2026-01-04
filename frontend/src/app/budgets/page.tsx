// Budgets page
'use client'

import React, { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { Budget, Category } from '@/types'
import { formatCurrency, formatMonth } from '@/lib/utils'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'

export default function BudgetsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const { data: budgets, loading, mutate } = useAPI<Budget[]>(
    user ? `/api/budgets/month/${selectedMonth}` : null
  )
  const { data: categories } = useAPI<Category[]>(user ? '/api/categories' : null)
  const [formData, setFormData] = useState({
    category_id: '',
    amount: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [editingBudgetId, setEditingBudgetId] = useState<number | null>(null)
  const [editAmount, setEditAmount] = useState('')

  const totalBudget = budgets?.reduce((sum, budget) => sum + Number(budget.amount), 0) ?? 0
  const totalSpent = budgets?.reduce((sum, budget) => sum + Number(budget.spent), 0) ?? 0
  const totalRemaining = totalBudget - totalSpent
  const totalUsage = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0

  const monthLabel = selectedMonth ? formatMonth(`${selectedMonth}-01`) : 'Select month'

  const budgetTone = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500'
    if (percentage >= 80) return 'bg-amber-500'
    return 'bg-emerald-500'
  }

  const handleCreateOrUpdateBudget = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!formData.category_id) {
      setFormError('Please choose a category.')
      return
    }
    const amount = parseFloat(formData.amount)
    if (!amount || Number.isNaN(amount) || amount <= 0) {
      setFormError('Enter a valid amount greater than 0.')
      return
    }

    setIsSubmitting(true)
    try {
      const existing = budgets?.find(
        (budget) => budget.category_id === Number(formData.category_id)
      )
      if (existing) {
        await apiClient.put(`/api/budgets/${existing.id}`, {
          amount,
        })
      } else {
        await apiClient.post('/api/budgets', {
          category_id: Number(formData.category_id),
          amount,
          month: `${selectedMonth}-01`,
        })
      }
      setFormData({ category_id: '', amount: '' })
      mutate()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to save the budget.'
      setFormError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteBudget = async (budgetId: number) => {
    try {
      await apiClient.delete(`/api/budgets/${budgetId}`)
      mutate()
    } catch (err) {
      setFormError('Unable to delete the budget.')
    }
  }

  const handleUpdateBudgetAmount = async (budgetId: number) => {
    const amount = parseFloat(editAmount)
    if (!amount || Number.isNaN(amount) || amount <= 0) {
      setFormError('Enter a valid amount greater than 0.')
      return
    }
    try {
      await apiClient.put(`/api/budgets/${budgetId}`, { amount })
      setEditingBudgetId(null)
      setEditAmount('')
      mutate()
    } catch (err) {
      setFormError('Unable to update the budget.')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Budgets"
        subtitle="Set monthly guardrails, spot overspending early, and keep every category on track."
        actions={
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-600">Month</label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="select-field max-w-[180px]"
            />
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="surface p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">Monthly overview</h3>
                  <p className="text-sm text-gray-500">{monthLabel}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Total budget</p>
                  <p className="text-xl font-semibold">{formatCurrency(totalBudget)}</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Spent</p>
                  <p className="text-lg font-semibold text-red-600">{formatCurrency(totalSpent)}</p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Remaining</p>
                  <p className={`text-lg font-semibold ${totalRemaining >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {formatCurrency(Math.abs(totalRemaining))}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Usage</p>
                  <p className="text-lg font-semibold">{totalUsage.toFixed(1)}%</p>
                </div>
              </div>
              <div className="mt-4">
                <div className="progress-track">
                  <div
                    className={`progress-bar ${budgetTone(totalUsage)}`}
                    style={{ width: `${Math.min(totalUsage, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {formError && (
              <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70">
                {formError}
              </div>
            )}

            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Budget categories</h3>
                <span className="text-sm text-gray-500">{monthLabel}</span>
              </div>

              {loading ? (
                <p className="text-gray-600">Loading budgets...</p>
              ) : budgets && budgets.length > 0 ? (
                <div className="space-y-4 stagger">
                  {budgets.map((budget) => {
                    const isOver = budget.percentage_used >= 100
                    const remainingLabel = budget.remaining >= 0 ? 'Remaining' : 'Over by'
                    return (
                      <div
                        key={budget.id}
                        className={`surface-muted p-4 ${
                          isOver ? 'border border-red-200 bg-red-50/50' : ''
                        }`}
                      >
                        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                          <div>
                            <h4 className="text-base font-semibold">{budget.category_name}</h4>
                            <p className="text-xs text-gray-500">
                              Budget: {formatCurrency(budget.amount)}
                            </p>
                          </div>
                          <div className="text-sm text-gray-600">
                            <p>Spent: {formatCurrency(budget.spent)}</p>
                            <p>
                              {remainingLabel}:{' '}
                              <span className={budget.remaining >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                                {formatCurrency(Math.abs(budget.remaining))}
                              </span>
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {editingBudgetId === budget.id ? (
                              <>
                                <input
                                  type="number"
                                  min="0"
                                  step="0.01"
                                  value={editAmount}
                                  onChange={(e) => setEditAmount(e.target.value)}
                                  className="input-field w-28 px-2 py-1"
                                />
                                <button
                                  type="button"
                                  onClick={() => handleUpdateBudgetAmount(budget.id)}
                                  className="btn-primary text-sm px-3 py-1"
                                >
                                  Save
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingBudgetId(null)
                                    setEditAmount('')
                                  }}
                                  className="btn-secondary text-sm px-3 py-1"
                                >
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingBudgetId(budget.id)
                                    setEditAmount(String(budget.amount))
                                  }}
                                  className="btn-secondary text-sm px-3 py-1"
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleDeleteBudget(budget.id)}
                                  className="text-sm px-3 py-1 rounded-lg border border-red-200 text-red-600"
                                >
                                  Delete
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="mt-3">
                          <div className="progress-track">
                            <div
                              className={`progress-bar ${budgetTone(budget.percentage_used)}`}
                              style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-xs text-gray-500 mt-2">
                            <span>{budget.percentage_used.toFixed(1)}%</span>
                            <span>{formatCurrency(budget.amount)}</span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="surface-muted p-6 text-center text-gray-600">
                  <p className="font-semibold">No budgets yet for this month.</p>
                  <p className="text-sm">Create your first budget to start tracking.</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Create or update a budget</h3>
              <p className="text-sm text-gray-600 mb-4">
                Pick a category and set a monthly limit. If the budget already exists, we'll update it.
              </p>
              <form onSubmit={handleCreateOrUpdateBudget} className="space-y-3">
                <select
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="select-field"
                  required
                >
                  <option value="">Select category</option>
                  {categories?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name} {category.is_income ? '(Income)' : ''}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="Monthly amount"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="input-field"
                  required
                />
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary w-full disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save budget'}
                </button>
              </form>
            </div>

            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">How to stay on track</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>Set realistic limits based on your last 3 months.</li>
                <li>Review categories that go above 80% mid-month.</li>
                <li>Update budgets as your income changes.</li>
              </ul>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
