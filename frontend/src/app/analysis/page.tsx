// Forecast analysis page
'use client'

import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import apiClient from '@/lib/api'
import { ForecastResponse } from '@/types'
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

export default function AnalysisPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const [years, setYears] = useState(5)
  const [annualReturn, setAnnualReturn] = useState(5)
  const [monthlyContribution, setMonthlyContribution] = useState('')
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runForecast = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const payload: any = {
        years,
        annual_return_rate: annualReturn,
      }
      if (monthlyContribution !== '') {
        payload.monthly_contribution = parseFloat(monthlyContribution)
      }
      const response = await apiClient.post('/api/analysis/forecast', payload)
      setForecast(response.data)
    } catch (err) {
      setError('Unable to run forecast. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [annualReturn, monthlyContribution, years])

  useEffect(() => {
    if (user) {
      runForecast()
    }
  }, [runForecast, user])

  const projected = forecast?.projection?.[forecast.projection.length - 1]

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Forecast analysis"
        subtitle="Model how your net worth evolves based on contributions and expected returns."
        actions={
          <button type="button" onClick={runForecast} className="btn-primary" disabled={loading}>
            {loading ? 'Running...' : 'Run forecast'}
          </button>
        }
      >
        {error && (
          <div className="surface p-4 text-red-700 border border-red-200 bg-red-50/70">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="surface p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">Projection overview</h3>
                  <p className="text-sm text-gray-500">{years}-year outlook</p>
                </div>
                <p className="text-2xl font-semibold">
                  {projected ? formatCurrency(projected.net_worth) : '--'}
                </p>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Starting net worth</p>
                  <p className="text-lg font-semibold">
                    {forecast ? formatCurrency(forecast.start_net_worth) : '--'}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Monthly contribution</p>
                  <p className="text-lg font-semibold">
                    {forecast ? formatCurrency(forecast.monthly_contribution) : '--'}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Annual return</p>
                  <p className="text-lg font-semibold">
                    {forecast ? `${forecast.annual_return_rate.toFixed(1)}%` : '--'}
                  </p>
                </div>
              </div>
              <div className="mt-6 h-72">
                {forecast?.projection?.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={forecast.projection}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      <Line type="monotone" dataKey="net_worth" stroke="#0f172a" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-500">Run a forecast to see results.</p>
                )}
              </div>
            </div>

            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Assumptions</h3>
              <p className="text-sm text-gray-600 mb-4">
                We estimate your average monthly net cashflow from the last 6 months, unless you override it.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Average monthly net</p>
                  <p className="text-lg font-semibold">
                    {forecast ? formatCurrency(forecast.average_monthly_net) : '--'}
                  </p>
                </div>
                <div className="stat-tile">
                  <p className="text-xs uppercase text-gray-500">Forecast horizon</p>
                  <p className="text-lg font-semibold">{years} years</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Forecast controls</h3>
              <p className="text-sm text-gray-600 mb-4">Adjust assumptions and re-run the forecast.</p>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Years ahead</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={years}
                    onChange={(e) => setYears(Number(e.target.value))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Monthly contribution</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Use average net if empty"
                    value={monthlyContribution}
                    onChange={(e) => setMonthlyContribution(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Annual return rate (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={annualReturn}
                    onChange={(e) => setAnnualReturn(Number(e.target.value))}
                    className="input-field"
                  />
                </div>
                <button type="button" onClick={runForecast} className="btn-primary w-full" disabled={loading}>
                  {loading ? 'Running...' : 'Update forecast'}
                </button>
              </div>
            </div>

            <div className="surface p-6">
              <h3 className="text-lg font-semibold mb-2">Guidance</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>Use conservative return rates to avoid over-optimism.</li>
                <li>Increase monthly contributions to test faster growth paths.</li>
                <li>Re-run after big life changes to keep forecasts current.</li>
              </ul>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGate>
  )
}
