import { atom } from 'tldraw'

import { loadModelPaths, readUserJson, writeUserJson } from './comfy'
import { t } from './i18n'

export interface ModelDef {
  id: string
  label: string
  desc: string
  files: string[]
  video?: boolean
  refs?: 'qwen' | 'latent'
  prompt?: string
  seed?: [string, string]
  steps?: [string, Record<string, number>]
  sizes?: string[]
  vae?: string
  caption?: string
  control?: string
}

export type ModelModality = 'image' | 'video' | 'speech' | 'music' | 'model'
export interface ModelStatus {
  id: string
  available: boolean
  missing: string[]
  capabilities: Record<string, unknown>
}

export const IMAGE_MODELS: ModelDef[] = [
  {
    id: 'qwen-image-2.1-t2i.api.json', label: 'Qwen Image 2.1', desc: t('models.highOverallQualityAccurateChinese'), files: ['qwen_image_2.1_int8_convrot.safetensors'],
    refs: 'qwen', prompt: 'prompt', seed: ['7', 'seed'], steps: ['7', { fast: 12, standard: 25, high: 40 }], sizes: ['5'], vae: '4',
  },
  {
    id: 'z-image-turbo-t2i.api.json', label: 'Z-Image Turbo', desc: t('models.fast8StepGenerationGreat'), files: ['z_image_turbo_bf16.safetensors'],
    prompt: 'text', seed: ['7', 'seed'], sizes: ['5'], vae: '3',
  },
  {
    id: 'flux2-klein-9b-t2i.api.json', label: 'Flux.2 Klein 9B', desc: t('models.fast4StepGenerationSupports'), files: ['flux-2-klein-9b-nvfp4.safetensors'],
    refs: 'latent', prompt: 'text', seed: ['14', 'noise_seed'], sizes: ['5', '13'], vae: '3',
  },
  {
    id: 'qwen-image-2512-t2i.api.json', label: 'Qwen Image 2512', desc: t('models.solidDetailAndCompositionSupports'), files: ['qwen_image_2512_fp8_e4m3fn.safetensors'],
    prompt: 'text', seed: ['7', 'seed'], steps: ['7', { fast: 20, standard: 30, high: 50 }], sizes: ['5'], vae: '3', control: 'Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors',
  },
  {
    id: 'ideogram4-t2i.api.json', label: 'Ideogram 4', desc: t('models.greatAtLayoutLogosAnd'), files: ['ideogram4_fp8_scaled.safetensors', 'ideogram4_unconditional_fp8_scaled.safetensors'],
    prompt: 'text', caption: 'ideogram4-caption.json',
    seed: ['14', 'noise_seed'], steps: ['13', { fast: 12, standard: 20, high: 48 }], sizes: ['5', '13'], vae: '3',
  },
  {
    id: 'krea2-turbo-t2i.api.json', label: 'Krea2 Turbo', desc: 'Krea2 Turbo', files: [],
    prompt: 'text', seed: ['7', 'seed'], steps: ['7', { fast: 6, standard: 10, high: 15 }], sizes: ['5'], vae: '4',
  },
]

export const VIDEO_MODELS: ModelDef[] = [
  { id: 't2v-minimax-h3.api.json', label: 'MiniMax H3', desc: t('models.syncedAudioAndVideoSupports'), files: ['minimax_h3_fl2va_pruned_int8_convrot.safetensors'], video: true },
]

export const SPEECH_MODELS: ModelDef[] = [
  { id: 'speech-drama3.api.json', label: 'Fish Audio Drama3', desc: t('models.drama3'), files: [] },
  { id: 'speech-kokoro.api.json', label: 'Kokoro', desc: t('audio.voiceover'), files: [] },
  { id: 'voice-clone-indextts.api.json', label: 'IndexTTS', desc: t('audio.cloneSelected'), files: [] },
]
export const MUSIC_MODELS: ModelDef[] = [
  { id: 'music-yue2.api.json', label: 'YuE2', desc: t('models.yue2'), files: [] },
  { id: 'music-ace-step.api.json', label: 'ACE Step', desc: t('audio.music'), files: [] },
  { id: 'sfx-stable-audio.api.json', label: 'Stable Audio', desc: t('audio.soundEffect'), files: [] },
]
export const MODEL_MODELS: ModelDef[] = [
  { id: 'image-to-3d-trellis2.api.json', label: 'Trellis2', desc: t('models.trellis2'), files: [] },
]
export const MODEL_GROUPS: Record<ModelModality, ModelDef[]> = {
  image: IMAGE_MODELS, video: VIDEO_MODELS, speech: SPEECH_MODELS, music: MUSIC_MODELS, model: MODEL_MODELS,
}
export const MODEL_MODALITIES: ModelModality[] = ['image', 'video', 'speech', 'music', 'model']
export const ALL_MODELS = Object.values(MODEL_GROUPS).flat()

