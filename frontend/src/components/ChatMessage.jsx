import ReactMarkdown from 'react-markdown'
import GroundednessBadge from './GroundednessBadge'
import SourceCitations from './SourceCitations'

export default function ChatMessage({ msg }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-y-1`}>
      <div className={`w-full sm:max-w-[78%] rounded-2xl px-4 py-3 ${
        isUser ? 'bg-accent text-white' : 'bg-surface text-body'
      }`}>

        {/* Intent / rewrite meta — assistant only */}
        {!isUser && (msg.intent || msg.rewritten_query) && (
          <div className="flex gap-1.5 mb-2 flex-wrap">
            {msg.intent && (
              <span className="text-[10px] text-muted bg-white/5 px-2 py-0.5 rounded-full">
                {msg.intent}
              </span>
            )}
            {msg.rewritten_query && (
              <span className="text-[10px] text-accent/80 bg-accent/10 px-2 py-0.5 rounded-full">
                ↩ {msg.rewritten_query}
              </span>
            )}
          </div>
        )}

        {/* Message body */}
        <div className="prose prose-invert prose-sm max-w-none leading-[1.65]
          prose-p:my-1 prose-ul:my-1 prose-li:my-0">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>

        {/* Footer row — assistant only */}
        {!isUser && (
          <div className="mt-2 flex items-center gap-3">
            <GroundednessBadge score={msg.groundedness_score} flagged={msg.flagged} />
            <span className="text-[11px] text-muted ml-auto">
              {new Date(msg.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}

        {isUser && (
          <p className="text-[11px] text-white/40 mt-1 text-right">
            {new Date(msg.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}

        {!isUser && <SourceCitations sources={msg.sources} />}
      </div>
    </div>
  )
}
