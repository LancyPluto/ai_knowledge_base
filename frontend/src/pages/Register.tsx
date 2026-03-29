import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { register, sendCode } from "../api"

export default function Register() {
  const [email, setEmail] = useState("")
  const [code, setCode] = useState("")
  const [password, setPassword] = useState("")
  const [info, setInfo] = useState<{ type: "ok" | "err"; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [codeBusy, setCodeBusy] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const nav = useNavigate()

  async function doSendCode() {
    if (!email) {
      setInfo({ type: "err", text: "请先输入邮箱" })
      return
    }
    setInfo(null)
    setCodeBusy(true)
    try {
      await sendCode(email, "register")
      setInfo({ type: "ok", text: "验证码已发送，请查收邮件" })
      setCountdown(60)
      const timer = setInterval(() => {
        setCountdown((c) => {
          if (c <= 1) {
            clearInterval(timer)
            return 0
          }
          return c - 1
        })
      }, 1000)
    } catch (e: any) {
      setInfo({ type: "err", text: e?.message || "发送验证码失败" })
    } finally {
      setCodeBusy(false)
    }
  }

  async function doRegister() {
    if (!email || !code || !password) {
      setInfo({ type: "err", text: "请填写完整信息" })
      return
    }
    setInfo(null)
    setBusy(true)
    try {
      await register(email, code, password)
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
                <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="邮箱地址" />
              </div>
              <div className="field rowWrap">
                <input className="input" style={{flex: 1}} value={code} onChange={e => setCode(e.target.value)} placeholder="6位验证码" />
                <button 
                  className="btn" 
                  disabled={codeBusy || countdown > 0} 
                  onClick={doSendCode}
                >
                  {countdown > 0 ? `${countdown}s 后重试` : "获取验证码"}
                </button>
              </div>
              <div className="field">
                <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="密码" />
              </div>
              <div className="rowWrap">
                <button className="btn btnPrimary" disabled={busy} onClick={doRegister}>注册</button>
              </div>
              {info ? (
                <div className={"alert " + (info.type === "ok" ? "alertOk" : "alertErr")} style={{marginTop:10}}>
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
                - 每个用户的数据互相隔离<br />
                - 如果收不到验证码，请检查垃圾邮件箱
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
