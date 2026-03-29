import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { uploadFile } from "../api"

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const nav = useNavigate()
  const canUpload = useMemo(() => !!file && !busy, [file, busy])

  function reset() {
    setFile(null)
    setResult(null)
    setErr(null)
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')
    if (input) input.value = ""
  }

  async function submit() {
    if (!file) return
    setErr(null)
    setBusy(true)
    try {
      const res = await uploadFile(file)
      setResult(res)
    } catch (e: any) {
      setErr(e?.message || "上传失败")
    } finally {
      setBusy(false)
    }
  }
  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">上传文档</div>
          <div className="pageDesc">支持 PDF / DOCX / TXT / Markdown，后台会自动分片与向量化</div>
        </div>
        <div className="rowWrap">
          <button className="btn" onClick={() => nav(-1)}>返回</button>
        </div>
      </div>
      <div className="card">
        <div className="cardBody">
          <div className="grid2">
            <div>
              <div className="field">
                <input className="input" type="file" onChange={e => setFile(e.target.files?.[0] ?? null)} />
              </div>
              <div className="rowWrap">
                <button className="btn btnPrimary" disabled={!canUpload} onClick={submit}>
                  {busy ? "上传中..." : "开始上传"}
                </button>
                <span className="note">{file ? file.name : "请选择一个文件"}</span>
              </div>
              {err ? <div className="alert alertErr" style={{marginTop:10}}>{err}</div> : null}
              {result ? (
                <div style={{marginTop:10}}>
                  <div className="alert alertOk">
                    上传成功：doc_id={result.doc_id}，已开始后台处理
                  </div>
                  <div className="rowWrap" style={{marginTop:10}}>
                    <button className="btn" onClick={reset}>继续上传</button>
                    <button className="btn btnPrimary" onClick={() => nav("/chat")}>智能问答</button>
                    <button className="btn" onClick={() => nav("/docs")}>查看文档</button>
                  </div>
                  <div className="alert alertInfo" style={{marginTop:8}}>
                    提示：后台处理需要几秒~几十秒，处理完成后问答效果更好
                  </div>
                </div>
              ) : null}
            </div>
            <div>
              <div className="note">处理流程</div>
              <div className="divider" />
              <div className="note">
                1) 保存文件到 uploads/<br />
                2) 写入 MySQL 元数据（状态 PROCESSING）<br />
                3) 后台分片 → 向量入库（Chroma）<br />
                4) 成功后状态变为 COMPLETED（失败会记录 error_message）
              </div>
            </div>
          </div>
          {result ? (
            <div style={{marginTop:12}}>
              <div className="note">返回内容</div>
              <pre className="codePanel" style={{marginTop:10}}>{JSON.stringify(result, null, 2)}</pre>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
