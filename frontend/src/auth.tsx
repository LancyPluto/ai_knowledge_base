import React, { createContext, useContext, useEffect, useMemo, useState } from "react"
import { me as apiMe } from "./api"

type AuthUser = { id: string; username: string; is_active: boolean }

type AuthState = {
  token: string | null
  user: AuthUser | null
  loading: boolean
  setToken: (token: string | null) => void
  refreshMe: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider(props: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem("token"))
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  function setToken(t: string | null) {
    if (t) localStorage.setItem("token", t)
    else localStorage.removeItem("token")
    setTokenState(t)
  }

  async function refreshMe() {
    if (!token) {
      setUser(null)
      return
    }
    try {
      const u = await apiMe()
      setUser(u)
    } catch {
      setToken(null)
      setUser(null)
    }
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    ;(async () => {
      setLoading(true)
      await refreshMe()
      setLoading(false)
    })()
  }, [token])

  const value = useMemo<AuthState>(
    () => ({ token, user, loading, setToken, refreshMe, logout }),
    [token, user, loading]
  )

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("AuthProvider missing")
  return ctx
}

