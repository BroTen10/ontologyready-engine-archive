import type { ImageGeneratorDefinition } from './types'

function getImageDimensions(aspectRatio: string): { width: number; height: number } {
  switch (aspectRatio) {
    case '16:9': return { width: 1792, height: 1024 }
    case '9:16': return { width: 1024, height: 1792 }
    case '3:4': return { width: 768, height: 1024 }
    case '4:3': return { width: 1024, height: 768 }
    case '1:1':
    default: return { width: 1024, height: 1024 }
  }
}

export const pollinationsGenerator: ImageGeneratorDefinition = {
  id: 'pollinations',
  name: 'Pollinations.ai',
  description: '免费AI图像生成（默认，无需API密钥）',
  configFields: [],
  async generate(params, _config) {
    const { width, height } = getImageDimensions(params.aspectRatio)
    const images: string[] = []

    for (let i = 0; i < params.count; i++) {
      const uniquePrompt = `${params.prompt}, variation ${i + 1}, seed:${Date.now() + i}`
      const encodedPrompt = encodeURIComponent(uniquePrompt)
      const imageUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&nologo=true&seed=${Date.now() + i}`
      images.push(imageUrl)
    }

    return { images }
  },
}
