// Custom hook for API data fetching
'use client'

import useSWR from 'swr'
import apiClient from '@/lib/api'

const fetcher = (url: string) => apiClient.get(url).then(res => res.data)

export const useAPI = <T,>(url: string | null) => {
  const { data, error, isLoading, mutate } = useSWR<T>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  )

  return {
    data,
    error,
    loading: isLoading,
    mutate,
  }
}
