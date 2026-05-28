import { useState } from 'react'
import { useSettings } from '@/contexts/SettingsContext'
import { getAllGenerators, generateWithGenerator } from '@/lib/imageGenerators'
import type { GeneratorInstanceConfig } from '@/lib/imageGenerators'
import { Loader2, CheckCircle2, XCircle, Eye, EyeOff } from 'lucide-react'

interface Props {
  onTestResult?: (message: string) => void
}

export function ImageGeneratorSettings({ onTestResult }: Props) {
  const { settings, activeGenerator, setActiveGenerator, updateGeneratorConfig } = useSettings()
  const allDefs = getAllGenerators()
  const [testingId, setTestingId] = useState<string | null>(null)
  const [showKey, setShowKey] = useState<Record<string, boolean>>({})

  const activeDef = allDefs.find(d => d.id === settings.activeGeneratorId)

  const handleTest = async (defId: string) => {
    setTestingId(defId)
    const genConfig = settings.generators.find(g => g.id === defId)
    try {
      const result = await generateWithGenerator(defId, {
        prompt: 'test connection',
        aspectRatio: '1:1',
        count: 1,
      }, genConfig)
      if (result.error) {
        onTestResult?.(`❌ ${defId} 测试失败: ${result.error.message}`)
      } else {
        onTestResult?.(`✅ ${defId} 测试成功!`)
      }
    } catch {
      onTestResult?.(`❌ ${defId} 测试异常`)
    } finally {
      setTestingId(null)
    }
  }

  const genConfigMap = new Map(settings.generators.map(g => [g.id, g]))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h3 text-neutral-600 mb-4">图片生成服务</h2>
        <p className="text-small text-neutral-500 mb-6">
          选择图片生成后端，Pollinations.ai 免费无需配置；自定义API可接入你自己的服务。
        </p>
      </div>

      {/* Generator selector */}
      <div className="space-y-3">
        {allDefs.map(def => {
          const stored = genConfigMap.get(def.id) as GeneratorInstanceConfig | undefined
          const isActive = settings.activeGeneratorId === def.id
          const hasConfig = def.configFields.length > 0

          return (
            <div
              key={def.id}
              className={`rounded-lg border p-4 transition-all ${
                isActive
                  ? 'border-primary-500 bg-primary-500/5'
                  : 'border-neutral-300 hover:border-neutral-400'
              }`}
            >
              {/* Header row */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <input
                    type="radio"
                    name="image-generator"
                    checked={isActive}
                    onChange={() => setActiveGenerator(def.id)}
                    className="mt-1 accent-primary-500"
                  />
                  <div>
                    <label
                      className="text-body font-medium text-neutral-600 cursor-pointer"
                      onClick={() => setActiveGenerator(def.id)}
                    >
                      {def.name}
                    </label>
                    <p className="text-caption text-neutral-500 mt-0.5">{def.description}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleTest(def.id)}
                  disabled={testingId === def.id}
                  className="btn-ghost h-8 px-3 text-caption flex items-center gap-1.5"
                >
                  {testingId === def.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <span>测试连接</span>
                  )}
                </button>
              </div>

              {/* Config fields (expand when active and has config) */}
              {isActive && hasConfig && (
                <div className="mt-4 ml-7 space-y-3 border-t border-neutral-300 pt-4">
                  {def.configFields.map(field => {
                    const currentVal = stored?.config?.[field.key] || ''
                    const isPassword = field.type === 'password'
                    const isRevealed = showKey[`${def.id}-${field.key}`]

                    return (
                      <div key={field.key}>
                        <label className="block text-small font-medium text-neutral-600 mb-1">
                          {field.label}
                          {field.required && <span className="text-error ml-0.5">*</span>}
                        </label>
                        <div className="relative">
                          {field.type === 'select' ? (
                            <select
                              className="w-full input-field appearance-none"
                              value={currentVal}
                              onChange={e => {
                                const updated = { ...stored?.config }
                                updated[field.key] = e.target.value
                                updateGeneratorConfig(def.id, updated)
                              }}
                            >
                              <option value="">请选择...</option>
                              {field.options?.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type={isPassword && !isRevealed ? 'password' : 'text'}
                              className="w-full input-field pr-9"
                              placeholder={field.placeholder}
                              value={currentVal}
                              required={field.required}
                              onChange={e => {
                                const updated = { ...stored?.config }
                                updated[field.key] = e.target.value
                                updateGeneratorConfig(def.id, updated)
                              }}
                            />
                          )}
                          {isPassword && (
                            <button
                              type="button"
                              onClick={() => setShowKey(prev => ({ ...prev, [`${def.id}-${field.key}`]: !prev[`${def.id}-${field.key}`] }))}
                              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
                            >
                              {isRevealed ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
