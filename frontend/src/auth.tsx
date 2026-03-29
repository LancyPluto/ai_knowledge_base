import { createContext, useContext, useState, useEffect, ReactNode, useMemo } from "react"
import { getMe } from "./api"

interface AuthState {
  token: string | null
  user: any | null
  loading: boolean
  setToken: (t: string | null) => void
  logout: () => void
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthState>({} as any)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(localStorage.getItem("token"))
  const [user, setUser] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  function setToken(t: string | null) {
    if (t) {
      localStorage.setItem("token", t)
    } else {
      localStorage.removeItem("token")
    }
    setTokenState(t)
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  async function refreshMe() {
    const currentToken = localStorage.getItem("token")
    if (!currentToken) {
      setUser(null)
      return
    }
    try {
      const u = await getMe(currentToken)
      setUser(u)
    } catch (e) {
      console.error("fetch me failed", e)
      // DO NOT clear token immediately on failed fetch in case it's a temporary network error
      // setToken(null)
      // setUser(null)
    }
  }

  useEffect(() => {
    async function init() {
      setLoading(true)
      await refreshMe()
      setLoading(false)
    }
    init()
  }, [token]) // Re-run when token state changes

  const value = useMemo<AuthState>(
    () => ({
      token,
      user,
      loading,
      setToken,
      logout,
      refreshMe,
    }),
    [token, user, loading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}

