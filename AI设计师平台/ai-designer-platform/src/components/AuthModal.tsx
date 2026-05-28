import { useState } from 'react'
import { X, Mail, Lock, Loader2, AlertCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { signIn, signUp, isConfigured } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (isLogin) {
        const { error } = await signIn(email, password)
        if (error) throw error
        onClose()
      } else {
        const { error } = await signUp(email, password)
        if (error) throw error
        setSuccess('注册成功!请查收验证邮件。')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-neutral-100 rounded-xl shadow-modal w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-300">
          <h2 className="text-h2 text-neutral-600">
            {isLogin ? '登录' : '注册'}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-neutral-200 transition-colors flex items-center justify-center"
          >
            <X className="w-5 h-5 text-neutral-500" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {!isConfigured && (
            <div className="bg-warning/20 border border-warning/50 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-small text-warning font-medium">演示模式</p>
                <p className="text-caption text-warning/80">
                  Supabase未配置,用户系统不可用
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-error/20 border border-error/50 rounded-lg p-3 text-small text-error">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-success/20 border border-success/50 rounded-lg p-3 text-small text-success">
              {success}
            </div>
          )}

          <div>
            <label className="block text-small font-medium text-neutral-600 mb-2">
              邮箱
            </label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                disabled={!isConfigured}
                className="w-full input-field pl-12"
              />
            </div>
          </div>

          <div>
            <label className="block text-small font-medium text-neutral-600 mb-2">
              密码
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                required
                minLength={6}
                disabled={!isConfigured}
                className="w-full input-field pl-12"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !isConfigured}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>处理中...</span>
              </>
            ) : (
              <span>{isLogin ? '登录' : '注册'}</span>
            )}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin)
                setError(null)
                setSuccess(null)
              }}
              className="text-small text-primary-500 hover:text-primary-600 transition-colors"
            >
              {isLogin ? '没有账号?立即注册' : '已有账号?立即登录'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
