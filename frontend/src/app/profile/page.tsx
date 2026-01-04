// Profile page
'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { OnboardingProfile } from '@/types'
import { formatCurrency } from '@/lib/utils'

export default function ProfilePage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: onboarding } = useAPI<OnboardingProfile | null>(user ? '/api/onboarding' : null)

  const targetLabel = useMemo(() => {
    if (!onboarding?.target_date) return null
    const date = new Date(onboarding.target_date)
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }, [onboarding?.target_date])

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Profile"
        subtitle="Your investor identity and account preferences."
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="surface p-6 lg:col-span-2 space-y-6">
            <h2 className="text-lg font-semibold">Profile overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Email</p>
                <p className="font-semibold">{user?.email}</p>
              </div>
              <div>
                <p className="text-gray-500">Status</p>
                <p className="font-semibold text-emerald-600">Active</p>
              </div>
              <div>
                <p className="text-gray-500">Investor profile</p>
                <p className="font-semibold capitalize">
                  {onboarding?.investor_profile || 'Not set'}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Risk appetite</p>
                <p className="font-semibold capitalize">
                  {onboarding?.risk_appetite || 'Not set'}
                </p>
              </div>
            </div>
            {onboarding ? (
              <div className="surface-muted p-4 text-sm">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-500">Target net worth</p>
                    <p className="font-semibold">{formatCurrency(onboarding.goal_value)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Target horizon</p>
                    <p className="font-semibold">
                      {onboarding.goal_horizon_years} years {targetLabel ? `· ${targetLabel}` : ''}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Asset allocation</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {onboarding.asset_allocation.map((item) => (
                        <span key={item} className="tag-chip">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-gray-500">Investment interests</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {onboarding.investment_interests.map((item) => (
                        <span key={item} className="tag-chip">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                {onboarding.vision ? (
                  <div className="mt-4 text-gray-600">
                    <p className="text-xs uppercase tracking-widest text-gray-400">Vision</p>
                    <p className="mt-1">{onboarding.vision}</p>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="surface-muted p-4 text-sm text-gray-600">
                Your investor profile is not set yet. Complete onboarding to unlock strategy insights.
              </div>
            )}
          </div>
          <div className="surface p-6 space-y-3">
            <h2 className="text-lg font-semibold">Account</h2>
            <p className="text-sm text-gray-600">
              Upgrade plan, manage billing details, or request account removal.
            </p>
            <div className="flex flex-col gap-2">
              <Link href="/pricing" className="btn-primary text-center">
                Review plans
              </Link>
              <button className="btn-secondary" type="button">
                Manage account
              </button>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
