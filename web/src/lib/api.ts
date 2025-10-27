export type Task = {
  id: number
  url: string
  mode: 'simple' | 'auto'
  status: string
  stage?: string | null
  progress?: number | null
  video_id?: string | null
  original_filename?: string | null
  downloaded_path?: string | null
  processed_path?: string | null
  clips_dir?: string | null
  transcript_path?: string | null
  clips_json_path?: string | null
  error?: string | null
  start_time?: number | null
  end_time?: number | null
}

export type DownloadedItem = {
  id: number
  url: string
  title: string
  created_at: string
}

export type ClipFragment = {
  id: number
  start_time: string
  end_time: string
  text: string
  visual_suggestion?: string | null
  order: number
}

export type Clip = {
  id: number
  task_id: number
  short_id: number
  title: string
  description: string
  duration_estimate?: string | null
  hook_strength?: string | null
  why_it_works?: string | null
  file_path?: string | null
  created_at: string
  fragments: ClipFragment[]
  status?: string | null
  channel?: string | null
}

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export async function listTasks(): Promise<Task[]> {
  try {
    console.log('listTasks: API_BASE =', API_BASE)
    console.log('listTasks: Making request to', `${API_BASE}/api/tasks`)
    const res = await fetch(`${API_BASE}/api/tasks`, { cache: 'no-store', mode: 'cors' })
    console.log('listTasks: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('listTasks: Success, returned', data.length, 'tasks')
    return data
  } catch (e) {
    console.error('listTasks: Error =', e)
    return []
  }
}

export async function createTask(payload: { url: string; mode?: 'simple' | 'auto'; start?: string | number | null; end?: string | number | null }): Promise<Task> {
  try {
    console.log('createTask: API_BASE =', API_BASE)
    console.log('createTask: Payload =', payload)
    const res = await fetch(`${API_BASE}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      mode: 'cors',
    })
    console.log('createTask: Response status =', res.status)
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      console.error('createTask: Error body =', text)
      throw new Error(`Failed to create task: HTTP ${res.status}`)
    }
    const data = await res.json()
    console.log('createTask: Success, id =', data?.id)
    return data
  } catch (e) {
    console.error('createTask: Error =', e)
    throw e
  }
}

export async function deleteTask(id: number): Promise<{ ok: boolean }> {
  try {
    console.log('deleteTask: API_BASE =', API_BASE, 'id =', id)
    const res = await fetch(`${API_BASE}/api/tasks/${id}`, { method: 'DELETE', mode: 'cors' })
    console.log('deleteTask: Response status =', res.status)
    if (!res.ok) throw new Error(`Failed to delete task: HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('deleteTask: Error =', e)
    throw e
  }
}

export async function clearTasks(): Promise<{ ok: boolean }> {
  try {
    console.log('clearTasks: API_BASE =', API_BASE)
    const res = await fetch(`${API_BASE}/api/tasks`, { method: 'DELETE', mode: 'cors' })
    console.log('clearTasks: Response status =', res.status)
    if (!res.ok) throw new Error(`Failed to clear tasks: HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('clearTasks: Error =', e)
    throw e
  }
}

export async function retryTask(id: number): Promise<Task> {
  try {
    console.log('retryTask: API_BASE =', API_BASE, 'id =', id)
    const res = await fetch(`${API_BASE}/api/tasks/${id}/retry`, { method: 'POST', mode: 'cors' })
    console.log('retryTask: Response status =', res.status)
    if (!res.ok) throw new Error(`Failed to retry task: HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('retryTask: Error =', e)
    throw e
  }
}

export async function listDownloads(): Promise<DownloadedItem[]> {
  try {
    console.log('listDownloads: API_BASE =', API_BASE)
    console.log('listDownloads: Making request to', `${API_BASE}/api/downloads`)
    const res = await fetch(`${API_BASE}/api/downloads`, { cache: 'no-store', mode: 'cors' })
    console.log('listDownloads: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.log('listDownloads: Success, returned', data.length, 'downloads')
    return data
  } catch (e) {
    console.error('listDownloads: Error =', e)
    return []
  }
}

export async function deleteDownload(id: number): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/api/downloads/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete download')
  return res.json()
}

export async function getTaskClips(taskId: number): Promise<Clip[]> {
  try {
    console.log('getTaskClips: API_BASE =', API_BASE, 'taskId =', taskId)
    const res = await fetch(`${API_BASE}/api/tasks/${taskId}/clips`, { cache: 'no-store', mode: 'cors' })
    console.log('getTaskClips: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('getTaskClips: Error =', e)
    return []
  }
}

export async function getClip(clipId: number): Promise<Clip | null> {
  try {
    console.log('getClip: API_BASE =', API_BASE, 'clipId =', clipId)
    const res = await fetch(`${API_BASE}/api/clips/${clipId}`, { cache: 'no-store', mode: 'cors' })
    console.log('getClip: Response status =', res.status)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } catch (e) {
    console.error('getClip: Error =', e)
    return null
  }
}

export async function updateClip(clipId: number, data: { status?: string; channel?: string }): Promise<{ ok: boolean }> {
  try {
    console.log('updateClip: API_BASE =', API_BASE, 'clipId =', clipId, 'data =', data)
    const res = await fetch(`${API_BASE}/api/clips/${clipId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      mode: 'cors',
    })
    console.log('updateClip: Response status =', res.status)
    if (!res.ok) throw new Error(`Failed to update clip: HTTP ${res.status}`)
    return { ok: true }
  } catch (e) {
    console.error('updateClip: Error =', e)
    throw e
  }
}
