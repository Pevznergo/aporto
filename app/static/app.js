async function refresh() {
  const resp = await fetch('/api/tasks');
  if (!resp.ok) return;
  const data = await resp.json();
  const tbody = document.getElementById('tasks-body');
  tbody.innerHTML = '';
  for (const t of data) {
    const tr = document.createElement('tr');
    const dlLink = t.downloaded_path ? `<a href="/videos/${t.downloaded_path.split('/').pop()}">${t.original_filename || 'файл'}</a>` : '-';
    const outLink = t.processed_path ? `<a href="/videos/${t.processed_path.split('/').pop()}" download>скачать</a>` : '-';
    const actions = t.status === 'error' ? `<span class="error">${t.error || ''}</span> <button data-id="${t.id}" class="retry">Повторить</button>` : '-';
    tr.innerHTML = `
      <td>${t.id}</td>
      <td>${t.status}</td>
      <td><a href="${t.url}" target="_blank">ссылка</a></td>
      <td>${dlLink}</td>
      <td>${outLink}</td>
      <td>${actions}</td>
    `;
    tbody.appendChild(tr);
  }
}

const form = document.getElementById('add-form');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  const payload = {
    url: fd.get('url'),
    start: fd.get('start') || null,
    end: fd.get('end') || null,
  };
  const resp = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    alert('Ошибка создания задачи');
  } else {
    form.reset();
    await refresh();
  }
});

// Retry button delegation
const tasksEl = document.getElementById('tasks-body');
tasksEl.addEventListener('click', async (e) => {
  const btn = e.target.closest('button.retry');
  if (!btn) return;
  const id = btn.getAttribute('data-id');
  const resp = await fetch(`/api/tasks/${id}/retry`, { method: 'POST' });
  if (!resp.ok) {
    alert('Не удалось перезапустить задачу');
  } else {
    await refresh();
  }
});

// Downloads list
async function refreshDownloads() {
  const resp = await fetch('/api/downloads');
  if (!resp.ok) return;
  const data = await resp.json();
  const tbody = document.getElementById('downloads-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  for (const d of data) {
    const tr = document.createElement('tr');
    const title = d.title ? d.title : '(без названия)';
    tr.innerHTML = `
      <td>${d.id}</td>
      <td>${title}</td>
      <td><a href="${d.url}" target="_blank">ссылка</a></td>
      <td><button class="del-download" data-id="${d.id}">🗑️</button></td>
    `;
    tbody.appendChild(tr);
  }
}

// Delete download row
const downloadsBody = document.getElementById('downloads-body');
if (downloadsBody) {
  downloadsBody.addEventListener('click', async (e) => {
    const btn = e.target.closest('button.del-download');
    if (!btn) return;
    const id = btn.getAttribute('data-id');
    const resp = await fetch(`/api/downloads/${id}`, { method: 'DELETE' });
    if (!resp.ok) {
      alert('Не удалось удалить запись');
    }
    await refreshDownloads();
  });
}

setInterval(() => { refresh(); refreshDownloads(); }, 3000);
window.addEventListener('load', () => { refresh(); refreshDownloads(); });
