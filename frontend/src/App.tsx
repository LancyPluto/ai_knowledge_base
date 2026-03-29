import { NavLink, Route, Routes, Navigate, useLocation, useNavigate } from "react-router-dom"
import { Login, Register, Upload, Docs, Chat, Home } from "./pages"
import { useAuth } from "./auth"

function Protected(props: { children: React.ReactNode }) {
  const { token, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="card"><div className="cardBody">加载中...</div></div>
  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <>{props.children}</>
}

function Sidebar() {
  const { user, token, logout } = useAuth()
  const nav = useNavigate()

  const handleLogout = () => {
    logout()
    nav("/login")
  }

  return (
    <div className="sidebar">
      <div className="brand">
        <div className="brandMark" />
        <div>
          <div className="brandTitle">智能知识库</div>
          <div className="brandSub">RAG · FastAPI · Chroma</div>
        </div>
      </div>
      <div className="nav">
        <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/home">
          主页
        </NavLink>
        <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/upload">
          上传文档
        </NavLink>
        <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/docs">
          文档管理
        </NavLink>
        <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/chat">
          智能问答
        </NavLink>
        {!token && (
          <>
            <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/login">
              登录
            </NavLink>
            <NavLink className={({ isActive }) => "navItem" + (isActive ? " navItemActive" : "")} to="/register">
              注册
            </NavLink>
          </>
        )}
      </div>
      <div className="sidebarFooter">
        <div className="rowWrap" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "nowrap" }}>
          <span className="pill" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '160px' }} title={token && user ? (user.email || user.username) : "未登录"}>
            {token && user ? (user.email || user.username) : "未登录"}
          </span>
          {token && (
            <button className="btn btnGhost" onClick={handleLogout} style={{ padding: '6px 8px', fontSize: '13px', flexShrink: 0 }}>
              退出
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="app">
      <Sidebar />
      <div className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/home" element={<Protected><Home /></Protected>} />
          <Route path="/upload" element={<Protected><Upload /></Protected>} />
          <Route path="/docs" element={<Protected><Docs /></Protected>} />
          <Route path="/chat" element={<Protected><Chat /></Protected>} />
        </Routes>
      </div>
    </div>
  )
}
