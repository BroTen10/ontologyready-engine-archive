import { useState } from 'react'
import { Search, Tag, Zap, Layout, Signpost, Image, Gift, Palette } from 'lucide-react'
import type { Template } from '@/types'

interface TemplateLibraryProps {
  onApplyTemplate: (template: Template) => void
}

// Preset templates
const presetTemplates: Template[] = [
  {
    id: 'tech-booth',
    name: '科技展台效果图',
    description: '适用于科技类展览的现代化展台设计',
    category: '展台',
    contentType: 'booth',
    stylePreferences: ['futuristic', 'minimalist', 'tech'],
    keywords: ['科技感', '未来主义', '互动体验'],
    aspectRatio: '16:9',
    specialRequirements: ['high-detail'],
    promptTemplate: 'futuristic exhibition booth design, high-tech displays, LED lighting, interactive elements',
  },
  {
    id: 'culture-poster',
    name: '国潮文化海报',
    description: '融合传统与现代的国潮风格主视觉',
    category: '海报',
    contentType: 'poster',
    stylePreferences: ['guochao', 'retro'],
    keywords: ['国潮', '传统文化', '现代设计'],
    aspectRatio: '3:4',
    specialRequirements: ['whitespace', 'high-detail'],
    promptTemplate: 'Chinese traditional style poster, guochao design, cultural heritage elements, modern interpretation',
  },
  {
    id: 'kids-signage',
    name: '儿童展区导视',
    description: '活泼有趣的儿童展览导视系统',
    category: '导视',
    contentType: 'signage',
    stylePreferences: ['organic'],
    keywords: ['童趣', '活力', '教育'],
    aspectRatio: '1:1',
    specialRequirements: ['high-detail'],
    promptTemplate: 'playful wayfinding signage, children-friendly design, colorful, educational elements',
  },
  {
    id: 'eco-merchandise',
    name: '生态环保文创',
    description: '自然有机风格的环保文创产品设计',
    category: '文创',
    contentType: 'merchandise',
    stylePreferences: ['organic', 'minimalist'],
    keywords: ['环保', '自然', '可持续'],
    aspectRatio: '1:1',
    specialRequirements: ['transparent'],
    promptTemplate: 'eco-friendly merchandise design, sustainable materials, organic shapes, natural colors',
  },
  {
    id: 'cyberpunk-mood',
    name: '赛博朋克氛围',
    description: '赛博朋克风格的未来城市氛围参考',
    category: '氛围',
    contentType: 'mood',
    stylePreferences: ['cyberpunk', 'futuristic'],
    keywords: ['霓虹', '未来城市', '科幻'],
    aspectRatio: '16:9',
    specialRequirements: ['high-detail'],
    promptTemplate: 'cyberpunk cityscape, neon lights, futuristic atmosphere, dark ambient mood',
  },
  {
    id: 'industrial-booth',
    name: '工业风展台',
    description: '原始材质感的工业风格展台设计',
    category: '展台',
    contentType: 'booth',
    stylePreferences: ['industrial', 'minimalist'],
    keywords: ['工业', '金属', '混凝土'],
    aspectRatio: '16:9',
    specialRequirements: ['multi-angle', 'high-detail'],
    promptTemplate: 'industrial style exhibition booth, raw materials, metal and concrete, factory aesthetic',
  },
]

const categories = ['全部', '展台', '海报', '导视', '文创', '氛围']

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  booth: Layout,
  signage: Signpost,
  poster: Image,
  merchandise: Gift,
  mood: Palette,
}

export function TemplateLibrary({ onApplyTemplate }: TemplateLibraryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('全部')

  const filteredTemplates = presetTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.keywords.some(k => k.includes(searchQuery))
    const matchesCategory = selectedCategory === '全部' || template.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索模板..."
            className="w-full input-field pl-12"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-full text-small font-medium whitespace-nowrap transition-all duration-150 ${
              selectedCategory === category
                ? 'bg-primary-500 text-white'
                : 'bg-neutral-200 text-neutral-500 hover:bg-neutral-300'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map(template => {
          const IconComponent = iconMap[template.contentType] || Image
          return (
            <div
              key={template.id}
              className="card group cursor-pointer"
              onClick={() => onApplyTemplate(template)}
            >
              {/* Template Preview */}
              <div className="aspect-video bg-gradient-to-br from-primary-50 to-secondary-50 rounded-lg mb-4 flex items-center justify-center">
                <IconComponent className="w-12 h-12 text-primary-500/50" />
              </div>

              {/* Template Info */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-primary-500" />
                  <span className="text-caption text-neutral-500">{template.category}</span>
                </div>
                <h3 className="text-body font-semibold text-neutral-600 group-hover:text-primary-500 transition-colors">
                  {template.name}
                </h3>
                <p className="text-small text-neutral-500 line-clamp-2">
                  {template.description}
                </p>

                {/* Keywords */}
                <div className="flex flex-wrap gap-1 pt-2">
                  {template.keywords.slice(0, 3).map(keyword => (
                    <span key={keyword} className="text-caption bg-neutral-200 text-neutral-500 px-2 py-0.5 rounded">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              {/* Quick Apply Button */}
              <button
                className="mt-4 w-full btn-secondary h-10 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => {
                  e.stopPropagation()
                  onApplyTemplate(template)
                }}
              >
                <Zap className="w-4 h-4" />
                <span>快速应用</span>
              </button>
            </div>
          )
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-16">
          <div className="w-16 h-16 rounded-full bg-neutral-200 flex items-center justify-center mx-auto mb-4">
            <Search className="w-8 h-8 text-neutral-400" />
          </div>
          <h3 className="text-h3 text-neutral-600 mb-2">未找到匹配的模板</h3>
          <p className="text-small text-neutral-500">
            尝试调整搜索关键词或选择其他分类
          </p>
        </div>
      )}
    </div>
  )
}
