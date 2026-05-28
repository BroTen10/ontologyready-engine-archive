import { useState } from 'react'
import { X, Plus, Layout, Signpost, Image, Gift, Palette } from 'lucide-react'
import type { ContentType, StylePreference, AspectRatio, SpecialRequirement, GenerationRequest } from '@/types'

interface GenerationFormProps {
  contentTypes: ContentType[]
  stylePreferences: StylePreference[]
  aspectRatios: AspectRatio[]
  specialRequirements: SpecialRequirement[]
  request: GenerationRequest
  onRequestChange: (request: GenerationRequest) => void
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  layout: Layout,
  signpost: Signpost,
  image: Image,
  gift: Gift,
  palette: Palette,
}

export function GenerationForm({
  contentTypes,
  stylePreferences,
  aspectRatios,
  specialRequirements,
  request,
  onRequestChange,
}: GenerationFormProps) {
  const [keywordInput, setKeywordInput] = useState('')

  const updateRequest = (updates: Partial<GenerationRequest>) => {
    onRequestChange({ ...request, ...updates })
  }

  const addKeyword = () => {
    if (keywordInput.trim() && !request.keywords.includes(keywordInput.trim())) {
      updateRequest({ keywords: [...request.keywords, keywordInput.trim()] })
      setKeywordInput('')
    }
  }

  const removeKeyword = (keyword: string) => {
    updateRequest({ keywords: request.keywords.filter(k => k !== keyword) })
  }

  const toggleStyle = (styleId: string) => {
    const styles = request.stylePreferences.includes(styleId)
      ? request.stylePreferences.filter(s => s !== styleId)
      : [...request.stylePreferences, styleId]
    updateRequest({ stylePreferences: styles })
  }

  const toggleRequirement = (reqId: string) => {
    const reqs = request.specialRequirements.includes(reqId)
      ? request.specialRequirements.filter(r => r !== reqId)
      : [...request.specialRequirements, reqId]
    updateRequest({ specialRequirements: reqs })
  }

  return (
    <div className="space-y-6">
      {/* Content Type */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          内容类型
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
          {contentTypes.map(type => {
            const IconComponent = iconMap[type.icon] || Image
            return (
              <button
                key={type.id}
                onClick={() => updateRequest({ contentType: type.id })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border transition-all duration-150 ${
                  request.contentType === type.id
                    ? 'bg-primary-50 border-primary-500 text-primary-500'
                    : 'bg-neutral-100 border-neutral-300 text-neutral-500 hover:bg-neutral-200'
                }`}
              >
                <IconComponent className="w-6 h-6" />
                <span className="text-caption font-medium text-center">{type.name}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Keywords */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          主题关键词
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
            placeholder="输入关键词,按回车添加..."
            className="flex-1 input-field"
          />
          <button
            onClick={addKeyword}
            className="btn-secondary h-12 px-4"
            disabled={!keywordInput.trim()}
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        {request.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {request.keywords.map(keyword => (
              <span key={keyword} className="tag">
                {keyword}
                <button
                  onClick={() => removeKeyword(keyword)}
                  className="ml-1 hover:text-error transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Style Preferences */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          风格偏好 (可多选)
        </label>
        <div className="flex flex-wrap gap-2">
          {stylePreferences.map(style => (
            <button
              key={style.id}
              onClick={() => toggleStyle(style.id)}
              className={`px-4 py-2 rounded-full text-small font-medium transition-all duration-150 ${
                request.stylePreferences.includes(style.id)
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-200 text-neutral-500 hover:bg-neutral-300'
              }`}
            >
              {style.name}
            </button>
          ))}
        </div>
      </div>

      {/* Aspect Ratio */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          构图与比例
        </label>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {aspectRatios.map(ratio => (
            <button
              key={ratio.id}
              onClick={() => updateRequest({ aspectRatio: ratio.id })}
              className={`flex flex-col items-center gap-2 p-3 rounded-lg border transition-all duration-150 ${
                request.aspectRatio === ratio.id
                  ? 'bg-primary-50 border-primary-500 text-primary-500'
                  : 'bg-neutral-100 border-neutral-300 text-neutral-500 hover:bg-neutral-200'
              }`}
            >
              {ratio.width && ratio.height && (
                <div
                  className="border-2 border-current"
                  style={{
                    width: `${Math.min(ratio.width / ratio.height, 1) * 24}px`,
                    height: `${Math.min(ratio.height / ratio.width, 1) * 24}px`,
                  }}
                />
              )}
              <span className="text-caption font-medium">{ratio.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Special Requirements */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          特殊要求
        </label>
        <div className="flex flex-wrap gap-2">
          {specialRequirements.map(req => (
            <label
              key={req.id}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all duration-150 ${
                request.specialRequirements.includes(req.id)
                  ? 'bg-secondary-50 border border-secondary-500 text-secondary-500'
                  : 'bg-neutral-100 border border-neutral-300 text-neutral-500 hover:bg-neutral-200'
              }`}
            >
              <input
                type="checkbox"
                checked={request.specialRequirements.includes(req.id)}
                onChange={() => toggleRequirement(req.id)}
                className="sr-only"
              />
              <span className="text-small font-medium">{req.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-small font-medium text-neutral-600 mb-3">
          详细描述 (可选)
        </label>
        <textarea
          value={request.description}
          onChange={(e) => updateRequest({ description: e.target.value })}
          placeholder="描述您想要生成的画面细节..."
          rows={4}
          className="w-full input-field resize-none"
        />
      </div>
    </div>
  )
}
