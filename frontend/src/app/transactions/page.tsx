// Transactions page
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { Account, Category, Transaction } from '@/types'
import { formatCurrency } from '@/lib/utils'

export default function TransactionsPage() {
  const { user, logout } = useAuth()
  const { data: accounts, mutate: mutateAccounts } = useAPI<Account[]>('/api/accounts')
  const { data: categories, mutate: mutateCategories } = useAPI<Category[]>('/api/categories')
  const { data: transactions, mutate: mutateTransactions } = useAPI<any>('/api/transactions?limit=20')
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

  if (!user) {
    return <div>Loading...</div>
  }

  const recentTransactions = transactions?.items ?? []
  const hasAccounts = accounts && accounts.length > 0

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
        account_type: accountForm.account_type,
        currency: accountForm.currency,
        balance: parseFloat(accountForm.balance || '0'),
      })
      setAccountForm({ ...accountForm, name: '', balance: '0' })
      setIsCreatingAccount(false)
      mutateAccounts()
    } catch (err) {
      setFormError('Unable to create account.')
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
      setFormError('Unable to create category.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Finance Tracker</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">{user.email}</span>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-4">
          <Link href="/dashboard" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Dashboard
          </Link>
          <Link href="/transactions" className="px-3 py-4 border-b-2 border-blue-500 text-blue-600 font-bold">
            Transactions
          </Link>
          <Link href="/budgets" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Budgets
          </Link>
          <Link href="/net-worth" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Net Worth
          </Link>
          <Link href="/accounts" className="px-3 py-4 hover:border-b-2 hover:border-gray-300">
            Accounts
          </Link>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Transactions</h2>
          <div className="flex flex-wrap gap-3">
            <a
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              href="/api/data/export/transactions.csv"
            >
              Export CSV
            </a>
            <a
              className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-900"
              href="/api/data/export/transactions.json"
            >
              Export JSON
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="glass-panel rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Add transaction</h3>
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4">
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
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
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
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
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
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                    placeholder="0.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Date</label>
                  <input
                    type="date"
                    name="transaction_date"
                    value={formData.transaction_date}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Currency</label>
                  <input
                    name="currency"
                    value={formData.currency}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Account</label>
                  <select
                    name="account_id"
                    value={formData.account_id}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                    required
                  >
                    <option value="">Select an account</option>
                    {accounts?.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.name}
                      </option>
                    ))}
                  </select>
                  {!hasAccounts && (
                    <p className="text-xs text-gray-500 mt-2">Create an account to get started.</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Category</label>
                  <select
                    name="category_id"
                    value={formData.category_id}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                  >
                    <option value="">Uncategorized</option>
                    {categories?.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Tags</label>
                  <input
                    name="tags"
                    value={formData.tags}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                    placeholder="travel, recurring"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                  <input
                    name="notes"
                    value={formData.notes}
                    onChange={handleTransactionChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl"
                    placeholder="Optional context"
                  />
                </div>

                <div className="md:col-span-2">
                  <button
                    type="submit"
                    className="w-full bg-black text-white font-semibold py-3 px-4 rounded-xl hover:bg-gray-900 transition"
                  >
                    Add transaction
                  </button>
                </div>
              </form>
            </div>

            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Recent transactions</h3>
              {recentTransactions.length === 0 ? (
                <p className="text-gray-600">No transactions yet.</p>
              ) : (
                <div className="space-y-3">
                  {recentTransactions.map((tx: Transaction) => {
                    const amountValue = Number(tx.amount)
                    return (
                      <div key={tx.id} className="flex items-center justify-between border-b pb-2">
                      <div>
                        <p className="font-semibold">{tx.description}</p>
                        <p className="text-xs text-gray-500">{tx.transaction_date}</p>
                      </div>
                      <span className={amountValue < 0 ? 'text-red-600 font-semibold' : 'text-emerald-600 font-semibold'}>
                        {formatCurrency(tx.amount)}
                      </span>
                    </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Accounts</h3>
                <button
                  type="button"
                  onClick={() => setIsCreatingAccount(!isCreatingAccount)}
                  className="text-sm text-blue-600 font-semibold"
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
                    className="w-full px-3 py-2 border border-gray-200 rounded-xl"
                    required
                  />
                  <select
                    value={accountForm.account_type}
                    onChange={(e) => setAccountForm({ ...accountForm, account_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-xl"
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
                    className="w-full px-3 py-2 border border-gray-200 rounded-xl"
                  />
                  <input
                    placeholder="Starting balance"
                    value={accountForm.balance}
                    onChange={(e) => setAccountForm({ ...accountForm, balance: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-xl"
                  />
                  <button
                    type="submit"
                    className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700"
                  >
                    Save account
                  </button>
                </form>
              )}
            </div>

            <div className="glass-panel rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Categories</h3>
                <button
                  type="button"
                  onClick={() => setIsCreatingCategory(!isCreatingCategory)}
                  className="text-sm text-blue-600 font-semibold"
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
                    className="w-full px-3 py-2 border border-gray-200 rounded-xl"
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
                  <button
                    type="submit"
                    className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700"
                  >
                    Save category
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
