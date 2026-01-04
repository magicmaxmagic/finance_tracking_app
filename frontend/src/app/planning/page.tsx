'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import apiClient from '@/lib/api'
import { useAPI } from '@/hooks/useAPI'
import { useAuth } from '@/hooks/useAuth'
import { AppShell } from '@/components/AppShell'
import { AuthGate } from '@/components/AuthGate'
import { CalendarConnection, CalendarEvent, CalendarImportStatus, ScheduleBlock, UserSettings } from '@/types'

type BlockFormState = {
  title: string
  description: string
  category: string
  day_of_week: string
  start_time: string
  duration_minutes: string
  is_active: boolean
}

type AppleFormState = {
  email: string
  app_password: string
  calendar_name: string
}

type OptimizationPreferences = {
  goal: string
  focusCategory: string
  workdayStart: string
  workdayEnd: string
  focusWindowStart: string
  focusWindowEnd: string
  minBreakMinutes: string
  targetFinanceHours: string
  targetRevenueHours: string
  targetSkillHours: string
  avoidDays: string[]
  moveAcrossDays: boolean
}

type ExternalEvent = CalendarEvent & {
  source: 'apple' | 'google' | 'import'
}

type EventSlot = {
  date: Date
  startMinutes: number
  endMinutes: number
  summary: string | null
  isAllDay: boolean
  source: ExternalEvent['source']
}

type SelectionRange = {
  dayIndex: number
  startMinutes: number
  endMinutes: number
}

type DragPreview = {
  blockId: number
  dayIndex: number
  startMinutes: number
}

const dayOptions = [
  { value: '0', label: 'Monday' },
  { value: '1', label: 'Tuesday' },
  { value: '2', label: 'Wednesday' },
  { value: '3', label: 'Thursday' },
  { value: '4', label: 'Friday' },
  { value: '5', label: 'Saturday' },
  { value: '6', label: 'Sunday' },
]

const CALENDAR_START_HOUR = 6
const CALENDAR_END_HOUR = 22
const HOUR_HEIGHT = 64
const MIN_BLOCK_HEIGHT = 28
const CALENDAR_START_MINUTES = CALENDAR_START_HOUR * 60
const CALENDAR_END_MINUTES = CALENDAR_END_HOUR * 60
const CALENDAR_HEIGHT = (CALENDAR_END_HOUR - CALENDAR_START_HOUR) * HOUR_HEIGHT
const EVENT_MIN_HEIGHT = 20
const CALENDAR_STEP_MINUTES = 15
const DRAFT_FORM_HEIGHT = 240

const categoryStyles: Record<string, string> = {
  FINANCE: 'bg-amber-100 border-amber-200 text-amber-900',
  REVENUE: 'bg-emerald-100 border-emerald-200 text-emerald-900',
  SKILL: 'bg-sky-100 border-sky-200 text-sky-900',
  DEFAULT: 'bg-slate-100 border-slate-200 text-slate-700',
}

const eventStyles: Record<ExternalEvent['source'], string> = {
  google: 'bg-sky-50/80 border-sky-200 text-sky-700',
  apple: 'bg-amber-50/80 border-amber-200 text-amber-700',
  import: 'bg-slate-100/80 border-slate-200 text-slate-600',
}

const defaultForm: BlockFormState = {
  title: '',
  description: '',
  category: 'FINANCE',
  day_of_week: '0',
  start_time: '08:30',
  duration_minutes: '60',
  is_active: true,
}

const defaultAppleForm: AppleFormState = {
  email: '',
  app_password: '',
  calendar_name: '',
}

const defaultPreferences: OptimizationPreferences = {
  goal: '',
  focusCategory: 'REVENUE',
  workdayStart: '08:00',
  workdayEnd: '18:00',
  focusWindowStart: '09:00',
  focusWindowEnd: '12:00',
  minBreakMinutes: '15',
  targetFinanceHours: '3',
  targetRevenueHours: '10',
  targetSkillHours: '4',
  avoidDays: [],
  moveAcrossDays: true,
}

const normalizePreferences = (
  input?: Partial<OptimizationPreferences> | null
): OptimizationPreferences => {
  const merged = { ...defaultPreferences, ...(input || {}) }
  const focusCategory = ['REVENUE', 'FINANCE', 'SKILL'].includes(merged.focusCategory)
    ? merged.focusCategory
    : defaultPreferences.focusCategory
  const normalizeNumber = (value: string | number, fallback: string) => {
    if (value === null || value === undefined || value === '') return fallback
    return String(value)
  }
  const normalizeTimeValue = (value: string, fallback: string) => (value ? value : fallback)
  const avoidDays = Array.isArray(merged.avoidDays) ? merged.avoidDays.map((day) => String(day)) : []

  return {
    goal: merged.goal || '',
    focusCategory,
    workdayStart: normalizeTimeValue(merged.workdayStart, defaultPreferences.workdayStart),
    workdayEnd: normalizeTimeValue(merged.workdayEnd, defaultPreferences.workdayEnd),
    focusWindowStart: normalizeTimeValue(merged.focusWindowStart, defaultPreferences.focusWindowStart),
    focusWindowEnd: normalizeTimeValue(merged.focusWindowEnd, defaultPreferences.focusWindowEnd),
    minBreakMinutes: normalizeNumber(merged.minBreakMinutes, defaultPreferences.minBreakMinutes),
    targetFinanceHours: normalizeNumber(merged.targetFinanceHours, defaultPreferences.targetFinanceHours),
    targetRevenueHours: normalizeNumber(merged.targetRevenueHours, defaultPreferences.targetRevenueHours),
    targetSkillHours: normalizeNumber(merged.targetSkillHours, defaultPreferences.targetSkillHours),
    avoidDays,
    moveAcrossDays:
      typeof merged.moveAcrossDays === 'boolean' ? merged.moveAcrossDays : defaultPreferences.moveAcrossDays,
  }
}

const buildPreferencesPayload = (prefs: OptimizationPreferences) => ({
  goal: prefs.goal,
  focusCategory: prefs.focusCategory,
  workdayStart: prefs.workdayStart,
  workdayEnd: prefs.workdayEnd,
  focusWindowStart: prefs.focusWindowStart,
  focusWindowEnd: prefs.focusWindowEnd,
  minBreakMinutes: Number(prefs.minBreakMinutes) || 0,
  targetFinanceHours: Number(prefs.targetFinanceHours) || 0,
  targetRevenueHours: Number(prefs.targetRevenueHours) || 0,
  targetSkillHours: Number(prefs.targetSkillHours) || 0,
  avoidDays: prefs.avoidDays,
  moveAcrossDays: prefs.moveAcrossDays,
})

const toMinutes = (timeValue: string) => {
  if (!timeValue) return 0
  const [hours, minutes] = timeValue.split(':')
  return Number(hours || 0) * 60 + Number(minutes || 0)
}

