import type { Project, GenerationRequest } from '@/types'

interface PromptConfig {
  projectContext: string
  contentType: string
  keywords: string[]
  stylePreferences: string[]
  aspectRatio: string
  specialRequirements: string[]
  description: string
  brandColors: {
    primary: string
    secondary: string
    accent: string
  }
}

// Content type descriptions for different AI platforms
const contentTypeDescriptions: Record<string, Record<string, string>> = {
  booth: {
    dalle: 'exhibition booth design, 3D architectural visualization, trade show display',
    midjourney: 'exhibition booth design --v 6 --style raw, architectural visualization, trade show',
    'stable-diffusion': 'exhibition booth, 3D render, architectural visualization, trade show display',
    tongyi: '展台设计效果图,3D建筑可视化,展会展示设计',
  },
  signage: {
    dalle: 'wayfinding signage system, environmental graphics, directional signs',
    midjourney: 'signage system design --v 6, wayfinding graphics, environmental design',
    'stable-diffusion': 'signage system, wayfinding design, environmental graphics',
    tongyi: '导视系统设计,环境图形,指示牌设计',
  },
  poster: {
    dalle: 'promotional poster design, key visual, graphic design, marketing material',
    midjourney: 'poster design --v 6 --ar 2:3, key visual, graphic design composition',
    'stable-diffusion': 'promotional poster, key visual design, graphic design, marketing',
    tongyi: '宣传海报设计,主视觉设计,平面设计',
  },
  merchandise: {
    dalle: 'cultural creative merchandise, product design, branded items, souvenirs',
    midjourney: 'merchandise design --v 6, product mockup, branded items, souvenirs',
    'stable-diffusion': 'merchandise design, product visualization, branded items',
    tongyi: '文创产品设计,品牌衍生品,纪念品设计',
  },
  mood: {
    dalle: 'mood board, atmosphere reference, ambient environment, design inspiration',
    midjourney: 'mood board --v 6 --style raw, atmospheric scene, ambient lighting',
    'stable-diffusion': 'mood board, atmosphere reference, ambient design, inspiration',
    tongyi: '氛围参考图,环境氛围,设计灵感板',
  },
}

// Style preference translations
const styleTranslations: Record<string, Record<string, string>> = {
  minimalist: {
    dalle: 'minimalist design, clean aesthetic, simple geometric forms',
    midjourney: 'minimalist --v 6, clean lines, simple forms',
    'stable-diffusion': 'minimalist, clean design, simple aesthetic',
    tongyi: '极简主义,简洁设计,干净利落',
  },
  cyberpunk: {
    dalle: 'cyberpunk aesthetic, neon lights, futuristic technology, dark atmosphere',
    midjourney: 'cyberpunk --v 6, neon glow, futuristic, dark tech',
    'stable-diffusion': 'cyberpunk, neon lights, futuristic technology',
    tongyi: '赛博朋克风格,霓虹灯光,未来科技感',
  },
  organic: {
    dalle: 'organic design, natural forms, biophilic elements, flowing curves',
    midjourney: 'organic design --v 6, natural forms, biophilic',
    'stable-diffusion': 'organic shapes, natural design, flowing forms',
    tongyi: '自然有机风格,生态设计,流动曲线',
  },
  guochao: {
    dalle: 'Chinese traditional aesthetics, national trend design, cultural heritage elements',
    midjourney: 'Chinese traditional style --v 6, guochao design, cultural elements',
    'stable-diffusion': 'Chinese traditional, guochao style, cultural design',
    tongyi: '国潮风格,中国传统美学,文化元素融合',
  },
  industrial: {
    dalle: 'industrial design, raw materials, metal and concrete, factory aesthetic',
    midjourney: 'industrial style --v 6, raw materials, factory aesthetic',
    'stable-diffusion': 'industrial design, metal concrete, raw aesthetic',
    tongyi: '工业风格,原始材质,金属混凝土',
  },
  futuristic: {
    dalle: 'futuristic design, advanced technology, sleek surfaces, sci-fi aesthetic',
    midjourney: 'futuristic --v 6, sci-fi design, advanced tech',
    'stable-diffusion': 'futuristic, sci-fi aesthetic, advanced technology',
    tongyi: '未来主义风格,科幻设计,先进科技感',
  },
  retro: {
    dalle: 'retro design, vintage aesthetic, nostalgic elements, classic style',
    midjourney: 'retro style --v 6, vintage aesthetic, nostalgic',
    'stable-diffusion': 'retro design, vintage, nostalgic aesthetic',
    tongyi: '复古风格,怀旧设计,经典美学',
  },
  tech: {
    dalle: 'high-tech design, digital aesthetic, modern technology, innovation',
    midjourney: 'high-tech --v 6, digital design, modern technology',
    'stable-diffusion': 'high-tech, digital aesthetic, modern innovation',
    tongyi: '科技感设计,数字美学,现代创新',
  },
}