export const isVideo = (workflow: string) => VIDEO_MODELS.some((m) => m.id === workflow)
export const modelOf = (workflow: string) => ALL_MODELS.find((m) => m.id === workflow)

export interface ModelPrefs { auto: boolean; enabled: string[] }

const FILE = 'comfyart/models.json'
const ALL = ALL_MODELS.map((m) => m.id)

export const modelPrefsAtom = atom<ModelPrefs>('model prefs', { auto: true, enabled: ALL })
export const installedAtom = atom<string[] | null>('installed models', null)
export const modelStatusAtom = atom<ModelStatus[]>('model status', [])

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)

export function parseModelCatalog(value: unknown): ModelStatus[] {
  if (!isRecord(value) || !Array.isArray(value.models)) throw new Error('Invalid model catalog')
  return value.models.map((item: unknown) => {
    if (!isRecord(item) || typeof item.id !== 'string' || typeof item.available !== 'boolean' ||
      !Array.isArray(item.missing) || !item.missing.every((x: unknown) => typeof x === 'string')) throw new Error('Invalid model status')
    return { id: item.id, available: item.available, missing: item.missing, capabilities: isRecord(item.capabilities) ? item.capabilities : {} }
  })
}

export async function loadModels() {
  const [prefs, response] = await Promise.all([readUserJson<ModelPrefs | null>(FILE, null), fetch('/comfyart/model-catalog'), loadModelPaths()])
  if (prefs) modelPrefsAtom.set(prefs)
  if (!response.ok) { installedAtom.set([]); throw new Error(t('models.catalogFailed')) }
  const statuses = parseModelCatalog(await response.json())
  modelStatusAtom.set(statuses)
  installedAtom.set(statuses.filter((m) => m.available).map((m) => m.id))
}

export async function saveModelPrefs(prefs: ModelPrefs) {
  modelPrefsAtom.set(prefs)
  await writeUserJson(FILE, prefs)
}

export function installedModels(group: boolean | ModelModality): ModelDef[] {
  return MODEL_GROUPS[typeof group === 'boolean' ? group ? 'video' : 'image' : group].filter((m) => isInstalled(m.id))
}

export function agentModels(group: boolean | ModelModality): ModelDef[] {
  const { auto, enabled } = modelPrefsAtom.get()
  const list = installedModels(group)
  return auto ? list : list.filter((m) => enabled.includes(m.id))
}

export function isInstalled(id: string): boolean {
  const installed = installedAtom.get()
  return !!installed?.includes(id)
}

export function modelMissing(id: string): string[] {
  return modelStatusAtom.get().find((m) => m.id === id)?.missing ?? [t('models.notChecked')]
}

export function requireModel(group: ModelModality, id?: string, accept: (model: ModelDef) => boolean = () => true): ModelDef {
  const choices = id ? installedModels(group) : agentModels(group)
  const model = choices.find((m) => (!id || m.id === id) && accept(m))
  if (!model) throw new Error(id ? `${modelOf(id)?.label ?? id}: ${modelMissing(id).join('; ') || t('models.disabled')}` : t('models.noneAvailable', group))
  return model
}

export function modelCapability(id: string, name: string): boolean {
  const value = modelStatusAtom.get().find((m) => m.id === id)?.capabilities[name]
  return isInstalled(id) && (value === true || typeof value === 'number' && value > 0)
}

export function modelReferenceLimit(id: string, name: string, maximum: number): number {
  if (!modelCapability(id, name)) return 0
  const value = modelStatusAtom.get().find((m) => m.id === id)?.capabilities[name]
  return typeof value === 'number' ? Math.max(0, Math.min(maximum, Math.floor(value))) : maximum
}
