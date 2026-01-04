// Shared application shell (header + nav + hero)
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useAPI } from '@/hooks/useAPI'
import { UserSettings } from '@/types'

type AppShellProps = {
  user: { email?: string }
  onLogout: () => void
  title: string
  subtitle?: string
  actions?: React.ReactNode
  section?: 'tracking' | 'planning' | 'strategy'
  children: React.ReactNode
}

const getActiveItemHref = (items: { href: string }[], pathname: string) => {
  const matches = items.filter(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`)
  )
  if (!matches.length) return null
  return matches.sort((a, b) => b.href.length - a.href.length)[0].href
}

const navCategories = [
  {
    id: 'overview',
    label: 'Overview',
    items: [
      { href: '/dashboard', label: 'Dashboard' },
      { href: '/workspace', label: 'Workspace' },
    ],
  },
  {
    id: 'operations',
    label: 'Operations',
    items: [
      { href: '/transactions', label: 'Transactions' },
      { href: '/budgets', label: 'Budgets' },
      { href: '/accounts', label: 'Accounts' },
    ],
  },
  {
    id: 'portfolio',
    label: 'Portfolio',
    items: [
      { href: '/portfolio', label: 'Investments' },
      { href: '/net-worth', label: 'Net worth' },
    ],
  },
  {
    id: 'strategy',
    label: 'Strategy',
    items: [
      { href: '/planning', label: 'Planning' },
      { href: '/planning/goals', label: 'Goals' },
      { href: '/planning/assumptions', label: 'Assumptions' },
      { href: '/strategy/scenarios', label: 'Scenarios' },
      { href: '/strategy/decisions', label: 'Decision Lab' },
      { href: '/analysis', label: 'Forecast' },
    ],
  },
]

export function AppShell({ user, onLogout, title, subtitle, actions, section, children }: AppShellProps) {
  const pathname = usePathname()
  const { data: userSettings } = useAPI<UserSettings>(user ? '/api/settings' : null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [openCategory, setOpenCategory] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement | null>(null)
  const bannerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    setOpenCategory(null)
  }, [pathname])

  useEffect(() => {
    if (!menuOpen) return
    const handleClick = (event: MouseEvent) => {
      if (!menuRef.current) return
      if (!menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [menuOpen])

  useEffect(() => {
    if (!openCategory) return
    const handleClick = (event: MouseEvent) => {
      if (!bannerRef.current) return
      if (!bannerRef.current.contains(event.target as Node)) {
        setOpenCategory(null)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [openCategory])

  const activeCategoryId = useMemo(
    () =>
      navCategories.find((category) =>
        category.items.some((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))
      )?.id,
    [pathname]
  )
  const eyebrowLabel =
    navCategories.find((category) => category.id === activeCategoryId)?.label || 'Overview'
  const plan = userSettings?.plan ?? 'starter'
  const isPro = plan === 'pro'

  return (
    <div className="min-h-screen">
      <div className="page-shell">
        <header className="topbar">
          <div className="brand">
            <span className="brand-mark">FT</span>
            <div>
              <p className="brand-title">Finance Tracker</p>
              <p className="brand-subtitle">Wealth intelligence workspace</p>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="plan-pill">
              <span className="plan-badge">{isPro ? 'Pro' : 'Starter'}</span>
              {isPro ? (
                <Link className="btn-secondary btn-small" href="/settings">
                  Manage
                </Link>
              ) : (
                <Link className="btn-primary btn-small" href="/pricing">
                  Upgrade
                </Link>
              )}
            </div>
            <div className="user-pill">
              <span>{user.email || 'Account'}</span>
              <button className="btn-ghost" type="button" onClick={onLogout}>
                Sign out
              </button>
            </div>
            <div className="menu-wrapper" ref={menuRef}>
              <button
                className="menu-button"
                type="button"
                aria-label="Open menu"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((prev) => !prev)}
              >
                <span className="menu-line" />
                <span className="menu-line" />
                <span className="menu-line" />
              </button>
              {menuOpen ? (
                <div className="menu-panel">
                  <Link className="menu-item" href="/settings" onClick={() => setMenuOpen(false)}>
                    App settings
                  </Link>
                  <Link className="menu-item" href="/profile" onClick={() => setMenuOpen(false)}>
                    Profile
                  </Link>
                  <Link className="menu-item" href="/pricing" onClick={() => setMenuOpen(false)}>
                    Pro pricing
                  </Link>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <nav className="nav-banner" ref={bannerRef}>
          {navCategories.map((category) => {
            const isActive = activeCategoryId === category.id
            const isOpen = openCategory === category.id
            const activeItemHref = getActiveItemHref(category.items, pathname)
            return (
              <div
                key={category.id}
                className={isActive ? 'nav-category nav-category-active' : 'nav-category'}
              >
                <button
                  type="button"
                  className="nav-category-button"
                  onClick={() => setOpenCategory(isOpen ? null : category.id)}
                >
                  {category.label}
                  <span className="nav-category-caret">{isOpen ? '−' : '+'}</span>
                </button>
                {isOpen ? (
                  <div className="nav-dropdown">
                    {category.items.map((item) => {
                      const isItemActive = activeItemHref === item.href
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          className={isItemActive ? 'nav-dropdown-link nav-dropdown-active' : 'nav-dropdown-link'}
                          onClick={() => setOpenCategory(null)}
                        >
                          {item.label}
                        </Link>
                      )
                    })}
                  </div>
                ) : null}
              </div>
            )
          })}
        </nav>

        <section className="page-hero fade-up">
          <div>
            <p className="eyebrow">{eyebrowLabel}</p>
            <h1 className="page-title">{title}</h1>
            {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
          </div>
          {actions ? <div className="hero-actions">{actions}</div> : null}
        </section>

        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}
