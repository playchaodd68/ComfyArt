import { createShapeId, type Editor, type TLImageShape, type TLShapeId } from 'tldraw'

import { loadWorkflow } from './comfy'
import { freeSpot } from './generate'
import { registerPlacer, selectResults, spawnHolder, startJob, type ErrorSink } from './jobs'
import { AUDIO, AUDIO_SIZE, MODEL } from './shapes/EmbedShapes'
import { GENERATOR } from './shapes/GeneratorShape'
import { annotated, type Built } from './workflows'
import { t } from './i18n'
import { requireModel } from './models'

export const VOICES = ['zf_xiaoxiao', 'zf_xiaoyi', 'zf_xiaobei', 'zf_xiaoni', 'zm_yunxi', 'zm_yunjian', 'zm_yunyang', 'zm_yunxia', 'af_heart', 'af_bella', 'af_nicole', 'am_adam', 'am_michael', 'bf_emma', 'bm_george', 'jf_alpha', 'jm_kumo']
const LANGS: Record<string, string> = { a: 'English', b: 'English (British)', j: 'Japanese', z: 'Mandarin Chinese', e: 'Spanish', f: 'French', h: 'Hindi', i: 'Italian', p: 'Brazilian Portuguese' }
export const MUSIC_SECONDS = [15, 30, 60, 120]
export const SFX_SECONDS = [3, 5, 8, 15]
const MODEL_SIZE = 480
const GAP = 40

export type AudioSpec = (
  | { kind: 'music'; prompt: string; lyrics: string; seconds: number }
  | { kind: 'speech'; text: string; voice: string }
  | { kind: 'clone'; text: string; reference: string; transcript?: string }
  | { kind: 'sfx'; prompt: string; seconds: number }
) & { model?: string }

const seed = () => Math.floor(Math.random() * 2 ** 31)

async function audioGraph(spec: AudioSpec): Promise<Built> {
  const model = requireModel(spec.kind === 'music' || spec.kind === 'sfx' ? 'music' : 'speech', spec.model,
    (m) => spec.kind === 'sfx' ? m.id === 'sfx-stable-audio.api.json'
      : spec.kind === 'music' ? m.id !== 'sfx-stable-audio.api.json'
      : spec.kind === 'clone' ? m.id !== 'speech-kokoro.api.json' : m.id !== 'voice-clone-indextts.api.json')
  if (model.id === 'speech-drama3.api.json') {
    if (spec.kind !== 'speech' && spec.kind !== 'clone') throw new Error('Drama3 requires speech')
    const graph = await loadWorkflow(model.id)
    const entry = Object.entries(graph).find(([, node]) => node.class_type === 'Drama3Generate')
    const codec = Object.entries(graph).find(([, node]) => node.class_type === 'Drama3CodecLoader')
    const result = Object.entries(graph).find(([, node]) => node.class_type === 'SaveAudio' || node.class_type === 'SaveAudioAdvanced')
    if (!entry || !codec || !result) throw new Error('Invalid Drama3 workflow')
    Object.assign(entry[1].inputs, { text: spec.text, seed: seed() })
    if (spec.kind === 'clone') {
      if (!spec.transcript?.trim()) throw new Error(t('audio.transcriptRequired'))
      graph['ca-reference'] = { class_type: 'LoadAudio', inputs: { audio: annotated(spec.reference) } }
      graph['ca-voice'] = { class_type: 'Drama3EncodeVoice', inputs: { codec: [codec[0], 0], audio: ['ca-reference', 0], transcript: spec.transcript } }
      entry[1].inputs['voices.voice0'] = ['ca-voice', 0]
    }
    return { graph, result: result[0] }
  }
  if (model.id === 'music-yue2.api.json') {
    if (spec.kind !== 'music') throw new Error('YuE2 requires music')
    const graph = await loadWorkflow(model.id)
    const result = Object.entries(graph).find(([, node]) => node.class_type === 'SaveAudio' || node.class_type === 'SaveAudioAdvanced')
    if (!result) throw new Error('Invalid YuE2 workflow')
    for (const node of Object.values(graph)) {
      if (node.class_type === 'YuE2GenerateABC' || node.class_type === 'YuE2GenerateMusic') Object.assign(node.inputs, { style: spec.prompt, lyrics: spec.lyrics, seed: seed() })
      if (node.class_type === 'YuE2GenerateMusic') node.inputs.max_duration = spec.seconds
      if (node.class_type === 'KSampler') node.inputs.seed = seed()
    }
    return { graph, result: result[0] }
  }
  if (spec.kind === 'music') {
    const g = await loadWorkflow('music-ace-step.api.json')
    Object.assign(g['3'].inputs, { tags: spec.prompt, lyrics: spec.lyrics || '[instrumental]' })
    g['5'].inputs.seconds = spec.seconds
    g['6'].inputs.seed = seed()
    return { graph: g, result: '8' }
  }
  if (spec.kind === 'sfx') {
    const g = await loadWorkflow('sfx-stable-audio.api.json')
    g['3'].inputs.text = spec.prompt
    g['5'].inputs.seconds = spec.seconds
    g['6'].inputs.seed = seed()
    return { graph: g, result: '8' }
  }
  if (spec.kind === 'speech') {
    const g = await loadWorkflow('speech-kokoro.api.json')
    g['1'].inputs.speaker_name = spec.voice
    Object.assign(g['2'].inputs, { text: spec.text, lang: LANGS[spec.voice[0]] ?? 'English' })
    return { graph: g, result: '3' }
  }
  const g = await loadWorkflow('voice-clone-indextts.api.json')
  g['1'].inputs.audio = annotated(spec.reference)
  Object.assign(g['3'].inputs, { text: spec.text, seed: seed() })
  return { graph: g, result: '4' }
}

