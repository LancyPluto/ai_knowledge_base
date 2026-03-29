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

export async function register(email: string, code: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register_email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code, password })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function sendCode(email: string, purpose: "register" | "login" = "register") {
  const res = await fetch(`${API_BASE}/auth/send_code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, purpose })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login_email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getMe(token: string) {
  const r = await fetch(API_BASE + "/auth/me", {
    headers: {
      Authorization: "Bearer " + token,
    },
  })
  if (!r.ok) throw new Error("not authenticated")
  return await r.json()
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

export async function chatStream(message: string, sessionId: string | null, onEvent: (evt: any) => void) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message, session_id: sessionId })
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

export async function getChatSessions() {
  const res = await fetch(`${API_BASE}/chat/sessions`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function createChatSession(title: string = "新对话") {
  const res = await fetch(`${API_BASE}/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ title })
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteChatSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: authHeaders()
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getChatMessages(sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages`, { headers: authHeaders() })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
