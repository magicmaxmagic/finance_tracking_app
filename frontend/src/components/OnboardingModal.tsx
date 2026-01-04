// Onboarding modal overlay
'use client'

import { useEffect, useMemo, useState } from 'react'
import apiClient from '@/lib/api'

type OnboardingModalProps = {
  isOpen: boolean
  onClose: () => void
  onComplete?: () => void
}

type Step = {
  id: string
  label: string
  title: string
  description: string
}

const steps: Step[] = [
  {
    id: 'risk',
    label: 'Risk Appetite',
    title: 'How do you feel about market swings?',
    description: 'Pick the comfort zone that feels natural. We will calibrate your strategy.',
  },
  {
    id: 'goal',
    label: 'Goal',
    title: 'Set a target and horizon',
    description: 'Tell us where you want to be and how fast you want to get there.',
  },
  {
    id: 'profile',
    label: 'Profile',
    title: 'Define your investor profile',
    description: 'Match your style and show where your money is currently allocated.',
  },
  {
    id: 'interests',
    label: 'Interests',
    title: 'What should we explore next?',
    description: 'Select themes you care about and share a short 5-10 year vision.',
  },
]

const riskOptions = [
  { value: 'low', title: 'Low', detail: 'Stability first, gentle growth.' },
  { value: 'medium', title: 'Medium', detail: 'Balanced moves, steady gains.' },
  { value: 'high', title: 'High', detail: 'Comfortable with volatility.' },
]

const profileOptions = [
  { value: 'conservative', title: 'Conservative', detail: 'Protect capital.' },
  { value: 'balanced', title: 'Balanced', detail: 'Mix safety and growth.' },
  { value: 'growth', title: 'Growth', detail: 'Maximize long-term upside.' },
  { value: 'active', title: 'Active', detail: 'Hands-on, tactical bets.' },
]

const horizonOptions = [3, 5, 10, 15, 20]

const allocationOptions = [
  'Cash',
  'Savings',
  'Stocks',
  'ETFs',
  'Bonds',
  'Real estate',
  'Crypto',
  'Private equity',
  'Other',
]

const interestOptions = [
  'Index funds',
  'Dividend investing',
  'Real estate',
  'Crypto',
  'Private markets',
  'High growth',
  'Capital preservation',
  'Impact investing',
]

