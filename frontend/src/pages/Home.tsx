import { useNavigate } from "react-router-dom"
import { useAuth } from "../auth"

export default function Home() {
  const nav = useNavigate()
  const { user } = useAuth()
  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">主页</div>
          <div className="pageDesc">选择你要进行的操作：上传文档、智能问答或管理文档</div>
        </div>
      </div>
      <div className="grid2">
        <div className="card">
          <div className="cardBody">
            <div className="pageTitle">上传文档</div>
            <div className="note">支持 PDF / DOCX / TXT / Markdown，后台自动分片与向量化。</div>
            <div className="rowWrap" style={{marginTop:12}}>
              <button className="btn btnPrimary" onClick={() => nav("/upload")}>前往上传</button>
              <span className="pill">{user ? `当前用户：${user.username}` : "未登录"}</span>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="cardBody">
            <div className="pageTitle">智能问答</div>
            <div className="note">基于你上传的文档进行检索后回答，支持临时会话。</div>
            <div className="rowWrap" style={{marginTop:12}}>
              <button className="btn btnPrimary" onClick={() => nav("/chat")}>开始聊天</button>
              <button className="btn" onClick={() => nav("/docs")}>查看文档</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
