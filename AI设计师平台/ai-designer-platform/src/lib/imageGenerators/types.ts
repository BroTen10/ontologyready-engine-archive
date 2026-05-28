export interface ConfigField {
  key: string
  label: string
  type: 'text' | 'password' | 'select'
  required: boolean
  placeholder?: string
  options?: { label: string; value: string }[]
}

export interface GenerateParams {
  prompt: string
  aspectRatio: string
  count: number
}

export interface GenerateResult {
  images: string[]
  error?: Error
}

export interface ImageGeneratorDefinition {
  id: string
  name: string
  description: string
  configFields: ConfigField[]
  generate(params: GenerateParams, config?: Record<string, string>): Promise<GenerateResult>
}

export interface GeneratorInstanceConfig {
  id: string
  label?: string
  config: Record<string, string>
}
