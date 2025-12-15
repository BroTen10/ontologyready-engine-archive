import { ChevronDown, Palette, PlusCircle, Trash2, X, Save } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import type { Project } from '@/types'

interface ProjectSelectorProps {
  projects: Project[]
  selectedProject: Project | null
  onSelect: (project: Project) => void
  onDelete: (projectId: string) => void
  onAddNew: (name: string, description: string) => void
}

export function ProjectSelector({ projects, selectedProject, onSelect, onDelete, onAddNew }: ProjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setShowAddForm(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleAddProject = () => {
    if (newProjectName.trim()) {
      onAddNew(newProjectName, newProjectDescription)
      setNewProjectName('')
      setNewProjectDescription('')
      setShowAddForm(false)
      setIsOpen(false)
    }
  }

  return (
    <div className="bg-neutral-100 rounded-lg p-4 border border-neutral-300">
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        {/* Project Dropdown */}
        <div className="flex-1" ref={dropdownRef}>
          <label className="block text-caption text-neutral-500 mb-2">选择项目</label>
          <div className="relative">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="w-full select-field flex items-center justify-between"
            >
              <span className={selectedProject ? 'text-neutral-600' : 'text-neutral-400'}>
                {selectedProject?.name || '请选择项目...'}
              </span>
              <ChevronDown className={`w-5 h-5 text-neutral-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-neutral-200 rounded-lg shadow-modal border border-neutral-300 overflow-hidden z-20">
                {/* New Project Button */}
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="w-full px-4 py-3 text-left hover:bg-neutral-300 transition-colors text-primary-500 flex items-center gap-2"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>新建项目</span>
                </button>

                {/* Add Project Form */}
                {showAddForm && (
                  <div className="px-4 py-3 border-t border-neutral-300">
                    <div className="space-y-2">
                      <input
                        type="text"
                        placeholder="项目名称"
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        className="w-full input-field text-small"
                        autoFocus
                      />
                      <input
                        type="text"
                        placeholder="项目描述"
                        value={newProjectDescription}
                        onChange={(e) => setNewProjectDescription(e.target.value)}
                        className="w-full input-field text-small"
                      />
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={handleAddProject}
                          className="flex-1 btn-primary h-8 text-small flex items-center justify-center gap-1"
                          disabled={!newProjectName.trim()}
                        >
                          <Save className="w-3.5 h-3.5" />
                          保存
                        </button>
                        <button
                          onClick={() => setShowAddForm(false)}
                          className="btn-ghost h-8 px-3 text-small flex items-center justify-center gap-1"
                        >
                          <X className="w-3.5 h-3.5" />
                          取消
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Project List */}
                {projects.map(project => (
                  <button
                    key={project.id}
                    onClick={() => {
                      onSelect(project)
                      setIsOpen(false)
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-neutral-300 transition-colors ${selectedProject?.id === project.id ? 'bg-primary-50 text-primary-500' : 'text-neutral-600'}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{project.name}</div>
                        <div className="text-caption text-neutral-500 mt-0.5">{project.description}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onDelete(project.id)
                        }}
                        className="text-error hover:text-error-600 p-1 rounded hover:bg-error/10 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Brand Profile Preview */}
        {selectedProject && (
          <div className="flex-1 bg-neutral-200 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <Palette className="w-5 h-5 text-primary-500" />
              <span className="text-small font-medium text-neutral-600">品牌规范</span>
            </div>

            <div className="flex flex-wrap gap-3">
              {/* Color Swatches */}
              <div className="flex items-center gap-2">
                <div
                  className="w-6 h-6 rounded-md border border-white/20"
                  style={{ backgroundColor: selectedProject.brand_profile.primary_color }}
                  title="主色"
                />
                <div
                  className="w-6 h-6 rounded-md border border-white/20"
                  style={{ backgroundColor: selectedProject.brand_profile.secondary_color }}
                  title="辅助色"
                />
                <div
                  className="w-6 h-6 rounded-md border border-white/20"
                  style={{ backgroundColor: selectedProject.brand_profile.accent_color }}
                  title="强调色"
                />
              </div>

              {/* Style Keywords */}
              <div className="flex flex-wrap gap-1">
                {selectedProject.brand_profile.style_keywords.slice(0, 3).map(keyword => (
                  <span key={keyword} className="tag text-caption">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>

            {/* Restrictions Notice */}
            {selectedProject.brand_profile.restrictions.length > 0 && (
              <div className="mt-3 pt-3 border-t border-neutral-300">
                <p className="text-caption text-warning">
                  注意: {selectedProject.brand_profile.restrictions[0]}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
