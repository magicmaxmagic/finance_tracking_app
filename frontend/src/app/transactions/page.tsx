// Transactions page
'use client'

import { useMemo, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { Account, Category, Transaction } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'

export default function TransactionsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: accounts, mutate: mutateAccounts } = useAPI<Account[]>(
    user ? '/api/accounts' : null
  )
  const { data: categories, mutate: mutateCategories } = useAPI<Category[]>(
    user ? '/api/categories' : null
  )
  const { data: transactions, mutate: mutateTransactions } = useAPI<any>(
    user ? '/api/transactions?limit=20' : null
  )
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvPreview, setCsvPreview] = useState<any | null>(null)
  const [csvLoading, setCsvLoading] = useState(false)
  const [csvError, setCsvError] = useState<string | null>(null)
  const [isCreatingAccount, setIsCreatingAccount] = useState(false)
  const [isCreatingCategory, setIsCreatingCategory] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    currency: 'USD',
    transaction_date: new Date().toISOString().slice(0, 10),
    account_id: '',
    category_id: '',
    type: 'expense',
    notes: '',
    tags: '',
  })
  const [accountForm, setAccountForm] = useState({
    name: '',
    account_type: 'checking',
    currency: 'USD',
    balance: '0',
  })
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    is_income: false,
  })

  const recentTransactions = transactions?.items ?? []
  const selectedAccount = useMemo(
    () => accounts?.find((acc) => String(acc.id) === formData.account_id),
    [accounts, formData.account_id]
  )

  const handleTransactionChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!formData.account_id) {
      setFormError('Please select an account.')
      return
    }
    const numericAmount = parseFloat(formData.amount)
    if (!numericAmount || Number.isNaN(numericAmount)) {
      setFormError('Please enter a valid amount.')
      return
    }

    const signedAmount = formData.type === 'expense' ? -Math.abs(numericAmount) : Math.abs(numericAmount)

    try {
      await apiClient.post('/api/transactions', {
        description: formData.description,
        amount: signedAmount,
        currency: formData.currency,
        transaction_date: `${formData.transaction_date}T00:00:00`,
        account_id: Number(formData.account_id),
        category_id: formData.category_id ? Number(formData.category_id) : null,
        notes: formData.notes || null,
        tags: formData.tags || null,
      })
      setFormData({
        ...formData,
        description: '',
        amount: '',
        notes: '',
        tags: '',
      })
      mutateTransactions()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to create transaction.'
      setFormError(message)
    }
  }

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiClient.post('/api/accounts', {
        name: accountForm.name,
        account_type: accountForm.account_type.toLowerCase(),
        currency: accountForm.currency,
        balance: parseFloat(accountForm.balance || '0'),
      })
      setAccountForm({ ...accountForm, name: '', balance: '0' })
      setIsCreatingAccount(false)
      mutateAccounts()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to create account.'
      setFormError(message)
    }
  }

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiClient.post('/api/categories', {
        name: categoryForm.name,
        is_income: categoryForm.is_income,
      })
      setCategoryForm({ name: '', is_income: false })
      setIsCreatingCategory(false)
      mutateCategories()
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to create category.'
      setFormError(message)
    }
  }

  const handleCsvPreview = async () => {
    if (!csvFile) return
    setCsvLoading(true)
    setCsvError(null)
    try {
      const formData = new FormData()
      formData.append('file', csvFile)
      const response = await apiClient.post('/api/transactions/import/preview', formData)
      setCsvPreview(response.data)
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Unable to analyze the CSV file.'
      setCsvError(message)
    } finally {
      setCsvLoading(false)
    }
  }

  const handleCsvImport = async () => {
    if (!csvFile || !selectedAccount) {
      setCsvError('Please select an account before importing.')
      return
    }
    setCsvLoading(true)
    setCsvError(null)
    try {
      const formData = new FormData()
      formData.append('file', csvFile)
      const response = await apiClient.post(
        `/api/transactions/import/csv?account_id=${selectedAccount.id}`,
        formData
      )
      setCsvPreview(null)
      setCsvFile(null)
      mutateTransactions()
      return response.data
    } catch (err) {
      const message = (err as any)?.response?.data?.detail || 'Import failed. Please verify the CSV format.'
      setCsvError(message)
    } finally {
      setCsvLoading(false)
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Transactions"
        subtitle="Log spending, sync statements, and tag every transaction for clearer insight."
        actions={
          <div className="flex flex-wrap gap-3">
            <a className="btn-secondary" href="/api/data/export/transactions.csv">
              Export CSV
            </a>
            <a className="btn-primary" href="/api/data/export/transactions.json">
              Export JSON
            </a>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
          <div className="surface p-6">
            <h3 className="text-lg font-semibold mb-2">CSV import (bank statement)</h3>
            <p className="text-sm text-gray-600 mb-4">
              Upload your statement with + / - amounts, then preview earnings vs expenses before importing.
            </p>
            <div className="flex flex-col md:flex-row md:items-center gap-3">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="flex-1 text-sm"
              />
              <button
                type="button"
                onClick={handleCsvPreview}
                disabled={!csvFile || csvLoading}
                className="btn-primary disabled:opacity-50"
              >
                {csvLoading ? 'Analyzing...' : 'Analyze CSV'}
              </button>
            </div>

            {csvError && (
              <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70 mt-4">
                {csvError}
              </div>
            )}

            {csvPreview && (
              <div className="mt-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="stat-tile">
                    <p className="text-xs uppercase text-gray-500">Earnings</p>
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
                  <div className="md:col-span-3 text-xs text-gray-500">
                    Rows analyzed: {csvPreview.rows} - Errors: {csvPreview.errors}
                  </div>
                </div>

                {csvPreview.warnings?.length ? (
                  <div className="surface p-3 text-amber-700 border border-amber-200 bg-amber-50/70 text-sm">
                    {csvPreview.warnings.join(' ')}
                  </div>
                ) : null}

                {(csvPreview.detected_fields || csvPreview.unmapped_columns) && (
                  <div className="text-xs text-gray-500">
                    Detected fields: {csvPreview.detected_fields?.join(', ') || 'None'} -
                    Unmapped columns: {csvPreview.unmapped_columns?.join(', ') || 'None'}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="surface-muted p-4">
                    <p className="text-sm font-semibold mb-2">Top expense sources</p>
                    <div className="space-y-2">
                      {csvPreview.top_expense_sources?.length ? (
                        csvPreview.top_expense_sources.map((item: any) => (
                          <div key={item.name} className="flex items-center justify-between text-sm">
                            <span className="text-gray-700">{item.name}</span>
                            <span className="font-semibold text-red-600">
                              {formatCurrency(item.amount)}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-gray-500">No expense rows detected.</p>
                      )}
                    </div>
                  </div>
                  <div className="surface-muted p-4">
                    <p className="text-sm font-semibold mb-2">Top income sources</p>
                    <div className="space-y-2">
                      {csvPreview.top_income_sources?.length ? (
                        csvPreview.top_income_sources.map((item: any) => (
                          <div key={item.name} className="flex items-center justify-between text-sm">
                            <span className="text-gray-700">{item.name}</span>
                            <span className="font-semibold text-emerald-600">
                              {formatCurrency(item.amount)}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-gray-500">No income rows detected.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-4 flex flex-col md:flex-row md:items-center gap-3">
              <select
                name="account_id"
                value={formData.account_id}
                onChange={handleTransactionChange}
                className="select-field md:w-1/2"
              >
                <option value="">Select account for import</option>
                {accounts?.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={handleCsvImport}
                disabled={!csvFile || !selectedAccount || csvLoading}
                className="btn-primary disabled:opacity-50"
              >
                Import transactions
              </button>
            </div>
          </div>

          <div className="surface p-6">
            <h3 className="text-lg font-semibold mb-4">Add transaction</h3>
            {formError && (
              <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70 mb-4">
                {formError}
              </div>
            )}
            <form onSubmit={handleCreateTransaction} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                <input
                  name="description"
                  value={formData.description}
                  onChange={handleTransactionChange}
                  className="input-field"
                  placeholder="Coffee, salary, groceries..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Type</label>
                <select
                  name="type"
                  value={formData.type}
                  onChange={handleTransactionChange}
                  className="select-field"
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Amount</label>
                <input
                  name="amount"
                  value={formData.amount}
                  onChange={handleTransactionChange}
                  className="input-field"
                  type="number"
                  step="0.01"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Currency</label>
                <input
                  name="currency"
                  value={formData.currency}
                  onChange={handleTransactionChange}
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Date</label>
                <input
                  name="transaction_date"
                  value={formData.transaction_date}
                  onChange={handleTransactionChange}
                  className="input-field"
                  type="date"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Account</label>
                <select
                  name="account_id"
                  value={formData.account_id}
                  onChange={handleTransactionChange}
                  className="select-field"
                  required
                >
                  <option value="">Select account</option>
                  {accounts?.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Category</label>
                <select
                  name="category_id"
                  value={formData.category_id}
                  onChange={handleTransactionChange}
                  className="select-field"
                >
                  <option value="">Auto categorize</option>
                  {categories?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                <input
                  name="notes"
                  value={formData.notes}
                  onChange={handleTransactionChange}
                  className="input-field"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Tags</label>
                <input
                  name="tags"
                  value={formData.tags}
                  onChange={handleTransactionChange}
                  className="input-field"
                />
              </div>

              <button type="submit" className="btn-primary md:col-span-2">
                Add transaction
              </button>
            </form>
          </div>

          <div className="surface p-6">
            <h3 className="text-lg font-semibold mb-4">Recent transactions</h3>
            {recentTransactions.length === 0 ? (
              <p className="text-gray-600">No transactions yet.</p>
            ) : (
              <div className="space-y-3">
                {recentTransactions.map((tx: Transaction) => {
                  const amountValue = Number(tx.amount)
                  return (
                    <div key={tx.id} className="flex items-center justify-between border-b border-gray-100 pb-2">
                      <div>
                        <p className="font-semibold">{tx.description}</p>
                        <p className="text-xs text-gray-500">{tx.transaction_date}</p>
                      </div>
                      <span className={amountValue < 0 ? 'text-red-600 font-semibold' : 'text-emerald-600 font-semibold'}>
                        {formatCurrency(tx.amount, tx.currency)}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Accounts</h3>
              <button
                type="button"
                onClick={() => setIsCreatingAccount(!isCreatingAccount)}
                className="btn-secondary text-sm"
              >
                {isCreatingAccount ? 'Close' : 'Add'}
              </button>
            </div>
            {isCreatingAccount && (
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
                <button
                  type="submit"
                  className="btn-primary w-full"
                >
                  Save account
                </button>
              </form>
            )}
          </div>

          <div className="surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Categories</h3>
              <button
                type="button"
                onClick={() => setIsCreatingCategory(!isCreatingCategory)}
                className="btn-secondary text-sm"
              >
                {isCreatingCategory ? 'Close' : 'Add'}
              </button>
            </div>
            {isCreatingCategory && (
              <form onSubmit={handleCreateCategory} className="space-y-3">
                <input
                  placeholder="Category name"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  className="input-field"
                  required
                />
                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={categoryForm.is_income}
                    onChange={(e) => setCategoryForm({ ...categoryForm, is_income: e.target.checked })}
                  />
                  Income category
                </label>
                <button type="submit" className="btn-primary w-full">
                  Save category
                </button>
              </form>
            )}
          </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
