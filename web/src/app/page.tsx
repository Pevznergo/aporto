'use client'

import React from 'react'
/// <reference types="react" />
import { useEffect, useState } from 'react'
import { createTask, listTasks, retryTask, deleteTask, clearTasks, listDownloads, deleteDownload, getTaskClips, type Task, type DownloadedItem, type Clip } from '@/lib/api'
import { useUpscaleTasks, triggerUpscaleScan, retryUpscale, getUpscaleSettings, saveUpscaleSettings, ensureUpscaleInstance, deleteUpscale, clearUpscale, listUpscaleTasks, type UpscaleTask } from '@/lib/upscale'

function StageChip({ stage }: { stage?: string | null }) {
  const map: Record<string, { label: string; color: string }> = {
    downloading: { label: 'Скачивание', color: '#2563eb' },
    queued_process: { label: 'В очереди', color: '#475569' },
    transcribing: { label: 'Транскрипция', color: '#a855f7' },
    gpt: { label: 'GPT', color: '#22c55e' },
    cutting: { label: 'Нарезка', color: '#f59e0b' },
    done: { label: 'Готово', color: '#16a34a' },
    error: { label: 'Ошибка', color: '#dc2626' },
    ensuring_instance: { label: 'Запуск инстанса', color: '#38bdf8' },
    uploading: { label: 'Загрузка', color: '#3b82f6' },
    processing: { label: 'Обработка', color: '#f59e0b' },
    downloading_result: { label: 'Скачивание', color: '#10b981' }
  }
  const key = (stage || '').toLowerCase()
  const item = map[key] || { label: key || '—', color: '#64748b' }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '2px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046', color: item.color }}>
      <span style={{ width: 8, height: 8, borderRadius: 999, background: item.color }} />
      <span>{item.label}</span>
    </span>
  )
}

