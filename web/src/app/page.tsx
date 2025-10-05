import { createTask, listTasks, retryTask, type Task } from '@/lib/api'
import { useEffect, useState } from 'react'

function VideosLinks({ t }: { t: Task }) {
  const videosBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'
  const fileName = (p?: string | null) => p ? p.split('/').pop() : null
  const dl = t.downloaded_path ? `${videosBase}/videos/${fileName(t.downloaded_path)}` : null
  const processed = t.processed_path ? `${videosBase}/videos/${fileName(t.processed_path)}` : null
  const clips = t.clips_dir ? `${videosBase}/clips/${t.clips_dir.split('/').pop()}` : null
  const transcript = t.transcript_path ? `${videosBase}/clips/${fileName(t.transcript_path)}` : null
  const clipsJson = t.clips_json_path ? `${videosBase}/clips/${fileName(t.clips_json_path)}` : null

  return (
    <>
      <td>
        {dl ? <a href={dl} target="_blank">скачанное</a> : '-'}
      </td>
      <td>
        {processed ? <a href={processed} download>результат</a> : (t.mode === 'auto' ? (clips ? <a href={clips} target="_blank">папка клипов</a> : '-') : '-')}
      </td>
      <td>
        {transcript ? <a href={transcript} target="_blank">транскрипт</a> : '-'} | {clipsJson ? <a href={clipsJson} target="_blank">clips.json</a> : '-'}
      </td>
    </>
  )
}

export default function Page() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)

  async function refresh() {
    const data = await listTasks()
    setTasks(data)
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [])

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const payload = {
      url: String(fd.get('url') || ''),
      mode: (String(fd.get('mode') || 'simple') as 'simple' | 'auto'),
      start: fd.get('start') ? String(fd.get('start')) : null,
      end: fd.get('end') ? String(fd.get('end')) : null,
    }
    setLoading(true)
    try {
      await createTask(payload)
      e.currentTarget.reset()
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
      <h1>Видео: загрузка и обрезка (Next.js)</h1>

      <section>
        <h2>Добавить задачу</h2>
        <form onSubmit={onSubmit}>
          <label>Ссылка на YouTube:
            <input type="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required />
          </label>
          <div style={{ display: 'flex', gap: 12 }}>
            <label>Режим:
              <select name="mode" defaultValue="simple">
                <option value="simple">simple (start/end)</option>
                <option value="auto">auto (Whisper+GPT)</option>
              </select>
            </label>
            <label>Начало (сек/HH:MM:SS):
              <input type="text" name="start" placeholder="например 12 или 00:00:12" />
            </label>
            <label>Конец (сек/HH:MM:SS):
              <input type="text" name="end" placeholder="например 35 или 00:00:35" />
            </label>
          </div>
          <button type="submit" disabled={loading}>{loading ? 'Добавление...' : 'Добавить'}</button>
        </form>
      </section>

      <section>
        <h2>Задачи</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Режим</th><th>Статус</th><th>Видео</th><th>Файлы</th><th>Результаты</th><th>Логи</th><th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.mode}</td>
                <td>{t.status}</td>
                <td><a href={t.url} target="_blank">ссылка</a></td>
                <VideosLinks t={t} />
                <td>{t.error ? <span style={{ color: '#b00020' }}>{t.error}</span> : '-'}</td>
                <td>
                  {t.status === 'error' ? (
                    <button onClick={() => onRetry(t.id)}>Повторить</button>
                  ) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
