// Register page
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'

export default function RegisterPage() {
  const { register, loading, error } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    if (formData.password !== confirmPassword) {
      setLocalError('Passwords do not match.')
      return
    }
    await register(formData.email, formData.password, formData.fullName)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
        <div className="auth-shell rounded-3xl p-8 lg:p-10 order-2 lg:order-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold">Create account</h2>
            <p className="text-gray-600 mt-2">Set up your wealth workspace in minutes.</p>
          </div>

          {(error || localError) && (
            <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70 mb-4">
              {localError || error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Full name</label>
              <input
                type="text"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className="input-field"
                placeholder="Maxence Legendre"
              />
            </div>

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

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Confirm password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-field"
                minLength={8}
                required
              />
              <p className="text-xs text-gray-500 mt-2">Password must be at least 8 characters.</p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create my account'}
            </button>
          </form>

          <div className="mt-6 text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="text-emerald-600 font-semibold hover:underline">
              Sign in
            </Link>
          </div>
        </div>

        <div className="order-1 lg:order-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 border border-white text-xs uppercase tracking-widest">
            Onboarding
          </div>
          <h1 className="text-4xl lg:text-5xl font-bold mt-6 leading-tight">
            Build a plan that adapts as your wealth grows.
          </h1>
          <p className="text-gray-600 mt-4 text-lg">
            Centralize accounts, budgets, and forecasts to steer every financial move.
          </p>
          <ul className="mt-8 space-y-3 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-600" />
              Fast transaction entry
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              Smart budget alerts
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-600" />
              Long-term forecasts
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
