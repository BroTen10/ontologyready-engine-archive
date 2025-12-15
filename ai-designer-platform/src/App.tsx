import { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { ProjectSelector } from './components/ProjectSelector'
import { GenerationForm } from './components/GenerationForm'
import { PromptPreview } from './components/PromptPreview'
import { ResultsGrid } from './components/ResultsGrid'
import { TemplateLibrary } from './components/TemplateLibrary'
import { AuthModal } from './components/AuthModal'
import { useBrandData } from './hooks/useBrandData'
import { useAuth } from './contexts/AuthContext'
import { generatePromptFromRequest } from './lib/promptBuilder'
import { isSupabaseConfigured } from './lib/supabase'
import { 
  generateImages, 
  saveGenerationHistory, 
  getGenerationHistory,
  clearGenerationHistory,
  saveUserTemplate,
  getUserTemplates,
  deleteUserTemplate
} from './lib/dataService'
import type { Project, GenerationRequest, GeneratedImage, Template } from './types'
import { Loader2, Clock, Trash2, User, LogOut, LogIn, Download, Layout, Signpost, Image, Gift, Palette, Tag, Zap } from 'lucide-react'

// Initial empty request
const initialRequest: GenerationRequest = {
  projectId: '',
  contentType: '',
  keywords: [],
  stylePreferences: [],
  aspectRatio: '16:9',
  specialRequirements: [],
  description: '',
  aiPlatform: 'dalle',
  prompt: '',
}

function App() {
  const { data: brandData, loading: brandLoading, error: brandError, createProject, deleteProject } = useBrandData()
  const { user, loading: authLoading, signOut, isConfigured } = useAuth()
  const [activeTab, setActiveTab] = useState('workspace')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [request, setRequest] = useState<GenerationRequest>(initialRequest)
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [history, setHistory] = useState<GeneratedImage[]>([])
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [userTemplates, setUserTemplates] = useState<Template[]>([])

  // Load history from database when user logs in
  useEffect(() => {
    if (user && isConfigured) {
      loadHistory()
      loadUserTemplates()
    }
  }, [user, isConfigured])

  async function loadHistory() {
    const { data } = await getGenerationHistory(user?.id, 50)
    if (data && data.length > 0) {
      const images: GeneratedImage[] = data.flatMap(record => 
        (record.result_images || []).map((url: string, index: number) => ({
          id: `${record.id}-${index}`,
          url,
          prompt: record.prompt,
          timestamp: new Date(record.created_at),
        }))
      )
      setHistory(images)
    }
  }

  async function loadUserTemplates() {
    if (!user) return
    const { data } = await getUserTemplates(user.id)
    if (data) {
      setUserTemplates(data.map(t => ({
        id: t.id,
        name: t.name,
        description: t.description || '',
        category: 'user',
        contentType: t.content_type,
        stylePreferences: t.style_preferences || [],
        keywords: t.keywords || [],
        aspectRatio: t.aspect_ratio || '16:9',
        specialRequirements: t.special_requirements || [],
        promptTemplate: t.prompt_template || '',
      })))
    }
  }

  // Handle project creation
  const handleAddNewProject = (name: string, description: string) => {
    if (!brandData) return
    
    // Create a default project with basic brand profile
    const newProject = createProject({
      name: name,
      description: description || '这是一个新创建的项目',
      brand_profile: {
        primary_color: '#3B82F6',
        secondary_color: '#8B5CF6',
        accent_color: '#EC4899',
        font_family: 'Arial, sans-serif',
        logo_url: '',
        style_keywords: ['modern', 'clean', 'professional'],
        restrictions: []
      }
    })
    
    if (newProject) {
      setSelectedProject(newProject)
      setRequest(prev => ({ ...prev, projectId: newProject.id }))
    }
  }

  // Handle project deletion
  const handleDeleteProject = (projectId: string) => {
    if (selectedProject?.id === projectId) {
      setSelectedProject(null)
      setRequest(prev => ({ ...prev, projectId: '' }))
    }
    
    deleteProject(projectId)
  }

  // Update prompt when request changes
  useEffect(() => {
    if (request.contentType) {
      const newPrompt = generatePromptFromRequest(request, selectedProject)
      setRequest(prev => ({ ...prev, prompt: newPrompt }))
    }
  }, [
    request.contentType,
    request.keywords,
    request.stylePreferences,
    request.aspectRatio,
    request.specialRequirements,
    request.description,
    request.aiPlatform,
    selectedProject,
  ])

  // Handle project selection
  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project)
    setRequest(prev => ({ ...prev, projectId: project.id }))
  }

  // Handle AI platform change
  const handlePlatformChange = (platform: string) => {
    setRequest(prev => ({ ...prev, aiPlatform: platform }))
  }

  // Handle prompt change (manual edit)
  const handlePromptChange = (prompt: string) => {
    setRequest(prev => ({ ...prev, prompt }))
  }

  // Handle generation
  const handleGenerate = async () => {
    if (!request.prompt) return

    setIsGenerating(true)
    setProgress(0)
    setGeneratedImages([])

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev
        return prev + Math.random() * 15
      })
    }, 500)

    try {
      const { images } = await generateImages({
        prompt: request.prompt,
        platform: request.aiPlatform,
        aspectRatio: request.aspectRatio,
        count: 4,
      })

      const generatedImgs: GeneratedImage[] = images.map((url, index) => ({
        id: `${Date.now()}-${index}`,
        url,
        prompt: request.prompt,
        timestamp: new Date(),
      }))

      setGeneratedImages(generatedImgs)
      setHistory(prev => [...generatedImgs, ...prev])

      // Save to database
      if (user && isConfigured) {
        await saveGenerationHistory({
          userId: user.id,
          projectId: selectedProject?.id,
          contentType: request.contentType,
          keywords: request.keywords,
          stylePreferences: request.stylePreferences,
          aspectRatio: request.aspectRatio,
          specialRequirements: request.specialRequirements,
          aiPlatform: request.aiPlatform,
          prompt: request.prompt,
          resultImages: images,
          status: 'completed',
        })
      }
    } catch (err) {
      console.error('Generation failed:', err)
    } finally {
      clearInterval(progressInterval)
      setProgress(100)
      setTimeout(() => {
        setIsGenerating(false)
        setProgress(0)
      }, 500)
    }
  }

  // Handle save template
  const handleSaveTemplate = async () => {
    if (!user) {
      setShowAuthModal(true)
      return
    }

    const templateName = prompt('请输入模板名称:')
    if (templateName) {
      const { error, data } = await saveUserTemplate(user.id, {
        name: templateName,
        description: `${request.contentType} 模板`,
        contentType: request.contentType,
        stylePreferences: request.stylePreferences,
        keywords: request.keywords,
        aspectRatio: request.aspectRatio,
        specialRequirements: request.specialRequirements,
        promptTemplate: request.prompt,
      })

      if (error) {
        alert('保存失败: ' + error.message)
      } else {
        alert('模板保存成功!')
        
        // If we got data back (either from Supabase or mock), add it to userTemplates
        if (data) {
          // Check if it's already in the list (to avoid duplicates)
          setUserTemplates(prev => {
            if (prev.some(t => t.id === data.id)) {
              return prev
            }
            return [...prev, {
              id: data.id,
              name: data.name,
              description: data.description || '',
              category: 'user',
              contentType: data.content_type,
              stylePreferences: data.style_preferences || [],
              keywords: data.keywords || [],
              aspectRatio: data.aspect_ratio || '16:9',
              specialRequirements: data.special_requirements || [],
              promptTemplate: data.prompt_template || '',
            }]
          })
        } else {
          // Fallback: reload templates from database
          loadUserTemplates()
        }
      }
    }
  }

  // Handle download
  const handleDownload = async (image: GeneratedImage) => {
    try {
      const response = await fetch(image.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai-design-${image.id}.png`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  // Handle variation
  const handleVariation = (image: GeneratedImage) => {
    setRequest(prev => ({
      ...prev,
      prompt: `variation of: ${image.prompt}`,
    }))
  }

  // Handle favorite
  const handleFavorite = (image: GeneratedImage) => {
    console.log('Favorited:', image.id)
  }

  // Handle package download
  const handlePackageDownload = async () => {
    const selectedImages = generatedImages
    if (selectedImages.length === 0) {
      alert('请先选择要下载的图片')
      return
    }

    for (const img of selectedImages) {
      await handleDownload(img)
    }
  }

  // Handle feedback
  const handleFeedback = (feedback: string) => {
    console.log('Feedback:', feedback)
    alert('感谢您的反馈!')
  }

  // Handle template apply
  const handleApplyTemplate = (template: Template) => {
    setRequest({
      ...initialRequest,
      contentType: template.contentType,
      keywords: template.keywords,
      stylePreferences: template.stylePreferences,
      aspectRatio: template.aspectRatio,
      specialRequirements: template.specialRequirements,
      prompt: template.promptTemplate,
      aiPlatform: 'dalle',
    })
    setActiveTab('workspace')
  }

  // Handle template delete
  const handleDeleteTemplate = async (templateId: string) => {
    console.log('Deleting template:', templateId)
    if (!user) {
      console.log('No user logged in')
      return
    }
    
    try {
      // 先更新本地状态，给用户即时反馈
      setUserTemplates(prev => {
        const updated = prev.filter(t => t.id !== templateId)
        console.log('Updated templates locally:', updated)
        return updated
      })
      
      // 然后尝试调用Supabase API删除模板
      const { error } = await deleteUserTemplate(templateId, user.id)
      if (error) {
        console.error('Failed to delete template from database:', error)
        // 不回滚本地状态，保持用户体验一致性
      } else {
        console.log('Template deleted successfully from database')
      }
    } catch (err) {
      console.error('Error deleting template:', err)
    }
  }

  // Loading state
  if (brandLoading || authLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
          <span className="text-neutral-500">加载中...</span>
        </div>
      </div>
    )
  }

  // Error state
  if (brandError) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-h2 text-error mb-2">加载失败</h2>
          <p className="text-neutral-500">{brandError}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Custom Header with Auth */}
      <header className="fixed top-0 left-0 right-0 h-16 glass z-50">
        <div className="max-w-7xl mx-auto h-full px-4 lg:px-8 flex items-center justify-between">
          <Header activeTab={activeTab} onTabChange={setActiveTab} />
          
          {/* User Menu */}
          <div className="flex items-center gap-3">
            {!isConfigured && (
              <span className="text-caption text-warning bg-warning/20 px-2 py-1 rounded">
                演示模式
              </span>
            )}
            
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-small text-neutral-500">
                  <User className="w-4 h-4" />
                  <span className="hidden sm:inline">{user.email}</span>
                </div>
                <button
                  onClick={() => signOut()}
                  className="flex items-center gap-2 px-3 py-2 rounded-md text-small text-neutral-500 hover:bg-neutral-200 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">退出</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary-500 text-white text-small font-medium hover:bg-primary-600 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                <span>登录</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="pt-20 pb-8 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Workspace Tab */}
          {activeTab === 'workspace' && brandData && (
            <div className="space-y-6">
              {/* Project Selector */}
              <ProjectSelector
                projects={brandData.projects}
                selectedProject={selectedProject}
                onSelect={handleProjectSelect}
                onDelete={handleDeleteProject}
                onAddNew={handleAddNewProject}
              />

              {/* Main Workspace */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Generation Form - Left */}
                <div className="lg:col-span-3">
                  <div className="bg-neutral-100 rounded-lg border border-neutral-300 p-6">
                    <h2 className="text-h2 text-neutral-600 mb-6">生成需求</h2>
                    <GenerationForm
                      contentTypes={brandData.content_types}
                      stylePreferences={brandData.style_preferences}
                      aspectRatios={brandData.aspect_ratios}
                      specialRequirements={brandData.special_requirements}
                      request={request}
                      onRequestChange={setRequest}
                    />
                  </div>
                </div>

                {/* Prompt Preview - Right */}
                <div className="lg:col-span-2">
                  <PromptPreview
                    platforms={brandData.ai_platforms}
                    selectedPlatform={request.aiPlatform}
                    onPlatformChange={handlePlatformChange}
                    prompt={request.prompt}
                    onPromptChange={handlePromptChange}
                    onGenerate={handleGenerate}
                    onSaveTemplate={handleSaveTemplate}
                    isGenerating={isGenerating}
                  />
                </div>
              </div>

              {/* Results Grid */}
              <div>
                <h2 className="text-h2 text-neutral-600 mb-4">生成结果</h2>
                <ResultsGrid
                  images={generatedImages}
                  isLoading={isGenerating}
                  progress={progress}
                  onDownload={handleDownload}
                  onVariation={handleVariation}
                  onFavorite={handleFavorite}
                  onPackageDownload={handlePackageDownload}
                  onFeedback={handleFeedback}
                />
              </div>
            </div>
          )}

          {/* Templates Tab */}
          {activeTab === 'templates' && (
            <div>
              <h1 className="text-h1 text-neutral-600 mb-6">模板库</h1>
              
              {/* User Templates */}
              {user && userTemplates.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-h2 text-neutral-600 mb-4">我的模板</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                    {userTemplates.map(template => {
                      // Map content type to appropriate icon (same as in TemplateLibrary)
                      const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
                        booth: Layout,
                        signage: Signpost,
                        poster: Image,
                        merchandise: Gift,
                        mood: Palette,
                      };
                      const IconComponent = iconMap[template.contentType] || Image;
                      
                      return (
                        <div
                          key={template.id}
                          className="card group cursor-pointer"
                          onClick={() => handleApplyTemplate(template)}
                        >
                          {/* Template Preview */}
                          <div className="aspect-video bg-gradient-to-br from-primary-50 to-secondary-50 rounded-lg mb-4 flex items-center justify-center">
                            <IconComponent className="w-12 h-12 text-primary-500/50" />
                          </div>

                          {/* Template Info */}
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <Tag className="w-4 h-4 text-primary-500" />
                              <span className="text-caption text-neutral-500">
                                {template.category || template.contentType}
                              </span>
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

                          {/* Action Buttons */}
                          <div className="mt-4 flex gap-2">
                            <button
                              className="flex-1 btn-secondary h-10 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleApplyTemplate(template);
                              }}
                            >
                              <Zap className="w-4 h-4" />
                              <span>快速应用</span>
                            </button>
                            <button
                              className="btn-danger h-10 w-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteTemplate(template.id);
                              }}
                              title="删除模板"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              
              <h2 className="text-h2 text-neutral-600 mb-4">预设模板</h2>
              <TemplateLibrary onApplyTemplate={handleApplyTemplate} />
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                  <h1 className="text-h1 text-neutral-600">历史记录</h1>
                  {history.length > 0 && (
                    <button
                      onClick={async () => {
                        await clearGenerationHistory(user?.id)
                        setHistory([])
                      }}
                      className="btn-ghost h-10 px-4 text-small flex items-center gap-2 text-error hover:text-error"
                    >
                      <Trash2 className="w-4 h-4" />
                      清空历史
                    </button>
                  )}
                </div>

              {!user && (
                <div className="bg-info/20 border border-info/50 rounded-lg p-4 mb-6 flex items-center justify-between">
                  <p className="text-small text-info">
                    登录后可永久保存生成历史记录
                  </p>
                  <button
                    onClick={() => setShowAuthModal(true)}
                    className="btn-secondary h-8 px-4 text-small"
                  >
                    登录
                  </button>
                </div>
              )}

              {history.length === 0 ? (
                <div className="bg-neutral-100 rounded-lg border border-neutral-300 p-8">
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="w-16 h-16 rounded-full bg-neutral-200 flex items-center justify-center mb-4">
                      <Clock className="w-8 h-8 text-neutral-400" />
                    </div>
                    <h3 className="text-h3 text-neutral-600 mb-2">暂无历史记录</h3>
                    <p className="text-small text-neutral-500">
                      生成的图像将会显示在这里
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                  {history.map(image => (
                    <div
                      key={image.id}
                      className="group bg-neutral-100 rounded-lg overflow-hidden border border-neutral-300 hover:border-neutral-400 transition-all"
                    >
                      <div className="aspect-square bg-neutral-200 relative">
                        <img
                          src={image.url}
                          alt="Generated"
                          className="w-full h-full object-cover"
                        />
                        <button
                          onClick={() => handleDownload(image)}
                          className="absolute top-2 right-2 w-8 h-8 rounded-lg bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="p-3">
                        <p className="text-caption text-neutral-500 line-clamp-2 mb-2">
                          {image.prompt.substring(0, 50)}...
                        </p>
                        <p className="text-caption text-neutral-400">
                          {new Date(image.timestamp).toLocaleString('zh-CN')}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div>
              <h1 className="text-h1 text-neutral-600 mb-6">设置</h1>
              <div className="bg-neutral-100 rounded-lg border border-neutral-300 p-6 max-w-2xl">
                <h2 className="text-h3 text-neutral-600 mb-4">API配置</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-small font-medium text-neutral-600 mb-2">
                      Supabase URL
                    </label>
                    <input
                      type="text"
                      placeholder="https://your-project.supabase.co"
                      className="w-full input-field"
                      disabled
                      value={import.meta.env.VITE_SUPABASE_URL || '未配置'}
                    />
                  </div>
                  <div>
                    <label className="block text-small font-medium text-neutral-600 mb-2">
                      API 状态
                    </label>
                    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-small ${
                      isSupabaseConfigured()
                        ? 'bg-success/20 text-success'
                        : 'bg-warning/20 text-warning'
                    }`}>
                      <div className={`w-2 h-2 rounded-full ${
                        isSupabaseConfigured() ? 'bg-success' : 'bg-warning'
                      }`} />
                      {isSupabaseConfigured() ? '已连接' : '演示模式'}
                    </div>
                  </div>
                </div>

                {user && (
                  <div className="mt-8 pt-6 border-t border-neutral-300">
                    <h2 className="text-h3 text-neutral-600 mb-4">账户信息</h2>
                    <div className="space-y-2">
                      <p className="text-small text-neutral-500">
                        邮箱: {user.email}
                      </p>
                      <p className="text-small text-neutral-500">
                        用户ID: {user.id}
                      </p>
                    </div>
                  </div>
                )}

                <div className="mt-8 pt-6 border-t border-neutral-300">
                  <h2 className="text-h3 text-neutral-600 mb-4">关于</h2>
                  <p className="text-small text-neutral-500">
                    AI设计师工作台 v1.0.0<br />
                    一站式AI图像生成工作流平台
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </div>
  )
}

export default App
