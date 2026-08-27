import { useEffect, useState } from 'react'
import { Save, RotateCcw, MessageSquare, Mail, Send } from 'lucide-react'

const CHANNELS = [
  { value: 'webchat', label: 'Web Chat', icon: MessageSquare },
  { value: 'whatsapp', label: 'WhatsApp (Twilio)', icon: Send },
  { value: 'telegram', label: 'Telegram', icon: Send },
  { value: 'email', label: 'Email (Resend)', icon: Mail },
]

const inputStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 6, fontSize: 14,
  border: '1px solid var(--color-border)', background: 'var(--color-bg)',
  color: 'var(--color-text)', outline: 'none',
} as const

const labelStyle = { display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6 } as const

function Field({ label, value, onChange, placeholder, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={labelStyle}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder} style={inputStyle} />
    </div>
  )
}

export default function Settings() {
  const [settings, setSettings] = useState<any>({})
  const [demoMode, setDemoMode] = useState(true)
  const [storeName, setStoreName] = useState('')
  const [returnWindow, setReturnWindow] = useState(30)
  const [saved, setSaved] = useState(false)

  const [channel, setChannel] = useState('webchat')
  const [twilioSid, setTwilioSid] = useState('')
  const [twilioToken, setTwilioToken] = useState('')
  const [twilioNumber, setTwilioNumber] = useState('whatsapp:+14155238886')
  const [ownerWhatsapp, setOwnerWhatsapp] = useState('')
  const [telegramToken, setTelegramToken] = useState('')
  const [ownerTelegram, setOwnerTelegram] = useState('')
  const [resendKey, setResendKey] = useState('')
  const [supportEmail, setSupportEmail] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [channelSaved, setChannelSaved] = useState(false)

  useEffect(() => {
    fetch('/api/settings').then(r => r.json()).then(d => {
      setSettings(d)
      setDemoMode(d.demo_mode)
      setStoreName(d.store_name)
      setReturnWindow(d.return_window_days)
    })
    fetch('/api/channels').then(r => r.json()).then(d => {
      setChannel(d.channel || 'webchat')
      setTwilioSid(d.twilio_account_sid || '')
      setTwilioToken(d.twilio_auth_token || '')
      setTwilioNumber(d.twilio_whatsapp_number || 'whatsapp:+14155238886')
      setOwnerWhatsapp(d.owner_whatsapp_number || '')
      setTelegramToken(d.telegram_bot_token || '')
      setOwnerTelegram(d.owner_telegram_chat_id || '')
      setResendKey(d.resend_api_key || '')
      setSupportEmail(d.support_email || '')
      setOwnerEmail(d.owner_email || '')
    })
  }, [])

  const saveGeneral = async () => {
    await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_mode: demoMode, store_name: storeName, return_window_days: returnWindow }),
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const saveChannels = async () => {
    await fetch('/api/channels', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        channel, twilio_account_sid: twilioSid, twilio_auth_token: twilioToken,
        twilio_whatsapp_number: twilioNumber, owner_whatsapp_number: ownerWhatsapp,
        telegram_bot_token: telegramToken, owner_telegram_chat_id: ownerTelegram,
        resend_api_key: resendKey, support_email: supportEmail, owner_email: ownerEmail,
      }),
    })
    setChannelSaved(true)
    setTimeout(() => setChannelSaved(false), 2000)
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>Settings</h1>

      {/* General */}
      <div style={{
        background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', padding: 24, marginBottom: 24,
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>General</h2>

        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>Store Name</label>
          <input value={storeName} onChange={e => setStoreName(e.target.value)} style={inputStyle} />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>Return Window (days)</label>
          <input type="number" value={returnWindow} onChange={e => setReturnWindow(Number(e.target.value))}
            style={{ ...inputStyle, width: 120 }} />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <input type="checkbox" checked={demoMode} onChange={e => setDemoMode(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: 'var(--color-primary)' }} />
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Demo Mode</div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Use demo data instead of a real store</div>
            </div>
          </label>
        </div>

        <button onClick={saveGeneral} style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px',
          borderRadius: 8, border: 'none', background: 'var(--color-primary)',
          color: 'white', fontSize: 14, fontWeight: 500, cursor: 'pointer',
        }}>
          {saved ? <RotateCcw size={16} /> : <Save size={16} />}
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>

      {/* Channels */}
      <div style={{
        background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', padding: 24, marginBottom: 24,
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>Channels</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16 }}>
          Configure how customers reach the agent. Web chat works out of the box.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 20 }}>
          {CHANNELS.map(ch => (
            <button key={ch.value} onClick={() => setChannel(ch.value)} style={{
              padding: '10px 8px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: `1px solid ${channel === ch.value ? 'var(--color-primary)' : 'var(--color-border)'}`,
              background: channel === ch.value ? 'var(--color-primary)' + '15' : 'var(--color-bg)',
              color: channel === ch.value ? 'var(--color-primary)' : 'var(--color-text)',
              transition: 'all 0.15s',
            }}>
              {ch.label}
            </button>
          ))}
        </div>

        {channel === 'whatsapp' && (
          <div style={{ padding: 16, borderRadius: 8, background: 'var(--color-bg)', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12, color: 'var(--color-text-muted)' }}>
              Twilio WhatsApp Setup
            </div>
            <Field label="Account SID" value={twilioSid} onChange={setTwilioSid} placeholder="AC..." />
            <Field label="Auth Token" value={twilioToken} onChange={setTwilioToken} placeholder="your auth token" />
            <Field label="Twilio WhatsApp Number" value={twilioNumber} onChange={setTwilioNumber} placeholder="whatsapp:+14155238886" />
            <Field label="Your WhatsApp Number" value={ownerWhatsapp} onChange={setOwnerWhatsapp} placeholder="whatsapp:+234..." />
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
              Set your Twilio WhatsApp sandbox webhook to: <code>https://store-agent-app.onrender.com/webhook/whatsapp</code>
            </div>
          </div>
        )}

        {channel === 'telegram' && (
          <div style={{ padding: 16, borderRadius: 8, background: 'var(--color-bg)', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12, color: 'var(--color-text-muted)' }}>
              Telegram Bot Setup
            </div>
            <Field label="Bot Token" value={telegramToken} onChange={setTelegramToken} placeholder="123456:ABC..." />
            <Field label="Your Chat ID" value={ownerTelegram} onChange={setOwnerTelegram} placeholder="your chat id" />
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
              Message @BotFather on Telegram to create a bot. Then set the webhook by visiting:<br />
              <code>https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://store-agent-app.onrender.com/webhook/telegram</code>
            </div>
          </div>
        )}

        {channel === 'email' && (
          <div style={{ padding: 16, borderRadius: 8, background: 'var(--color-bg)', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12, color: 'var(--color-text-muted)' }}>
              Resend Email Setup
            </div>
            <Field label="Resend API Key" value={resendKey} onChange={setResendKey} placeholder="re_..." />
            <Field label="Support Email" value={supportEmail} onChange={setSupportEmail} placeholder="support@yourdomain.com" />
            <Field label="Your Email" value={ownerEmail} onChange={setOwnerEmail} placeholder="founder@yourdomain.com" />
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
              Sign up at resend.com. Free tier gives 100 emails/day. Verify your domain for production use.
            </div>
          </div>
        )}

        <button onClick={saveChannels} style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px',
          borderRadius: 8, border: 'none', background: 'var(--color-primary)',
          color: 'white', fontSize: 14, fontWeight: 500, cursor: 'pointer',
        }}>
          {channelSaved ? <RotateCcw size={16} /> : <Save size={16} />}
          {channelSaved ? 'Saved!' : 'Save Channel'}
        </button>
      </div>

      {/* System Info */}
      <div style={{
        background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', padding: 20,
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>System Info</h2>
        <div style={{ fontSize: 13, lineHeight: 2, color: 'var(--color-text-muted)' }}>
          <div><strong style={{ color: 'var(--color-text)' }}>LLM Provider:</strong> {settings.llm_provider}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Model:</strong> {settings.llm_model}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Channel:</strong> {channel}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Mode:</strong> {demoMode ? 'Demo (mock data)' : 'Live (real store)'}</div>
        </div>
      </div>
    </div>
  )
}
