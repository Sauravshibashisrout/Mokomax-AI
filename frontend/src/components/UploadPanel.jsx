import { useState } from 'react'
import { ingestDocument } from '../api/client'

const STRATEGIES = ['fixed', 'recursive', 'semantic']
const MODELS = ['all-MiniLM-L6-v2', 'BAAI/bge-large-en-v1.5', 'openai']

export default function UploadPanel({ onUploaded }) {
  const [file, setFile] = useState(null)
  const [strategy, setStrategy] = useState('fixed')
  const [model, setModel] = useState('all-MiniLM-L6-v2')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setStatus(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('chunking_strategy', strategy)
    fd.append('embedding_model', model)
    try {
      const { data } = await ingestDocument(fd)
      setStatus({ ok: true, msg: `${data.num_chunks} chunks ingested` })
      onUploaded?.(data)
    } catch (e) {
      setStatus({ ok: false, msg: e.response?.data?.detail || 'Upload failed' })
    } finally {
      setLoading(false)
    }
  }

  const selectCls = "w-full bg-white/5 rounded-2xl px-3 py-1.5 text-sm text-body outline-none focus-visible:shadow-accent-glow transition-shadow duration-150 appearance-none cursor-pointer"

  return (
    <div className="space-y-3">
      <p className="text-[11px] font-semibold text-muted uppercase tracking-widest">Document</p>

      {/* Drop zone */}
      <label className="flex flex-col items-center justify-center gap-1.5 w-full h-20
        bg-white/5 hover:bg-white/8 rounded-2xl cursor-pointer transition-colors duration-150
        border border-dashed border-white/10 hover:border-accent/40">
        <svg className="w-5 h-5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <span className="text-[11px] text-muted">{file ? file.name : 'PDF · DOCX · TXT'}</span>
        <input type="file" accept=".pdf,.txt,.docx" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
      </label>

      <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className={selectCls}>
        {STRATEGIES.map((s) => <option key={s} value={s}>{s} chunking</option>)}
      </select>

      <select value={model} onChange={(e) => setModel(e.target.value)} className={selectCls}>
        {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="w-full py-2 rounded-2xl bg-accent hover:bg-accent-hover disabled:opacity-30
          text-sm font-semibold text-white transition-colors duration-150"
      >
        {loading ? 'Ingesting…' : 'Upload & Ingest'}
      </button>

      {status && (
        <p className={`text-[11px] ${status.ok ? 'text-emerald-400' : 'text-red-400'}`}>{status.msg}</p>
      )}
    </div>
  )
}
