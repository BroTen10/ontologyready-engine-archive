import { supabase, isSupabaseConfigured } from './supabase'
import type { GeneratedImage, Template } from '@/types'

// Generation History Service
export async function saveGenerationHistory(data: {
  userId?: string
  projectId?: string
  contentType: string
  keywords: string[]
  stylePreferences: string[]
  aspectRatio: string
  specialRequirements: string[]
  aiPlatform: string
  prompt: string
  resultImages: string[]
  status: string
}) {
  if (!isSupabaseConfigured()) {
    console.log('Demo mode: Skipping save to database')
    return { data: null, error: null }
  }

  const { data: result, error } = await supabase
    .from('generation_history')
    .insert({
      user_id: data.userId,
      project_id: data.projectId,
      content_type: data.contentType,
      keywords: data.keywords,
      style_preferences: data.stylePreferences,
      aspect_ratio: data.aspectRatio,
      special_requirements: data.specialRequirements,
      ai_platform: data.aiPlatform,
      prompt: data.prompt,
      result_images: data.resultImages,
      status: data.status,
    })
    .select()
    .maybeSingle()

  return { data: result, error }
}

export async function getGenerationHistory(userId?: string, limit = 50) {
  if (!isSupabaseConfigured()) {
    return { data: [], error: null }
  }

  let query = supabase
    .from('generation_history')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit)

  if (userId) {
    query = query.eq('user_id', userId)
  }

  const { data, error } = await query

  return { data: data || [], error }
}

export async function clearGenerationHistory(userId?: string) {
  if (!isSupabaseConfigured()) {
    console.log('Demo mode: Skipping clear history from database')
    return { error: null }
  }

  let query = supabase
    .from('generation_history')
    .delete()

  if (userId) {
    query = query.eq('user_id', userId)
  }

  const { error } = await query

  return { error }
}

// User Templates Service
export async function saveUserTemplate(userId: string, template: {
  name: string
  description?: string
  contentType: string
  stylePreferences: string[]
  keywords: string[]
  aspectRatio: string
  specialRequirements: string[]
  promptTemplate: string
}) {
  console.log('Template save requested:', template.name)
  
  if (!isSupabaseConfigured()) {
    console.log('Demo mode: Skipping save to database')
    // 演示模式下返回模拟成功数据
    return { 
      data: {
        id: `template-${Date.now()}`,
        user_id: userId,
        name: template.name,
        description: template.description,
        content_type: template.contentType,
        style_preferences: template.stylePreferences,
        keywords: template.keywords,
        aspect_ratio: template.aspectRatio,
        special_requirements: template.specialRequirements,
        prompt_template: template.promptTemplate,
        created_at: new Date().toISOString()
      }, 
      error: null 
    }
  }

  // 实际调用Supabase API保存模板
  const { data: result, error } = await supabase
    .from('user_templates')
    .insert({
      user_id: userId,
      name: template.name,
      description: template.description,
      content_type: template.contentType,
      style_preferences: template.stylePreferences,
      keywords: template.keywords,
      aspect_ratio: template.aspectRatio,
      special_requirements: template.specialRequirements,
      prompt_template: template.promptTemplate,
    })
    .select()
    .maybeSingle()

  return { data: result, error }
}

export async function getUserTemplates(userId: string) {
  if (!isSupabaseConfigured()) {
    return { data: [], error: null }
  }

  const { data, error } = await supabase
    .from('user_templates')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  return { data: data || [], error }
}

export async function deleteUserTemplate(templateId: string, userId: string) {
  console.log('deleteUserTemplate called with:', {
    templateId,
    userId,
    isConfigured: isSupabaseConfigured()
  })
  
  if (!isSupabaseConfigured()) {
    console.log('Demo mode: returning success without deletion')
    // In demo mode, just return success (no actual deletion)
    return { error: null }
  }

  try {
    console.log('Attempting to delete template from Supabase')
    const { error } = await supabase
      .from('user_templates')
      .delete()
      .eq('id', templateId)
      .eq('user_id', userId)
    
    console.log('Delete operation result:', { error })
    
    return { error }
  } catch (err) {
    console.error('Unexpected error in deleteUserTemplate:', err)
    return { error: err as Error }
  }
}

// Get image dimensions based on aspect ratio
function getImageDimensions(aspectRatio: string): { width: number, height: number } {
  switch (aspectRatio) {
    case '16:9': return { width: 1792, height: 1024 }
    case '9:16': return { width: 1024, height: 1792 }
    case '3:4': return { width: 768, height: 1024 }
    case '4:3': return { width: 1024, height: 768 }
    case '1:1':
    default: return { width: 1024, height: 1024 }
  }
}

// Generate AI images using Pollinations.ai (free, no API key required)
async function generateWithPollinations(prompt: string, aspectRatio: string, count: number): Promise<string[]> {
  const { width, height } = getImageDimensions(aspectRatio)
  const images: string[] = []
  
  for (let i = 0; i < count; i++) {
    // Add unique seed to get different variations
    const uniquePrompt = `${prompt}, variation ${i + 1}, seed:${Date.now() + i}`
    const encodedPrompt = encodeURIComponent(uniquePrompt)
    // Pollinations.ai provides free AI image generation with FLUX model
    const imageUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&nologo=true&seed=${Date.now() + i}`
    images.push(imageUrl)
  }
  
  return images
}

// AI Image Generation Service
export async function generateImages(params: {
  prompt: string
  platform: string
  aspectRatio: string
  count?: number
}): Promise<{ images: string[], error: Error | null }> {
  const count = params.count || 4
  
  // Try to use Supabase Edge Function if configured
  if (isSupabaseConfigured()) {
    try {
      const { data, error } = await supabase.functions.invoke('generate-image', {
        body: {
          prompt: params.prompt,
          platform: params.platform,
          aspectRatio: params.aspectRatio,
          count: count,
        },
      })

      if (!error && data?.data?.images && data.data.images.length > 0) {
        return { images: data.data.images, error: null }
      }
    } catch (err) {
      console.error('Edge function error:', err)
    }
  }

  // Use Pollinations.ai for real AI image generation (free, no API key)
  // This works in both demo mode and as fallback
  console.log('Using Pollinations.ai for AI image generation')
  
  try {
    const images = await generateWithPollinations(params.prompt, params.aspectRatio, count)
    return { images, error: null }
  } catch (err) {
    console.error('Pollinations error:', err)
    // Ultimate fallback to placeholder images
    const images = Array.from({ length: count }, (_, i) => 
      `https://picsum.photos/seed/${Date.now() + i}/800/800`
    )
    return { images, error: err as Error }
  }
}

// Preset Templates (from database or static)
export async function getPresetTemplates(): Promise<Template[]> {
  if (isSupabaseConfigured()) {
    const { data, error } = await supabase
      .from('generation_templates')
      .select('*')
      .eq('is_preset', true)
      .order('created_at', { ascending: false })

    if (!error && data && data.length > 0) {
      return data.map(t => ({
        id: t.id,
        name: t.name,
        description: t.description || '',
        category: t.category || '',
        contentType: t.content_type,
        stylePreferences: t.style_preferences || [],
        keywords: t.keywords || [],
        aspectRatio: t.aspect_ratio || '16:9',
        specialRequirements: t.special_requirements || [],
        promptTemplate: t.prompt_template || '',
      }))
    }
  }

  // Return static templates if database not available
  return [
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
}
