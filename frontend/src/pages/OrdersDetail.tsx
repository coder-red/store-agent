import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Package, ExternalLink, Truck, Mail, CreditCard } from 'lucide-react'

interface LineItem {
  title: string
  quantity: number
  price: string
  sku: string
}

interface OrderDetail {
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
  line_items: LineItem[]
}

const PAY_COLORS: Record<string, string> = {
  paid: '#22C55E', authorized: '#F59E0B', partially_paid: '#F59E0B',
  pending: '#F59E0B', refunded: '#EF4444', voided: '#EF4444',
}
const FUL_COLORS: Record<string, string> = {
  fulfilled: '#22C55E', partial: '#F59E0B', unfulfilled: '#9CA3AF',
}
const label = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '—')

function Badge({ text, colors }: { text: string; colors: Record<string, string> }) {
  const c = colors[text.toLowerCase()] || '#9CA3AF'
  return (
    <span style={{ fontSize: 12, fontWeight: 500, color: c, background: c + '20', padding: '3px 10px', borderRadius: 12 }}>
      {label(text)}
    </span>
  )
}

export default function OrdersDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState<OrderDetail | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    fetch(`/api/orders/${id}`)
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then(setOrder)
      .catch(() => setNotFound(true))
  }, [id])

  if (notFound) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--color-text-muted)' }}>
        <Package size={44} style={{ margin: '0 auto 12px', opacity: 0.4, display: 'block' }} />
        <div>Order not found.</div>
        <button onClick={() => navigate('/orders')} style={{
          marginTop: 12, background: 'none', border: 'none', color: 'var(--color-primary)',
          cursor: 'pointer', fontSize: 14,
        }}>Back to Orders</button>
      </div>
    )
  }

  if (!order) return <div style={{ color: 'var(--color-text-muted)' }}>Loading...</div>

  const itemsTotal = order.line_items.reduce((sum, li) => sum + parseFloat(li.price) * li.quantity, 0)

  return (
    <div style={{ maxWidth: 860 }}>
      <button onClick={() => navigate('/orders')} style={{
        display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-muted)',
        background: 'none', border: 'none', cursor: 'pointer', fontSize: 13, marginBottom: 16, padding: 0,
      }}>
        <ArrowLeft size={16} /> Back to Orders
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ width: 44, height: 44, borderRadius: 10, background: 'var(--color-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Package size={22} />
        </div>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 600, margin: 0 }}>Order #{order.order_number}</h1>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 2 }}>
            Placed {new Date(order.created_at).toLocaleString()}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginLeft: 'auto' }}>
          <Badge text={order.status} colors={PAY_COLORS} />
          <Badge text={order.fulfillment} colors={FUL_COLORS} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
        <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 12, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 12 }}>
            <Mail size={14} /> Customer
          </div>
          <div style={{ fontSize: 15, fontWeight: 600 }}>{order.customer_name}</div>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 2 }}>{order.customer_email}</div>
        </div>

        <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 12, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 12 }}>
            <Truck size={14} /> Shipment
          </div>
          {order.tracking_number ? (
            <a href={order.tracking_url || '#'} target="_blank" rel="noopener"
              style={{ color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              {order.tracking_company || 'Tracking'} · {order.tracking_number} <ExternalLink size={13} />
            </a>
          ) : (
            <div style={{ color: 'var(--color-text-muted)', fontSize: 14 }}>Not yet shipped</div>
          )}
        </div>

        <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 12, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 12 }}>
            <CreditCard size={14} /> Total
          </div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{order.currency} {order.total}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{order.line_items.length} line item(s)</div>
        </div>
      </div>

      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', fontWeight: 600, fontSize: 15 }}>
          Items
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--color-text-muted)', fontSize: 12 }}>
              {['Item', 'SKU', 'Price', 'Qty', 'Line total'].map(h => (
                <th key={h} style={{ padding: '10px 20px', borderBottom: '1px solid var(--color-border)', fontWeight: 500 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {order.line_items.map((li, i) => (
              <tr key={i} style={{ borderBottom: i === order.line_items.length - 1 ? 'none' : '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 20px' }}>{li.title}</td>
                <td style={{ padding: '12px 20px', color: 'var(--color-text-muted)', fontSize: 13 }}>{li.sku || '—'}</td>
                <td style={{ padding: '12px 20px' }}>{order.currency} {li.price}</td>
                <td style={{ padding: '12px 20px' }}>{li.quantity}</td>
                <td style={{ padding: '12px 20px', fontWeight: 600 }}>{order.currency} {(parseFloat(li.price) * li.quantity).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '14px 20px', display: 'flex', justifyContent: 'flex-end', gap: 8, borderTop: '1px solid var(--color-border)', background: 'var(--color-surface-light)', fontSize: 14 }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Subtotal</span>
          <span style={{ fontWeight: 700 }}>{order.currency} {itemsTotal.toFixed(2)}</span>
        </div>
      </div>
    </div>
  )
}
