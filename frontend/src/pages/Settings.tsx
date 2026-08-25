import { useEffect, useState } from 'react'
import { Save, RotateCcw } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState<any>({})
  const [demoMode, setDemoMode] = useState(true)
  const [storeName, setStoreName] = useState('')
  const [returnWindow, setReturnWindow] = useState(30)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch('/api/settings')
      .then(r => r.json())
      .then(d => {
        setSettings(d)
        setDemoMode(d.demo_mode)
        setStoreName(d.store_name)
        setReturnWindow(d.return_window_days)
      })
  }, [])

  const save = async () => {
    await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_mode: demoMode, store_name: storeName, return_window_days: returnWindow }),
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div style={{ maxWidth: 700 }}>
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>Settings</h1>

      <div style={{
        background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', padding: 24,
      }}>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Store Name</label>
          <input value={storeName} onChange={e => setStoreName(e.target.value)}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 6, fontSize: 14,
              border: '1px solid var(--color-border)', background: 'var(--color-bg)',
              color: 'var(--color-text)', outline: 'none',
            }}
          />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Return Window (days)</label>
          <input type="number" value={returnWindow} onChange={e => setReturnWindow(Number(e.target.value))}
            style={{
              width: 120, padding: '10px 12px', borderRadius: 6, fontSize: 14,
              border: '1px solid var(--color-border)', background: 'var(--color-bg)',
              color: 'var(--color-text)', outline: 'none',
            }}
          />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <input type="checkbox" checked={demoMode} onChange={e => setDemoMode(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: 'var(--color-primary)' }}
            />
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Demo Mode</div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Use demo data instead of a real store</div>
            </div>
          </label>
        </div>

        <button onClick={save} style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px',
          borderRadius: 8, border: 'none', background: 'var(--color-primary)',
          color: 'white', fontSize: 14, fontWeight: 500, cursor: 'pointer',
        }}>
          {saved ? <RotateCcw size={16} /> : <Save size={16} />}
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>

      <div style={{
        marginTop: 24, background: 'var(--color-surface)', borderRadius: 12,
        border: '1px solid var(--color-border)', padding: 20,
      }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>System Info</h2>
        <div style={{ fontSize: 13, lineHeight: 2, color: 'var(--color-text-muted)' }}>
          <div><strong style={{ color: 'var(--color-text)' }}>LLM Provider:</strong> {settings.llm_provider}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Model:</strong> {settings.llm_model}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Channel:</strong> {settings.channel}</div>
          <div><strong style={{ color: 'var(--color-text)' }}>Mode:</strong> {settings.demo_mode ? 'Demo (mock data)' : 'Live (real store)'}</div>
        </div>
      </div>
    </div>
  )
}
