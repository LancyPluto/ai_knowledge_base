import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { login } from "../api"
import { useAuth } from "../auth"

export default function Login() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [info, setInfo] = useState<{ type: "ok" | "err"; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const { setToken, refreshMe } = useAuth()
  const nav = useNavigate()
  const location = useLocation() as any
  const nextPath = location?.state?.from || "/home"

  async function doLogin() {
    setInfo(null)
    setBusy(true)
    try {
      const res = await login(username, password)
      setToken(res.access_token)
      await refreshMe()
      setInfo({ type: "ok", text: "登录成功" })
      nav(nextPath)
    } catch (e: any) {
      setInfo({ type: "err", text: e?.message || "登录失败" })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">登录 / 注册</div>
          <div className="pageDesc">获取访问令牌后，才能上传与检索你的文档</div>
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
                <input className="input" value={username} onChange={e => setUsername(e.target.value)} placeholder="用户名" />
              </div>
              <div className="field">
                <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="密码" />
              </div>
              <div className="rowWrap">
                <button className="btn btnPrimary" disabled={busy} onClick={doLogin}>登录</button>
          <button className="btn" onClick={() => nav("/register")}>去注册</button>
              </div>
              <div className="note" style={{marginTop:10}}>登录成功后会自动跳转到上传页</div>
              {info ? (
                <div className={"note " + (info.type === "ok" ? "success" : "error")} style={{marginTop:10}}>
                  {info.text}
                </div>
              ) : null}
            </div>
            <div>
              <div className="note">提示</div>
              <div className="divider" />
              <div className="note">
                - token 会保存在本地浏览器存储中<br />
                - token 过期后需要重新登录获取新 token<br />
                - 每个用户只能访问自己上传的文档
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
