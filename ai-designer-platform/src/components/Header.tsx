import { Palette, History, Settings, Bookmark, Menu, X } from 'lucide-react'
import { useState } from 'react'

interface HeaderProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems = [
    { id: 'workspace', label: '工作台', icon: Palette },
    { id: 'templates', label: '模板库', icon: Bookmark },
    { id: 'history', label: '历史记录', icon: History },
    { id: 'settings', label: '设置', icon: Settings },
  ]

  return (
    <>
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
          <Palette className="w-5 h-5 text-white" />
        </div>
        <span className="text-h3 text-neutral-600 font-semibold hidden sm:block">
          AI设计师工作台
        </span>
      </div>

      {/* Desktop Navigation */}
      <nav className="hidden md:flex items-center gap-1 absolute left-1/2 -translate-x-1/2">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-150 ${
              activeTab === item.id
                ? 'bg-neutral-200 text-primary-500'
                : 'text-neutral-500 hover:bg-neutral-200 hover:text-neutral-600'
            }`}
          >
            <item.icon className="w-4 h-4" />
            <span className="text-small font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Mobile Menu Button */}
      <button
        className="md:hidden p-2 rounded-md hover:bg-neutral-200 transition-colors absolute right-16"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        {mobileMenuOpen ? (
          <X className="w-6 h-6 text-neutral-500" />
        ) : (
          <Menu className="w-6 h-6 text-neutral-500" />
        )}
      </button>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed top-16 left-0 right-0 bg-neutral-100 border-b border-neutral-300 shadow-modal z-40">
          <nav className="flex flex-col p-2">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id)
                  setMobileMenuOpen(false)
                }}
                className={`flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-150 ${
                  activeTab === item.id
                    ? 'bg-neutral-200 text-primary-500'
                    : 'text-neutral-500 hover:bg-neutral-200'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
      )}
    </>
  )
}
