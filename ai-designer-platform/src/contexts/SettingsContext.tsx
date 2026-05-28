import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { GeneratorInstanceConfig } from '@/lib/imageGenerators'

const STORAGE_KEY = 'ai-designer-settings'

export interface AppSettings {
  activeGeneratorId: string
  generators: GeneratorInstanceConfig[]
}

interface SettingsContextValue {
  settings: AppSettings
  activeGenerator: GeneratorInstanceConfig | undefined
  setActiveGenerator: (id: string) => void
  updateGeneratorConfig: (id: string, config: Record<string, string>) => void
  updateGeneratorLabel: (id: string, label: string) => void
}

function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as AppSettings
      // Ensure at least pollinations exists
      if (!parsed.generators.some(g => g.id === 'pollinations')) {
        parsed.generators.push({ id: 'pollinations', config: {} })
      }
      // Ensure custom-api exists
      if (!parsed.generators.some(g => g.id === 'custom-api')) {
        parsed.generators.push({ id: 'custom-api', config: {} })
      }
      return parsed
    }
  } catch {
    // ignore
  }
  return {
    activeGeneratorId: 'pollinations',
    generators: [
      { id: 'pollinations', config: {} },
      { id: 'custom-api', label: '自定义API', config: {} },
    ],
  }
}

function persistSettings(s: AppSettings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  } catch {
    // ignore
  }
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(loadSettings)

  // Persist on every change
  useEffect(() => {
    persistSettings(settings)
  }, [settings])

  const activeGenerator = settings.generators.find(g => g.id === settings.activeGeneratorId)

  const setActiveGenerator = useCallback((id: string) => {
    setSettings(prev => ({ ...prev, activeGeneratorId: id }))
  }, [])

  const updateGeneratorConfig = useCallback((id: string, config: Record<string, string>) => {
    setSettings(prev => ({
      ...prev,
      generators: prev.generators.map(g =>
        g.id === id ? { ...g, config: { ...g.config, ...config } } : g
      ),
    }))
  }, [])

  const updateGeneratorLabel = useCallback((id: string, label: string) => {
    setSettings(prev => ({
      ...prev,
      generators: prev.generators.map(g =>
        g.id === id ? { ...g, label } : g
      ),
    }))
  }, [])

  return (
    <SettingsContext.Provider value={{ settings, activeGenerator, setActiveGenerator, updateGeneratorConfig, updateGeneratorLabel }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}
