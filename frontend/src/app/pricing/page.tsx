// Pricing page
'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { UserSettings } from '@/types'
import apiClient from '@/lib/api'

const tiers = [
  {
    name: 'Starter',
    monthly: 0,
    annual: 0,
    description: 'Personal tracking and baseline strategy.',
    features: ['CSV import', 'Budgets & alerts', 'Basic forecast', 'Net worth snapshots'],
  },
  {
    name: 'Pro Strategy',
    monthly: 19,
    annual: 190,
    description: 'Scenario modeling and decision intelligence.',
    features: [
      'Trajectory engine',
      'Scenario comparisons',
      'Goal tracking KPIs',
      'Decision impact lab',
    ],
    highlight: true,
  },
  {
    name: 'Wealth Lab',
    monthly: 49,
    annual: 490,
    description: 'Advanced forecasts with tailored guidance.',
    features: [
      'Multi-goal planning',
      'Priority recommendations',
      'Custom assumptions',
      'Priority support',
    ],
  },
]

export default function PricingPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: settings } = useAPI<UserSettings>(user ? '/api/settings' : null)
  const [billing, setBilling] = useState<'monthly' | 'annual'>('monthly')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isPro = settings?.plan === 'pro'

  const startCheckout = async () => {
    setBusy(true)
    setError(null)
    try {
      const response = await apiClient.post('/api/billing/checkout', {
        interval: billing,
      })
      if (response.data?.url) {
        window.location.href = response.data.url
        return
      }
      setError('Unable to start checkout')
    } catch {
      setError('Unable to start checkout')
    } finally {
      setBusy(false)
    }
  }

  const openPortal = async () => {
    setBusy(true)
    setError(null)
    try {
      const response = await apiClient.post('/api/billing/portal')
      if (response.data?.url) {
        window.location.href = response.data.url
        return
      }
      setError('Unable to open billing portal')
    } catch {
      setError('Unable to open billing portal')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Pro pricing"
        subtitle="Choose the depth of strategy support your team needs."
      >
        <div className="surface p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Scale from tracking to strategy</h2>
            <p className="text-sm text-gray-600 mt-2">
              Upgrade when you need scenario modeling, decision intelligence, or team-level forecasting.
            </p>
            {error ? <p className="text-sm text-rose-600 mt-2">{error}</p> : null}
          </div>
          <div className="pricing-toggle">
            <button
              className={billing === 'monthly' ? 'pricing-toggle-active' : 'pricing-toggle-button'}
              type="button"
              onClick={() => setBilling('monthly')}
            >
              Monthly
            </button>
            <button
              className={billing === 'annual' ? 'pricing-toggle-active' : 'pricing-toggle-button'}
              type="button"
              onClick={() => setBilling('annual')}
            >
              Annual (2 months free)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {tiers.map((tier) => {
            const price = billing === 'monthly' ? tier.monthly : tier.annual
            const isProTier = tier.name === 'Pro Strategy'
            const actionLabel = isProTier ? (isPro ? 'Manage subscription' : 'Upgrade to Pro') : 'Select'
            return (
              <div
                key={tier.name}
                className={`surface p-6 space-y-4 ${tier.highlight ? 'ring-2 ring-emerald-400/70' : ''}`}
              >
                {tier.highlight ? <span className="pricing-badge">Most popular</span> : null}
                <div>
                  <p className="text-xs uppercase tracking-widest text-gray-500">{tier.name}</p>
                  <div className="flex items-baseline gap-2 mt-3">
                    <p className="text-3xl font-bold">{price === 0 ? 'Free' : `$${price}`}</p>
                    {price > 0 ? (
                      <span className="text-sm text-gray-500">{billing === 'monthly' ? '/mo' : '/yr'}</span>
                    ) : null}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">{tier.description}</p>
                </div>
                <ul className="text-sm text-gray-600 space-y-2">
                  {tier.features.map((feature) => (
                    <li key={feature}>• {feature}</li>
                  ))}
                </ul>
                <button
                  className={tier.highlight ? 'btn-primary w-full' : 'btn-secondary w-full'}
                  type="button"
                  onClick={isProTier ? (isPro ? openPortal : startCheckout) : undefined}
                  disabled={busy && isProTier}
                >
                  {actionLabel}
                </button>
              </div>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="surface p-6 space-y-3">
            <h3 className="text-lg font-semibold">Security & compliance</h3>
            <p className="text-sm text-gray-600">
              SOC-ready logging, refresh-token rotation, and encrypted storage of sensitive data.
            </p>
          </div>
          <div className="surface p-6 space-y-3">
            <h3 className="text-lg font-semibold">Team-ready controls</h3>
            <p className="text-sm text-gray-600">
              Role-based access, exportable audit logs, and workflow-ready approvals.
            </p>
          </div>
          <div className="surface p-6 space-y-3">
            <h3 className="text-lg font-semibold">Support & onboarding</h3>
            <p className="text-sm text-gray-600">
              Priority onboarding, portfolio reviews, and guided configuration assistance.
            </p>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
