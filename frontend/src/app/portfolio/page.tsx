// Portfolio investments page
'use client'

import { useMemo, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { InvestmentAsset } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'

const categoryOptions = [
  { value: 'rental', label: 'Rental' },
  { value: 'stocks', label: 'Stocks' },
  { value: 'funds', label: 'Funds' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'portfolio', label: 'Portfolio' },
  { value: 'business', label: 'Business' },
  { value: 'other', label: 'Other' },
]

const categoryLabels = new Map(categoryOptions.map((item) => [item.value, item.label]))

export default function PortfolioPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: investments, loading, mutate } = useAPI<InvestmentAsset[]>(
    user ? '/api/investments' : null
  )
  const [formError, setFormError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [investmentForm, setInvestmentForm] = useState({
    name: '',
    category: 'stocks',
    current_value: '0',
    currency: 'USD',
    notes: '',
  })
  const [editForm, setEditForm] = useState({
    name: '',
    category: 'stocks',
    current_value: '0',
    currency: 'USD',
    notes: '',
    is_active: true,
  })

  const totals = useMemo(() => {
    const activeAssets = investments?.filter((asset) => asset.is_active) ?? []
    const totalValue = activeAssets.reduce((sum, asset) => sum + Number(asset.current_value || 0), 0)
    return {
      count: activeAssets.length,
      totalValue,
    }
  }, [investments])

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault()
    setFormError(null)
    try {
      await apiClient.post('/api/investments', {
        name: investmentForm.name,
        category: investmentForm.category,
        current_value: parseFloat(investmentForm.current_value || '0'),
        currency: investmentForm.currency,
        notes: investmentForm.notes || null,
        is_active: true,
      })
      setInvestmentForm({
        name: '',
        category: 'stocks',
        current_value: '0',
        currency: 'USD',
        notes: '',
      })
      setIsCreating(false)
      mutate()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to add investment.'
      setFormError(message)
    }
  }

  const startEdit = (asset: InvestmentAsset) => {
    setEditingId(asset.id)
    setEditForm({
      name: asset.name,
      category: asset.category,
      current_value: String(asset.current_value ?? '0'),
      currency: asset.currency,
      notes: asset.notes || '',
      is_active: asset.is_active,
    })
  }

  const handleUpdate = async (assetId: number) => {
    setFormError(null)
    try {
      await apiClient.put(`/api/investments/${assetId}`, {
        name: editForm.name,
        category: editForm.category,
        current_value: parseFloat(editForm.current_value || '0'),
        currency: editForm.currency,
        notes: editForm.notes || null,
        is_active: editForm.is_active,
      })
      setEditingId(null)
      mutate()
    } catch (err) {
      setFormError('Unable to update investment.')
    }
  }

  const handleDelete = async (assetId: number) => {
    setFormError(null)
    try {
      await apiClient.delete(`/api/investments/${assetId}`)
      mutate()
    } catch (err) {
      setFormError('Unable to delete investment.')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Portfolio"
        subtitle="Track external investments to complete your asset allocation."
      >
        {formError && (
          <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70">
            {formError}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="surface p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">External holdings</h3>
                  <p className="text-sm text-gray-500">Add rentals, stocks, or other assets.</p>
                </div>
                <p className="text-xl font-semibold">{formatCurrency(totals.totalValue)}</p>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Active investments</p>
                  <p className="text-lg font-semibold">{totals.count}</p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Total value</p>
                  <p className="text-lg font-semibold text-emerald-600">
                    {formatCurrency(totals.totalValue)}
                  </p>
                </div>
              </div>
            </div>

            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Holdings list</h3>
                  <p className="text-sm text-gray-500">Keep track of off-platform assets.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCreating(!isCreating)}
                  className="btn-secondary text-sm"
                >
                  {isCreating ? 'Close' : 'Add investment'}
                </button>
              </div>

              {loading ? (
                <p className="text-gray-600">Loading investments...</p>
              ) : investments && investments.length > 0 ? (
                <div className="space-y-4">
                  {investments.map((asset) => {
                    const categoryLabel = categoryLabels.get(asset.category) || asset.category
                    return (
                      <div key={asset.id} className="surface-muted p-4">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="text-sm text-gray-500 uppercase">{categoryLabel}</p>
                            <h4 className="text-base font-semibold">{asset.name}</h4>
                            <p className="text-xs text-gray-500">{asset.currency}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-semibold text-emerald-600">
                              {formatCurrency(asset.current_value, asset.currency)}
                            </p>
                            <p className="text-xs text-gray-500">
                              {asset.is_active ? 'Active' : 'Inactive'}
                            </p>
                          </div>
                        </div>

                        {asset.notes && editingId !== asset.id && (
                          <p className="text-sm text-gray-600 mt-3">{asset.notes}</p>
                        )}

                        {editingId === asset.id ? (
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                            <input
                              value={editForm.name}
                              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                              className="input-field"
                              placeholder="Investment name"
                            />
                            <select
                              value={editForm.category}
                              onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                              className="select-field"
                            >
                              {categoryOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            <input
                              value={editForm.current_value}
                              onChange={(e) => setEditForm({ ...editForm, current_value: e.target.value })}
                              className="input-field"
                              placeholder="Current value"
                              type="number"
                              step="0.01"
                            />
                            <input
                              value={editForm.currency}
                              onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                              className="input-field"
                              placeholder="Currency"
                            />
                            <input
                              value={editForm.notes}
                              onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                              className="input-field md:col-span-2"
                              placeholder="Notes"
                            />
                            <div className="md:col-span-2 flex items-center justify-between">
                              <label className="toggle">
                                <input
                                  type="checkbox"
                                  checked={editForm.is_active}
                                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                                />
                                <span className="toggle-track">
                                  <span className="toggle-thumb" />
                                </span>
                                Active asset
                              </label>
                              <div className="flex gap-2">
                                <button
                                  type="button"
                                  className="btn-secondary"
                                  onClick={() => setEditingId(null)}
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  className="btn-primary"
                                  onClick={() => handleUpdate(asset.id)}
                                >
                                  Save
                                </button>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-4 flex flex-wrap gap-2">
                            <button
                              type="button"
                              className="btn-secondary"
                              onClick={() => startEdit(asset)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              onClick={() => handleDelete(asset.id)}
                            >
                              Remove
                            </button>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-gray-600">No investments yet. Add your first asset.</p>
              )}

              {isCreating && (
                <form onSubmit={handleCreate} className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                  <input
                    value={investmentForm.name}
                    onChange={(e) => setInvestmentForm({ ...investmentForm, name: e.target.value })}
                    className="input-field"
                    placeholder="Investment name"
                    required
                  />
                  <select
                    value={investmentForm.category}
                    onChange={(e) => setInvestmentForm({ ...investmentForm, category: e.target.value })}
                    className="select-field"
                  >
                    {categoryOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <input
                    value={investmentForm.current_value}
                    onChange={(e) => setInvestmentForm({ ...investmentForm, current_value: e.target.value })}
                    className="input-field"
                    placeholder="Current value"
                    type="number"
                    step="0.01"
                  />
                  <input
                    value={investmentForm.currency}
                    onChange={(e) => setInvestmentForm({ ...investmentForm, currency: e.target.value })}
                    className="input-field"
                    placeholder="Currency"
                  />
                  <input
                    value={investmentForm.notes}
                    onChange={(e) => setInvestmentForm({ ...investmentForm, notes: e.target.value })}
                    className="input-field md:col-span-2"
                    placeholder="Notes (optional)"
                  />
                  <button type="submit" className="btn-primary md:col-span-2">
                    Save investment
                  </button>
                </form>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Allocation tips</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>Keep holdings updated to improve the strategy engine.</li>
                <li>Mark inactive assets instead of deleting to keep history.</li>
                <li>Use notes for context (loan terms, yield, tenant).</li>
              </ul>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
