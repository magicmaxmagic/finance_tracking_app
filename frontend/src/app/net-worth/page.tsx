// Net worth page
'use client'

import { useMemo, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAPI } from '@/hooks/useAPI'
import apiClient from '@/lib/api'
import { NetWorthHistoryPoint, NetWorthSummary } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'

export default function NetWorthPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const { data: summary, mutate: mutateSummary } = useAPI<NetWorthSummary>(
    user ? '/api/net-worth/summary' : null
  )
  const [snapshotStatus, setSnapshotStatus] = useState<string | null>(null)

  const dateRange = useMemo(() => {
    const end = new Date()
    const start = new Date()
    start.setMonth(start.getMonth() - 11)
    const format = (date: Date) => date.toISOString().slice(0, 10)
    return { start: format(start), end: format(end) }
  }, [])

  const { data: history, mutate: mutateHistory } = useAPI<NetWorthHistoryPoint[]>(
    user ? `/api/net-worth/history?start_date=${dateRange.start}&end_date=${dateRange.end}` : null
  )

  const breakdownEntries = summary ? Object.entries(summary.breakdown || {}) : []

  const handleCaptureSnapshot = async () => {
    setSnapshotStatus(null)
    try {
      await apiClient.post('/api/net-worth/snapshot')
      setSnapshotStatus('Snapshot captured.')
      mutateSummary()
      mutateHistory()
    } catch (err) {
      setSnapshotStatus('Unable to capture snapshot.')
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Net worth"
        subtitle="Track your balance sheet and monitor progress across assets and liabilities."
        actions={
          <button type="button" onClick={handleCaptureSnapshot} className="btn-primary">
            Capture snapshot
          </button>
        }
      >
        {snapshotStatus && (
          <div className="surface p-3 text-sm text-gray-600">{snapshotStatus}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="surface p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">Net worth overview</h3>
                  <p className="text-sm text-gray-500">Updated {summary?.date || 'today'}</p>
                </div>
                <p className="text-2xl font-semibold">{formatCurrency(summary?.net_worth || 0)}</p>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Assets</p>
                  <p className="text-lg font-semibold text-emerald-600">
                    {formatCurrency(summary?.total_assets || 0)}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Liabilities</p>
                  <p className="text-lg font-semibold text-red-600">
                    {formatCurrency(summary?.total_liabilities || 0)}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Net worth</p>
                  <p className="text-lg font-semibold">{formatCurrency(summary?.net_worth || 0)}</p>
                </div>
              </div>
            </div>

            <div className="surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Net worth history</h3>
                <span className="text-sm text-gray-500">Last 12 months</span>
              </div>
              {history && history.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      <Line type="monotone" dataKey="net_worth" stroke="#0f172a" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="surface-muted p-6 text-center text-gray-600">
                  <p className="font-semibold">No history yet.</p>
                  <p className="text-sm">Capture a snapshot to start tracking net worth over time.</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-4">Balance breakdown</h3>
              {breakdownEntries.length > 0 ? (
                <div className="space-y-3">
                  {breakdownEntries.map(([type, amount]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">{type}</span>
                      <span className="text-sm font-semibold">{formatCurrency(Number(amount))}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No accounts available.</p>
              )}
            </div>

            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Next steps</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>Capture a snapshot each month for clean trend lines.</li>
                <li>Review liabilities monthly to keep debt visible.</li>
                <li>Use the forecast view to set long-term targets.</li>
              </ul>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