const LABELS: Record<AudioSpec['kind'], string> = { music: t('audio.music'), speech: t('audio.voiceover'), clone: t('audio.voiceover'), sfx: t('audio.soundEffect') }

export function generateAudio(editor: Editor, spec: AudioSpec, onError: ErrorSink, quiet = false): TLShapeId {
  const [w, h] = AUDIO_SIZE
  const [x, y] = freeSpot(editor, w, h)
  const id = createShapeId()
  editor.createShape({ id, type: GENERATOR, x, y, props: { w, h }, meta: { temp: true, quiet } })
  if (!quiet) editor.zoomToBounds({ x, y, w, h }, { inset: 200, animation: { duration: 200 } })
  const text = spec.kind === 'speech' || spec.kind === 'clone' ? spec.text : spec.prompt
  void startJob(editor, id, audioGraph(spec), { name: `${LABELS[spec.kind]} · ${text.slice(0, 24)}`, kind: 'audio', placer: 'audio' }, onError)
  return id
}

async function modelGraph(image: string, model?: string): Promise<Built> {
  const selected = requireModel('model', model)
  const g = await loadWorkflow(selected.id)
  g['1'].inputs.image = image
  return { graph: g, result: '30' }
}

export function imageTo3d(editor: Editor, shape: TLImageShape, onError: ErrorSink, model?: string) {
  const asset = shape.props.assetId ? editor.getAsset(shape.props.assetId) : null
  if (asset?.type !== 'image' || !asset.props.src) return
  const holder = spawnHolder(editor, shape, [MODEL_SIZE, MODEL_SIZE])
  void startJob(editor, holder, modelGraph(annotated(asset.props.src), model), { name: `${asset.props.name || t('common.image')} · 3D`, kind: 'model', placer: 'model' }, onError)
  return holder
}

registerPlacer('audio', async (editor, holder, media, job) => {
  const ids: TLShapeId[] = []
  editor.run(() => {
    editor.deleteShape(holder.id)
    media.forEach((m, i) => {
      const id = createShapeId()
      editor.createShape({ id, type: AUDIO, x: holder.x, y: holder.y + i * (AUDIO_SIZE[1] + GAP), parentId: holder.parentId, props: { src: m.src, name: job.name } })
      ids.push(id)
    })
  }, { history: 'ignore' })
  selectResults(editor, holder, ids)
})

registerPlacer('model', async (editor, holder, media, job) => {
  const { w, h } = holder.props as { w: number; h: number }
  const ids: TLShapeId[] = []
  editor.run(() => {
    editor.deleteShape(holder.id)
    media.forEach((m, i) => {
      const id = createShapeId()
      editor.createShape({ id, type: MODEL, x: holder.x + i * (w + GAP), y: holder.y, parentId: holder.parentId, props: { w, h, src: m.src, name: job.name, ext: 'glb' } })
      ids.push(id)
    })
  }, { history: 'ignore' })
  selectResults(editor, holder, ids)
})
