import { useState, useRef, useEffect } from 'react'
import ChatMessage from '../components/ChatMessage'
import UploadPanel from '../components/UploadPanel'
import { sendQuery } from '../api/client'

const MODELS = [
  { id: 'all-MiniLM-L6-v2', label: 'MiniLM-L6' },
  { id: 'BAAI/bge-large-en-v1.5', label: 'BGE-large' },
  { id: 'openai', label: 'OpenAI' },
]

function SkeletonBubble() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[60%] bg-surface rounded-2xl px-4 py-3 space-y-2">
        <div className="h-3 rounded-full shimmer w-48" />
        <div className="h-3 rounded-full shimmer w-64" />
        <div className="h-3 rounded-full shimmer w-36" />
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [embModel, setEmbModel] = useState('all-MiniLM-L6-v2')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const history = messages.map((m) => ({ role: m.role, content: m.content }))

  async function handleSend() {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    inputRef.current?.focus()

    setMessages((prev) => [...prev, { role: 'user', content: q, timestamp: new Date().toISOString() }])
    setLoading(true)

    try {
      const { data } = await sendQuery({
        query: q,
        session_id: sessionId,
        history: history.slice(-6),
        embedding_model: embModel,
      })
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: data.answer,
        intent: data.intent,
        intent_confidence: data.intent_confidence,
        groundedness_score: data.groundedness_score,
        flagged: data.flagged,
        sources: data.sources,
        rewritten_query: data.rewritten_query,
        timestamp: data.timestamp,
      }])
    } catch (e) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '⚠ ' + (e.response?.data?.detail || e.message),
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#0d0d0f]">

      {/* ── Sidebar — hidden on mobile, visible on md+ ── */}
      <aside
        className={`hidden md:flex flex-col shrink-0 bg-surface transition-all duration-200 ease-in-out overflow-hidden
          ${sidebarOpen ? 'w-64' : 'w-14'}`}
      >
        {/* Logo row */}
        <div className="flex items-center h-14 px-3 gap-3 shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-8 h-8 rounded-2xl bg-accent flex items-center justify-center shrink-0
              hover:bg-accent-hover transition-colors duration-150"
            aria-label="Toggle sidebar"
          >
            <span className="font-semibold text-sm text-white">M</span>
          </button>
          {sidebarOpen && (
            <span className="font-semibold text-body whitespace-nowrap overflow-hidden">MokoMax AI</span>
          )}
        </div>

        {sidebarOpen && (
          <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-5">
            <UploadPanel />
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-muted uppercase tracking-widest">Embedding</p>
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setEmbModel(m.id)}
                  className={`w-full text-left text-sm px-3 py-1.5 rounded-2xl transition-colors duration-150
                    ${embModel === m.id ? 'bg-accent/20 text-accent font-semibold' : 'text-muted hover:bg-white/5'}`}
                >
                  {m.label}
                </button>
              ))}
            </div>
            <a href="/admin" className="block text-[11px] text-muted hover:text-accent transition-colors duration-150">
              Admin / Eval →
            </a>
          </div>
        )}

        {!sidebarOpen && (
          <div className="flex flex-col items-center gap-3 pt-2 px-3">
            <a href="/admin" title="Admin Dashboard"
              className="w-8 h-8 flex items-center justify-center rounded-2xl text-muted hover:text-accent hover:bg-white/5 transition-colors duration-150">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </a>
          </div>
        )}
      </aside>

      {/* ── Mobile drawer overlay ── */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div className={`md:hidden fixed inset-y-0 left-0 z-50 w-72 bg-surface flex flex-col
        transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between h-14 px-4 shrink-0">
          <span className="font-semibold text-body">MokoMax AI</span>
          <button onClick={() => setSidebarOpen(false)}
            className="w-8 h-8 flex items-center justify-center rounded-xl text-muted hover:text-body">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 pb-6 space-y-5">
          <UploadPanel />
          <div className="space-y-2">
            <p className="text-[11px] font-semibold text-muted uppercase tracking-widest">Embedding</p>
            {MODELS.map((m) => (
              <button
                key={m.id}
                onClick={() => { setEmbModel(m.id); setSidebarOpen(false) }}
                className={`w-full text-left text-sm px-3 py-2 rounded-2xl transition-colors duration-150
                  ${embModel === m.id ? 'bg-accent/20 text-accent font-semibold' : 'text-muted hover:bg-white/5'}`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <a href="/admin" className="block text-sm text-muted hover:text-accent transition-colors duration-150">
            Admin / Eval →
          </a>
        </div>
      </div>

      {/* ── Main chat area ── */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Mobile top bar */}
        <div className="md:hidden flex items-center h-14 px-4 gap-3 bg-surface shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-8 h-8 rounded-2xl bg-accent flex items-center justify-center shrink-0"
            aria-label="Open menu"
          >
            <span className="font-semibold text-sm text-white">M</span>
          </button>
          <span className="font-semibold text-body text-sm">MokoMax AI</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 sm:py-6 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-full gap-3 select-none px-4 text-center">
              <div className="w-12 h-12 rounded-2xl bg-accent/20 flex items-center justify-center">
                <span className="text-2xl">✦</span>
              </div>
              <p className="font-semibold text-body">Ask anything about your documents</p>
              <p className="text-sm text-muted">Upload a PDF, DOCX, or TXT to get started</p>
            </div>
          )}

          {messages.map((msg, i) => <ChatMessage key={i} msg={msg} />)}
          {loading && <SkeletonBubble />}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-3 sm:px-4 pb-4 pt-2">
          <div className="flex items-center gap-2 bg-surface rounded-2xl px-4 py-2
            focus-within:shadow-accent-glow transition-shadow duration-150">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask a question…"
              className="flex-1 bg-transparent text-sm text-body placeholder:text-muted outline-none py-1"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              aria-label="Send"
              className="w-8 h-8 rounded-xl bg-accent hover:bg-accent-hover disabled:opacity-30
                flex items-center justify-center shrink-0 transition-colors duration-150"
            >
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
