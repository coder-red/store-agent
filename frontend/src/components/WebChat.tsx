import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function WebChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I\'m your store support agent. Try asking me:\n• "Where is my order?"\n• "Can I return order #1001?"\n• "Tell me about your backpacks"\n• "What\'s the status of order #1006?"' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(m => [...m, { role: 'user', content: userMsg }])
    setLoading(true)
    try {
      const res = await fetch('/webhook/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, customer_identifier: 'dashboard-user' }),
      })
      const data = await res.json()
      setMessages(m => [...m, { role: 'assistant', content: data.response || 'No response' }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Sorry, I encountered an error.' }])
    }
    setLoading(false)
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: 380,
      background: 'var(--color-bg)', borderRadius: 8,
      border: '1px solid var(--color-border)', overflow: 'hidden',
    }}>
      <div style={{ flex: 1, overflow: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            display: 'flex', gap: 8, alignItems: 'flex-start',
            flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: 6, flexShrink: 0,
              background: m.role === 'user' ? 'var(--color-primary)' : 'var(--color-surface-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div style={{
              maxWidth: '80%', padding: '8px 12px', borderRadius: 8, fontSize: 13, lineHeight: 1.5, whiteSpace: 'pre-wrap',
              background: m.role === 'user' ? 'var(--color-primary)' : 'var(--color-surface-light)',
              color: m.role === 'user' ? 'white' : 'var(--color-text)',
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--color-text-muted)', fontSize: 13, padding: 4 }}>
            <Bot size={14} /> Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--color-border)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask about an order, product, or return..."
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)', color: 'var(--color-text)',
            fontSize: 13, outline: 'none',
          }}
        />
        <button onClick={send} disabled={loading} style={{
          padding: '8px 12px', borderRadius: 6, border: 'none',
          background: 'var(--color-primary)', color: 'white', cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.5 : 1, display: 'flex', alignItems: 'center',
        }}>
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
