import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Conversations from './pages/Conversations'
import ConversationDetail from './pages/ConversationDetail'
import Orders from './pages/Orders'
import Analytics from './pages/Analytics'
import Email from './pages/Email'
import CartRecovery from './pages/CartRecovery'
import ProductDescriptions from './pages/ProductDescriptions'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto', padding: '32px', background: 'var(--color-bg)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/conversations" element={<Conversations />} />
          <Route path="/conversations/:id" element={<ConversationDetail />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/email" element={<Email />} />
          <Route path="/cart-recovery" element={<CartRecovery />} />
          <Route path="/product-descriptions" element={<ProductDescriptions />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
