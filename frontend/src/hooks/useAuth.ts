// Auth hook for managing authentication state
'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import apiClient from '@/lib/api'

interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_email_verified: boolean
  created_at: string
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null)
  const router = useRouter()
  const pathname = usePathname()

  const parseError = (err: unknown, fallback: string) => {
    const detail = (err as any)?.response?.data?.detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg || item?.message)
        .filter(Boolean)
        .join(', ') || fallback
    }
    if (typeof detail === 'string') {
      return detail
    }
    return fallback
  }

  useEffect(() => {
    if (pathname === '/login' || pathname === '/register') {
      setLoading(false)
      return
    }
    fetchCurrentUser()
  }, [pathname])

  const fetchCurrentUser = async () => {
    try {
      const response = await apiClient.get('/api/users/me')
      setUser(response.data)
      setError(null)
      await fetchOnboardingStatus()
    } catch (err) {
      setUser(null)
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  const resolveDefaultRoute = async () => {
    try {
      const response = await apiClient.get('/api/settings')
      const view = response.data?.default_view
      if (view === 'workspace') return '/workspace'
      if (view === 'transactions') return '/transactions'
      return '/dashboard'
    } catch {
      return '/dashboard'
    }
  }

  const fetchOnboardingStatus = async () => {
    try {
      const response = await apiClient.get('/api/onboarding/status')
      const completed = response.data?.is_completed ?? false
      setOnboardingComplete(completed)
      return completed
    } catch (err) {
      setOnboardingComplete(null)
      return null
    }
  }

  const login = async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post('/api/auth/login', {
        email,
        password,
      })
      setUser(response.data.user)
      await fetchOnboardingStatus()
      const destination = await resolveDefaultRoute()
      router.push(destination)
    } catch (err) {
      setError(parseError(err, 'Invalid credentials'))
    } finally {
      setLoading(false)
    }
  }

  const register = async (email: string, password: string, fullName?: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.post('/api/auth/register', {
        email,
        password,
        full_name: fullName,
      })
      setUser(response.data.user)
      await fetchOnboardingStatus()
      const destination = await resolveDefaultRoute()
      router.push(destination)
    } catch (err) {
      setError(parseError(err, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    apiClient.post('/api/auth/logout').catch(() => null)
    setUser(null)
    router.push('/login')
  }

  return {
    user,
    loading,
    error,
    onboardingComplete,
    refreshOnboardingStatus: fetchOnboardingStatus,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }
}
