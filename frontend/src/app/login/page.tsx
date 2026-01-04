// Login page
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import apiClient from '@/lib/api'

export default function LoginPage() {
  const { login, loading, error } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [resetOpen, setResetOpen] = useState(false)
  const [resetEmail, setResetEmail] = useState('')
  const [resetStatus, setResetStatus] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await login(formData.email, formData.password)
  }

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setResetStatus(null)
    try {
      await apiClient.post('/api/auth/request-password-reset', {
        email: resetEmail,
      })
      setResetStatus('If the account exists, a reset email has been sent.')
    } catch (err) {
      setResetStatus('Unable to send the request right now.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
        <div className="text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 border border-white text-xs uppercase tracking-widest">
            Wealth OS
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold mt-6 leading-tight">
            See every decision. Plan the path to your target net worth.
          </h1>
          <p className="text-gray-600 mt-4 text-lg">
            Track income, expenses, and budgets while modeling the fastest routes to long-term wealth.
          </p>
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm text-gray-600">
            <div className="surface-muted p-3">
              <p className="font-semibold">Clarity</p>
              <p className="text-xs">Monthly insights in seconds.</p>
            </div>
            <div className="surface-muted p-3">
              <p className="font-semibold">Control</p>
              <p className="text-xs">Budgets that adapt to you.</p>
            </div>
            <div className="surface-muted p-3">
              <p className="font-semibold">Forecast</p>
              <p className="text-xs">Build scenarios for any horizon.</p>
            </div>
          </div>
        </div>

        <div className="auth-shell rounded-3xl p-8 lg:p-10">
          <div className="mb-6">
            <h2 className="text-2xl font-bold">Sign in</h2>
            <p className="text-gray-600 mt-2">Welcome back. Your plan is waiting.</p>
          </div>

          {error && (
            <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70 mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pr-12"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-500"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 flex flex-col gap-3 text-sm">
            <button
              type="button"
              onClick={() => setResetOpen(!resetOpen)}
              className="text-left text-gray-600 hover:text-gray-900"
            >
              Forgot password?
            </button>

            {resetOpen && (
              <form onSubmit={handleReset} className="space-y-3">
                <input
                  type="email"
                  placeholder="Your email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="input-field"
                  required
                />
                <button type="submit" className="btn-secondary w-full">
                  Send reset link
                </button>
                {resetStatus && <p className="text-xs text-gray-500">{resetStatus}</p>}
              </form>
            )}
          </div>

          <div className="mt-6 text-sm text-gray-600">
            New here?{' '}
            <Link href="/register" className="text-emerald-600 font-semibold hover:underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
