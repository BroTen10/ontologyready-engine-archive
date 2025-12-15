import { useState } from 'react'
import { Copy, Check, Sparkles, Save, Loader2 } from 'lucide-react'
import type { AIPlatform } from '@/types'

interface PromptPreviewProps {
  platforms: AIPlatform[]
  selectedPlatform: string
  onPlatformChange: (platform: string) => void
  prompt: string
  onPromptChange: (prompt: string) => void
  onGenerate: () => void
  onSaveTemplate: () => void
  isGenerating: boolean
}

const platformIcons: Record<string, string> = {
  dalle: 'D',
  midjourney: 'M',
  'stable-diffusion': 'S',
  tongyi: 'T',
}

export function PromptPreview({
  platforms,
  selectedPlatform,
  onPlatformChange,
  prompt,
  onPromptChange,
  onGenerate,
  onSaveTemplate,
  isGenerating,
}: PromptPreviewProps) {
  const [copied, setCopied] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(prompt)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="bg-neutral-100 rounded-lg border border-neutral-300 overflow-hidden sticky top-20">
      {/* Platform Tabs */}
      <div className="flex p-1 bg-neutral-200 m-3 rounded-lg">
        {platforms.map(platform => (
          <button
            key={platform.id}
            onClick={() => onPlatformChange(platform.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-small font-medium transition-all duration-200 ${
              selectedPlatform === platform.id
                ? 'bg-neutral-100 text-neutral-600 shadow-sm'
                : 'text-neutral-500 hover:text-neutral-600'
            }`}
          >
            <span className="w-5 h-5 rounded bg-gradient-to-br from-primary-500 to-secondary-500 text-white text-caption flex items-center justify-center font-bold">
              {platformIcons[platform.id] || platform.name[0]}
            </span>
            <span className="hidden sm:inline">{platform.name}</span>
          </button>
        ))}
      </div>

      {/* Prompt Preview */}
      <div className="px-4 pb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-small font-medium text-neutral-600">Prompt 预览</span>
          <div className="flex gap-2">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="text-caption text-primary-500 hover:text-primary-600 transition-colors"
            >
              {isEditing ? '完成编辑' : '手动编辑'}
            </button>
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1 text-caption text-neutral-500 hover:text-neutral-600 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-success" />
                  <span className="text-success">已复制</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>复制</span>
                </>
              )}
            </button>
          </div>
        </div>

        {isEditing ? (
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            className="w-full h-48 input-field font-mono text-small resize-none"
          />
        ) : (
          <div className="bg-neutral-0 rounded-lg p-4 h-48 overflow-y-auto">
            <pre className="font-mono text-small text-neutral-500 whitespace-pre-wrap break-words">
              {prompt || '请选择内容类型和设置参数以生成 Prompt...'}
            </pre>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="p-4 bg-neutral-200 border-t border-neutral-300 space-y-3">
        <button
          onClick={onGenerate}
          disabled={!prompt || isGenerating}
          className={`w-full btn-primary flex items-center justify-center gap-2 ${
            isGenerating ? 'animate-pulse-glow' : ''
          }`}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>生成中...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>开始生成</span>
            </>
          )}
        </button>

        <button
          onClick={onSaveTemplate}
          disabled={!prompt}
          className="w-full btn-ghost flex items-center justify-center gap-2"
        >
          <Save className="w-5 h-5" />
          <span>保存为模板</span>
        </button>
      </div>
    </div>
  )
}
