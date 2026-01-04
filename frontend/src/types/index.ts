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
  monthly_income: number
  monthly_expenses: number
  monthly_net: number
  savings_rate: number
  burn_rate: number
  current_net_worth: number
  avg_monthly_income: number
  avg_monthly_expenses: number
  income_change_pct: number
  expense_change_pct: number
  net_change_pct: number
  time_to_goal_months?: number | null
  required_savings_rate?: number | null
  required_investment_rate?: number | null
  trajectory_deviation_score?: number | null
  decision_impact_score?: number | null
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

export interface AssetCategory {
  key: string
  label: string
  amount: number
  percentage: number
}

export interface MonthlyExpense {
  month: string
  total: number
}

export interface TopMerchant {
  name: string
  amount: number
  count: number
}

export interface DashboardData {
  kpi: DashboardKPI
  expenses_by_category: CategoryExpense[]
  assets_by_category: AssetCategory[]
  monthly_expenses: MonthlyExpense[]
  cashflow: { month: string; income: number; expenses: number; net: number }[]
  recent_transactions: Transaction[]
  onboarding: { key: string; label: string; completed: boolean }[]
  expenses_by_label: { label: string; amount: number; percentage: number }[]
  income_by_label: { label: string; amount: number; percentage: number }[]
  top_expense_merchants: TopMerchant[]
  top_income_merchants: TopMerchant[]
}

// Account types
export interface Account {
  id: number
  name: string
  account_type: string
  balance: number
  currency: string
  description?: string | null
}

// Investment asset types
export interface InvestmentAsset {
  id: number
  user_id: number
  name: string
  category: string
  current_value: number
  currency: string
  notes?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
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

export interface NetWorthSummary {
  total_assets: number
  total_liabilities: number
  net_worth: number
  breakdown: Record<string, number>
  date: string
}

export interface NetWorthHistoryPoint {
  date: string
  net_worth: number
}

export interface ForecastPoint {
  year: number
  net_worth: number
}

export interface ForecastResponse {
  start_net_worth: number
  monthly_contribution: number
  annual_return_rate: number
  average_monthly_net: number
  projection: ForecastPoint[]
}

// Strategy types
export interface FinancialGoal {
  id: number
  user_id: number
  name: string
  target_type: 'net_worth' | 'liquid_assets'
  target_value: number
  target_date: string
  status: 'active' | 'achieved' | 'archived'
  created_at: string
  updated_at: string
}

export interface AssumptionVersion {
  id: number
  user_id: number
  name: string
  version: number
  income_growth_rate: number
  expense_inflation_rate: number
  investment_return_rate: number
  volatility: number
  risk_level: 'low' | 'medium' | 'high'
  notes?: string | null
  is_active: boolean
  created_at: string
}

export interface ScheduleBlock {
  id: number
  user_id: number
  title: string
  description?: string | null
  category: string
  day_of_week: number
  start_time: string
  duration_minutes: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CalendarConnection {
  id: number
  provider: 'apple' | 'google'
  account_email: string
  calendar_name?: string | null
  is_active: boolean
  last_sync_at?: string | null
  created_at: string
  updated_at: string
}

export interface CalendarEvent {
  start: string
  end: string
  summary?: string | null
  is_all_day: boolean
}

export interface CalendarInfo {
  name: string
  url: string
}

export interface CalendarImportStatus {
  provider: 'apple' | 'google'
  source: string
  calendar_name?: string | null
  event_count: number
  last_imported_at?: string | null
}

export interface ScenarioAction {
  id?: number
  action_type: 'income_delta' | 'expense_delta' | 'investment_delta' | 'one_time_investment'
  value: number
  start_date: string
  end_date?: string | null
  created_at?: string
}

export interface Scenario {
  id: number
  user_id: number
  goal_id?: number | null
  assumption_id?: number | null
  name: string
  description?: string | null
  scenario_group_id: string
  version: number
  is_baseline: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  actions: ScenarioAction[]
}

export interface TrajectoryPoint {
  month_index: number
  date: string
  net_worth: number
  income: number
  expenses: number
  contribution: number
  return_applied: number
}

export interface SensitivityResult {
  label: string
  net_worth: number
  months_to_goal?: number | null
}

export interface TrajectoryResponse {
  start_net_worth: number
  target_value?: number | null
  target_date?: string | null
  time_to_goal_months?: number | null
  capital_gap?: number | null
  sensitivity: SensitivityResult[]
  trajectory: TrajectoryPoint[]
}

export interface ScenarioComparisonItem {
  scenario_id: number
  name: string
  months_to_goal?: number | null
  final_net_worth: number
  delta_months?: number | null
  delta_net_worth: number
}

export interface ScenarioComparisonResponse {
  baseline_scenario_id: number
  comparisons: ScenarioComparisonItem[]
}

export interface DecisionImpact {
  name: string
  action_type: string
  monthly_delta: number
  months_saved?: number | null
  efficiency_score?: number | null
}

export interface DecisionRecommendation {
  headline: string
  detail: string
}

export interface DecisionOverview {
  decision_impact_score?: number | null
  opportunities: DecisionImpact[]
  recommendations: DecisionRecommendation[]
}

export interface StrategyAlert {
  deviation_score?: number | null
  expected_net_worth?: number | null
  actual_net_worth?: number | null
  message?: string | null
}

export interface OnboardingProfile {
  id: number
  user_id: number
  risk_appetite: 'low' | 'medium' | 'high'
  investor_profile: 'conservative' | 'balanced' | 'growth' | 'active'
  goal_value: number
  goal_horizon_years: number
  target_date: string
  asset_allocation: string[]
  investment_interests: string[]
  vision?: string | null
  is_completed: boolean
  completed_at: string
  created_at: string
  updated_at: string
}

export interface UserSettings {
  id: number
  user_id: number
  currency: string
  timezone: string
  date_format: string
  start_of_week: string
  default_view: string
  data_retention: string
  digest_enabled: boolean
  transaction_alerts: boolean
  budget_alerts: boolean
  auto_categorization: boolean
  import_deduplication: boolean
  analytics_opt_in: boolean
  planning_preferences?: Record<string, unknown> | null
  calendar_feed_token?: string | null
  plan: 'starter' | 'pro'
  subscription_status?: string | null
  current_period_end?: string | null
  cancel_at_period_end?: boolean | null
  created_at: string
  updated_at: string
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
