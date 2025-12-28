// User types
export interface User {
  id: number
  email: string
  name: string
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
  category?: string
  date?: string
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
  category: string
  amount: number
  spent: number
  period: string
}

// Category types
export interface Category {
  id: number
  name: string
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