// Special requirement translations
const requirementTranslations: Record<string, Record<string, string>> = {
  whitespace: {
    dalle: 'with empty space for text placement, negative space design',
    midjourney: 'with text placement area --v 6, negative space',
    'stable-diffusion': 'with empty space for text, negative space',
    tongyi: '预留文字放置区域,负空间设计',
  },
  'multi-angle': {
    dalle: 'multiple viewing angles, different perspectives',
    midjourney: 'multiple angles --v 6, different perspectives',
    'stable-diffusion': 'multiple angles, various perspectives',
    tongyi: '多角度展示,不同视角',
  },
  'high-detail': {
    dalle: 'highly detailed, 8K resolution, intricate details',
    midjourney: 'highly detailed --v 6 --q 2, 8K, intricate',
    'stable-diffusion': 'highly detailed, 8K resolution, intricate',
    tongyi: '高清细节,8K分辨率,精致细腻',
  },
  seamless: {
    dalle: 'seamless pattern, tileable design',
    midjourney: 'seamless pattern --v 6 --tile',
    'stable-diffusion': 'seamless, tileable pattern',
    tongyi: '无缝拼接,可平铺设计',
  },
  transparent: {
    dalle: 'transparent background, isolated subject',
    midjourney: 'transparent background --v 6',
    'stable-diffusion': 'transparent background, isolated',
    tongyi: '透明背景,主体分离',
  },
}

// Aspect ratio parameters for different platforms
const aspectRatioParams: Record<string, Record<string, string>> = {
  '16:9': {
    dalle: '',
    midjourney: '--ar 16:9',
    'stable-diffusion': '',
    tongyi: '',
  },
  '9:16': {
    dalle: '',
    midjourney: '--ar 9:16',
    'stable-diffusion': '',
    tongyi: '',
  },
  '1:1': {
    dalle: '',
    midjourney: '--ar 1:1',
    'stable-diffusion': '',
    tongyi: '',
  },
  '3:4': {
    dalle: '',
    midjourney: '--ar 3:4',
    'stable-diffusion': '',
    tongyi: '',
  },
  '4:3': {
    dalle: '',
    midjourney: '--ar 4:3',
    'stable-diffusion': '',
    tongyi: '',
  },
}

export function buildPrompt(
  config: PromptConfig,
  platform: string
): string {
  const parts: string[] = []

  // 1. Content type base description
  const contentDesc = contentTypeDescriptions[config.contentType]?.[platform] || config.contentType
  parts.push(contentDesc)

  // 2. Add style preferences
  const styles = config.stylePreferences
    .map(style => styleTranslations[style]?.[platform] || style)
    .join(', ')
  if (styles) {
    parts.push(styles)
  }

  // 3. Add keywords
  if (config.keywords.length > 0) {
    parts.push(config.keywords.join(', '))
  }

  // 4. Add brand colors context
  if (config.brandColors.primary) {
    const colorContext = platform === 'tongyi'
      ? `主色调${config.brandColors.primary},辅助色${config.brandColors.secondary}`
      : `primary color ${config.brandColors.primary}, secondary color ${config.brandColors.secondary}`
    parts.push(colorContext)
  }

  // 5. Add user description
  if (config.description) {
    parts.push(config.description)
  }

  // 6. Add special requirements
  const requirements = config.specialRequirements
    .map(req => requirementTranslations[req]?.[platform] || req)
    .join(', ')
  if (requirements) {
    parts.push(requirements)
  }

  // 7. Add project context
  if (config.projectContext) {
    parts.push(platform === 'tongyi' ? `项目背景: ${config.projectContext}` : `context: ${config.projectContext}`)
  }

  // Build base prompt
  let prompt = parts.filter(Boolean).join(', ')

  // 8. Add aspect ratio for Midjourney
  if (platform === 'midjourney') {
    const arParam = aspectRatioParams[config.aspectRatio]?.midjourney || ''
    if (arParam && !prompt.includes('--ar')) {
      prompt = `${prompt} ${arParam}`
    }
  }

  // 9. Add quality modifiers
  if (platform === 'dalle') {
    prompt = `${prompt}, professional quality, high resolution, detailed rendering`
  } else if (platform === 'midjourney' && !prompt.includes('--v')) {
    prompt = `${prompt} --v 6 --q 2`
  } else if (platform === 'stable-diffusion') {
    prompt = `${prompt}, masterpiece, best quality, highly detailed`
  }

  return prompt
}

export function generatePromptFromRequest(
  request: GenerationRequest,
  project: Project | null
): string {
  const config: PromptConfig = {
    projectContext: project?.description || '',
    contentType: request.contentType,
    keywords: request.keywords,
    stylePreferences: request.stylePreferences,
    aspectRatio: request.aspectRatio,
    specialRequirements: request.specialRequirements,
    description: request.description,
    brandColors: {
      primary: project?.brand_profile?.primary_color || '',
      secondary: project?.brand_profile?.secondary_color || '',
      accent: project?.brand_profile?.accent_color || '',
    },
  }

  return buildPrompt(config, request.aiPlatform)
}
