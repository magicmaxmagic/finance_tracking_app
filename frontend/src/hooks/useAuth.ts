// Auth hook for managing authentication state
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import apiClient from '@/lib/api'
import { setTokens, clearTokens, isAuthenticated as checkAuth } from '@/lib/auth'

interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already authenticated
    if (checkAuth()) {
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await apiClient.get('/api/users/me')
      setUser(response.data)
      setError(null)
    } catch (err) {
      setUser(null)
      setError('Failed to fetch user')
    } finally {
      setLoading(false)
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
      setTokens(response.data.access_token, response.data.refresh_token)
      setUser(response.data.user)
      router.push('/dashboard')
    } catch (err) {
      setError('Invalid credentials')
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
      setTokens(response.data.access_token, response.data.refresh_token)
      setUser(response.data.user)
      router.push('/dashboard')
    } catch (err) {
      setError('Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    clearTokens()
    setUser(null)
    router.push('/login')
  }

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  }
}