function ClipsModal({ task, onClose }: { task: Task; onClose: () => void }) {
  const [clips, setClips] = useState<Clip[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    async function loadClips() {
      setLoading(true)
      const clipData = await getTaskClips(task.id)
      setClips(clipData)
      setLoading(false)
    }
    loadClips()
  }, [task.id])
  
  const videosBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'
  
  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      background: 'rgba(0, 0, 0, 0.8)', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: '#0f1624',
        border: '1px solid #223046',
        borderRadius: 12,
        padding: 24,
        maxWidth: '90vw',
        maxHeight: '90vh',
        overflow: 'auto',
        width: '800px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, color: '#e6eaf2' }}>Клипы для: {task.original_filename}</h3>
          <button 
            onClick={onClose}
            style={{ 
              background: 'transparent', 
              border: '1px solid #223046', 
              borderRadius: 8, 
              padding: '4px 8px',
              color: '#e6eaf2',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>
        
        {loading ? (
          <p style={{ color: '#e6eaf2' }}>Загрузка клипов...</p>
        ) : clips.length === 0 ? (
          <p style={{ color: '#e6eaf2' }}>Клипы не найдены в базе данных</p>
        ) : (
          <div style={{ display: 'grid', gap: 16 }}>
            {clips.map((clip) => (
              <div key={clip.id} style={{
                background: '#162033',
                border: '1px solid #223046',
                borderRadius: 8,
                padding: 16
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <h4 style={{ margin: 0, marginBottom: 4, color: '#e6eaf2' }}>#{clip.short_id}: {clip.title}</h4>
                    <p style={{ margin: 0, marginBottom: 8, color: '#9ca3af', fontSize: 14 }}>{clip.description}</p>
                    <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#6b7280' }}>
                      {clip.duration_estimate && <span>Длительность: {clip.duration_estimate}</span>}
                      {clip.hook_strength && <span>Hook: {clip.hook_strength}</span>}
                    </div>
                  </div>
                  {clip.file_path && (
                    <a 
                      href={`${videosBase}/clips/${clip.file_path.split('/').pop()}`}
                      target="_blank"
                      style={{
                        padding: '6px 12px',
                        background: '#2563eb',
                        color: 'white',
                        borderRadius: 6,
                        textDecoration: 'none',
                        fontSize: 12
                      }}
                    >
                      Скачать
                    </a>
                  )}
                </div>
                
                {clip.why_it_works && (
                  <div style={{ marginBottom: 12 }}>
                    <strong style={{ color: '#e6eaf2', fontSize: 12 }}>Почему работает:</strong>
                    <p style={{ margin: 0, marginTop: 4, color: '#9ca3af', fontSize: 12 }}>{clip.why_it_works}</p>
                  </div>
                )}
                
                {clip.fragments.length > 0 && (
                  <div>
                    <strong style={{ color: '#e6eaf2', fontSize: 12 }}>Фрагменты:</strong>
                    <div style={{ marginTop: 8, display: 'grid', gap: 8 }}>
                      {clip.fragments.map((fragment) => (
                        <div key={fragment.id} style={{
                          background: '#0f1624',
                          border: '1px solid #374151',
                          borderRadius: 4,
                          padding: 8
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <span style={{ fontSize: 11, color: '#6b7280' }}>
                              {fragment.start_time} - {fragment.end_time}
                            </span>
                            {fragment.visual_suggestion && (
                              <span style={{ fontSize: 10, color: '#9ca3af', fontStyle: 'italic' }}>
                                {fragment.visual_suggestion}
                              </span>
                            )}
                          </div>
                          <p style={{ margin: 0, fontSize: 12, color: '#e6eaf2' }}>{fragment.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function VideosLinks({ t, onShowClips }: { t: Task; onShowClips: () => void }) {
  const videosBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'
  const fileName = (p?: string | null) => (p ? p.split('/').pop() : null)
  const dl = t.downloaded_path ? `${videosBase}/videos/${fileName(t.downloaded_path)}` : null
  const processed = t.processed_path ? `${videosBase}/videos/${fileName(t.processed_path)}` : null
  const clips = t.clips_dir ? `${videosBase}/clips/${t.clips_dir.split('/').pop()}` : null
  const transcript = t.transcript_path ? `${videosBase}/clips/${fileName(t.transcript_path)}` : null
  const clipsJson = t.clips_json_path ? `${videosBase}/clips/${fileName(t.clips_json_path)}` : null

  return (
    <>
      <td>{dl ? <a href={dl} target="_blank">скачанное</a> : '-'}</td>
      <td>
        {processed ? (
          <a href={processed} download>результат</a>
        ) : t.mode === 'auto' ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {clips ? <a href={clips} target="_blank">папка клипов</a> : '-'}
            <button 
              onClick={onShowClips}
              style={{
                padding: '2px 6px',
                fontSize: 11,
                border: '1px solid #223046',
                background: '#162033',
                color: '#e6eaf2',
                borderRadius: 4,
                cursor: 'pointer'
              }}
            >
              Клипы из БД
            </button>
          </div>
        ) : (
          '-'
        )}
      </td>
      <td>
        {transcript ? <a href={transcript} target="_blank">транскрипт</a> : '-'} | {clipsJson ? <a href={clipsJson} target="_blank">clips.json</a> : '-'}
      </td>
    </>
  )
}

type Tab = 'cut' | 'upscale' | 'downloads' | 'clips'

function UpscaleSection() {
  const { tasks, refresh } = useUpscaleTasks()
  const [showSettings, setShowSettings] = useState(false)
  const [image, setImage] = useState('')
  const [conc, setConc] = useState(2)
  const [vastId, setVastId] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const s = await getUpscaleSettings()
        setImage(s.UPSCALE_IMAGE)
        setConc(s.UPSCALE_CONCURRENCY)
        setVastId(s.VAST_INSTANCE_ID || '')
      } catch {}
    }
    load()
  }, [])

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault()
    await saveUpscaleSettings({ UPSCALE_IMAGE: image, UPSCALE_CONCURRENCY: conc, VAST_INSTANCE_ID: vastId || undefined })
    setShowSettings(false)
  }

  return (
    <section style={{ background: '#0f1624', border: '1px solid #223046', borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ marginTop: 0 }}>Upscale задачи</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => triggerUpscaleScan().then(refresh)} style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', background: '#162033', color: '#e6eaf2' }}>Сканировать to_upscale</button>
          <button onClick={() => ensureUpscaleInstance().then(refresh)} style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', background: '#162033', color: '#e6eaf2' }}>Запустить инстанс</button>
          <button onClick={() => setShowSettings(s => !s)} style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', color: '#e6eaf2' }}>{showSettings ? 'Закрыть' : 'Настройки'}</button>
          <a href="/clips_upscaled" target="_blank" style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', color: '#e6eaf2' }}>Открыть clips_upscaled</a>
          <button
            onClick={async () => {
              if (!confirm('Очистить все задачи Upscale? Входные файлы из to_upscale также будут удалены.')) return
              try {
                await clearUpscale()
                await refresh()
              } catch (e) {
                alert('Не удалось очистить Upscale: ' + (e as Error).message)
              }
            }}
            style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #7f1d1d', background: '#1f2937', color: '#fca5a5' }}
          >Очистить все</button>
        </div>
      </div>
      {showSettings && (
        <form onSubmit={saveSettings} style={{ display: 'grid', gap: 12, marginTop: 12, padding: 12, border: '1px solid #223046', borderRadius: 8 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, opacity: 0.8 }}>UPSCALE_IMAGE</label>
            <input value={image} onChange={e => setImage(e.target.value)} placeholder="docker/image:tag" style={{ width: '100%', padding: '6px 8px' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, opacity: 0.8 }}>Параллелизм (1-4)</label>
            <input type="number" min={1} max={4} value={conc} onChange={e => setConc(parseInt(e.target.value || '1', 10))} style={{ width: 120, padding: '6px 8px' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, opacity: 0.8 }}>VAST_INSTANCE_ID (опционально)</label>
            <input value={vastId} onChange={e => setVastId(e.target.value)} placeholder="например 123456" style={{ width: '100%', padding: '6px 8px' }} />
            <div style={{ fontSize: 12, opacity: 0.7, marginTop: 6 }}>
              Если создание через API недоступно, укажите ID уже созданного инстанса Vast — сервис будет его запускать/останавливать.
            </div>
          </div>
          <div>
            <button type="submit" style={{ padding: '6px 10px', borderRadius: 8, background: '#2563eb', border: '1px solid #2563eb', color: 'white' }}>Сохранить</button>
          </div>
        </form>
      )}
      <p style={{ marginTop: 12, opacity: 0.8, fontSize: 13 }}>Положите файлы в корневую папку to_upscale/. До 2 задач обрабатываются параллельно. Результаты — в clips_upscaled/.</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Файл</th>
            <th>Статус</th>
            <th>Прогресс</th>
            <th>Результат</th>
            <th>Действия</th>
            <th>Ошибка</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t: UpscaleTask) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.file_path.split('/').pop()}</td>
              <td>{t.status}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <progress value={t.progress ?? 0} max={100} style={{ width: 120 }} />
                  <StageChip stage={t.stage} />
                  <span style={{ opacity: 0.8 }}>{t.progress ?? 0}%</span>
                </div>
              </td>
              <td>
                {t.result_path ? <a href={`/clips_upscaled/${t.result_path.split('/').pop()}`} target="_blank">скачать</a> : '-'}
              </td>
              <td>
                <div style={{ display: 'flex', gap: 8 }}>
                  {t.status === 'error' ? (
                    <button onClick={() => retryUpscale(t.id).then(refresh)}>Повторить</button>
                  ) : null}
                  <button
                    onClick={async () => {
                      if (!confirm('Удалить задачу и входной файл из to_upscale/?')) return
                      try {
                        await deleteUpscale(t.id)
                        await refresh()
                      } catch (e) {
                        alert('Не удалось удалить задачу: ' + (e as Error).message)
                      }
                    }}
                  >Удалить</button>
                </div>
              </td>
              <td>{t.error || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

export default function Page() {
  const [tab, setTab] = useState<Tab>('cut')
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [modeUI, setModeUI] = useState<'simple'|'auto'>('auto')
  const [downloads, setDownloads] = useState<DownloadedItem[]>([])
  const [cutQueued, setCutQueued] = useState(0)
  const [cutProcessing, setCutProcessing] = useState(0)
  const [upQueued, setUpQueued] = useState(0)
  const [upProcessing, setUpProcessing] = useState(0)
  const [selectedTaskForClips, setSelectedTaskForClips] = useState<Task | null>(null)
  const [clips, setClips] = useState<Clip[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [channelFilter, setChannelFilter] = useState<string>('all')

  async function refresh() {
    const data = await listTasks()
    setTasks(data)
    const d = await listDownloads()
    setDownloads(d)
    
    if (tab === 'clips') {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || ''
        const clipsData = await fetch(`${API_BASE}/api/clips`).then(res => res.json())
        setClips(clipsData)
      } catch (e) {
        console.error('Failed to fetch clips:', e)
      }
    }
    try {
      const ups = await listUpscaleTasks()
      setUpQueued(ups.filter(u => (u.status || '').toLowerCase() === 'queued').length)
      setUpProcessing(ups.filter(u => (u.status || '').toLowerCase() === 'processing').length)
    } catch {}
    const cq = data.filter(t => {
      const s = (t.status || '').toLowerCase()
      return s === 'queued_download' || s === 'queued_process'
    }).length
    const cp = data.filter(t => (t.status || '').toLowerCase() === 'processing').length
    setCutQueued(cq)
    setCutProcessing(cp)
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [])

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const fd = new FormData(form)

    const mode = modeUI
    const url = String(fd.get('url') || '')

    // В auto режиме игнорируем start/end
    const startRaw = mode === 'auto' ? null : fd.get('start')
    const endRaw = mode === 'auto' ? null : fd.get('end')

    const start = startRaw && String(startRaw).trim() !== '' ? String(startRaw) : null
    const end = endRaw && String(endRaw).trim() !== '' ? String(endRaw) : null

    const payload = { url, mode, start, end }

    setLoading(true)
    try {
      await createTask(payload)
      form.reset()
      await refresh()
    } finally {
      setLoading(false)
    }
  }

  async function onRetry(id: number) {
    await retryTask(id)
    await refresh()
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ padding: '8px 12px', borderRadius: 10, border: '1px solid #223046', background: '#0f1624', color: '#e6eaf2', display: 'flex', gap: 10, alignItems: 'center' }}>
          <strong style={{ opacity: 0.9 }}>Cut</strong>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '2px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046', color: '#475569' }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: '#475569' }} />
            <span>Queued: {cutQueued}</span>
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '2px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046', color: '#f59e0b' }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: '#f59e0b' }} />
            <span>Processing: {cutProcessing}</span>
          </span>
        </div>
        <div style={{ padding: '8px 12px', borderRadius: 10, border: '1px solid #223046', background: '#0f1624', color: '#e6eaf2', display: 'flex', gap: 10, alignItems: 'center' }}>
          <strong style={{ opacity: 0.9 }}>Upscale</strong>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '2px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046', color: '#475569' }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: '#475569' }} />
            <span>Queued: {upQueued}</span>
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '2px 8px', borderRadius: 999, background: '#0f1624', border: '1px solid #223046', color: '#f59e0b' }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: '#f59e0b' }} />
            <span>Processing: {upProcessing}</span>
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <button onClick={() => setTab('cut')} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #223046', background: tab==='cut' ? '#162033' : 'transparent', color: '#e6eaf2' }}>Cut</button>
        <button onClick={() => setTab('upscale')} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #223046', background: tab==='upscale' ? '#162033' : 'transparent', color: '#e6eaf2' }}>Upscale</button>
        <button onClick={() => setTab('downloads')} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #223046', background: tab==='downloads' ? '#162033' : 'transparent', color: '#e6eaf2' }}>Downloads</button>
        <button onClick={() => setTab('clips')} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #223046', background: tab==='clips' ? '#162033' : 'transparent', color: '#e6eaf2' }}>Clips</button>
      </div>

      {tab === 'cut' && (
      <section style={{ background: '#0f1624', border: '1px solid #223046', borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Добавить задачу</h2>
        <form onSubmit={onSubmit}>
          <label>Ссылка на YouTube:
            <input type="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required />
          </label>
          <div style={{ display: 'flex', gap: 12 }}>
            <label>Режим:
              <select name="mode" value={modeUI} onChange={e => setModeUI((e.target.value as 'simple'|'auto'))}>
                <option value="auto">auto (Whisper+GPT)</option>
                <option value="auto_resize">auto + resize 9/16</option>
                <option value="simple">simple (start/end)</option>
              </select>
            </label>
            {modeUI === 'simple' && (
              <>
                <label>Начало (сек/HH:MM:SS):
                  <input type="text" name="start" placeholder="например 12 или 00:00:12" />
                </label>
                <label>Конец (сек/HH:MM:SS):
                  <input type="text" name="end" placeholder="например 35 или 00:00:35" />
                </label>
              </>
            )}
          </div>
          <button type="submit" disabled={loading}>{loading ? 'Добавление...' : 'Добавить'}</button>
        </form>
      </section>
      )}

      {tab === 'cut' && (
      <section style={{ background: '#0f1624', border: '1px solid #223046', borderRadius: 12, padding: 16, marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ marginTop: 0 }}>Задачи</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <a href="/clips" target="_blank" style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', color: '#e6eaf2' }}>Открыть clips</a>
            <a href="/cuted" target="_blank" style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #223046', color: '#e6eaf2' }}>Открыть cuted</a>
            <button
              onClick={async () => {
                if (!confirm('Очистить все задачи Cut? Файлы в videos/ и clips/ для этих задач будут удалены.')) return
                try {
                  await clearTasks()
                  await refresh()
                } catch (e) {
                  alert('Не удалось очистить Cut: ' + (e as Error).message)
                }
              }}
              style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid #7f1d1d', background: '#1f2937', color: '#fca5a5' }}
            >Очистить все</button>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Режим</th>
              <th>Статус</th>
              <th>Прогресс</th>
              <th>Видео</th>
              <th>Файлы</th>
              <th>Результаты</th>
              <th>Логи</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.original_filename || '-'}</td>
                <td>{t.mode}</td>
                <td>{t.status}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <progress value={t.progress ?? 0} max={100} style={{ width: 120 }} />
                    <StageChip stage={t.stage} />
                    <span style={{ opacity: 0.8 }}>{(t.progress ?? 0)}%</span>
                  </div>
                </td>
                <td><a href={t.url} target="_blank">ссылка</a></td>
                <VideosLinks t={t} onShowClips={() => setSelectedTaskForClips(t)} />
                <td>{t.error ? <span style={{ color: '#b00020' }}>{t.error}</span> : '-'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {t.status === 'error' ? (
                      <button onClick={() => onRetry(t.id)}>Повторить</button>
                    ) : null}
                    <button
                      title="Удалить задачу"
                      onClick={async () => {
                        if (!confirm('Удалить задачу и связанные с ней локальные файлы?')) return
                        try {
                          await deleteTask(t.id)
                          await refresh()
                        } catch (e) {
                          alert('Не удалось удалить задачу: ' + (e as Error).message)
                        }
                      }}
                    >🗑️</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      )}

      {tab === 'upscale' && (
        <UpscaleSection />
      )}

      {tab === 'downloads' && (
        <section style={{ background: '#0f1624', border: '1px solid #223046', borderRadius: 12, padding: 16, marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ margin: 0 }}>Downloads</h2>
          </div>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>URL</th>
                <th>Создано</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {downloads.map(d => (
                <tr key={d.id}>
                  <td>{d.id}</td>
                  <td>{d.title}</td>
                  <td><a href={d.url} target="_blank">ссылка</a></td>
                  <td>{new Date(d.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      onClick={async () => {
                        try {
                          await deleteDownload(d.id)
                          await refresh()
                        } catch (e) {
                          alert('Не удалось удалить запись: ' + (e as Error).message)
                        }
                      }}
                    >Удалить</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'clips' && (
        <section style={{ background: '#0f1624', border: '1px solid #223046', borderRadius: 12, padding: 16, marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ margin: 0 }}>Clips</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Short #</th>
                  <th>Title</th>
                  <th>Description</th>
                  <th>File</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {clips.map((clip) => (
                  <tr key={clip.id}>
                    <td>{clip.id}</td>
                    <td>{clip.task_id}</td>
                    <td>{clip.short_id}</td>
                    <td>{clip.title}</td>
                    <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{clip.description}</td>
                    <td>{clip.file_path ? <a href={`/clips/${clip.file_path.split('/').pop()}`} target="_blank">скачать</a> : '-'}</td>
                    <td>{new Date(clip.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      
      {selectedTaskForClips && (
        <ClipsModal 
          task={selectedTaskForClips} 
          onClose={() => setSelectedTaskForClips(null)}
        />
      )}
    </div>
  )
}

