import { useState } from 'react'
import { Download, Maximize2, Layers, Heart, MessageSquare, X } from 'lucide-react'
import * as Tooltip from '@radix-ui/react-tooltip'
import type { GeneratedImage } from '@/types'

interface ResultsGridProps {
  images: GeneratedImage[]
  isLoading: boolean
  progress: number
  onDownload: (image: GeneratedImage) => void
  onVariation: (image: GeneratedImage) => void
  onFavorite: (image: GeneratedImage) => void
  onFeedback: (feedback: string) => void
  error?: string | null
}

export function ResultsGrid({
  images,
  isLoading,
  progress,
  onDownload,
  onVariation,
  onFavorite,
  onFeedback,
  error,
}: ResultsGridProps) {
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')

  const submitFeedback = () => {
    if (feedbackText.trim()) {
      onFeedback(feedbackText)
      setFeedbackText('')
      setShowFeedback(false)
    }
  }

  // Loading State
  if (isLoading) {
    return (
      <div className="bg-neutral-100 rounded-lg border border-neutral-300 p-8">
        <div className="flex flex-col items-center justify-center py-12">
          {/* Progress Ring */}
          <div className="relative w-24 h-24 mb-6">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="44"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-neutral-300"
              />
              <circle
                cx="48"
                cy="48"
                r="44"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 44}`}
                strokeDashoffset={`${2 * Math.PI * 44 * (1 - progress / 100)}`}
                className="text-primary-500 transition-all duration-300"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-h2 font-bold text-primary-500">{progress}%</span>
            </div>
          </div>

          <h3 className="text-h3 text-neutral-600 mb-2 animate-pulse">AI正在创作中...</h3>
          <p className="text-small text-neutral-500">正在生成高品质图像，请稍候</p>

          {/* Skeleton placeholder */}
          <div className="w-full max-w-md mt-8">
            <div className="shimmer h-48 rounded-lg w-full" />
          </div>
        </div>
      </div>
    )
  }

  // Empty State
  if (images.length === 0) {
    return (
      <div className="bg-gradient-to-b from-neutral-100 to-neutral-0 rounded-lg border border-neutral-300 p-8">
        {error && (
          <div className="mb-6 rounded-lg bg-error/10 border border-error/30 p-4 text-small text-error animate-fade-in-up">
            {error}
          </div>
        )}
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500/20 to-secondary-500/20
                          flex items-center justify-center mb-6 ring-1 ring-white/5">
            <Layers className="w-10 h-10 text-primary-500/50" />
          </div>
          <h3 className="text-h3 text-neutral-600 mb-2">等待生成</h3>
          <p className="text-small text-neutral-500 max-w-md">
            选择项目、填写生成参数后，点击"开始生成"按钮创建AI图像
          </p>
        </div>
      </div>
    )
  }

  return (
    <Tooltip.Provider delayDuration={300}>
      <div className="space-y-4">
        {/* Error Banner */}
        {error && (
          <div className="rounded-lg bg-error/10 border border-error/30 p-4 text-small text-error animate-fade-in-up">
            {error}
          </div>
        )}

        {/* Simple Toolbar */}
        <div className="flex items-center justify-between bg-neutral-100 rounded-lg p-4 border border-neutral-300">
          <span className="text-small text-neutral-500">
            共 1 张图片
          </span>
          <button
            onClick={() => setShowFeedback(true)}
            className="btn-ghost h-10 px-4 text-small flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="hidden sm:inline">反馈建议</span>
          </button>
        </div>

        {/* Single Image Display - Centered */}
        <div className="max-w-3xl mx-auto">
          {images.map((image, index) => (
            <div
              key={image.id}
              className="relative group bg-neutral-100 rounded-xl overflow-hidden border border-neutral-300 hover:border-primary-500/50 transition-all duration-300 animate-fade-in-up shadow-card hover:shadow-card-hover"
              style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'backwards' }}
            >
              {/* Image */}
              <div className="aspect-video bg-neutral-200">
                <img
                  src={image.url}
                  alt="Generated"
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <div className="flex justify-center gap-3">
                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <button
                          onClick={() => setSelectedImage(image)}
                          className="w-11 h-11 rounded-xl bg-white/10 backdrop-blur-sm text-white hover:bg-white/25 transition-all flex items-center justify-center hover:scale-110"
                        >
                          <Maximize2 className="w-5 h-5" />
                        </button>
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content className="bg-neutral-600 text-white text-caption px-2.5 py-1.5 rounded-md shadow-md" sideOffset={4}>
                          放大查看
                          <Tooltip.Arrow className="fill-neutral-600" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>

                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <button
                          onClick={() => onVariation(image)}
                          className="w-11 h-11 rounded-xl bg-white/10 backdrop-blur-sm text-white hover:bg-white/25 transition-all flex items-center justify-center hover:scale-110"
                        >
                          <Layers className="w-5 h-5" />
                        </button>
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content className="bg-neutral-600 text-white text-caption px-2.5 py-1.5 rounded-md shadow-md" sideOffset={4}>
                          生成变体
                          <Tooltip.Arrow className="fill-neutral-600" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>

                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <button
                          onClick={() => onDownload(image)}
                          className="w-11 h-11 rounded-xl bg-white/10 backdrop-blur-sm text-white hover:bg-white/25 transition-all flex items-center justify-center hover:scale-110"
                        >
                          <Download className="w-5 h-5" />
                        </button>
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content className="bg-neutral-600 text-white text-caption px-2.5 py-1.5 rounded-md shadow-md" sideOffset={4}>
                          下载高清图
                          <Tooltip.Arrow className="fill-neutral-600" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>

                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <button
                          onClick={() => onFavorite(image)}
                          className="w-11 h-11 rounded-xl bg-white/10 backdrop-blur-sm text-white hover:bg-white/25 transition-all flex items-center justify-center hover:scale-110"
                        >
                          <Heart className="w-5 h-5" />
                        </button>
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content className="bg-neutral-600 text-white text-caption px-2.5 py-1.5 rounded-md shadow-md" sideOffset={4}>
                          收藏
                          <Tooltip.Arrow className="fill-neutral-600" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Lightbox Modal */}
        {selectedImage && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 animate-scale-in"
            onClick={() => setSelectedImage(null)}
          >
            <button
              className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors flex items-center justify-center"
              onClick={() => setSelectedImage(null)}
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedImage.url}
              alt="Full size"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}

        {/* Feedback Modal */}
        {showFeedback && (
          <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
            <div className="bg-neutral-100 rounded-xl shadow-modal w-full max-w-md p-6 animate-scale-in" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-h3 text-neutral-600">反馈与建议</h3>
                <button
                  onClick={() => setShowFeedback(false)}
                  className="w-8 h-8 rounded-full hover:bg-neutral-200 transition-colors flex items-center justify-center"
                >
                  <X className="w-5 h-5 text-neutral-500" />
                </button>
              </div>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="请告诉我们您对生成结果的看法,或提出改进建议..."
                rows={5}
                className="w-full input-field resize-none mb-4"
              />
              <div className="flex gap-3">
                <button onClick={() => setShowFeedback(false)} className="flex-1 btn-ghost">
                  取消
                </button>
                <button onClick={submitFeedback} className="flex-1 btn-primary">
                  提交反馈
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Tooltip.Provider>
  )
}
