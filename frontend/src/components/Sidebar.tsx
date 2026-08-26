import { NavLink } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, Package, BarChart3, Settings, HeadphonesIcon, Mail, ShoppingCart, FileText } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/conversations', label: 'Conversations', icon: MessageSquare },
  { to: '/orders', label: 'Orders', icon: Package },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/email', label: 'Email Inbox', icon: Mail },
  { to: '/cart-recovery', label: 'Cart Recovery', icon: ShoppingCart },
  { to: '/product-descriptions', label: 'Descriptions', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside style={{
      width: 240,
      background: 'var(--color-surface)',
      borderRight: '1px solid var(--color-border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 40, paddingLeft: 8 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: 'var(--color-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <HeadphonesIcon size={20} color="white" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>Support AI</div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Store Agent</div>
        </div>
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {links.map(l => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 12px', borderRadius: 8,
              fontSize: 14, fontWeight: 500,
              textDecoration: 'none',
              color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)',
              background: isActive ? 'var(--color-surface-light)' : 'transparent',
              transition: 'all 0.15s',
            })}
          >
            <l.icon size={18} />
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ marginTop: 'auto', padding: '12px', borderRadius: 8, background: 'var(--color-surface-light)', fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
        <div style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>Demo Mode</div>
        Running with demo store data. No real store connected.
      </div>
    </aside>
  )
}
