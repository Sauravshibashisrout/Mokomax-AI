import { useState, useEffect } from 'react'
import { getEvalResults, triggerEval } from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const CORPUS = `Retrieval-Augmented Generation (RAG) combines a retrieval system with a language model.
Chunking strategy determines the granularity of indexed text segments.
Supported embedding models include all-MiniLM-L6-v2, BGE-large, and OpenAI text-embedding-3-small.`

const TEST_ITEMS = [
  { query: 'What is retrieval-augmented generation?', relevant_chunks: ['Retrieval-Augmented Generation (RAG) combines a retrieval system with a language model'], reference_answer: 'RAG combines retrieval with LLM generation.' },
  { query: 'How does chunking affect retrieval quality?', relevant_chunks: ['Chunking strategy determines the granularity of indexed text segments'], reference_answer: 'Chunking controls text segment size.' },
  { query: 'What embedding models are supported?', relevant_chunks: ['Supported embedding models include all-MiniLM-L6-v2, BGE-large, and OpenAI text-embedding-3-small'], reference_answer: 'MokoMax supports MiniLM, BGE-large, and OpenAI.' },
]

function ScorePill({ value }) {
  if (value === null || value === undefined) return <span className="text-muted">—</span>
  const color = value >= 0.7 ? 'text-emerald-400' : value >= 0.4 ? 'text-amber-400' : 'text-red-400'
  return <span className={`font-semibold ${color}`}>{value}</span>
}

export default function AdminPage() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)

  useEffect(() => { fetchResults() }, [])

  async function fetchResults() {
    setLoading(true)
    try {
      const { data } = await getEvalResults()
      setResults(data.results || [])
    } finally {
      setLoading(false)
    }
  }

  async function handleRunEval() {
    setRunning(true)
    try {
      await triggerEval({ corpus_text: CORPUS, test_items: TEST_ITEMS })
      await fetchResults()
    } finally {
      setRunning(false)
    }
  }

  const chartData = results.map((r) => ({
    name: `${r.chunking_strategy} / ${r.embedding_model.split('/').pop().split('-')[0]}`,
    'Precision@k': r.precision_at_k,
    'Recall@k': r.recall_at_k,
    'Groundedness': r.avg_groundedness,
  }))

  return (
    <div className="min-h-screen bg-[#0d0d0f] text-body font-sans">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start gap-3 sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold">Eval Dashboard</h1>
            <p className="text-sm text-muted mt-0.5">Chunking × Embedding model performance</p>
          </div>
          <div className="flex items-center gap-3">
            <a href="/" className="text-sm text-muted hover:text-accent transition-colors duration-150">
              ← Chat
            </a>
            <button
              onClick={handleRunEval}
              disabled={running}
              className="px-4 py-2 bg-accent hover:bg-accent-hover disabled:opacity-30
                rounded-2xl text-sm font-semibold text-white transition-colors duration-150"
            >
              {running ? 'Running…' : 'Run Evaluation'}
            </button>
          </div>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="bg-surface rounded-2xl p-4 sm:p-5">
            <p className="text-sm font-semibold mb-4">Metrics Comparison</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} margin={{ top: 4, right: 16, left: -16, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="name" tick={{ fill: '#8a8a8f', fontSize: 11 }} angle={-18} textAnchor="end" tickLine={false} axisLine={false} />
                <YAxis domain={[0, 1]} tick={{ fill: '#8a8a8f', fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }} contentStyle={{ backgroundColor: '#1a1a1d', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, fontSize: 12, color: '#e5e5e5' }} />
                <Legend wrapperStyle={{ color: '#8a8a8f', fontSize: 12, paddingTop: 12 }} iconType="circle" iconSize={8} />
                <Bar dataKey="Precision@k" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Recall@k" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Groundedness" fill="#c4b5fd" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Table — horizontally scrollable on mobile */}
        <div className="bg-surface rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[600px]">
              <thead>
                <tr className="border-b border-white/5">
                  {['Chunking', 'Embedding', 'Precision@k', 'Recall@k', 'Groundedness', 'Items', 'Run at'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-muted uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted text-sm">
                      <div className="flex justify-center gap-1.5">
                        {[0,1,2].map(i => (
                          <span key={i} className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce"
                            style={{ animationDelay: `${i * 0.15}s` }} />
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
                {!loading && results.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted text-sm">
                      No results yet — click Run Evaluation
                    </td>
                  </tr>
                )}
                {results.map((r, i) => (
                  <tr key={r.run_id}
                    className={`border-b border-white/5 hover:bg-white/[0.03] transition-colors duration-150
                      ${i === results.length - 1 ? 'border-b-0' : ''}`}>
                    <td className="px-4 py-3 font-semibold text-accent">{r.chunking_strategy}</td>
                    <td className="px-4 py-3 text-muted text-xs">{r.embedding_model}</td>
                    <td className="px-4 py-3"><ScorePill value={r.precision_at_k} /></td>
                    <td className="px-4 py-3"><ScorePill value={r.recall_at_k} /></td>
                    <td className="px-4 py-3"><ScorePill value={r.avg_groundedness} /></td>
                    <td className="px-4 py-3 text-muted">{r.num_test_items}</td>
                    <td className="px-4 py-3 text-muted text-xs">
                      {new Date(r.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  )
}
