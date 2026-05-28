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

export const customApiGenerator: ImageGeneratorDefinition = {
  id: 'custom-api',
  name: '自定义API',
  description: '使用自定义图片生成API（兼容 OpenAI、Volcengine ARK、Stable Diffusion 等）',
  configFields: [
    {
      key: 'endpoint',
      label: 'API Endpoint',
      type: 'text',
      required: true,
      placeholder: 'https://api.openai.com/v1/images/generations',
    },
    {
      key: 'apiKey',
      label: 'API Key',
      type: 'password',
      required: true,
      placeholder: 'sk-... / ARK API Key',
    },
    {
      key: 'model',
      label: '模型名称',
      type: 'text',
      required: false,
      placeholder: 'dall-e-3 / doubao-seedream-5-0-260128',
    },
    {
      key: 'size',
      label: '尺寸参数（可选）',
      type: 'text',
      required: false,
      placeholder: '留空自动根据比例生成 (如 1792x1024)，固定值如 2K 则填 2K',
    },
    {
      key: 'extraBody',
      label: '额外请求参数（可选）',
      type: 'text',
      required: false,
      placeholder: 'JSON 格式，如 {"response_format":"url","watermark":true}',
    },
  ],
  async generate(params, config) {
    const endpoint = config?.endpoint || ''
    const apiKey = config?.apiKey || ''
    const model = config?.model || ''
    const sizeOverride = config?.size || ''
    const extraBodyRaw = config?.extraBody || ''

    if (!endpoint || !apiKey) {
      return {
        images: [],
        error: new Error('请先配置自定义API的Endpoint和API Key'),
      }
    }

    const { width, height } = getImageDimensions(params.aspectRatio)

    // Make parallel requests to the API (OpenAI-compatible format)
    try {
      // Make parallel requests for each image (some APIs don't support n>1)
      const requests = Array.from({ length: params.count }, async () => {
        const body: Record<string, unknown> = {
          model: model || 'dall-e-3',
          prompt: params.prompt,
          n: 1,
          size: sizeOverride || `${width}x${height}`,
        }

        // Parse and merge extra body parameters (user can override any field)
        if (extraBodyRaw) {
          try {
            const extra = JSON.parse(extraBodyRaw)
            Object.assign(body, extra)
          } catch {
            return { images: [], error: new Error('额外请求参数格式错误，请填写有效的 JSON') }
          }
        }

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
          },
          body: JSON.stringify(body),
        })

        if (!response.ok) {
          const errorText = await response.text()
          return { images: [], error: new Error(`API 请求失败 (${response.status}): ${errorText}`) }
        }

        const data = await response.json()

        // Handle OpenAI format — array of { url } or { b64_json }
        if (data.data && Array.isArray(data.data)) {
          const urls = data.data.map((item: { url?: string; b64_json?: string }) =>
            item.url || (item.b64_json ? `data:image/png;base64,${item.b64_json}` : '')
          ).filter(Boolean)
          return { images: urls, error: null }
        }

        // Handle custom format — try common response shapes
        if (data.url) return { images: [data.url], error: null }
        if (data.image_url) return { images: [data.image_url], error: null }
        if (data.output?.[0]) return { images: [data.output[0]], error: null }
        if (data.images?.[0]?.url) return { images: [data.images[0].url], error: null }

        return { images: [], error: new Error('无法从API响应中识别图片URL，请检查响应格式') }
      }).map(p => p.catch(err => ({ images: [], error: err instanceof Error ? err : new Error(String(err)) })))

      const results = await Promise.all(requests)
      const allImages = results.flatMap(r => r.images || [])
      const firstError = results.find(r => r.error)?.error || null

      if (allImages.length === 0 && firstError) {
        return { images: [], error: firstError }
      }

      return { images: allImages }
    } catch (err) {
      return { images: [], error: err instanceof Error ? err : new Error(String(err)) }
    }
  },
}
