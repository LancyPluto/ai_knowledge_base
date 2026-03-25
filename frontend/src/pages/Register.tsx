import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { register } from "../api"

export default function Register() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [info, setInfo] = useState<{ type: "ok" | "err"; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function doRegister() {
    setInfo(null)
    setBusy(true)
    try {
      await register(username, password)
      setInfo({ type: "ok", text: "注册成功，即将跳转到登录页" })
      setTimeout(() => nav("/login"), 1000)
    } catch (e: any) {
      setInfo({ type: "err", text: e?.message || "注册失败" })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="topbar">
        <div>
          <div className="pageTitle">注册</div>
          <div className="pageDesc">创建你的账号后，前往登录获取访问令牌</div>
        </div>
        <div className="rowWrap">
          <button className="btn" onClick={() => nav(-1)}>返回</button>
          <button className="btn" onClick={() => nav("/login")}>去登录</button>
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
                <button className="btn btnPrimary" disabled={busy} onClick={doRegister}>注册</button>
              </div>
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
                - 注册成功后会自动跳转到登录界面<br />
                - 登录成功后进入主页选择操作<br />
                - 每个用户的数据互相隔离
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
