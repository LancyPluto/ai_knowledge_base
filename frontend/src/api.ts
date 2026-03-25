const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001"

function authHeaders() {
  const token = localStorage.getItem("token")
  const headers: Record<string, string> = {}
  if (token) headers["Authorization"] = `Bearer ${token}`
  return headers
}

async function parseError(res: Response) {
  const text = await res.text()
  try {
    const j = JSON.parse(text)
    if (typeof j?.detail === "string") return j.detail
    return text
  } catch {
    return text
  }
}

export async function register(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function me() {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function uploadFile(file: File) {
  const fd = new FormData()
  fd.append("file", file)
  const res = await fetch(`${API_BASE}/docs/upload`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: fd
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function listDocs() {
  const res = await fetch(`${API_BASE}/docs/`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteDoc(docId: number) {
  const res = await fetch(`${API_BASE}/docs/${docId}`, {
    method: "DELETE",
    headers: authHeaders()
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function reuploadDoc(docId: number, file: File) {
  const fd = new FormData()
  fd.append("file", file)
  const res = await fetch(`${API_BASE}/docs/${docId}/reupload`, {
    method: "PUT",
    headers: { ...authHeaders() },
    body: fd
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function chat(message: string, sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message, session_id: sessionId, ephemeral: true })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function chatStream(message: string, sessionId: string, onEvent: (evt: any) => void) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message, session_id: sessionId, ephemeral: true })
  })
  if (!res.ok || !res.body) throw new Error(await parseError(res))

  const reader = res.body.getReader()
  const decoder = new TextDecoder("utf-8")
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 1)
      if (!line) continue
      try {
        onEvent(JSON.parse(line))
      } catch {
        onEvent({ type: "token", data: line })
      }
    }
  }
}

export async function closeSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/session/close?session_id=${encodeURIComponent(sessionId)}`, {
    method: "POST",
    headers: authHeaders()
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
