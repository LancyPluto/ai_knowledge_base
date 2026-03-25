import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { deleteDoc, listDocs, reuploadDoc } from "../api"

export default function Docs() {
  const [docs, setDocs] = useState<any[]>([])
  const [busyId, setBusyId] = useState<number | null>(null)
  const [files, setFiles] = useState<Record<number, File | null>>({})
  const [err, setErr] = useState<string | null>(null)
  const nav = useNavigate()

  const statusBadge = useMemo(() => {
    return (status: string) => {
      const s = (status || "").toUpperCase()
      if (s === "COMPLETED") return "badge badgeOk"
      if (s === "FAILED") return "badge badgeErr"
      if (s === "PROCESSING") return "badge badgeWarn"
      return "badge"
    }
  }, [])

  async function load() {
    setErr(null)
    try {
      const res = await listDocs()
      setDocs(res)
    } catch (e: any) {
      setErr(e?.message || "加载失败")
    }
  }
  useEffect(()=>{ load() },[])
  async function remove(id: number) {
    setBusyId(id)
    setErr(null)
    try {
      await deleteDoc(id)
      await load()
    } catch (e: any) {
      setErr(e?.message || "删除失败")
    } finally {
      setBusyId(null)
    }
  }
  async function reupload(id: number) {
    const f = files[id]
    if (!f) return
    setBusyId(id)
    setErr(null)
    try {
      await reuploadDoc(id, f)
      setFiles(prev => ({ ...prev, [id]: null }))
      await load()
    } catch (e: any) {
      setErr(e?.message || "重传失败")
    } finally {
      setBusyId(null)
    }
  }
  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">文档管理</div>
          <div className="pageDesc">查看处理状态、失败原因，并支持删除与重传</div>
        </div>
        <div className="rowWrap">
          <button className="btn" onClick={() => nav(-1)}>返回</button>
          <button className="btn" onClick={load}>刷新</button>
        </div>
      </div>
      <div className="card">
        <div className="cardBody">
          {err ? <div className="note error" style={{marginBottom:10}}>{err}</div> : null}
          <table className="table">
            <thead>
              <tr>
                <th>文档</th>
                <th>状态</th>
                <th>失败原因</th>
                <th style={{width: 340}}>操作</th>
              </tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td>{d.filename}</td>
                  <td><span className={statusBadge(d.status)}>{d.status}</span></td>
                  <td className="note">{d.error_message || "-"}</td>
                  <td>
                    <div className="rowWrap">
                      <button className="btn btnDanger" disabled={busyId === d.id} onClick={() => remove(d.id)}>
                        {busyId === d.id ? "处理中..." : "删除"}
                      </button>
                      <input
                        className="input"
                        style={{ width: 190, padding: "8px 10px" }}
                        type="file"
                        onChange={e => setFiles(prev => ({ ...prev, [d.id]: e.target.files?.[0] ?? null }))}
                      />
                      <button className="btn" disabled={busyId === d.id || !files[d.id]} onClick={() => reupload(d.id)}>
                        重传
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {docs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="note">暂无文档</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
