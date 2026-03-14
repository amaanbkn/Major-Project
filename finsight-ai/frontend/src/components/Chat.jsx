import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Bot, User, Loader2, ChevronDown, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { streamChat } from '../api'

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `👋 Welcome to **FinSight AI**! I'm your intelligent market research assistant.

I can help you with:
- 📊 **Stock Analysis** — Live prices, technical signals (RSI, MA crossovers)
- 📈 **Buy/Hold/Sell Signals** — Data-driven recommendations
- 📰 **Market Sentiment** — Real-time news sentiment from ET, Moneycontrol & Reddit
- 📋 **IPO Tracking** — Upcoming IPOs with Grey Market Premium
- 💰 **SIP Advisory** — Personalized mutual fund recommendations
- 💼 **Paper Trading** — Practice with ₹1,00,000 virtual balance

Try asking: *"Analyze RELIANCE stock"* or *"What's the market sentiment today?"*

⚠️ *Disclaimer: This tool is for educational & research purposes only. Not financial advice.*`,
      steps: [],
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeSteps, setActiveSteps] = useState([])
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeSteps])

  const handleSend = async () => {
    const message = input.trim()
    if (!message || isLoading) return

    setInput('')
    setIsLoading(true)
    setActiveSteps([])

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: message }])

    // Stream response
    let assistantContent = ''
    const steps = []

    try {
      for await (const event of streamChat(message)) {
        if (event.type === 'step') {
          steps.push(event.content)
          setActiveSteps([...steps])
        } else if (event.type === 'chunk') {
          assistantContent += event.content
          setMessages(prev => {
            const updated = [...prev]
            const lastMsg = updated[updated.length - 1]
            if (lastMsg?.role === 'assistant' && lastMsg?._streaming) {
              lastMsg.content = assistantContent
              lastMsg.steps = [...steps]
            } else {
              updated.push({
                role: 'assistant',
                content: assistantContent,
                steps: [...steps],
                _streaming: true,
              })
            }
            return [...updated]
          })
        } else if (event.type === 'done') {
          setMessages(prev => {
            const updated = [...prev]
            const lastMsg = updated[updated.length - 1]
            if (lastMsg?._streaming) {
              delete lastMsg._streaming
            }
            return [...updated]
          })
        } else if (event.type === 'error') {
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: `⚠️ Error: ${event.content}`, steps },
          ])
        }
      }
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Connection error: ${error.message}. Please make sure the backend is running at http://localhost:8000`,
          steps,
        },
      ])
    }

    setIsLoading(false)
    setActiveSteps([])
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedQueries = [
    "Analyze TCS stock",
    "Market sentiment today",
    "Upcoming IPOs",
    "SIP for ₹5000/month, medium risk",
    "Buy 10 shares of INFY",
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="px-6 py-4 border-b border-[var(--border)] bg-[var(--bg-secondary)]/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">FinSight AI Chat</h2>
            <p className="text-xs text-[var(--text-muted)]">Powered by Gemini 1.5 Flash • Multi-Agent RAG</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-emerald-400 font-medium">Online</span>
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 animate-fadeIn ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
            )}

            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              {/* Reasoning steps */}
              {msg.steps && msg.steps.length > 0 && (
                <details className="mb-2 group" open={i === messages.length - 1}>
                  <summary className="flex items-center gap-2 cursor-pointer text-xs text-[var(--text-muted)] hover:text-indigo-400 transition-colors">
                    <Zap className="w-3 h-3" />
                    <span>{msg.steps.length} reasoning steps</span>
                    <ChevronDown className="w-3 h-3 group-open:rotate-180 transition-transform" />
                  </summary>
                  <div className="mt-2 space-y-1 pl-5 border-l-2 border-indigo-500/20">
                    {msg.steps.map((step, j) => (
                      <p key={j} className="text-xs text-[var(--text-muted)] py-0.5">
                        {step}
                      </p>
                    ))}
                  </div>
                </details>
              )}

              {/* Message bubble */}
              <div
                className={`
                  rounded-2xl px-4 py-3 text-sm leading-relaxed
                  ${msg.role === 'user'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-md'
                    : 'glass-card text-[var(--text-primary)] rounded-bl-md chat-content'
                  }
                `}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}

        {/* Active reasoning steps while loading */}
        {isLoading && activeSteps.length > 0 && (
          <div className="flex gap-3 animate-fadeIn">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-1 animate-pulse-glow">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="glass-card px-4 py-3 rounded-2xl rounded-bl-md">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                <span className="text-xs text-indigo-400 font-medium">Thinking...</span>
              </div>
              <div className="space-y-1 border-l-2 border-indigo-500/20 pl-3">
                {activeSteps.map((step, j) => (
                  <p key={j} className="text-xs text-[var(--text-muted)]">{step}</p>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {isLoading && activeSteps.length === 0 && (
          <div className="flex gap-3 animate-fadeIn">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 animate-pulse-glow">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="glass-card px-4 py-3 rounded-2xl rounded-bl-md flex items-center gap-1">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested queries */}
      {messages.length <= 1 && (
        <div className="px-6 pb-2">
          <div className="flex flex-wrap gap-2">
            {suggestedQueries.map((q, i) => (
              <button
                key={i}
                onClick={() => { setInput(q); inputRef.current?.focus() }}
                className="px-3 py-1.5 rounded-full text-xs font-medium
                  bg-[var(--bg-card)] border border-[var(--border)]
                  text-[var(--text-secondary)] hover:text-indigo-400
                  hover:border-indigo-500/30 hover:bg-indigo-500/5
                  transition-all duration-200 cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="px-4 md:px-6 py-4 border-t border-[var(--border)] bg-[var(--bg-secondary)]/80 backdrop-blur-sm">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about stocks, market sentiment, IPOs, SIP plans..."
              rows={1}
              className="input-field resize-none pr-4 min-h-[48px] max-h-[120px]"
              style={{ overflow: 'auto' }}
              disabled={isLoading}
            />
          </div>
          <button
            id="chat-send-btn"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className={`
              btn-primary h-[48px] px-5
              ${(isLoading || !input.trim()) ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-[10px] text-[var(--text-muted)] text-center mt-2">
          FinSight AI may produce inaccurate information. Not financial advice. SEBI Disclaimer applies.
        </p>
      </div>
    </div>
  )
}
