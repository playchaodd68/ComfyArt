import { useState } from 'react'
import { atom, useValue, type Editor } from 'tldraw'

import { generateAudio, MUSIC_SECONDS, SFX_SECONDS, VOICES, type AudioSpec } from '../assetGen'
import { AUDIO, type AudioShape } from '../shapes/EmbedShapes'
import { Icons } from './icons'
import { t } from '../i18n'
import { installedModels, modelStatusAtom } from '../models'

type Tab = 'music' | 'speech' | 'sfx'
const TABS: [Tab, string][] = [['music', t('audio.music')], ['speech', t('audio.voiceover')], ['sfx', t('audio.soundEffect')]]
const CLONE = 'clone'

export const audioDialogAtom = atom<boolean>('audio dialog', false)

export function AudioDialog({ editor, onError }: { editor: Editor; onError: (msg: string) => void }) {
  const open = useValue(audioDialogAtom)
  const [tab, setTab] = useState<Tab>('music')
  const [prompt, setPrompt] = useState('')
  const [lyrics, setLyrics] = useState('')
  const [seconds, setSeconds] = useState(30)
  const [voice, setVoice] = useState(VOICES[0])
  const [model, setModel] = useState('')
  const [transcript, setTranscript] = useState('')
  useValue(modelStatusAtom)
  const models = installedModels(tab === 'speech' ? 'speech' : 'music').filter((m) =>
    tab === 'sfx' ? m.id === 'sfx-stable-audio.api.json' : tab === 'music' ? m.id !== 'sfx-stable-audio.api.json' : true)
  const selected = models.find((m) => m.id === model) ?? models[0]
  const drama = selected?.id === 'speech-drama3.api.json'
  const indexTts = selected?.id === 'voice-clone-indextts.api.json'
  const selectedVoice = !drama && !indexTts && voice === CLONE ? VOICES[0] : voice
  const reference = useValue('selected audio', () => {
    const s = editor.getOnlySelectedShape()
    return s?.type === AUDIO ? (s as AudioShape).props.src : null
  }, [editor])
  if (!open) return null
  const close = () => audioDialogAtom.set(false)
  const durations = tab === 'music' ? MUSIC_SECONDS : SFX_SECONDS
  const pick = (next: Tab) => {
    setTab(next)
    setModel('')
    if (next !== 'speech') setSeconds(next === 'music' ? 30 : 8)
  }
  const spec = (): AudioSpec | null => {
    const text = prompt.trim()
    if (!text || !selected) return null
    if (tab === 'music') return { kind: 'music', prompt: text, lyrics: lyrics.trim(), seconds, model: selected.id }
    if (tab === 'sfx') return { kind: 'sfx', prompt: text, seconds, model: selected.id }
    const clone = indexTts || drama && selectedVoice === CLONE
    if (clone && !reference) return null
    if (clone && drama && !transcript.trim()) return null
    return clone && reference ? { kind: 'clone', text, reference, transcript, model: selected.id } : { kind: 'speech', text, voice: selectedVoice, model: selected.id }
  }
  const run = () => {
    const s = spec()
    if (!s) return
    close()
    generateAudio(editor, s, onError)
  }

  return (
    <div className="ca-modal" onPointerDown={(e) => { e.stopPropagation(); if (e.target === e.currentTarget) close() }}>
      <div className="ca-modal__card ca-rename">
        <div className="ca-side__head">
          <span>{t('audio.generateAudio')}</span>
          <button type="button" className="ca-panel__icon" title={t('common.close')} onClick={close}>{Icons.close}</button>
        </div>
        <div className="ca-rename__body">
          <div className="ca-panel__chips">
            {TABS.map(([k, label]) => <button key={k} type="button" className="ca-panel__chip" data-on={tab === k || undefined} onClick={() => pick(k)}>{label}</button>)}
          </div>
          <div className="ca-rename__field"><span>{t('agentPicker.model')}</span>
            <select className="ca-panel__input" value={selected?.id ?? ''} onChange={(e) => { setModel(e.target.value); setVoice(VOICES[0]) }} disabled={!models.length}>
              {!models.length && <option value="">{t('models.noneAvailable', t(`models.${tab === 'speech' ? 'speech' : 'music'}`))}</option>}
              {models.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </div>
          <textarea
            autoFocus
            className="ca-panel__prompt ca-panel__prompt--boxed"
            value={prompt}
            placeholder={tab === 'music' ? t('audio.musicPlaceholder') : tab === 'sfx' ? t('audio.sfxPlaceholder') : t('audio.speechPlaceholder')}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.stopPropagation()}
          />
          {tab === 'music' && (
            <textarea className="ca-panel__prompt ca-panel__prompt--boxed" value={lyrics} placeholder={t('audio.lyricsPlaceholder')} onChange={(e) => setLyrics(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />
          )}
          {tab === 'speech' ? !indexTts && (
            <div className="ca-rename__field"><span>{t('audio.voice')}</span>
              <select className="ca-panel__input" value={selectedVoice} onChange={(e) => setVoice(e.target.value)}>
                {reference && drama && <option value={CLONE}>{t('audio.cloneSelected')}</option>}
                {drama ? <option value={VOICES[0]}>{t('audio.dramaVoice')}</option> : VOICES.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          ) : (
            <div className="ca-rename__field"><span>{t('audio.duration')}</span>
              <div className="ca-panel__chips">
                {durations.map((s) => <button key={s} type="button" className="ca-panel__chip" data-on={seconds === s || undefined} onClick={() => setSeconds(s)}>{s}s</button>)}
              </div>
            </div>
          )}
          {tab === 'speech' && selected?.id === 'voice-clone-indextts.api.json' && !reference && <div className="ca-chat__hint">{t('audio.referenceRequired')}</div>}
          {tab === 'speech' && drama && voice === CLONE && reference && <textarea className="ca-panel__prompt ca-panel__prompt--boxed" value={transcript} placeholder={t('audio.referenceTranscript')} onChange={(e) => setTranscript(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />}
          <div className="ca-panel__foot">
            <button type="button" className="ca-panel__secondary" onClick={close}>{t('common.cancel')}</button>
            <button type="button" className="ca-panel__primary" disabled={!spec()} onClick={run}>{t('common.generate')}</button>
          </div>
        </div>
      </div>
    </div>
  )
}
