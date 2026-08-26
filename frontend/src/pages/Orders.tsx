import { useEffect, useState } from 'react'
import { Package, Search, ExternalLink } from 'lucide-react'

interface Order {
  id: number
  order_number: number
  customer_name: string
  customer_email: string
  total: string
  currency: string
  status: string
  fulfillment: string
  created_at: string
  tracking_company: string
  tracking_number: string
  tracking_url: string
}

const PAY_COLORS: Record<string, string> = {
  paid: '#22C55E', authorized: '#F59E0B', partially_paid: '#F59E0B',
  pending: '#F59E0B', refunded: '#EF4444', voided: '#EF4444',
}
const FUL_COLORS: Record<string, string> = {
  fulfilled: '#22C55E', partial: '#F59E0B', unfulfilled: '#9CA3AF',
}
const label = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '—')

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [query, setQuery] = useState('')
  const [pay, setPay] = useState('')
  const [ful, setFul] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetch('/api/orders')
      .then(r => r.json())
      .then(d => { setOrders(d.orders || []); setLoaded(true) })
  }, [])

  const q = query.toLowerCase()
  const filtered = orders
    .filter(o => !pay || o.status === pay)
    .filter(o => !ful || o.fulfillment === ful)
    .filter(o => !q
      || String(o.order_number).includes(q.replace('#', ''))
      || o.customer_name.toLowerCase().includes(q)
      || o.customer_email.toLowerCase().includes(q))
    .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))

  const badge = (text: string, colors: Record<string, string>) => (
    <span style={{
      fontSize: 12, fontWeight: 500,
      color: colors[text.toLowerCase()] || 'var(--color-text-muted)',
      background: (colors[text.toLowerCase()] || '#9CA3AF') + '20',
      padding: '3px 10px', borderRadius: 12,
    }}>{label(text)}</span>
  )

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>Orders</h1>

      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: 11, color: 'var(--color-text-muted)' }} />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search order #, customer, or email..."
            style={{
              width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8,
              border: '1px solid var(--color-border)', fontSize: 14,
              background: 'var(--color-surface)', color: 'var(--color-text)', outline: 'none',
            }}
          />
        </div>
        <select value={pay} onChange={e => setPay(e.target.value)} style={selectStyle}>
          <option value="">All payments</option>
          {[...new Set(orders.map(o => o.status))].filter(Boolean).sort().map(s => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </select>
        <select value={ful} onChange={e => setFul(e.target.value)} style={selectStyle}>
          <option value="">All fulfillment</option>
          {[...new Set(orders.map(o => o.fulfillment))].filter(Boolean).sort().map(s => (
            <option key={s} value={s}>{label(s)}</option>
          ))}
        </select>
      </div>

      <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        {filtered.length} of {orders.length} orders
      </div>

      <div style={{
        background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', overflowX: 'auto',
      }}>
        {loaded && filtered.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 14 }}>
            <Package size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            No orders match. Clear the search or filters.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--color-text-muted)', fontSize: 12 }}>
                {['Order', 'Customer', 'Total', 'Payment', 'Fulfillment', 'Placed', 'Tracking'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(o => (
                <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={cellStyle}><b>#{o.order_number}</b></td>
                  <td style={cellStyle}>
                    <div>{o.customer_name || '—'}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{o.customer_email}</div>
                  </td>
                  <td style={cellStyle}>{o.currency} {o.total}</td>
                  <td style={cellStyle}>{badge(o.status, PAY_COLORS)}</td>
                  <td style={cellStyle}>{badge(o.fulfillment, FUL_COLORS)}</td>
                  <td style={{ ...cellStyle, fontSize: 12, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                    {(o.created_at || '').slice(0, 10)}
                  </td>
                  <td style={cellStyle}>
                    {o.tracking_number ? (
                      <a href={o.tracking_url || '#'} target="_blank" rel="noopener"
                        style={{ color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {o.tracking_company || 'Track'} <ExternalLink size={12} />
                      </a>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

const cellStyle = { padding: '12px 16px', verticalAlign: 'top' } as const
const selectStyle = {
  padding: '10px 12px', borderRadius: 8, fontSize: 14,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)', color: 'var(--color-text)',
} as const
