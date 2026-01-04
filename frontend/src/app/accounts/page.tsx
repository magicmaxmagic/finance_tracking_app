// Accounts page
'use client'

import { useMemo, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { Account, NetWorthSummary } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'

const LIABILITY_TYPES = new Set(['credit', 'debt'])

export default function AccountsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: accounts, loading, mutate } = useAPI<Account[]>(user ? '/api/accounts' : null)
  const { data: summary, mutate: mutateSummary } = useAPI<NetWorthSummary>(
    user ? '/api/net-worth/summary' : null
  )
  const [formError, setFormError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [editingAccountId, setEditingAccountId] = useState<number | null>(null)
  const [accountForm, setAccountForm] = useState({
    name: '',
    account_type: 'checking',
    currency: 'USD',
    balance: '0',
    description: '',
  })
  const [editForm, setEditForm] = useState({
    name: '',
    currency: 'USD',
    balance: '0',
    description: '',
  })

  const totals = useMemo(() => {
    if (!summary) return { assets: 0, liabilities: 0, netWorth: 0 }
    return {
      assets: Number(summary.total_assets),
      liabilities: Number(summary.total_liabilities),
      netWorth: Number(summary.net_worth),
    }
  }, [summary])

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    try {
      await apiClient.post('/api/accounts', {
        name: accountForm.name,
        account_type: accountForm.account_type.toLowerCase(),
        currency: accountForm.currency,
        balance: parseFloat(accountForm.balance || '0'),
        description: accountForm.description || null,
      })
      setAccountForm({
        name: '',
        account_type: 'checking',
        currency: 'USD',
        balance: '0',
        description: '',
      })
      setIsCreating(false)
      mutate()
      mutateSummary()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to create account.'
      setFormError(message)
    }
  }

  const startEdit = (account: Account) => {
    setEditingAccountId(account.id)
    setEditForm({
      name: account.name,
      currency: account.currency,
      balance: String(account.balance ?? '0'),
      description: account.description || '',
    })
  }

  const handleUpdateAccount = async (accountId: number) => {
    setFormError(null)
    try {
      await apiClient.put(`/api/accounts/${accountId}`, {
        name: editForm.name,
        currency: editForm.currency,
        balance: parseFloat(editForm.balance || '0'),
        description: editForm.description || null,
      })
      setEditingAccountId(null)
      mutate()
      mutateSummary()
    } catch (err) {
      setFormError('Unable to update account.')
    }
  }

  const handleDeleteAccount = async (accountId: number) => {
    setFormError(null)
    try {
      await apiClient.delete(`/api/accounts/${accountId}`)
      mutate()
      mutateSummary()
    } catch (err) {
      setFormError('Unable to delete account.')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Accounts"
        subtitle="Organize every account and keep your balance sheet up to date."
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
                  <h3 className="text-lg font-semibold">Balance sheet</h3>
                  <p className="text-sm text-gray-500">Assets vs liabilities</p>
                </div>
                <p className="text-xl font-semibold">{formatCurrency(totals.netWorth)}</p>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Assets</p>
                  <p className="text-lg font-semibold text-emerald-600">{formatCurrency(totals.assets)}</p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Liabilities</p>
                  <p className="text-lg font-semibold text-red-600">{formatCurrency(totals.liabilities)}</p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Net worth</p>
                  <p className="text-lg font-semibold">{formatCurrency(totals.netWorth)}</p>
                </div>
              </div>
            </div>

            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Accounts list</h3>
                  <p className="text-sm text-gray-500">Track balances by account.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCreating(!isCreating)}
                  className="btn-secondary text-sm"
                >
                  {isCreating ? 'Close' : 'Add account'}
                </button>
              </div>

              {loading ? (
                <p className="text-gray-600">Loading accounts...</p>
              ) : accounts && accounts.length > 0 ? (
                <div className="space-y-4">
                  {accounts.map((account) => {
                    const isLiability = LIABILITY_TYPES.has(account.account_type)
                    return (
                      <div key={account.id} className="surface-muted p-4">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="text-sm text-gray-500 uppercase">{account.account_type}</p>
                            <h4 className="text-base font-semibold">{account.name}</h4>
                            <p className="text-xs text-gray-500">{account.currency}</p>
                          </div>
                          <div className="text-right">
                            <p className={`text-lg font-semibold ${isLiability ? 'text-red-600' : 'text-emerald-600'}`}>
                              {formatCurrency(account.balance, account.currency)}
                            </p>
                            <p className="text-xs text-gray-500">{isLiability ? 'Liability' : 'Asset'}</p>
                          </div>
                        </div>

                        {editingAccountId === account.id ? (
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                            <input
                              value={editForm.name}
                              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                              className="input-field"
                              placeholder="Account name"
                            />
                            <input
                              value={editForm.currency}
                              onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                              className="input-field"
                              placeholder="Currency"
                            />
                            <input
                              value={editForm.balance}
                              onChange={(e) => setEditForm({ ...editForm, balance: e.target.value })}
                              className="input-field"
                              placeholder="Balance"
                              type="number"
                              step="0.01"
                            />
                            <input
                              value={editForm.description}
                              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                              className="input-field"
                              placeholder="Description"
                            />
                            <div className="md:col-span-2 flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() => handleUpdateAccount(account.id)}
                                className="btn-primary text-sm"
                              >
                                Save changes
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingAccountId(null)}
                                className="btn-secondary text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-4 flex flex-wrap gap-2">
                            <button
                              type="button"
                              onClick={() => startEdit(account)}
                              className="btn-secondary text-sm"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteAccount(account.id)}
                              className="text-sm px-3 py-1 rounded-lg border border-red-200 text-red-600"
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="surface-muted p-6 text-center text-gray-600">
                  <p className="font-semibold">No accounts yet.</p>
                  <p className="text-sm">Add your first account to track net worth.</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Add a new account</h3>
              <p className="text-sm text-gray-600 mb-4">Create a new account with a starting balance.</p>
              <form onSubmit={handleCreateAccount} className="space-y-3">
                <input
                  placeholder="Account name"
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                  className="input-field"
                  required
                />
                <select
                  value={accountForm.account_type}
                  onChange={(e) => setAccountForm({ ...accountForm, account_type: e.target.value })}
                  className="select-field"
                >
                  <option value="checking">Checking</option>
                  <option value="savings">Savings</option>
                  <option value="cash">Cash</option>
                  <option value="credit">Credit</option>
                  <option value="investment">Investment</option>
                  <option value="debt">Debt</option>
                  <option value="other">Other</option>
                </select>
                <input
                  placeholder="Currency"
                  value={accountForm.currency}
                  onChange={(e) => setAccountForm({ ...accountForm, currency: e.target.value })}
                  className="input-field"
                />
                <input
                  placeholder="Starting balance"
                  value={accountForm.balance}
                  onChange={(e) => setAccountForm({ ...accountForm, balance: e.target.value })}
                  className="input-field"
                />
                <input
                  placeholder="Description"
                  value={accountForm.description}
                  onChange={(e) => setAccountForm({ ...accountForm, description: e.target.value })}
                  className="input-field"
                />
                <button type="submit" className="btn-primary w-full">
                  Create account
                </button>
              </form>
            </div>

            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Tips</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>Include credit cards and loans to keep liabilities visible.</li>
                <li>Update balances monthly for accurate net worth tracking.</li>
                <li>Use descriptions to note account goals or purpose.</li>
              </ul>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
