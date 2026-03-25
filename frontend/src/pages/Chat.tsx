import { useEffect, useMemo, useState } from "react"
import { chatStream, closeSession } from "../api"
import { useNavigate } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

export default function Chat() {
  const [sessionId, setSessionId] = useState<string>(()=>Math.random().toString(36).slice(2))
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<{role:string;content:string}[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [lastSources, setLastSources] = useState<string[]>([])
  const nav = useNavigate()

  const canSend = useMemo(() => !!input.trim() && !busy, [input, busy])

  async function send() {
    if (!input.trim() || busy) return
    const q = input
    setErr(null)
    setBusy(true)
    const assistantIndex = messages.length + 1
    setMessages(m=>[...m,{role:"user",content:q},{role:"assistant",content:""}])
    setInput("")
    try {
      await chatStream(q, sessionId, (evt) => {
        if (evt?.type === "start") {
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
  async function reset() {
    setBusy(true)
    setErr(null)
    try {
      await closeSession(sessionId)
    } catch {}
    setSessionId(Math.random().toString(36).slice(2))
    setMessages([])
    setLastSources([])
    setBusy(false)
  }
  useEffect(()=>{},[sessionId])
  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">智能问答</div>
          <div className="pageDesc">基于你上传的文档检索后回答，临时会话仅在当前会话有效</div>
        </div>
        <div className="rowWrap">
          <button className="btn" disabled={busy} onClick={() => nav(-1)}>返回</button>
          <span className="pill">session_id: {sessionId}</span>
          <button className="btn" disabled={busy} onClick={reset}>关闭并新建</button>
        </div>
      </div>
      <div className="card">
        <div className="cardBody">
          <div className="chatBox">
            {messages.length === 0 ? (
              <div className="note">从一个问题开始，例如：请总结刚上传文档的要点</div>
            ) : null}
            {messages.map((m,i)=>(
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
            <div className="note" style={{marginTop:10}}>来源：{lastSources.join("、")}</div>
          ) : null}
          {err ? <div className="note error" style={{marginTop:10}}>{err}</div> : null}
          <div className="row" style={{marginTop:12}}>
            <input
              className="input"
              value={input}
              onChange={e=>setInput(e.target.value)}
              placeholder="输入问题..."
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
            />
            <button className="btn btnPrimary" disabled={!canSend} onClick={send}>
              {busy ? "发送中..." : "发送"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
