import { useState } from 'react'
import { Download, Maximize2, Layers, Heart, Package, MessageSquare, X, Loader2 } from 'lucide-react'
import type { GeneratedImage } from '@/types'

interface ResultsGridProps {
  images: GeneratedImage[]
  isLoading: boolean
  progress: number
  onDownload: (image: GeneratedImage) => void
  onVariation: (image: GeneratedImage) => void
  onFavorite: (image: GeneratedImage) => void
  onPackageDownload: () => void
  onFeedback: (feedback: string) => void
}

export function ResultsGrid({
  images,
  isLoading,
  progress,
  onDownload,
  onVariation,
  onFavorite,
  onPackageDownload,
  onFeedback,
}: ResultsGridProps) {
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const selectAll = () => {
    if (selectedIds.size === images.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(images.map(img => img.id)))
    }
  }

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

          <h3 className="text-h3 text-neutral-600 mb-2">AI正在创作中...</h3>
          <p className="text-small text-neutral-500">预计剩余时间: {Math.ceil((100 - progress) / 10)} 秒</p>
        </div>
      </div>
    )
  }

  // Empty State
  if (images.length === 0) {
    return (
      <div className="bg-neutral-100 rounded-lg border border-neutral-300 p-8">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-neutral-200 flex items-center justify-center mb-4">
            <Layers className="w-8 h-8 text-neutral-400" />
          </div>
          <h3 className="text-h3 text-neutral-600 mb-2">等待生成</h3>
          <p className="text-small text-neutral-500 max-w-sm">
            选择项目、填写生成参数后,点击"开始生成"按钮创建AI图像
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-neutral-100 rounded-lg p-4 border border-neutral-300">
        <div className="flex items-center gap-4">
          <button
            onClick={selectAll}
            className="text-small text-neutral-500 hover:text-neutral-600 transition-colors"
          >
            {selectedIds.size === images.length ? '取消全选' : '全选'}
          </button>
          <span className="text-caption text-neutral-400">
            已选择 {selectedIds.size} 张图片
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onPackageDownload}
            disabled={selectedIds.size === 0}
            className="btn-secondary h-10 px-4 text-small flex items-center gap-2"
          >
            <Package className="w-4 h-4" />
            <span className="hidden sm:inline">打包下载</span>
          </button>
          <button
            onClick={() => setShowFeedback(true)}
            className="btn-ghost h-10 px-4 text-small flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="hidden sm:inline">反馈建议</span>
          </button>
        </div>
      </div>

      {/* Image Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {images.map(image => (
          <div
            key={image.id}
            className={`relative group bg-neutral-100 rounded-lg overflow-hidden border transition-all duration-200 ${
              selectedIds.has(image.id)
                ? 'border-primary-500 ring-2 ring-primary-500/20'
                : 'border-neutral-300 hover:border-neutral-400'
            }`}
          >
            {/* Selection Checkbox */}
            <button
              onClick={() => toggleSelect(image.id)}
              className={`absolute top-3 left-3 w-6 h-6 rounded-md border-2 z-10 transition-all duration-150 ${
                selectedIds.has(image.id)
                  ? 'bg-primary-500 border-primary-500'
                  : 'bg-neutral-100/50 border-white/50 opacity-0 group-hover:opacity-100'
              }`}
            >
              {selectedIds.has(image.id) && (
                <svg className="w-full h-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>

            {/* Image */}
            <div className="aspect-square bg-neutral-200">
              <img
                src={image.url}
                alt="Generated"
                className="w-full h-full object-cover"
              />
            </div>

            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <div className="absolute bottom-0 left-0 right-0 p-4">
                <div className="flex justify-center gap-2">
                  <button
                    onClick={() => setSelectedImage(image)}
                    className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors flex items-center justify-center"
                    title="放大查看"
                  >
                    <Maximize2 className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => onVariation(image)}
                    className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors flex items-center justify-center"
                    title="生成变体"
                  >
                    <Layers className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => onDownload(image)}
                    className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors flex items-center justify-center"
                    title="下载高清图"
                  >
                    <Download className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => onFavorite(image)}
                    className="w-10 h-10 rounded-lg bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-colors flex items-center justify-center"
                    title="收藏"
                  >
                    <Heart className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
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
          <div className="bg-neutral-100 rounded-xl shadow-modal w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
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
  )
}
