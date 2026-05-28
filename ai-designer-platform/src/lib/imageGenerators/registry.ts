import type { ImageGeneratorDefinition, GenerateParams, GenerateResult, GeneratorInstanceConfig } from './types'
import { pollinationsGenerator } from './pollinations'
import { customApiGenerator } from './customApi'

// Built-in generator definitions
const builtinGenerators: ImageGeneratorDefinition[] = [
  pollinationsGenerator,
  customApiGenerator,
]

// Registry — map id -> definition
const registry = new Map<string, ImageGeneratorDefinition>()
for (const g of builtinGenerators) {
  registry.set(g.id, g)
}

/** Register a custom generator at runtime */
export function registerGenerator(def: ImageGeneratorDefinition) {
  registry.set(def.id, def)
}

/** Get all registered generator definitions */
export function getAllGenerators(): ImageGeneratorDefinition[] {
  return Array.from(registry.values())
}

/** Get a single generator definition by id */
export function getGenerator(id: string): ImageGeneratorDefinition | undefined {
  return registry.get(id)
}

/** Run generation using a specific generator and its stored config */
export async function generateWithGenerator(
  generatorId: string,
  params: GenerateParams,
  instanceConfig?: GeneratorInstanceConfig,
): Promise<GenerateResult> {
  const def = registry.get(generatorId)
  if (!def) {
    return { images: [], error: new Error(`未知的图片生成器: ${generatorId}`) }
  }

  try {
    const result = await def.generate(params, instanceConfig?.config)
    return result
  } catch (err) {
    return { images: [], error: err instanceof Error ? err : new Error(String(err)) }
  }
}

export type { ImageGeneratorDefinition, GenerateParams, GenerateResult, GeneratorInstanceConfig }
