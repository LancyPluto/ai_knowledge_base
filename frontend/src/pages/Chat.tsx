import { useEffect, useMemo, useState, useRef } from "react"
import { chatStream, getChatSessions, createChatSession, deleteChatSession, getChatMessages } from "../api"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface Session {
  id: string
  title: string
  updated_at: string
}

interface Message {
  role: string
  content: string
}

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [lastSources, setLastSources] = useState<string[]>([])

  const chatBoxRef = useRef<HTMLDivElement>(null)

  const canSend = useMemo(() => !!input.trim() && !busy, [input, busy])

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId)
    } else {
      setMessages([])
      setLastSources([])
    }
  }, [activeSessionId])

  async function loadSessions() {
    try {
      const data = await getChatSessions()
      setSessions(data)
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id)
      }
    } catch (e) {
      console.error("Failed to load sessions", e)
    }
  }

  async function loadMessages(sid: string) {
    setBusy(true)
    setErr(null)
    try {
      const msgs = await getChatMessages(sid)
      setMessages(msgs)
      setLastSources([])
    } catch (e: any) {
      setErr("加载历史记录失败: " + (e?.message || ""))
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateSession() {
    setBusy(true)
    try {
      const s = await createChatSession()
      await loadSessions()
      setActiveSessionId(s.id)
    } catch (e: any) {
      setErr("创建新对话失败: " + (e?.message || ""))
    } finally {
      setBusy(false)
    }
  }

  async function handleDeleteSession(sid: string, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm("确定要删除这个对话吗？")) return
    try {
      await deleteChatSession(sid)
      if (activeSessionId === sid) {
        setActiveSessionId(null)
      }
      await loadSessions()
    } catch (err: any) {
      alert("删除失败: " + err.message)
    }
  }

  async function send() {
    if (!input.trim() || busy) return
    const q = input
    setErr(null)
    setBusy(true)
    
    const assistantIndex = messages.length + 1
    setMessages(m => [...m, {role: "user", content: q}, {role: "assistant", content: ""}])
    setInput("")
    
    try {
      await chatStream(q, activeSessionId, (evt) => {
        if (evt?.type === "start") {
          if (!activeSessionId && evt.session_id) {
             setActiveSessionId(evt.session_id)
             loadSessions()
          }
          setLastSources(evt.sources || [])
          return
        }
        if (evt?.type === "token") {
          const t = evt.data || ""
          if (!t) return
          setMessages(prev => {
            const next = [...prev]
            const cur = next[assistantIndex]
            if (cur && cur.role === "assistant") {
              next[assistantIndex] = { ...cur, content: (cur.content || "") + t }
            }
            return next
          })
          return
        }
        if (evt?.type === "error") {
          setErr(evt.error || "发送失败")
        }
      })
    } catch (e: any) {
      setErr(e?.message || "发送失败")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ display: "flex", gap: "20px", height: "calc(100vh - 44px)" }}>
      <div className="card" style={{ width: "260px", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div className="cardBody" style={{ paddingBottom: 0 }}>
          <div className="rowWrap" style={{ justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
            <div>
              <div className="sectionTitle">对话</div>
              <div className="note" style={{ marginTop: 4 }}>你的历史会话会长期保存</div>
            </div>
            <span className="pill">{sessions.length}</span>
          </div>
          <button className="btn btnPrimary" style={{ width: "100%" }} onClick={handleCreateSession} disabled={busy}>
            新建对话
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "0 16px 16px" }}>
          {sessions.length === 0 ? (
            <div className="note" style={{ textAlign: "center", marginTop: "20px" }}>暂无历史对话</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {sessions.map(s => (
                <div 
                  key={s.id} 
                  className={`navItem ${activeSessionId === s.id ? "navItemActive" : ""}`}
                  style={{ cursor: "pointer", justifyContent: "space-between" }}
                  onClick={() => setActiveSessionId(s.id)}
                >
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {s.title}
                  </span>
                  <button 
                    className="btn btnGhost" 
                    style={{ padding: "2px 8px", fontSize: "14px", opacity: 0.7 }}
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    aria-label="删除对话"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div className="cardBody" style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: "20px" }}>
          <div className="topbar" style={{ marginBottom: "12px" }}>
            <div>
              <div className="pageTitle">智能问答</div>
              <div className="pageDesc">基于你上传的文档检索后回答</div>
            </div>
          </div>
          
          <div className="chatBox" ref={chatBoxRef} style={{ flex: 1, height: "auto", marginBottom: "16px" }}>
            {messages.length === 0 ? (
              <div className="note" style={{ textAlign: "center", marginTop: "40px" }}>
                {activeSessionId ? "这是一个新的对话，请提问" : "在左侧选择对话或新建一个对话"}
              </div>
            ) : null}
            {messages.map((m, i) => (
              <div key={i} className={"bubble " + (m.role === "user" ? "bubbleUser" : "bubbleAi")}>
                {m.role === "assistant" ? (
                  <ReactMarkdown className="md" remarkPlugins={[remarkGfm]}>
                    {m.content}
                  </ReactMarkdown>
                ) : (
                  m.content
                )}
              </div>
            ))}
          </div>

          {lastSources.length ? (
            <div className="alert alertInfo" style={{ marginBottom: "10px" }}>来源：{lastSources.join("、")}</div>
          ) : null}
          {err ? <div className="alert alertErr" style={{ marginBottom: "10px" }}>{err}</div> : null}
          
          <div className="row">
            <input
              className="input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={activeSessionId ? "输入问题..." : "输入问题自动创建新对话..."}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
            />
            <button className="btn btnPrimary" disabled={!canSend} onClick={send} style={{ flexShrink: 0 }}>
              {busy ? "发送中..." : "发送"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
