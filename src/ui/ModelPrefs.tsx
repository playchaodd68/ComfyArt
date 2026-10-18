import { useState } from 'react'
import { useValue } from 'tldraw'

import { installedAtom, MODEL_GROUPS, MODEL_MODALITIES, modelMissing, modelPrefsAtom, modelStatusAtom, saveModelPrefs, type ModelModality } from '../models'
import { Icons } from './icons'
import { Popover } from './Popover'
import { t } from '../i18n'

export function ModelPrefs({ onError }: { onError: (msg: string) => void }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<ModelModality>('image')
  const prefs = useValue(modelPrefsAtom)
  const installed = useValue(installedAtom)
  useValue(modelStatusAtom)
  const save = (next: typeof prefs) => void saveModelPrefs(next).catch((e) => onError(String(e)))
  const toggle = (id: string) => save({ ...prefs, enabled: prefs.enabled.includes(id) ? prefs.enabled.filter((x) => x !== id) : [...prefs.enabled, id] })

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
      side="top"
      trigger={({ open: o, toggle: flip }) => (
        <button type="button" className="ca-bar__btn ca-bar__btn--icon" title={t('modelPrefs.modelPreferences')} data-open={o || undefined} onClick={flip}>
          <span className="ca-icon">{Icons.adjust}</span>
        </button>
      )}
    >
      <div className="ca-menu ca-modelprefs">
        <div className="ca-modelprefs__head">
          <span className="ca-menu__grow">{t('modelPrefs.modelPreferences')}</span>
          <span className="ca-chat__hint">{t('common.auto')}</span>
          <button type="button" className="ca-switch" role="switch" aria-checked={prefs.auto} data-on={prefs.auto || undefined} onClick={() => save({ ...prefs, auto: !prefs.auto })}><span /></button>
        </div>
        <div className="ca-panel__chips">
          {MODEL_MODALITIES.map((modality) => <button key={modality} type="button" className="ca-panel__chip" data-on={tab === modality || undefined} onClick={() => setTab(modality)}>{t(`models.${modality}`)}</button>)}
        </div>
        <div className="ca-chat__hint">{prefs.auto ? t('modelPrefs.theAgentPicksAutomaticallyFrom') : t('modelPrefs.theAgentOnlyUsesChecked')}</div>
        {MODEL_GROUPS[tab].map((m) => {
          const missing = !installed?.includes(m.id)
          const on = prefs.auto || prefs.enabled.includes(m.id)
          return (
            <label key={m.id} className="ca-menu__item ca-modelprefs__row" data-missing={missing || undefined}>
              <span className="ca-menu__grow ca-model"><span>{m.label}{missing && <span className="ca-model__tag">{installed ? t('modelPrefs.notInstalled') : t('models.notChecked')}</span>}</span><span className="ca-model__desc">{missing ? modelMissing(m.id).join(' · ') : m.desc}</span></span>
              <input type="checkbox" checked={on && !missing} disabled={prefs.auto || missing} onChange={() => toggle(m.id)} />
            </label>
          )
        })}
      </div>
    </Popover>
  )
}