const minutesToTime = (value: number) => {
  const hours = Math.floor(value / 60)
  const minutes = Math.floor(value % 60)
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

const formatTime = (timeValue: string) => {
  if (!timeValue) return '--:--'
  const [hours, minutes] = timeValue.split(':')
  return `${String(hours || '0').padStart(2, '0')}:${String(minutes || '0').padStart(2, '0')}`
}

const formatTimeRange = (start: string, duration: number) => {
  const startLabel = formatTime(start)
  if (!duration) return startLabel
  const endMinutes = (toMinutes(start) + duration) % (24 * 60)
  const endLabel = formatTime(`${Math.floor(endMinutes / 60)}:${endMinutes % 60}`)
  return `${startLabel} - ${endLabel}`
}

const normalizeTime = (timeValue: string) => (timeValue ? timeValue.slice(0, 5) : '')

const formatHourLabel = (hour: number) => `${String(hour).padStart(2, '0')}:00`

const startOfWeek = (value: Date) => {
  const date = new Date(value)
  date.setHours(0, 0, 0, 0)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  return date
}

const addDays = (value: Date, amount: number) => {
  const date = new Date(value)
  date.setDate(date.getDate() + amount)
  return date
}

const isSameDate = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()

const formatShortDate = (value: Date) =>
  value.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

const formatWeekRange = (start: Date) => {
  const end = addDays(start, 6)
  const startLabel = formatShortDate(start)
  const endLabel = formatShortDate(end)
  const yearLabel = end.getFullYear()
  return `${startLabel} - ${endLabel}, ${yearLabel}`
}

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

const getTimedEventLayout = (slot: EventSlot) => {
  const visibleStart = Math.max(slot.startMinutes, CALENDAR_START_MINUTES)
  const visibleEnd = Math.min(slot.endMinutes, CALENDAR_END_MINUTES)
  if (visibleEnd <= CALENDAR_START_MINUTES || visibleStart >= CALENDAR_END_MINUTES) return null
  const top = ((visibleStart - CALENDAR_START_MINUTES) / 60) * HOUR_HEIGHT
  const rawHeight = ((visibleEnd - visibleStart) / 60) * HOUR_HEIGHT
  const height = Math.min(Math.max(rawHeight, EVENT_MIN_HEIGHT), CALENDAR_HEIGHT - top)
  return { top, height }
}

const normalizeDateOnly = (value: Date) =>
  new Date(value.getFullYear(), value.getMonth(), value.getDate())

const getDayIndex = (value: Date) => (value.getDay() + 6) % 7

const getEventSlotsForWeek = (events: ExternalEvent[], weekStart: Date) => {
  const slotsByDay = new Map<number, EventSlot[]>()
  for (let index = 0; index < 7; index += 1) {
    slotsByDay.set(index, [])
  }
  if (!events.length) return slotsByDay

  const weekStartDate = normalizeDateOnly(weekStart)
  const weekEndDate = addDays(weekStartDate, 7)

  const addSlot = (slot: EventSlot) => {
    const slotDate = normalizeDateOnly(slot.date)
    if (slotDate < weekStartDate || slotDate >= weekEndDate) return
    const dayIndex = getDayIndex(slotDate)
    const list = slotsByDay.get(dayIndex) || []
    list.push(slot)
    slotsByDay.set(dayIndex, list)
  }

  events.forEach((event) => {
    const start = new Date(event.start)
    const end = new Date(event.end || event.start)
    if (event.is_all_day) {
      const startDate = normalizeDateOnly(start)
      const endDate = normalizeDateOnly(end)
      const endExclusive = endDate > startDate ? endDate : addDays(startDate, 1)
      for (let current = startDate; current < endExclusive; current = addDays(current, 1)) {
        addSlot({
          date: current,
          startMinutes: 0,
          endMinutes: 24 * 60,
          summary: event.summary || null,
          isAllDay: true,
          source: event.source,
        })
      }
      return
    }

    const startDate = normalizeDateOnly(start)
    const endDate = normalizeDateOnly(end)
    const startMinutes = start.getHours() * 60 + start.getMinutes()
    const endMinutes = end.getHours() * 60 + end.getMinutes()

    if (startDate.getTime() === endDate.getTime()) {
      addSlot({
        date: startDate,
        startMinutes,
        endMinutes: Math.max(endMinutes, startMinutes),
        summary: event.summary || null,
        isAllDay: false,
        source: event.source,
      })
      return
    }

    addSlot({
      date: startDate,
      startMinutes,
      endMinutes: 24 * 60,
      summary: event.summary || null,
      isAllDay: false,
      source: event.source,
    })

    let current = addDays(startDate, 1)
    while (current < endDate) {
      addSlot({
        date: current,
        startMinutes: 0,
        endMinutes: 24 * 60,
        summary: event.summary || null,
        isAllDay: false,
        source: event.source,
      })
      current = addDays(current, 1)
    }

    addSlot({
      date: endDate,
      startMinutes: 0,
      endMinutes,
      summary: event.summary || null,
      isAllDay: false,
      source: event.source,
    })
  })

  slotsByDay.forEach((list) => {
    list.sort((a, b) => a.startMinutes - b.startMinutes)
  })

  return slotsByDay
}

const getLayoutFromMinutes = (startMinutes: number, durationMinutes: number) => {
  const endMinutes = startMinutes + durationMinutes
  const visibleStart = Math.max(startMinutes, CALENDAR_START_MINUTES)
  const visibleEnd = Math.min(endMinutes, CALENDAR_END_MINUTES)
  if (visibleEnd <= CALENDAR_START_MINUTES || visibleStart >= CALENDAR_END_MINUTES) return null
  const top = ((visibleStart - CALENDAR_START_MINUTES) / 60) * HOUR_HEIGHT
  const rawHeight = ((visibleEnd - visibleStart) / 60) * HOUR_HEIGHT
  const height = Math.min(Math.max(rawHeight, MIN_BLOCK_HEIGHT), CALENDAR_HEIGHT - top)
  return { top, height }
}

const getBlockLayout = (block: ScheduleBlock) => {
  const startMinutes = toMinutes(normalizeTime(block.start_time))
  return getLayoutFromMinutes(startMinutes, block.duration_minutes)
}

export default function PlanningPage() {
  const { user, logout, loading: authLoading } = useAuth()
  const [googleParam, setGoogleParam] = useState<string | null>(null)
  const { data: blocks, loading, error, mutate } = useAPI<ScheduleBlock[]>(
    user ? '/api/schedule/blocks' : null
  )
  const { data: appleConnection, mutate: mutateApple } = useAPI<CalendarConnection | null>(
    user ? '/api/calendar/apple' : null
  )
  const { data: googleConnection, mutate: mutateGoogle } = useAPI<CalendarConnection | null>(
    user ? '/api/calendar/google' : null
  )
  const { data: appleImportStatus, mutate: mutateAppleImport } = useAPI<CalendarImportStatus>(
    user ? '/api/calendar/apple/import/status' : null
  )
  const { data: settings, mutate: mutateSettings } = useAPI<UserSettings>(
    user ? '/api/settings' : null
  )
  const calendarGridRef = useRef<HTMLDivElement | null>(null)
  const selectionRef = useRef<SelectionRange | null>(null)
  const suppressClickRef = useRef(false)
  const dragStateRef = useRef<{ block: ScheduleBlock; offsetMinutes: number } | null>(null)
  const [selection, setSelection] = useState<SelectionRange | null>(null)
  const [dragPreview, setDragPreview] = useState<DragPreview | null>(null)
  const [draftForm, setDraftForm] = useState<BlockFormState>(defaultForm)
  const [draftDayIndex, setDraftDayIndex] = useState<number | null>(null)
  const [draftTop, setDraftTop] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<BlockFormState | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [appleForm, setAppleForm] = useState<AppleFormState>(defaultAppleForm)
  const [appleStatus, setAppleStatus] = useState<string | null>(null)
  const [appleError, setAppleError] = useState<string | null>(null)
  const [appleBusy, setAppleBusy] = useState(false)
  const [eventsBusy, setEventsBusy] = useState(false)
  const [includeDetails, setIncludeDetails] = useState(false)
  const [appleEvents, setAppleEvents] = useState<CalendarEvent[]>([])
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importBusy, setImportBusy] = useState(false)
  const [importStatus, setImportStatus] = useState<string | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [importEvents, setImportEvents] = useState<CalendarEvent[]>([])
  const [includeImportDetails, setIncludeImportDetails] = useState(false)
  const [googleStatus, setGoogleStatus] = useState<string | null>(null)
  const [googleError, setGoogleError] = useState<string | null>(null)
  const [googleBusy, setGoogleBusy] = useState(false)
  const [googleEventsBusy, setGoogleEventsBusy] = useState(false)
  const [googleEvents, setGoogleEvents] = useState<CalendarEvent[]>([])
  const [includeGoogleDetails, setIncludeGoogleDetails] = useState(false)
  const [weekStart, setWeekStart] = useState<Date>(() => startOfWeek(new Date()))
  const [preferences, setPreferences] = useState<OptimizationPreferences>(defaultPreferences)
  const [preferencesSaved, setPreferencesSaved] = useState(false)
  const [preferencesTouched, setPreferencesTouched] = useState(false)
  const [preferencesError, setPreferencesError] = useState<string | null>(null)
  const [googleAutoSynced, setGoogleAutoSynced] = useState(false)
  const [appleAutoSynced, setAppleAutoSynced] = useState(false)

  const hourLabels = useMemo(
    () =>
      Array.from(
        { length: CALENDAR_END_HOUR - CALENDAR_START_HOUR },
        (_, index) => CALENDAR_START_HOUR + index
      ),
    []
  )
  const weekLabel = useMemo(() => formatWeekRange(weekStart), [weekStart])
  const externalEvents = useMemo<ExternalEvent[]>(
    () => [
      ...appleEvents.map((event) => ({ ...event, source: 'apple' as const })),
      ...googleEvents.map((event) => ({ ...event, source: 'google' as const })),
      ...importEvents.map((event) => ({ ...event, source: 'import' as const })),
    ],
    [appleEvents, googleEvents, importEvents]
  )
  const eventSlotsByDay = useMemo(
    () => getEventSlotsForWeek(externalEvents, weekStart),
    [externalEvents, weekStart]
  )
  const draggingBlock = useMemo(() => {
    if (!dragPreview || !blocks?.length) return null
    return blocks.find((block) => block.id === dragPreview.blockId) || null
  }, [dragPreview, blocks])
  const dragLayout = useMemo(() => {
    if (!dragPreview || !draggingBlock) return null
    return getLayoutFromMinutes(dragPreview.startMinutes, draggingBlock.duration_minutes)
  }, [dragPreview, draggingBlock])

  const workdayStartMinutes = useMemo(() => {
    const raw = preferences.workdayStart || formatHourLabel(CALENDAR_START_HOUR)
    return toMinutes(raw)
  }, [preferences.workdayStart])

  const workdayEndMinutes = useMemo(() => {
    const raw = preferences.workdayEnd || formatHourLabel(CALENDAR_END_HOUR)
    return toMinutes(raw)
  }, [preferences.workdayEnd])

  const focusWindowStartMinutes = useMemo(() => {
    if (!preferences.focusWindowStart) return null
    return toMinutes(preferences.focusWindowStart)
  }, [preferences.focusWindowStart])

  const focusWindowEndMinutes = useMemo(() => {
    if (!preferences.focusWindowEnd) return null
    return toMinutes(preferences.focusWindowEnd)
  }, [preferences.focusWindowEnd])

  const minBreakMinutes = useMemo(
    () => Math.max(Number(preferences.minBreakMinutes) || 0, 0),
    [preferences.minBreakMinutes]
  )

  const groupedBlocks = useMemo(() => {
    const grouped = new Map<string, ScheduleBlock[]>()
    dayOptions.forEach((day) => grouped.set(day.value, []))
    if (blocks) {
      blocks.forEach((block) => {
        const key = String(block.day_of_week)
        const list = grouped.get(key) || []
        list.push(block)
        grouped.set(key, list)
      })
    }
    return dayOptions.map((day) => ({
      day,
      blocks: grouped.get(day.value) || [],
    }))
  }, [blocks])

  const conflictsByBlock = useMemo(() => {
    const map = new Map<number, EventSlot[]>()
    if (!blocks?.length) return map
    if (!externalEvents.length) return map
    blocks.forEach((block) => {
      const daySlots = eventSlotsByDay.get(block.day_of_week) || []
      if (!daySlots.length) return
      const blockStart = toMinutes(normalizeTime(block.start_time))
      const blockEnd = blockStart + block.duration_minutes
      const overlaps = daySlots.filter((slot) => {
        const slotStart = Math.max(0, slot.startMinutes - minBreakMinutes)
        const slotEnd = Math.min(24 * 60, slot.endMinutes + minBreakMinutes)
        return slotStart < blockEnd && slotEnd > blockStart
      })
      if (overlaps.length) {
        map.set(block.id, overlaps)
      }
    })
    return map
  }, [blocks, eventSlotsByDay, externalEvents, minBreakMinutes])

  const conflictSummaries = useMemo(() => {
    if (!blocks?.length) return []
    const workdayStart = Math.min(workdayStartMinutes, workdayEndMinutes)
    const workdayEnd = Math.max(workdayStartMinutes, workdayEndMinutes)
    const focusStart =
      focusWindowStartMinutes !== null && focusWindowEndMinutes !== null
        ? Math.min(focusWindowStartMinutes, focusWindowEndMinutes)
        : null
    const focusEnd =
      focusWindowStartMinutes !== null && focusWindowEndMinutes !== null
        ? Math.max(focusWindowStartMinutes, focusWindowEndMinutes)
        : null
    const avoidDaySet = new Set(preferences.avoidDays)
    const step = 15

    const mergeIntervals = (slots: { start: number; end: number }[]) => {
      if (!slots.length) return []
      const sorted = [...slots].sort((a, b) => a.start - b.start)
      const merged: { start: number; end: number }[] = [sorted[0]]
      for (let i = 1; i < sorted.length; i += 1) {
        const current = sorted[i]
        const last = merged[merged.length - 1]
        if (current.start <= last.end) {
          last.end = Math.max(last.end, current.end)
        } else {
          merged.push({ ...current })
        }
      }
      return merged
    }

    const isSlotFree = (busy: { start: number; end: number }[], start: number, end: number) =>
      !busy.some((slot) => slot.start < end && slot.end > start)

    const findSlotInRange = (
      busy: { start: number; end: number }[],
      rangeStart: number,
      rangeEnd: number,
      duration: number
    ) => {
      for (let time = rangeStart; time + duration <= rangeEnd; time += step) {
        if (isSlotFree(busy, time, time + duration)) {
          return time
        }
      }
      return null
    }

    const findSuggestionForDay = (dayIndex: number, block: ScheduleBlock) => {
      const busySlots: { start: number; end: number }[] = []
      const externalSlots = eventSlotsByDay.get(dayIndex) || []
      externalSlots.forEach((slot) => {
        busySlots.push({
          start: Math.max(0, slot.startMinutes - minBreakMinutes),
          end: Math.min(24 * 60, slot.endMinutes + minBreakMinutes),
        })
      })
      blocks.forEach((other) => {
        if (other.id === block.id || other.day_of_week !== dayIndex) return
        const start = toMinutes(normalizeTime(other.start_time))
        const end = start + other.duration_minutes
        busySlots.push({
          start: Math.max(0, start - minBreakMinutes),
          end: Math.min(24 * 60, end + minBreakMinutes),
        })
      })
      const mergedBusy = mergeIntervals(busySlots)

      const firstRangeStart = focusStart !== null ? Math.max(workdayStart, focusStart) : workdayStart
      const firstRangeEnd = focusEnd !== null ? Math.min(workdayEnd, focusEnd) : workdayEnd
      const duration = block.duration_minutes

      const preferredSlot =
        firstRangeEnd > firstRangeStart ? findSlotInRange(mergedBusy, firstRangeStart, firstRangeEnd, duration) : null
      if (preferredSlot !== null) return preferredSlot

      return findSlotInRange(mergedBusy, workdayStart, workdayEnd, duration)
    }

    const summaries: {
      block: ScheduleBlock
      conflicts: EventSlot[]
      suggestion: { dayIndex: number; startMinutes: number } | null
    }[] = []
    for (const [blockId, conflicts] of conflictsByBlock.entries()) {
      const block = blocks.find((item) => item.id === blockId)
      if (!block) continue

      let suggestion: { dayIndex: number; startMinutes: number } | null = null
      const dayCandidates = [block.day_of_week]
      if (preferences.moveAcrossDays) {
        for (let offset = 1; offset < 7; offset += 1) {
          const dayIndex = (block.day_of_week + offset) % 7
          dayCandidates.push(dayIndex)
        }
      }

      for (const dayIndex of dayCandidates) {
        if (avoidDaySet.has(String(dayIndex))) continue
        const slot = findSuggestionForDay(dayIndex, block)
        if (slot !== null) {
          suggestion = { dayIndex, startMinutes: slot }
          break
        }
      }

      summaries.push({ block, conflicts, suggestion })
    }

    return summaries
  }, [
    blocks,
    conflictsByBlock,
    eventSlotsByDay,
    focusWindowEndMinutes,
    focusWindowStartMinutes,
    minBreakMinutes,
    preferences.avoidDays,
    preferences.moveAcrossDays,
    workdayEndMinutes,
    workdayStartMinutes,
  ])

  useEffect(() => {
    if (!appleConnection) return
    setAppleForm((prev) => ({
      ...prev,
      email: appleConnection.account_email,
      calendar_name: appleConnection.calendar_name || '',
      app_password: '',
    }))
  }, [appleConnection])

  useEffect(() => {
    if (!appleImportStatus?.event_count) return
    fetchImportedEvents()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appleImportStatus?.event_count, includeImportDetails])

  useEffect(() => {
    if (!googleEvents.length) return
    syncGoogleEvents()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeGoogleDetails])

  useEffect(() => {
    if (!googleConnection || googleAutoSynced || googleEventsBusy) return
    syncGoogleEvents().finally(() => setGoogleAutoSynced(true))
  }, [googleConnection, googleAutoSynced, googleEventsBusy])

  useEffect(() => {
    if (!appleConnection || appleAutoSynced || eventsBusy) return
    syncAppleEvents().finally(() => setAppleAutoSynced(true))
  }, [appleConnection, appleAutoSynced, eventsBusy])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    setGoogleParam(params.get('google'))
  }, [])

  useEffect(() => {
    if (!googleParam) return
    if (googleParam === 'connected') {
      setGoogleStatus('Google Calendar connected')
      setGoogleError(null)
      mutateGoogle()
      window.setTimeout(() => setGoogleStatus(null), 2500)
      return
    }
    if (googleParam === 'error') {
      setGoogleError('Unable to connect Google Calendar')
      window.setTimeout(() => setGoogleError(null), 3000)
    }
  }, [googleParam, mutateGoogle])

  useEffect(() => {
    setDraftDayIndex(null)
    setSelection(null)
    selectionRef.current = null
    setDragPreview(null)
    dragStateRef.current = null
  }, [weekStart])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const stored = window.localStorage.getItem('planning_preferences')
    if (!stored) return
    try {
      const parsed = JSON.parse(stored) as Partial<OptimizationPreferences>
      setPreferences(normalizePreferences(parsed))
    } catch {
      window.localStorage.removeItem('planning_preferences')
    }
  }, [])

  useEffect(() => {
    if (!settings?.planning_preferences || preferencesTouched) return
    const normalized = normalizePreferences(settings.planning_preferences as Partial<OptimizationPreferences>)
    setPreferences(normalized)
  }, [settings, preferencesTouched])

  const updateDraftField = (key: keyof BlockFormState, value: string | boolean) => {
    setDraftForm((prev) => ({ ...prev, [key]: value }))
    if (key === 'day_of_week') {
      const nextIndex = Number(value)
      if (!Number.isNaN(nextIndex)) {
        setDraftDayIndex(nextIndex)
      }
    }
    if (key === 'start_time' && typeof value === 'string') {
      const minutes = toMinutes(value)
      const top = clamp(
        ((minutes - CALENDAR_START_MINUTES) / 60) * HOUR_HEIGHT,
        0,
        CALENDAR_HEIGHT - DRAFT_FORM_HEIGHT
      )
      setDraftTop(top)
    }
  }

  const updateEditField = (key: keyof BlockFormState, value: string | boolean) => {
    setEditForm((prev) => (prev ? { ...prev, [key]: value } : prev))
  }

  const resetStatus = () => {
    window.setTimeout(() => setStatus(null), 2000)
  }

  const resetError = () => {
    window.setTimeout(() => setFormError(null), 2500)
  }

  const announceStatus = (message: string) => {
    setStatus(message)
    resetStatus()
  }

  const announceError = (message: string) => {
    setFormError(message)
    resetError()
  }

  const updateAppleField = (key: keyof AppleFormState, value: string) => {
    setAppleForm((prev) => ({ ...prev, [key]: value }))
  }

  const resetAppleStatus = () => {
    window.setTimeout(() => setAppleStatus(null), 2500)
  }

  const resetAppleError = () => {
    window.setTimeout(() => setAppleError(null), 3000)
  }

  const announceAppleStatus = (message: string) => {
    setAppleStatus(message)
    resetAppleStatus()
  }

  const announceAppleError = (message: string) => {
    setAppleError(message)
    resetAppleError()
  }

  const announceImportStatus = (message: string) => {
    setImportStatus(message)
    window.setTimeout(() => setImportStatus(null), 2500)
  }

  const announceImportError = (message: string) => {
    setImportError(message)
    window.setTimeout(() => setImportError(null), 3000)
  }

  const resetGoogleStatus = () => {
    window.setTimeout(() => setGoogleStatus(null), 2500)
  }

  const resetGoogleError = () => {
    window.setTimeout(() => setGoogleError(null), 3000)
  }

  const announceGoogleStatus = (message: string) => {
    setGoogleStatus(message)
    resetGoogleStatus()
  }

  const announceGoogleError = (message: string) => {
    setGoogleError(message)
    resetGoogleError()
  }

  const goToPreviousWeek = () => {
    setWeekStart((prev) => addDays(prev, -7))
  }

  const goToNextWeek = () => {
    setWeekStart((prev) => addDays(prev, 7))
  }

  const goToCurrentWeek = () => {
    setWeekStart(startOfWeek(new Date()))
  }

  const getPointerMetrics = (clientX: number, clientY: number) => {
    const grid = calendarGridRef.current
    if (!grid) return null
    const rect = grid.getBoundingClientRect()
    const x = clamp(clientX - rect.left, 0, rect.width)
    const y = clamp(clientY - rect.top, 0, CALENDAR_HEIGHT)
    const columnWidth = rect.width / 7
    const dayIndex = Math.min(6, Math.max(0, Math.floor(x / columnWidth)))
    const minutesFromTop = (y / HOUR_HEIGHT) * 60
    const rawMinutes = clamp(
      CALENDAR_START_MINUTES + minutesFromTop,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES
    )
    const roundedMinutes = clamp(
      Math.round(rawMinutes / CALENDAR_STEP_MINUTES) * CALENDAR_STEP_MINUTES,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES
    )
    return { dayIndex, rawMinutes, roundedMinutes }
  }

  const openDraftAtMinutes = (dayIndex: number, startMinutes: number, durationMinutes?: number) => {
    const safeStart = clamp(
      startMinutes,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES - CALENDAR_STEP_MINUTES
    )
    const top = clamp(
      ((safeStart - CALENDAR_START_MINUTES) / 60) * HOUR_HEIGHT,
      0,
      CALENDAR_HEIGHT - DRAFT_FORM_HEIGHT
    )
    setDraftForm((prev) => {
      const previousDuration = Number(prev.duration_minutes)
      const fallbackDuration =
        Number.isFinite(previousDuration) && previousDuration > 0
          ? previousDuration
          : Number(defaultForm.duration_minutes)
      const resolvedDuration = durationMinutes ?? fallbackDuration
      return {
        ...prev,
        title: '',
        description: '',
        day_of_week: String(dayIndex),
        start_time: minutesToTime(safeStart),
        duration_minutes: String(Math.max(CALENDAR_STEP_MINUTES, resolvedDuration)),
      }
    })
    setDraftTop(top)
    setDraftDayIndex(dayIndex)
    setFormError(null)
  }

  const closeDraft = () => {
    setDraftDayIndex(null)
  }

  const openDraftAt = (event: React.MouseEvent<HTMLDivElement>, dayIndex: number) => {
    if (suppressClickRef.current) {
      suppressClickRef.current = false
      return
    }
    const target = event.target as HTMLElement
    if (target.closest('[data-calendar-block], [data-calendar-event], [data-calendar-draft]')) return
    const rect = event.currentTarget.getBoundingClientRect()
    const offset = clamp(event.clientY - rect.top, 0, CALENDAR_HEIGHT)
    const minutesFromStart = (offset / HOUR_HEIGHT) * 60
    const roundedMinutes =
      Math.round(minutesFromStart / CALENDAR_STEP_MINUTES) * CALENDAR_STEP_MINUTES
    const startMinutes = clamp(
      CALENDAR_START_MINUTES + roundedMinutes,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES - CALENDAR_STEP_MINUTES
    )
    openDraftAtMinutes(dayIndex, startMinutes)
  }

  const startSelection = (event: React.PointerEvent<HTMLDivElement>, dayIndex: number) => {
    if (dragStateRef.current) return
    if (event.button !== 0) return
    const target = event.target as HTMLElement
    if (target.closest('[data-calendar-block], [data-calendar-event], [data-calendar-draft]')) return
    const rect = event.currentTarget.getBoundingClientRect()
    const offset = clamp(event.clientY - rect.top, 0, CALENDAR_HEIGHT)
    const minutesFromStart = (offset / HOUR_HEIGHT) * 60
    const roundedMinutes =
      Math.round(minutesFromStart / CALENDAR_STEP_MINUTES) * CALENDAR_STEP_MINUTES
    const startMinutes = clamp(
      CALENDAR_START_MINUTES + roundedMinutes,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES
    )
    const selectionState = { dayIndex, startMinutes, endMinutes: startMinutes }
    selectionRef.current = selectionState
    suppressClickRef.current = false
    setSelection(selectionState)
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  const updateSelection = (event: React.PointerEvent<HTMLDivElement>) => {
    const current = selectionRef.current
    if (!current) return
    const rect = event.currentTarget.getBoundingClientRect()
    const offset = clamp(event.clientY - rect.top, 0, CALENDAR_HEIGHT)
    const minutesFromStart = (offset / HOUR_HEIGHT) * 60
    const roundedMinutes =
      Math.round(minutesFromStart / CALENDAR_STEP_MINUTES) * CALENDAR_STEP_MINUTES
    const endMinutes = clamp(
      CALENDAR_START_MINUTES + roundedMinutes,
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES
    )
    if (Math.abs(endMinutes - current.startMinutes) >= CALENDAR_STEP_MINUTES) {
      suppressClickRef.current = true
    }
    const updated = { ...current, endMinutes }
    selectionRef.current = updated
    setSelection(updated)
  }

  const finishSelection = () => {
    const current = selectionRef.current
    if (!current) return
    selectionRef.current = null
    setSelection(null)
    if (!suppressClickRef.current) return
    const start = Math.min(current.startMinutes, current.endMinutes)
    const end = Math.max(current.startMinutes, current.endMinutes)
    const duration = Math.max(CALENDAR_STEP_MINUTES, end - start)
    suppressClickRef.current = true
    openDraftAtMinutes(current.dayIndex, start, duration)
    window.setTimeout(() => {
      suppressClickRef.current = false
    }, 50)
  }

  const startBlockDrag = (event: React.PointerEvent<HTMLDivElement>, block: ScheduleBlock) => {
    if (event.button !== 0) return
    const metrics = getPointerMetrics(event.clientX, event.clientY)
    if (!metrics) return
    event.stopPropagation()
    suppressClickRef.current = true
    const blockStart = toMinutes(normalizeTime(block.start_time))
    dragStateRef.current = { block, offsetMinutes: metrics.rawMinutes - blockStart }
    setDragPreview({ blockId: block.id, dayIndex: block.day_of_week, startMinutes: blockStart })
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  const updateBlockDrag = (event: React.PointerEvent<HTMLDivElement>) => {
    const dragState = dragStateRef.current
    if (!dragState) return
    const metrics = getPointerMetrics(event.clientX, event.clientY)
    if (!metrics) return
    const rawStart = metrics.rawMinutes - dragState.offsetMinutes
    const roundedStart =
      Math.round(rawStart / CALENDAR_STEP_MINUTES) * CALENDAR_STEP_MINUTES
    const maxStart = Math.max(
      CALENDAR_START_MINUTES,
      CALENDAR_END_MINUTES - dragState.block.duration_minutes
    )
    const nextStart = clamp(roundedStart, CALENDAR_START_MINUTES, maxStart)
    setDragPreview({
      blockId: dragState.block.id,
      dayIndex: metrics.dayIndex,
      startMinutes: nextStart,
    })
  }

  const finishBlockDrag = async () => {
    const dragState = dragStateRef.current
    if (!dragState || !dragPreview) return
    dragStateRef.current = null
    const { block } = dragState
    const nextDay = dragPreview.dayIndex
    const nextStart = dragPreview.startMinutes
    setDragPreview(null)
    suppressClickRef.current = true
    const currentStart = toMinutes(normalizeTime(block.start_time))
    if (block.day_of_week === nextDay && currentStart === nextStart) {
      window.setTimeout(() => {
        suppressClickRef.current = false
      }, 50)
      return
    }
    setBusyId(block.id)
    setFormError(null)
    try {
      await apiClient.put(`/api/schedule/blocks/${block.id}`, {
        day_of_week: nextDay,
        start_time: minutesToTime(nextStart),
      })
      await mutate()
      announceStatus('Block moved')
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to move block')
    } finally {
      setBusyId(null)
    }
    window.setTimeout(() => {
      suppressClickRef.current = false
    }, 50)
  }

  const updatePreferenceField = <K extends keyof OptimizationPreferences>(
    key: K,
    value: OptimizationPreferences[K]
  ) => {
    setPreferences((prev) => ({ ...prev, [key]: value }))
    setPreferencesSaved(false)
    setPreferencesTouched(true)
  }

  const toggleAvoidDay = (dayValue: string) => {
    setPreferences((prev) => {
      const exists = prev.avoidDays.includes(dayValue)
      const next = exists
        ? prev.avoidDays.filter((value) => value !== dayValue)
        : [...prev.avoidDays, dayValue]
      return { ...prev, avoidDays: next }
    })
    setPreferencesSaved(false)
    setPreferencesTouched(true)
  }

  const savePreferences = async () => {
    if (typeof window === 'undefined') return
    setPreferencesError(null)
    try {
      const payload = buildPreferencesPayload(preferences)
      await apiClient.put('/api/settings', { planning_preferences: payload })
      await mutateSettings()
      window.localStorage.setItem('planning_preferences', JSON.stringify(payload))
      setPreferencesSaved(true)
      window.setTimeout(() => setPreferencesSaved(false), 2500)
    } catch (err: any) {
      setPreferencesError(err?.response?.data?.detail || 'Unable to save preferences')
    }
  }

  const applySuggestedMove = async (
    block: ScheduleBlock,
    suggestion: { dayIndex: number; startMinutes: number } | null
  ) => {
    if (!suggestion) return
    setBusyId(block.id)
    setFormError(null)
    try {
      await apiClient.put(`/api/schedule/blocks/${block.id}`, {
        day_of_week: suggestion.dayIndex,
        start_time: minutesToTime(suggestion.startMinutes),
      })
      await mutate()
      announceStatus('Block rescheduled')
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to apply recommendation')
    } finally {
      setBusyId(null)
    }
  }

  const connectAppleCalendar = async () => {
    setAppleBusy(true)
    setAppleError(null)
    try {
      await apiClient.post('/api/calendar/apple/connect', {
        email: appleForm.email,
        app_password: appleForm.app_password,
        calendar_name: appleForm.calendar_name || null,
      })
      await mutateApple()
      setAppleForm((prev) => ({ ...prev, app_password: '' }))
      announceAppleStatus('Apple Calendar connected')
    } catch (err: any) {
      announceAppleError(err?.response?.data?.detail || 'Unable to connect Apple Calendar')
    } finally {
      setAppleBusy(false)
    }
  }

  const disconnectAppleCalendar = async () => {
    setAppleBusy(true)
    setAppleError(null)
    try {
      await apiClient.delete('/api/calendar/apple')
      await mutateApple()
      setAppleEvents([])
      announceAppleStatus('Apple Calendar disconnected')
    } catch (err: any) {
      announceAppleError(err?.response?.data?.detail || 'Unable to disconnect Apple Calendar')
    } finally {
      setAppleBusy(false)
    }
  }

  const connectGoogleCalendar = async () => {
    setGoogleBusy(true)
    setGoogleError(null)
    try {
      const response = await apiClient.get('/api/calendar/google/auth-url')
      const authUrl = response.data?.url
      if (!authUrl) {
        throw new Error('Missing authorization URL')
      }
      window.location.href = authUrl
    } catch (err: any) {
      announceGoogleError(err?.response?.data?.detail || 'Unable to connect Google Calendar')
    } finally {
      setGoogleBusy(false)
    }
  }

  const disconnectGoogleCalendar = async () => {
    setGoogleBusy(true)
    setGoogleError(null)
    try {
      await apiClient.delete('/api/calendar/google')
      await mutateGoogle()
      setGoogleEvents([])
      announceGoogleStatus('Google Calendar disconnected')
    } catch (err: any) {
      announceGoogleError(err?.response?.data?.detail || 'Unable to disconnect Google Calendar')
    } finally {
      setGoogleBusy(false)
    }
  }

  const syncGoogleEvents = async () => {
    setGoogleEventsBusy(true)
    setGoogleError(null)
    try {
      const response = await apiClient.get('/api/calendar/google/events', {
        params: {
          include_details: includeGoogleDetails,
        },
      })
      setGoogleEvents(response.data || [])
      await mutateGoogle()
      announceGoogleStatus('Events synced')
    } catch (err: any) {
      announceGoogleError(err?.response?.data?.detail || 'Unable to sync Google events')
    } finally {
      setGoogleEventsBusy(false)
    }
  }

  const syncAppleEvents = async () => {
    setEventsBusy(true)
    setAppleError(null)
    try {
      const response = await apiClient.get('/api/calendar/apple/events', {
        params: {
          include_details: includeDetails,
        },
      })
      setAppleEvents(response.data || [])
      announceAppleStatus('Events synced')
    } catch (err: any) {
      announceAppleError(err?.response?.data?.detail || 'Unable to sync Apple events')
    } finally {
      setEventsBusy(false)
    }
  }

  const importAppleCalendar = async () => {
    if (!importFile) {
      announceImportError('Select an .ics file first')
      return
    }
    setImportBusy(true)
    setImportError(null)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      await apiClient.post('/api/calendar/apple/import', formData)
      setImportFile(null)
      await mutateAppleImport()
      await fetchImportedEvents()
      announceImportStatus('Import completed')
    } catch (err: any) {
      announceImportError(err?.response?.data?.detail || 'Unable to import calendar')
    } finally {
      setImportBusy(false)
    }
  }

  const fetchImportedEvents = async () => {
    setImportBusy(true)
    setImportError(null)
    try {
      const response = await apiClient.get('/api/calendar/apple/import/events', {
        params: { include_details: includeImportDetails },
      })
      setImportEvents(response.data || [])
    } catch (err: any) {
      announceImportError(err?.response?.data?.detail || 'Unable to load imported events')
    } finally {
      setImportBusy(false)
    }
  }

  const clearImportedEvents = async () => {
    setImportBusy(true)
    setImportError(null)
    try {
      await apiClient.delete('/api/calendar/apple/import')
      await mutateAppleImport()
      setImportEvents([])
      announceImportStatus('Imported events cleared')
    } catch (err: any) {
      announceImportError(err?.response?.data?.detail || 'Unable to clear imported events')
    } finally {
      setImportBusy(false)
    }
  }

  const createDraftBlock = async (event?: React.FormEvent) => {
    event?.preventDefault()
    setSubmitting(true)
    setFormError(null)
    try {
      await apiClient.post('/api/schedule/blocks', {
        title: draftForm.title.trim(),
        description: draftForm.description.trim() || null,
        category: draftForm.category.trim(),
        day_of_week: Number(draftForm.day_of_week),
        start_time: draftForm.start_time,
        duration_minutes: Number(draftForm.duration_minutes),
        is_active: draftForm.is_active,
      })
      setDraftForm((prev) => ({
        ...defaultForm,
        category: prev.category,
        duration_minutes: prev.duration_minutes,
      }))
      setDraftDayIndex(null)
      await mutate()
      announceStatus('Block added')
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to create block')
    } finally {
      setSubmitting(false)
    }
  }

  const startEdit = (block: ScheduleBlock) => {
    setEditingId(block.id)
    setEditForm({
      title: block.title,
      description: block.description || '',
      category: block.category,
      day_of_week: String(block.day_of_week),
      start_time: normalizeTime(block.start_time),
      duration_minutes: String(block.duration_minutes),
      is_active: block.is_active,
    })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditForm(null)
  }

  const handleUpdate = async (blockId: number) => {
    if (!editForm) return
    setBusyId(blockId)
    setFormError(null)
    try {
      await apiClient.put(`/api/schedule/blocks/${blockId}`, {
        title: editForm.title.trim(),
        description: editForm.description.trim() || null,
        category: editForm.category.trim(),
        day_of_week: Number(editForm.day_of_week),
        start_time: editForm.start_time,
        duration_minutes: Number(editForm.duration_minutes),
        is_active: editForm.is_active,
      })
      await mutate()
      announceStatus('Block updated')
      cancelEdit()
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to update block')
    } finally {
      setBusyId(null)
    }
  }

  const toggleActive = async (block: ScheduleBlock) => {
    setBusyId(block.id)
    setFormError(null)
    try {
      await apiClient.put(`/api/schedule/blocks/${block.id}`, {
        is_active: !block.is_active,
      })
      await mutate()
      announceStatus(block.is_active ? 'Block paused' : 'Block activated')
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to update block')
    } finally {
      setBusyId(null)
    }
  }

  const deleteBlock = async (blockId: number) => {
    const confirmed = window.confirm('Delete this schedule block?')
    if (!confirmed) return
    setBusyId(blockId)
    setFormError(null)
    try {
      await apiClient.delete(`/api/schedule/blocks/${blockId}`)
      await mutate()
      announceStatus('Block deleted')
    } catch (err: any) {
      announceError(err?.response?.data?.detail || 'Unable to delete block')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <AuthGate loading={authLoading} user={user}>
      <AppShell
        user={user!}
        onLogout={logout}
        title="Planning"
        subtitle="Plan your week at a glance."
      >
        <div className="space-y-6">
          <div className="surface p-6">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
                <div>
                  <h2 className="text-lg font-semibold">Calendar</h2>
                  <p className="text-sm text-gray-600">Weekly view of your schedule.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button className="btn-secondary btn-small" type="button" onClick={goToPreviousWeek}>
                    Prev
                  </button>
                  <button className="btn-secondary btn-small" type="button" onClick={goToCurrentWeek}>
                    Today
                  </button>
                  <button className="btn-secondary btn-small" type="button" onClick={goToNextWeek}>
                    Next
                  </button>
                  <span className="text-xs text-gray-500">
                    {weekLabel} · {formatHourLabel(CALENDAR_START_HOUR)} - {formatHourLabel(CALENDAR_END_HOUR)}
                  </span>
                  {status ? <span className="text-xs text-emerald-600">{status}</span> : null}
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Click or drag to add. Drag blocks to move.
              </p>

              <div className="overflow-x-auto">
                <div className="min-w-[960px]">
                  <div className="grid grid-cols-[80px_repeat(7,minmax(0,1fr))] text-xs text-gray-500">
                    <div />
                    {dayOptions.map((day, index) => {
                      const date = addDays(weekStart, index)
                      const isToday = isSameDate(date, new Date())
                      return (
                        <div
                          key={day.value}
                          className={`px-2 py-2 font-semibold ${isToday ? 'text-emerald-700' : 'text-gray-600'}`}
                        >
                          <div>{day.label}</div>
                          <div className="text-[11px] text-gray-400">{formatShortDate(date)}</div>
                        </div>
                      )
                    })}
                  </div>

                  <div className="mt-3 flex">
                    <div className="w-20 pr-2 text-right text-xs text-gray-400">
                      {hourLabels.map((hour) => (
                        <div
                          key={hour}
                          className="flex items-start justify-end"
                          style={{ height: HOUR_HEIGHT }}
                        >
                          <span className="relative -top-2">{formatHourLabel(hour)}</span>
                        </div>
                      ))}
                    </div>
                    <div className="relative flex-1">
                      <div
                        className="absolute inset-0 pointer-events-none"
                        style={{
                          backgroundImage:
                            'linear-gradient(to bottom, rgba(148, 163, 184, 0.35) 1px, transparent 1px)',
                          backgroundSize: `100% ${HOUR_HEIGHT}px`,
                        }}
                      />
                      <div
                        ref={calendarGridRef}
                        className="grid grid-cols-7 relative z-10 select-none"
                        style={{ height: CALENDAR_HEIGHT, touchAction: 'none' }}
                      >
                        {groupedBlocks.map(({ day, blocks: dayBlocks }, index) => (
                          <div
                            key={day.value}
                            className={`relative ${
                              index === 0 ? '' : 'border-l border-slate-200/70'
                            } cursor-crosshair`}
                            onPointerDown={(event) => startSelection(event, index)}
                            onPointerMove={updateSelection}
                            onPointerUp={finishSelection}
                            onPointerCancel={finishSelection}
                            onClick={(event) => openDraftAt(event, index)}
                          >
                            {(() => {
                              const daySlots = eventSlotsByDay.get(index) || []
                              if (!daySlots.length) return null
                              const allDaySlots = daySlots.filter((slot) => slot.isAllDay)
                              const timedSlots = daySlots.filter((slot) => !slot.isAllDay)
                              return (
                                <>
                                  {allDaySlots.map((slot, slotIndex) => (
                                    <div
                                      key={`all-day-${slotIndex}`}
                                      data-calendar-event
                                      className={`absolute left-2 right-2 rounded-md border px-2 py-0.5 text-[10px] ${eventStyles[slot.source]} opacity-80`}
                                      style={{ top: 4 + slotIndex * 18, height: 16 }}
                                    >
                                      <div className="flex items-center justify-between gap-2">
                                        <span className="truncate">{slot.summary || 'Client busy'}</span>
                                        <span className="text-[9px] uppercase tracking-wide">All day</span>
                                      </div>
                                    </div>
                                  ))}
                                  {timedSlots.map((slot, slotIndex) => {
                                    const layout = getTimedEventLayout(slot)
                                    if (!layout) return null
                                    const timeLabel = `${minutesToTime(slot.startMinutes)}-${minutesToTime(
                                      slot.endMinutes
                                    )}`
                                    return (
                                      <div
                                        key={`timed-${slotIndex}`}
                                        data-calendar-event
                                        className={`absolute left-2 right-2 rounded-lg border px-2 py-1 text-[10px] ${eventStyles[slot.source]} opacity-80`}
                                        style={{ top: layout.top, height: layout.height }}
                                      >
                                        <div className="flex items-center justify-between gap-2">
                                          <span className="font-semibold truncate">
                                            {slot.summary || 'Client busy'}
                                          </span>
                                          <span className="text-[9px] uppercase tracking-wide">
                                            {slot.source}
                                          </span>
                                        </div>
                                        <p className="text-[9px] text-gray-600">{timeLabel}</p>
                                      </div>
                                    )
                                  })}
                                </>
                              )
                            })()}
                            {selection && selection.dayIndex === index ? (
                              (() => {
                                const start = Math.min(selection.startMinutes, selection.endMinutes)
                                const end = Math.max(selection.startMinutes, selection.endMinutes)
                                const layout = getLayoutFromMinutes(start, Math.max(end - start, CALENDAR_STEP_MINUTES))
                                if (!layout) return null
                                return (
                                  <div
                                    data-calendar-selection
                                    className="absolute left-2 right-2 rounded-lg border border-dashed border-emerald-400/70 bg-emerald-100/40 pointer-events-none"
                                    style={{ top: layout.top, height: layout.height }}
                                  />
                                )
                              })()
                            ) : null}
                            {dragPreview && dragPreview.dayIndex === index && draggingBlock && dragLayout ? (
                              <div
                                data-calendar-block
                                className={`absolute left-2 right-2 rounded-xl border border-dashed px-2 py-1 text-[11px] shadow-sm opacity-80 pointer-events-none ${categoryStyles[draggingBlock.category?.toUpperCase() || 'DEFAULT']}`}
                                style={{ top: dragLayout.top, height: dragLayout.height }}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-semibold truncate">{draggingBlock.title}</span>
                                  <span className="text-[10px] uppercase tracking-wide">{draggingBlock.category}</span>
                                </div>
                                <p className="text-[10px] text-gray-600">
                                  {formatTimeRange(
                                    minutesToTime(dragPreview.startMinutes),
                                    draggingBlock.duration_minutes
                                  )}
                                </p>
                              </div>
                            ) : null}
                            {draftDayIndex === index ? (
                              <div
                                data-calendar-draft
                                className="absolute left-2 right-2 z-20 surface p-3 text-sm shadow-xl"
                                style={{ top: draftTop }}
                                onClick={(event) => event.stopPropagation()}
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <p className="text-xs uppercase tracking-widest text-gray-400">New block</p>
                                  <button
                                    className="text-xs text-gray-500 hover:text-gray-700"
                                    type="button"
                                    onClick={closeDraft}
                                  >
                                    Close
                                  </button>
                                </div>
                                <form className="grid gap-2" onSubmit={createDraftBlock}>
                                  <input
                                    className="input-field"
                                    placeholder="Block title"
                                    value={draftForm.title}
                                    onChange={(event) => updateDraftField('title', event.target.value)}
                                    required
                                  />
                                  <select
                                    className="select-field"
                                    value={draftForm.category}
                                    onChange={(event) => updateDraftField('category', event.target.value)}
                                  >
                                    <option value="FINANCE">FINANCE</option>
                                    <option value="REVENUE">REVENUE</option>
                                    <option value="SKILL">SKILL</option>
                                  </select>
                                  <div className="grid grid-cols-2 gap-2">
                                    <select
                                      className="select-field"
                                      value={draftForm.day_of_week}
                                      onChange={(event) => updateDraftField('day_of_week', event.target.value)}
                                    >
                                      {dayOptions.map((option) => (
                                        <option key={option.value} value={option.value}>
                                          {option.label}
                                        </option>
                                      ))}
                                    </select>
                                    <input
                                      className="input-field"
                                      type="time"
                                      step={900}
                                      value={draftForm.start_time}
                                      onChange={(event) => updateDraftField('start_time', event.target.value)}
                                      required
                                    />
                                  </div>
                                  <div className="grid grid-cols-2 gap-2">
                                    <input
                                      className="input-field"
                                      type="number"
                                      min={15}
                                      step={15}
                                      value={draftForm.duration_minutes}
                                      onChange={(event) =>
                                        updateDraftField('duration_minutes', event.target.value)
                                      }
                                      required
                                    />
                                    <label className="toggle">
                                      <input
                                        type="checkbox"
                                        checked={draftForm.is_active}
                                        onChange={(event) =>
                                          updateDraftField('is_active', event.target.checked)
                                        }
                                      />
                                      <span className="toggle-track">
                                        <span className="toggle-thumb" />
                                      </span>
                                      Active
                                    </label>
                                  </div>
                                  <textarea
                                    className="input-field"
                                    placeholder="Description (optional)"
                                    value={draftForm.description}
                                    onChange={(event) => updateDraftField('description', event.target.value)}
                                  />
                                  <div className="flex items-center gap-2">
                                    <button className="btn-primary btn-small" type="submit" disabled={submitting}>
                                      {submitting ? 'Saving...' : 'Add block'}
                                    </button>
                                    <button className="btn-secondary btn-small" type="button" onClick={closeDraft}>
                                      Cancel
                                    </button>
                                  </div>
                                  {formError ? (
                                    <p className="text-xs text-red-600">{formError}</p>
                                  ) : null}
                                </form>
                              </div>
                            ) : null}
                            {dayBlocks.map((block) => {
                              if (dragPreview?.blockId === block.id) return null
                              const layout = getBlockLayout(block)
                              if (!layout) return null
                              const toneKey = block.category?.toUpperCase() || 'DEFAULT'
                              const toneClass = categoryStyles[toneKey] || categoryStyles.DEFAULT
                              const conflictCount = conflictsByBlock.get(block.id)?.length || 0
                              const hasConflict = conflictCount > 0
                              return (
                                <div
                                  key={block.id}
                                  data-calendar-block
                                  className={`absolute left-2 right-2 rounded-xl border px-2 py-1 text-[11px] shadow-sm ${toneClass} cursor-grab active:cursor-grabbing ${
                                    block.is_active ? '' : 'opacity-60'
                                  } ${hasConflict ? 'ring-2 ring-rose-400/70' : ''}`}
                                  style={{ top: layout.top, height: layout.height }}
                                  title={
                                    hasConflict
                                      ? `Conflicts with ${conflictCount} client events`
                                      : `${block.title} · ${block.category}`
                                  }
                                  onPointerDown={(event) => startBlockDrag(event, block)}
                                  onPointerMove={updateBlockDrag}
                                  onPointerUp={finishBlockDrag}
                                  onPointerCancel={finishBlockDrag}
                                  onClick={(event) => event.stopPropagation()}
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <span className="font-semibold truncate">{block.title}</span>
                                    <div className="flex items-center gap-2">
                                      {hasConflict ? (
                                        <span className="text-[10px] font-semibold text-rose-600">Conflict</span>
                                      ) : null}
                                      <span className="text-[10px] uppercase tracking-wide">{block.category}</span>
                                    </div>
                                  </div>
                                  <p className="text-[10px] text-gray-600">
                                    {formatTimeRange(normalizeTime(block.start_time), block.duration_minutes)}
                                  </p>
                                  {layout.height > 60 && block.description ? (
                                    <p className="text-[10px] text-gray-600 truncate">{block.description}</p>
                                  ) : null}
                                </div>
                              )
                            })}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {loading ? (
                <p className="text-sm text-gray-500 mt-4">Loading calendar...</p>
              ) : !blocks?.length ? (
                <p className="text-sm text-gray-500 mt-4">No blocks scheduled yet.</p>
              ) : null}
            </div>
          <details className="surface p-6">
            <summary className="flex items-center justify-between cursor-pointer list-none">
              <span className="text-lg font-semibold">Recommendations</span>
              <span className="text-xs text-gray-500">{conflictSummaries.length} conflicts</span>
            </summary>
            <div className="mt-4 space-y-4">
              <p className="text-sm text-gray-600">Client agenda always has priority.</p>
              {!externalEvents.length ? (
                <p className="text-xs text-gray-500">Sync a calendar to detect conflicts.</p>
              ) : conflictSummaries.length === 0 ? (
                <p className="text-xs text-gray-500">No conflicts found this week.</p>
              ) : (
                <div className="space-y-3">
                  {conflictSummaries.map(({ block, conflicts, suggestion }) => {
                    const date = addDays(weekStart, block.day_of_week)
                    const baseLabel = `${dayOptions[block.day_of_week].label} · ${formatShortDate(date)}`
                    const suggestionLabel = suggestion
                      ? `${dayOptions[suggestion.dayIndex].label} ${formatShortDate(
                          addDays(weekStart, suggestion.dayIndex)
                        )} at ${minutesToTime(suggestion.startMinutes)}`
                      : 'No open slot within work hours'
                    return (
                      <div key={block.id} className="surface p-3 text-sm space-y-1">
                        <p className="text-xs text-gray-500">
                          {baseLabel} · {formatTimeRange(normalizeTime(block.start_time), block.duration_minutes)}
                        </p>
                        <p className="font-semibold text-gray-800">{block.title}</p>
                        <p className="text-xs text-rose-600">
                          Conflicts with {conflicts.length} client events.
                        </p>
                        <p className="text-xs text-gray-600">Suggested move: {suggestionLabel}</p>
                        {suggestion ? (
                          <button
                            className="btn-secondary btn-small mt-2"
                            type="button"
                            onClick={() => applySuggestedMove(block, suggestion)}
                            disabled={busyId === block.id}
                          >
                            {busyId === block.id ? 'Applying...' : 'Apply suggestion'}
                          </button>
                        ) : null}
                      </div>
                    )
                  })}
                </div>
              )}

              <details className="surface-muted p-4">
                <summary className="flex items-center justify-between cursor-pointer list-none">
                  <span className="text-xs uppercase tracking-widest text-gray-400">Preferences</span>
                  {preferencesSaved ? <span className="text-xs text-emerald-600">Saved</span> : null}
                </summary>
                <div className="mt-4 grid gap-3">
                  <textarea
                    className="input-field"
                    placeholder="Top goals this week"
                    value={preferences.goal}
                    onChange={(event) => updatePreferenceField('goal', event.target.value)}
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <select
                      className="select-field"
                      value={preferences.focusCategory}
                      onChange={(event) => updatePreferenceField('focusCategory', event.target.value)}
                    >
                      <option value="REVENUE">Revenue focus</option>
                      <option value="FINANCE">Finance focus</option>
                      <option value="SKILL">Skill focus</option>
                    </select>
                    <input
                      className="input-field"
                      type="number"
                      min={0}
                      step={5}
                      value={preferences.minBreakMinutes}
                      onChange={(event) => updatePreferenceField('minBreakMinutes', event.target.value)}
                      placeholder="Min break (minutes)"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      className="input-field"
                      type="time"
                      value={preferences.workdayStart}
                      onChange={(event) => updatePreferenceField('workdayStart', event.target.value)}
                    />
                    <input
                      className="input-field"
                      type="time"
                      value={preferences.workdayEnd}
                      onChange={(event) => updatePreferenceField('workdayEnd', event.target.value)}
                    />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-widest text-gray-400 mb-2">Avoid days</p>
                    <div className="flex flex-wrap gap-2">
                      {dayOptions.map((day) => {
                        const isActive = preferences.avoidDays.includes(day.value)
                        return (
                          <button
                            key={day.value}
                            type="button"
                            className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                              isActive
                                ? 'bg-rose-100 text-rose-700 border-rose-200'
                                : 'bg-white text-gray-600 border-gray-200'
                            }`}
                            onClick={() => toggleAvoidDay(day.value)}
                          >
                            {day.label.slice(0, 3)}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={preferences.moveAcrossDays}
                      onChange={(event) => updatePreferenceField('moveAcrossDays', event.target.checked)}
                    />
                    <span className="toggle-track">
                      <span className="toggle-thumb" />
                    </span>
                    Allow moving blocks to other days
                  </label>

                  <details className="surface-muted p-3">
                    <summary className="text-xs uppercase tracking-widest text-gray-400 cursor-pointer list-none">
                      Advanced
                    </summary>
                    <div className="mt-3 grid gap-3">
                      <div className="grid grid-cols-2 gap-3">
                        <input
                          className="input-field"
                          type="time"
                          value={preferences.focusWindowStart}
                          onChange={(event) =>
                            updatePreferenceField('focusWindowStart', event.target.value)
                          }
                          placeholder="Focus start"
                        />
                        <input
                          className="input-field"
                          type="time"
                          value={preferences.focusWindowEnd}
                          onChange={(event) =>
                            updatePreferenceField('focusWindowEnd', event.target.value)
                          }
                          placeholder="Focus end"
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <input
                          className="input-field"
                          type="number"
                          min={0}
                          step={0.5}
                          value={preferences.targetFinanceHours}
                          onChange={(event) =>
                            updatePreferenceField('targetFinanceHours', event.target.value)
                          }
                          placeholder="Finance hrs"
                        />
                        <input
                          className="input-field"
                          type="number"
                          min={0}
                          step={0.5}
                          value={preferences.targetRevenueHours}
                          onChange={(event) =>
                            updatePreferenceField('targetRevenueHours', event.target.value)
                          }
                          placeholder="Revenue hrs"
                        />
                        <input
                          className="input-field"
                          type="number"
                          min={0}
                          step={0.5}
                          value={preferences.targetSkillHours}
                          onChange={(event) =>
                            updatePreferenceField('targetSkillHours', event.target.value)
                          }
                          placeholder="Skill hrs"
                        />
                      </div>
                    </div>
                  </details>

                  <div className="flex items-center gap-3">
                    <button className="btn-secondary btn-small" type="button" onClick={savePreferences}>
                      Save preferences
                    </button>
                    {preferencesError ? <span className="text-xs text-red-600">{preferencesError}</span> : null}
                  </div>
                  <p className="text-xs text-gray-500">Client agenda is treated as non-movable.</p>
                </div>
              </details>
            </div>
          </details>

          <details className="surface p-6">
            <summary className="flex items-center justify-between cursor-pointer list-none">
              <span className="text-lg font-semibold">Calendar connections</span>
              <span className="text-xs text-gray-500">
                Google: {googleConnection ? 'connected' : 'not connected'} · Apple:{' '}
                {appleConnection ? 'connected' : 'not connected'}
              </span>
            </summary>

            <div className="mt-4 space-y-4">
              <div className="surface-muted p-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-gray-400">Google</p>
                    <p className="text-sm text-gray-600">Read-only OAuth.</p>
                  </div>
                  {googleStatus ? <span className="text-xs text-emerald-600">{googleStatus}</span> : null}
                </div>

                {googleConnection ? (
                  <div className="space-y-3">
                    <div className="text-sm text-gray-700 space-y-1">
                      <p className="font-semibold">{googleConnection.account_email}</p>
                      {googleConnection.last_sync_at ? (
                        <p className="text-xs text-gray-500">
                          Last sync: {new Date(googleConnection.last_sync_at).toLocaleString('en-US')}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        className="btn-secondary btn-small"
                        type="button"
                        onClick={syncGoogleEvents}
                        disabled={googleEventsBusy}
                      >
                        {googleEventsBusy ? 'Syncing...' : 'Sync events'}
                      </button>
                      <button
                        className="btn-secondary btn-small"
                        type="button"
                        onClick={disconnectGoogleCalendar}
                        disabled={googleBusy}
                      >
                        {googleBusy ? 'Disconnecting...' : 'Disconnect'}
                      </button>
                      <label className="toggle">
                        <input
                          type="checkbox"
                          checked={includeGoogleDetails}
                          onChange={(event) => setIncludeGoogleDetails(event.target.checked)}
                        />
                        <span className="toggle-track">
                          <span className="toggle-thumb" />
                        </span>
                        Show titles on calendar
                      </label>
                      {googleError ? <span className="text-xs text-red-600">{googleError}</span> : null}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      className="btn-primary btn-small"
                      type="button"
                      onClick={connectGoogleCalendar}
                      disabled={googleBusy}
                    >
                      {googleBusy ? 'Connecting...' : 'Connect Google'}
                    </button>
                    {googleError ? <span className="text-xs text-red-600">{googleError}</span> : null}
                  </div>
                )}
              </div>

              <div className="surface-muted p-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-gray-400">Apple iCloud</p>
                    <p className="text-sm text-gray-600">App password sync.</p>
                  </div>
                  {appleStatus ? <span className="text-xs text-emerald-600">{appleStatus}</span> : null}
                </div>

                {appleConnection ? (
                  <div className="space-y-3">
                    <div className="text-sm text-gray-700 space-y-1">
                      <p className="font-semibold">{appleConnection.account_email}</p>
                      {appleConnection.last_sync_at ? (
                        <p className="text-xs text-gray-500">
                          Last sync: {new Date(appleConnection.last_sync_at).toLocaleString('en-US')}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        className="btn-secondary btn-small"
                        type="button"
                        onClick={syncAppleEvents}
                        disabled={eventsBusy}
                      >
                        {eventsBusy ? 'Syncing...' : 'Sync events'}
                      </button>
                      <button
                        className="btn-secondary btn-small"
                        type="button"
                        onClick={disconnectAppleCalendar}
                        disabled={appleBusy}
                      >
                        {appleBusy ? 'Disconnecting...' : 'Disconnect'}
                      </button>
                      <label className="toggle">
                        <input
                          type="checkbox"
                          checked={includeDetails}
                          onChange={(event) => setIncludeDetails(event.target.checked)}
                        />
                        <span className="toggle-track">
                          <span className="toggle-thumb" />
                        </span>
                        Show titles on calendar
                      </label>
                      {appleError ? <span className="text-xs text-red-600">{appleError}</span> : null}
                    </div>
                  </div>
                ) : (
                  <form
                    className="grid grid-cols-1 gap-3"
                    onSubmit={(event) => {
                      event.preventDefault()
                      connectAppleCalendar()
                    }}
                  >
                    <input
                      className="input-field"
                      type="email"
                      placeholder="Apple ID email"
                      value={appleForm.email}
                      onChange={(event) => updateAppleField('email', event.target.value)}
                      required
                    />
                    <input
                      className="input-field"
                      type="password"
                      placeholder="App-specific password"
                      value={appleForm.app_password}
                      onChange={(event) => updateAppleField('app_password', event.target.value)}
                      required
                    />
                    <input
                      className="input-field"
                      placeholder="Calendar name (optional)"
                      value={appleForm.calendar_name}
                      onChange={(event) => updateAppleField('calendar_name', event.target.value)}
                    />
                    <div className="flex items-center gap-3">
                      <button className="btn-primary btn-small" type="submit" disabled={appleBusy}>
                        {appleBusy ? 'Connecting...' : 'Connect Apple'}
                      </button>
                      {appleError ? <span className="text-xs text-red-600">{appleError}</span> : null}
                    </div>
                  </form>
                )}
              </div>

              <details className="surface-muted p-4">
                <summary className="flex items-center justify-between gap-4 cursor-pointer list-none">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-gray-400">Apple Calendar import</p>
                    <p className="text-sm text-gray-600">Upload a local .ics export.</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    {appleImportStatus?.event_count ? `${appleImportStatus.event_count} events` : 'No events'}
                  </div>
                </summary>

                <div className="mt-4 space-y-3">
                  <input
                    className="input-field"
                    type="file"
                    accept=".ics,text/calendar"
                    onChange={(event) => setImportFile(event.target.files?.[0] || null)}
                  />
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      className="btn-primary btn-small"
                      type="button"
                      onClick={importAppleCalendar}
                      disabled={importBusy}
                    >
                      {importBusy ? 'Importing...' : 'Import calendar'}
                    </button>
                    <button
                      className="btn-secondary btn-small"
                      type="button"
                      onClick={clearImportedEvents}
                      disabled={importBusy || !(appleImportStatus?.event_count || 0)}
                    >
                      Clear
                    </button>
                    <label className="toggle">
                      <input
                        type="checkbox"
                        checked={includeImportDetails}
                        onChange={(event) => setIncludeImportDetails(event.target.checked)}
                      />
                      <span className="toggle-track">
                        <span className="toggle-thumb" />
                      </span>
                      Show titles on calendar
                    </label>
                  </div>
                  {importStatus ? <p className="text-xs text-emerald-600">{importStatus}</p> : null}
                  {importError ? <p className="text-xs text-red-600">{importError}</p> : null}
                  {appleImportStatus?.last_imported_at ? (
                    <p className="text-xs text-gray-500">
                      Last import: {new Date(appleImportStatus.last_imported_at).toLocaleString('en-US')}
                    </p>
                  ) : null}
                </div>
              </details>
            </div>
          </details>

          <details className="surface p-6">
            <summary className="flex items-center justify-between cursor-pointer list-none">
              <span className="text-lg font-semibold">Manage blocks</span>
              <span className="text-sm text-gray-500">{blocks?.length || 0} blocks</span>
            </summary>
            <div className="mt-4">
              {loading ? (
                <p className="text-sm text-gray-500">Loading schedule...</p>
              ) : error ? (
                <p className="text-sm text-red-600">Unable to load schedule.</p>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {groupedBlocks.map(({ day, blocks: dayBlocks }) => (
                    <div key={day.value} className="surface-muted p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">{day.label}</h3>
                        <span className="text-xs text-gray-500">{dayBlocks.length} blocks</span>
                      </div>
                      {dayBlocks.length ? (
                        dayBlocks.map((block) => (
                          <div key={block.id} className="surface p-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="space-y-2">
                                <p className="text-xs text-gray-500">
                                  {formatTimeRange(normalizeTime(block.start_time), block.duration_minutes)} ·{' '}
                                  {block.duration_minutes} min
                                </p>
                                <h4 className="text-lg font-semibold">{block.title}</h4>
                                {block.description ? (
                                  <p className="text-sm text-gray-600">{block.description}</p>
                                ) : null}
                                <div className="flex flex-wrap items-center gap-2 text-xs">
                                  <span className="surface-muted px-2 py-1 rounded-full uppercase tracking-wide text-gray-600">
                                    {block.category}
                                  </span>
                                  {block.is_active ? (
                                    <span className="text-emerald-600 font-semibold uppercase tracking-wide">
                                      Active
                                    </span>
                                  ) : (
                                    <span className="text-gray-400 font-semibold uppercase tracking-wide">
                                      Paused
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="flex flex-col gap-2">
                                <button
                                  className="btn-secondary btn-small"
                                  type="button"
                                  onClick={() => startEdit(block)}
                                  disabled={busyId === block.id}
                                >
                                  Edit
                                </button>
                                <button
                                  className="btn-secondary btn-small"
                                  type="button"
                                  onClick={() => toggleActive(block)}
                                  disabled={busyId === block.id}
                                >
                                  {block.is_active ? 'Pause' : 'Activate'}
                                </button>
                                <button
                                  className="btn-secondary btn-small"
                                  type="button"
                                  onClick={() => deleteBlock(block.id)}
                                  disabled={busyId === block.id}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>

                            {editingId === block.id && editForm ? (
                              <form
                                className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3"
                                onSubmit={(event) => {
                                  event.preventDefault()
                                  handleUpdate(block.id)
                                }}
                              >
                                <input
                                  className="input-field"
                                  value={editForm.title}
                                  onChange={(event) => updateEditField('title', event.target.value)}
                                  required
                                />
                                <input
                                  className="input-field"
                                  value={editForm.category}
                                  onChange={(event) => updateEditField('category', event.target.value)}
                                  required
                                />
                                <select
                                  className="select-field"
                                  value={editForm.day_of_week}
                                  onChange={(event) => updateEditField('day_of_week', event.target.value)}
                                >
                                  {dayOptions.map((day) => (
                                    <option key={day.value} value={day.value}>
                                      {day.label}
                                    </option>
                                  ))}
                                </select>
                                <input
                                  className="input-field"
                                  type="time"
                                  step={900}
                                  value={editForm.start_time}
                                  onChange={(event) => updateEditField('start_time', event.target.value)}
                                  required
                                />
                                <input
                                  className="input-field"
                                  type="number"
                                  min={15}
                                  step={15}
                                  value={editForm.duration_minutes}
                                  onChange={(event) => updateEditField('duration_minutes', event.target.value)}
                                  required
                                />
                                <label className="toggle">
                                  <input
                                    type="checkbox"
                                    checked={editForm.is_active}
                                    onChange={(event) => updateEditField('is_active', event.target.checked)}
                                  />
                                  <span className="toggle-track">
                                    <span className="toggle-thumb" />
                                  </span>
                                  Active block
                                </label>
                                <textarea
                                  className="input-field md:col-span-2"
                                  value={editForm.description}
                                  onChange={(event) => updateEditField('description', event.target.value)}
                                  placeholder="Description (optional)"
                                />
                                <div className="md:col-span-2 flex items-center gap-3">
                                  <button
                                    className="btn-primary"
                                    type="submit"
                                    disabled={busyId === block.id}
                                  >
                                    {busyId === block.id ? 'Saving...' : 'Save changes'}
                                  </button>
                                  <button className="btn-secondary" type="button" onClick={cancelEdit}>
                                    Cancel
                                  </button>
                                </div>
                              </form>
                            ) : null}
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-gray-500">No blocks scheduled.</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </details>
        </div>
      </AppShell>
    </AuthGate>
  )
}
