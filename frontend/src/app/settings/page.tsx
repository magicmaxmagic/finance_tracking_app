// Settings page
'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { UserSettings } from '@/types'
import apiClient from '@/lib/api'

type SettingsState = {
  currency: string
  timezone: string
  date_format: string
  start_of_week: string
  digest_enabled: boolean
  transaction_alerts: boolean
  budget_alerts: boolean
  auto_categorization: boolean
  import_deduplication: boolean
  default_view: string
  data_retention: string
  analytics_opt_in: boolean
}

const defaultSettings: SettingsState = {
  currency: 'USD',
  timezone: 'America/New_York',
  date_format: 'MM/DD/YYYY',
  start_of_week: 'Monday',
  digest_enabled: true,
  transaction_alerts: true,
  budget_alerts: true,
  auto_categorization: true,
  import_deduplication: true,
  default_view: 'dashboard',
  data_retention: 'forever',
  analytics_opt_in: true,
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export default function SettingsPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: remoteSettings, mutate } = useAPI<UserSettings>(user ? '/api/settings' : null)
  const [settings, setSettings] = useState<SettingsState>(defaultSettings)
  const [status, setStatus] = useState<string | null>(null)
  const [isDirty, setIsDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [billingStatus, setBillingStatus] = useState<string | null>(null)
  const [billingBusy, setBillingBusy] = useState(false)
  const [calendarStatus, setCalendarStatus] = useState<string | null>(null)
  const [calendarBusy, setCalendarBusy] = useState(false)
  const [copyStatus, setCopyStatus] = useState<string | null>(null)
  const [appleCopyStatus, setAppleCopyStatus] = useState<string | null>(null)

  const statusLabel = useMemo(() => {
    if (saving) return 'Saving...'
    return status
  }, [saving, status])

  const renewalLabel = useMemo(() => {
    if (!remoteSettings?.current_period_end) return null
    const date = new Date(remoteSettings.current_period_end)
    if (Number.isNaN(date.getTime())) return null
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }, [remoteSettings?.current_period_end])

  const calendarFeedUrl = useMemo(() => {
    if (!remoteSettings?.calendar_feed_token) return ''
    return `${API_BASE}/api/schedule/ics/public/${remoteSettings.calendar_feed_token}`
  }, [remoteSettings?.calendar_feed_token])

  const isSecureCalendarFeed = useMemo(
    () => Boolean(calendarFeedUrl && calendarFeedUrl.startsWith('https://')),
    [calendarFeedUrl]
  )

  const appleCalendarUrl = useMemo(() => {
    if (!calendarFeedUrl) return ''
    if (calendarFeedUrl.startsWith('webcal://')) return calendarFeedUrl
    return calendarFeedUrl.replace(/^https?:\/\//, 'webcal://')
  }, [calendarFeedUrl])

  useEffect(() => {
    if (!remoteSettings || isDirty) return
    setSettings({
      currency: remoteSettings.currency,
      timezone: remoteSettings.timezone,
      date_format: remoteSettings.date_format,
      start_of_week: remoteSettings.start_of_week,
      default_view: remoteSettings.default_view,
      data_retention: remoteSettings.data_retention,
      digest_enabled: remoteSettings.digest_enabled,
      transaction_alerts: remoteSettings.transaction_alerts,
      budget_alerts: remoteSettings.budget_alerts,
      auto_categorization: remoteSettings.auto_categorization,
      import_deduplication: remoteSettings.import_deduplication,
      analytics_opt_in: remoteSettings.analytics_opt_in,
    })
  }, [remoteSettings, isDirty])

  const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
    setIsDirty(true)
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const saveSettings = async () => {
    setSaving(true)
    setStatus(null)
    try {
      await apiClient.put('/api/settings', settings)
      await mutate()
      setIsDirty(false)
      setStatus('Saved')
    } catch {
      setStatus('Unable to save')
    } finally {
      setSaving(false)
      window.setTimeout(() => setStatus(null), 2000)
    }
  }

  const resetSettings = () => {
    setSettings(defaultSettings)
    setIsDirty(true)
    setStatus('Defaults restored')
    window.setTimeout(() => setStatus(null), 2000)
  }

  const openPortal = async () => {
    setBillingBusy(true)
    setBillingStatus(null)
    try {
      const response = await apiClient.post('/api/billing/portal')
      if (response.data?.url) {
        window.location.href = response.data.url
        return
      }
      setBillingStatus('Unable to open billing portal')
    } catch {
      setBillingStatus('Unable to open billing portal')
    } finally {
      setBillingBusy(false)
      window.setTimeout(() => setBillingStatus(null), 2500)
    }
  }

  const regenerateCalendarLink = async () => {
    setCalendarBusy(true)
    setCalendarStatus(null)
    try {
      await apiClient.post('/api/settings/calendar-feed/rotate')
      await mutate()
      setCalendarStatus('New link generated')
    } catch {
      setCalendarStatus('Unable to regenerate link')
    } finally {
      setCalendarBusy(false)
      window.setTimeout(() => setCalendarStatus(null), 2000)
    }
  }

  const copyCalendarLink = async () => {
    if (!calendarFeedUrl) return
    try {
      await navigator.clipboard.writeText(calendarFeedUrl)
      setCopyStatus('Copied')
    } catch {
      setCopyStatus('Copy failed')
    } finally {
      window.setTimeout(() => setCopyStatus(null), 2000)
    }
  }

  const copyAppleCalendarLink = async () => {
    if (!appleCalendarUrl) return
    try {
      await navigator.clipboard.writeText(appleCalendarUrl)
      setAppleCopyStatus('Copied')
    } catch {
      setAppleCopyStatus('Copy failed')
    } finally {
      window.setTimeout(() => setAppleCopyStatus(null), 2000)
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Settings"
        subtitle="Configure workspace defaults, automation rules, and security controls."
      >
        <div className="surface p-6 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-lg font-semibold">Workspace configuration</h2>
            <p className="text-sm text-gray-600">Changes apply instantly to your personal workspace.</p>
          </div>
          <div className="flex items-center gap-2">
            {statusLabel && <span className="text-sm text-emerald-600">{statusLabel}</span>}
            <button className="btn-secondary" type="button" onClick={resetSettings}>
              Reset
            </button>
            <button className="btn-primary" type="button" onClick={saveSettings}>
              Save changes
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="surface p-6 space-y-5">
            <h3 className="text-lg font-semibold">App preferences</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block text-gray-500 mb-2">Default currency</label>
                <select
                  className="select-field"
                  value={settings.currency}
                  onChange={(event) => updateSetting('currency', event.target.value)}
                >
                  <option value="USD">USD</option>
                  <option value="CAD">CAD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-500 mb-2">Timezone</label>
                <select
                  className="select-field"
                  value={settings.timezone}
                  onChange={(event) => updateSetting('timezone', event.target.value)}
                >
                  <option value="America/New_York">America/New_York</option>
                  <option value="America/Toronto">America/Toronto</option>
                  <option value="Europe/Paris">Europe/Paris</option>
                  <option value="Europe/London">Europe/London</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-500 mb-2">Date format</label>
                <select
                  className="select-field"
                  value={settings.date_format}
                  onChange={(event) => updateSetting('date_format', event.target.value)}
                >
                  <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                  <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-500 mb-2">Start of week</label>
                <select
                  className="select-field"
                  value={settings.start_of_week}
                  onChange={(event) => updateSetting('start_of_week', event.target.value)}
                >
                  <option value="Monday">Monday</option>
                  <option value="Sunday">Sunday</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-500 mb-2">Default landing view</label>
                <select
                  className="select-field"
                  value={settings.default_view}
                  onChange={(event) => updateSetting('default_view', event.target.value)}
                >
                  <option value="workspace">Workspace</option>
                  <option value="dashboard">Dashboard</option>
                  <option value="transactions">Transactions</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-500 mb-2">Data retention</label>
                <select
                  className="select-field"
                  value={settings.data_retention}
                  onChange={(event) => updateSetting('data_retention', event.target.value)}
                >
                  <option value="forever">Forever</option>
                  <option value="5_years">5 years</option>
                  <option value="3_years">3 years</option>
                </select>
              </div>
            </div>
          </div>

          <div className="surface p-6 space-y-5">
            <h3 className="text-lg font-semibold">Automation rules</h3>
            <p className="text-sm text-gray-600">
              Let the engine keep your ledger clean and insights accurate.
            </p>
            <div className="space-y-4 text-sm">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.auto_categorization}
                  onChange={(event) => updateSetting('auto_categorization', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Auto-categorize imports
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.import_deduplication}
                  onChange={(event) => updateSetting('import_deduplication', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Deduplicate transactions
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.analytics_opt_in}
                  onChange={(event) => updateSetting('analytics_opt_in', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Share anonymous usage analytics
              </label>
            </div>
          </div>

          <div className="surface p-6 space-y-5">
            <h3 className="text-lg font-semibold">Notifications</h3>
            <p className="text-sm text-gray-600">
              Keep an eye on budget drift, anomalies, and monthly summaries.
            </p>
            <div className="space-y-4 text-sm">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.digest_enabled}
                  onChange={(event) => updateSetting('digest_enabled', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Weekly strategy digest
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.transaction_alerts}
                  onChange={(event) => updateSetting('transaction_alerts', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Large transaction alerts
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.budget_alerts}
                  onChange={(event) => updateSetting('budget_alerts', event.target.checked)}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                Budget threshold alerts
              </label>
            </div>
          </div>

          <div className="surface p-6 space-y-4">
            <h3 className="text-lg font-semibold">Calendar integrations</h3>
            <p className="text-sm text-gray-600">
              Subscribe to your finance schedule (outbound) in Google, Outlook, or Apple calendars.
            </p>
            <div className="space-y-3 text-sm">
              <div className="space-y-2">
                <label className="block text-gray-500">Calendar feed link</label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    className="input-field"
                    readOnly
                    value={calendarFeedUrl}
                    placeholder="Calendar link will appear here"
                  />
                  <button
                    className="btn-secondary btn-small"
                    type="button"
                    onClick={copyCalendarLink}
                    disabled={!calendarFeedUrl}
                  >
                    {copyStatus || 'Copy link'}
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {appleCalendarUrl ? (
                    <a className="btn-secondary btn-small" href={appleCalendarUrl} rel="noreferrer">
                      Subscribe in Apple Calendar
                    </a>
                  ) : (
                    <button className="btn-secondary btn-small" type="button" disabled>
                      Subscribe in Apple Calendar
                    </button>
                  )}
                  <button
                    className="btn-secondary btn-small"
                    type="button"
                    onClick={copyAppleCalendarLink}
                    disabled={!appleCalendarUrl}
                  >
                    {appleCopyStatus || 'Copy Apple link'}
                  </button>
                  <button
                    className="btn-secondary btn-small"
                    type="button"
                    onClick={regenerateCalendarLink}
                    disabled={calendarBusy}
                  >
                    {calendarBusy ? 'Generating...' : 'Regenerate link'}
                  </button>
                  {calendarStatus ? <span className="text-xs text-emerald-600">{calendarStatus}</span> : null}
                </div>
                <p className="text-xs text-gray-500">Keep this URL private. Regenerate if it gets shared.</p>
                {!isSecureCalendarFeed ? (
                  <p className="text-xs text-amber-600">
                    Apple Calendar requires HTTPS. Use a secure public URL instead of localhost.
                  </p>
                ) : null}
              </div>
            </div>
          </div>

          <div className="surface p-6 space-y-4">
            <h3 className="text-lg font-semibold">Security & billing</h3>
            <div className="text-sm text-gray-600 space-y-3">
              <p>Session history and access logs are available in the audit center.</p>
              <div className="surface-muted p-3 text-sm">
                <p className="text-xs uppercase tracking-widest text-gray-400">Plan</p>
                <p className="font-semibold text-gray-800 capitalize">{remoteSettings?.plan || 'starter'}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Status: {remoteSettings?.subscription_status || 'Not subscribed'}
                </p>
                {renewalLabel ? (
                  <p className="text-xs text-gray-500 mt-1">
                    {remoteSettings?.cancel_at_period_end ? 'Ends on' : 'Renews on'} {renewalLabel}
                  </p>
                ) : null}
              </div>
              <div className="flex flex-col gap-2">
                <button className="btn-secondary" type="button">
                  View audit logs
                </button>
                <button className="btn-secondary" type="button">
                  Export account data
                </button>
                {remoteSettings?.plan === 'pro' ? (
                  <button className="btn-primary" type="button" onClick={openPortal} disabled={billingBusy}>
                    {billingBusy ? 'Opening portal...' : 'Manage subscription'}
                  </button>
                ) : (
                  <Link className="btn-primary text-center" href="/pricing">
                    Upgrade to Pro
                  </Link>
                )}
                {billingStatus ? <span className="text-xs text-rose-500">{billingStatus}</span> : null}
              </div>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