export function OnboardingModal({ isOpen, onClose, onComplete }: OnboardingModalProps) {
  const [stepIndex, setStepIndex] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    risk_appetite: 'medium',
    investor_profile: 'balanced',
    goal_value: '',
    goal_horizon_years: 10,
    asset_allocation: ['Cash'],
    investment_interests: ['Index funds'],
    vision: '',
  })

  const currentStep = steps[stepIndex]
  const progress = Math.round(((stepIndex + 1) / steps.length) * 100)
  const targetYear = useMemo(() => {
    const now = new Date()
    return now.getFullYear() + Number(formData.goal_horizon_years || 0)
  }, [formData.goal_horizon_years])

  useEffect(() => {
    if (!isOpen) return
    setStepIndex(0)
    setError(null)
  }, [isOpen])

  const toggleMulti = (field: 'asset_allocation' | 'investment_interests', value: string) => {
    setFormData((prev) => {
      const current = prev[field]
      if (current.includes(value)) {
        if (current.length === 1) return prev
        return { ...prev, [field]: current.filter((item) => item !== value) }
      }
      return { ...prev, [field]: [...current, value] }
    })
  }

  const validateStep = () => {
    setError(null)
    if (currentStep.id === 'goal') {
      const goalValue = Number(formData.goal_value)
      if (!goalValue || goalValue <= 0) {
        setError('Enter a goal value greater than zero.')
        return false
      }
      if (!formData.goal_horizon_years || formData.goal_horizon_years < 1) {
        setError('Pick a horizon between 1 and 40 years.')
        return false
      }
    }
    if (currentStep.id === 'profile') {
      if (!formData.investor_profile) {
        setError('Select an investor profile to continue.')
        return false
      }
      if (!formData.asset_allocation.length) {
        setError('Select at least one allocation.')
        return false
      }
    }
    if (currentStep.id === 'interests') {
      if (!formData.investment_interests.length) {
        setError('Select at least one interest.')
        return false
      }
    }
    return true
  }

  const handleNext = () => {
    if (!validateStep()) return
    setStepIndex((prev) => Math.min(prev + 1, steps.length - 1))
  }

  const handleBack = () => {
    setError(null)
    setStepIndex((prev) => Math.max(prev - 1, 0))
  }

  const handleSubmit = async () => {
    if (!validateStep()) return
    const goalValue = Number(formData.goal_value)
    if (!goalValue || goalValue <= 0) {
      setError('Enter a goal value greater than zero.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await apiClient.post('/api/onboarding/complete', {
        risk_appetite: formData.risk_appetite,
        investor_profile: formData.investor_profile,
        goal_value: goalValue,
        goal_horizon_years: formData.goal_horizon_years,
        asset_allocation: formData.asset_allocation,
        investment_interests: formData.investment_interests,
        vision: formData.vision || null,
      })
      onComplete?.()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Unable to save onboarding. Try again.')
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="modal-backdrop">
      <div className="modal-shell">
        <button className="modal-close" type="button" aria-label="Skip onboarding" onClick={onClose}>
          ×
        </button>
        <div className="modal-content">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <aside className="lg:col-span-3 onboarding-rail">
              <div className="onboarding-rail-header">
                <p className="eyebrow">Quick onboarding</p>
                <h2 className="text-xl font-semibold mt-2">Tune your strategy in minutes.</h2>
                <p className="text-sm text-gray-600 mt-2">
                  You can skip anytime and finish later from settings.
                </p>
              </div>
              <div className="onboarding-progress">
                <div className="onboarding-progress-bar" style={{ width: `${progress}%` }} />
              </div>
              <div className="onboarding-step-list">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className={
                      index === stepIndex
                        ? 'onboarding-step-compact onboarding-step-compact-active'
                        : 'onboarding-step-compact'
                    }
                  >
                    <span className="onboarding-step-dot" />
                    <div>
                      <p className="text-sm font-semibold">{step.label}</p>
                      <p className="text-xs text-gray-500">{step.title}</p>
                    </div>
                  </div>
                ))}
              </div>
            </aside>

            <div className="lg:col-span-9">
              <div className="onboarding-card">
                <div className="mb-6">
                  <p className="text-xs uppercase tracking-widest text-gray-500">{currentStep.label}</p>
                  <h3 className="text-2xl font-semibold mt-2">{currentStep.title}</h3>
                  <p className="text-gray-600 mt-2">{currentStep.description}</p>
                  <div className="onboarding-summary">
                    <div className="summary-chip">
                      <span className="summary-chip-label">Target</span>
                      <span className="summary-chip-value">
                        {formData.goal_value ? `$${Number(formData.goal_value).toLocaleString()}` : 'Not set'}
                      </span>
                    </div>
                    <div className="summary-chip">
                      <span className="summary-chip-label">Horizon</span>
                      <span className="summary-chip-value">{formData.goal_horizon_years}y</span>
                    </div>
                    <div className="summary-chip">
                      <span className="summary-chip-label">Risk</span>
                      <span className="summary-chip-value capitalize">{formData.risk_appetite}</span>
                    </div>
                    <div className="summary-chip">
                      <span className="summary-chip-label">Profile</span>
                      <span className="summary-chip-value capitalize">{formData.investor_profile}</span>
                    </div>
                  </div>
                </div>

                {currentStep.id === 'risk' && (
                  <div className="choice-grid">
                    {riskOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={
                          formData.risk_appetite === option.value
                            ? 'choice-tile choice-tile-active'
                            : 'choice-tile'
                        }
                        onClick={() =>
                          setFormData((prev) => ({ ...prev, risk_appetite: option.value }))
                        }
                      >
                        <p className="text-sm font-semibold">{option.title}</p>
                        <p className="text-xs text-gray-500 mt-1">{option.detail}</p>
                      </button>
                    ))}
                  </div>
                )}

                {currentStep.id === 'goal' && (
                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm font-semibold mb-2">Target net worth</label>
                      <input
                        type="number"
                        min={1000}
                        step={500}
                        value={formData.goal_value}
                        onChange={(event) => {
                          setError(null)
                          setFormData((prev) => ({
                            ...prev,
                            goal_value: event.target.value,
                          }))
                        }}
                        className="input-field"
                        placeholder="250000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">Time horizon (years)</label>
                      <div className="flex flex-wrap gap-2">
                        {horizonOptions.map((years) => (
                          <button
                            key={years}
                            type="button"
                            className={
                              formData.goal_horizon_years === years
                                ? 'choice-pill choice-pill-active'
                                : 'choice-pill'
                            }
                            onClick={() =>
                              setFormData((prev) => ({
                                ...prev,
                                goal_horizon_years: years,
                              }))
                            }
                          >
                            {years}y
                          </button>
                        ))}
                        <input
                          type="number"
                          min={1}
                          max={40}
                          value={formData.goal_horizon_years}
                          onChange={(event) => {
                            setError(null)
                            setFormData((prev) => ({
                              ...prev,
                              goal_horizon_years: Number(event.target.value),
                            }))
                          }}
                          className="input-field max-w-[120px]"
                        />
                      </div>
                    </div>
                    <div className="surface-muted p-4 text-sm">
                      Target year: <span className="font-semibold">{targetYear}</span>
                    </div>
                  </div>
                )}

                {currentStep.id === 'profile' && (
                  <div className="space-y-6">
                    <div className="choice-grid">
                      {profileOptions.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          className={
                            formData.investor_profile === option.value
                              ? 'choice-tile choice-tile-active'
                              : 'choice-tile'
                          }
                          onClick={() =>
                            setFormData((prev) => ({ ...prev, investor_profile: option.value }))
                          }
                        >
                          <p className="text-sm font-semibold">{option.title}</p>
                          <p className="text-xs text-gray-500 mt-1">{option.detail}</p>
                        </button>
                      ))}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">Where is your money now?</label>
                      <div className="tag-grid">
                        {allocationOptions.map((option) => {
                          const isActive = formData.asset_allocation.includes(option)
                          return (
                            <button
                              key={option}
                              type="button"
                              className={isActive ? 'tag-chip tag-chip-active' : 'tag-chip'}
                              onClick={() => toggleMulti('asset_allocation', option)}
                            >
                              {option}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {currentStep.id === 'interests' && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold mb-2">
                        Investments you want to explore
                      </label>
                      <div className="tag-grid">
                        {interestOptions.map((option) => {
                          const isActive = formData.investment_interests.includes(option)
                          return (
                            <button
                              key={option}
                              type="button"
                              className={isActive ? 'tag-chip tag-chip-active' : 'tag-chip'}
                              onClick={() => toggleMulti('investment_interests', option)}
                            >
                              {option}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold mb-2">
                        Where do you want to be in 5-10 years?
                      </label>
                      <textarea
                        value={formData.vision}
                        onChange={(event) =>
                          setFormData((prev) => ({ ...prev, vision: event.target.value }))
                        }
                        className="input-field min-h-[110px]"
                        placeholder="Example: financially independent with two properties and a dividend portfolio."
                      />
                    </div>
                  </div>
                )}

                {error && (
                  <div className="surface p-3 text-red-700 border border-red-200 bg-red-50/70 mt-5">
                    {error}
                  </div>
                )}

                <div className="flex items-center justify-between mt-8">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleBack}
                    disabled={stepIndex === 0}
                  >
                    Back
                  </button>
                  {stepIndex === steps.length - 1 ? (
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={handleSubmit}
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Finish setup'}
                    </button>
                  ) : (
                    <button type="button" className="btn-primary" onClick={handleNext}>
                      Next
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
