// User types
export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_email_verified: boolean
}

// Dashboard types
export interface DashboardKPI {
  monthly_expenses: number
  burn_rate: number
  current_net_worth: number
}

export interface Transaction {
  id: number
  description: string
  amount: number
  currency: string
  transaction_date: string
  category_id?: number
  account_id: number
  notes?: string | null
  tags?: string | null
}

export interface CategoryExpense {
  category_id: number
  category_name: string
  amount: number
  percentage: number
}

export interface MonthlyExpense {
  month: string
  total: number
}

export interface DashboardData {
  kpi: DashboardKPI
  expenses_by_category: CategoryExpense[]
  monthly_expenses: MonthlyExpense[]
  recent_transactions: Transaction[]
  onboarding: { key: string; label: string; completed: boolean }[]
}

// Account types
export interface Account {
  id: number
  name: string
  account_type: string
  balance: number
  currency: string
}

// Budget types
export interface Budget {
  id: number
  category_id: number
  category_name: string
  amount: number
  spent: number
  remaining: number
  percentage_used: number
  month: string
}

// Category types
export interface Category {
  id: number
  name: string
  color: string
  icon?: string
  is_income: boolean
  description?: string
}

// Net worth types
export interface NetWorthSnapshot {
  date: string
  total_assets: number
  total_liabilities: number
  net_worth: number
}

// API Response types
export interface ApiError {
  detail: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}
