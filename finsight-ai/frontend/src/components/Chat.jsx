import React, { useState, useRef, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Input } from './ui/Input';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';
import { StockCard } from './StockCard';
import { SentimentBar } from './SentimentBar';
import { NewsCard } from './NewsCard';
import { getNifty50, getMarketSentiment } from '../api';
import { supabase } from '../lib/supabase';
import ReactMarkdown from 'react-markdown';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
console.log('[Chat] API_BASE:', API_BASE);
console.log('[Chat] Chat endpoint:', `${API_BASE}/api/chat`);

const initialMessages = [
  {
    id: 1,
    role: 'assistant',
    content: "Good morning. I'm FinSight AI, your personal market intelligence terminal. I can analyze stocks, track IPOs, or provide SIP recommendations based on current Indian market conditions. What would you like to explore?",
    timestamp: "09:15 AM",
    steps: null
  }
];

export default function Chat() {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [currentSteps, setCurrentSteps] = useState([]);
  const [expandedSteps, setExpandedSteps] = useState(false);
  
  const [marketData, setMarketData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [newsData, setNewsData] = useState([]);
  
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, currentSteps, expandedSteps]);

  useEffect(() => {
    async function fetchSidebarData() {
      try {
        const [niftyRes, sentRes] = await Promise.allSettled([
          getNifty50(),
          getMarketSentiment()
        ]);

        if (niftyRes.status === 'fulfilled' && niftyRes.value) {
          setMarketData(niftyRes.value.index);
        }

        if (sentRes.status === 'fulfilled' && sentRes.value) {
          setSentimentData(sentRes.value);
          // Extract top news from sources
          const allNews = [];
          const sources = sentRes.value.sources || {};
          if (sources.economic_times && sources.economic_times.articles) {
            allNews.push(...sources.economic_times.articles.map(a => ({...a, source: 'ET'})));
          }
          if (sources.moneycontrol && sources.moneycontrol.articles) {
            allNews.push(...sources.moneycontrol.articles.map(a => ({...a, source: 'MC'})));
          }
          // Sort or slice if necessary, returning top 4
          setNewsData(allNews.slice(0, 4));
        }
      } catch (err) {
        console.error("Failed to fetch sidebar data", err);
      }
    }
    fetchSidebarData();
  }, []);

  const handleSend = async (e, customMessage = null) => {
    e?.preventDefault();
    const messageText = (customMessage !== null ? customMessage : inputValue).trim();
    if (!messageText || isTyping) return;
    
    // Add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);
    setIsStreaming(true);
    setCurrentSteps([]);
    setExpandedSteps(true);
    setStreamingText('');

    try {
      let fullText = '';
      let buffer = '';
      let stepList = [];

      const { data: { session } } = await supabase.auth.getSession();
      const headers = { 'Content-Type': 'application/json' };
      // Fall back to mock token in dev mode when Supabase is not configured
      const token = session?.access_token || 'mock_jwt_token';
      headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ message: messageText, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const jsonStr = trimmed.replace(/^data:\s*/, '').trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'chunk' && event.content) {
              fullText += event.content;
              setStreamingText(fullText);
            }

            if (event.type === 'step' && event.content) {
              stepList.push(event.content);
              setCurrentSteps([...stepList]);
            }

            if (event.type === 'done') {
              setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: fullText || 'Analysis complete.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                steps: stepList.length > 0 ? stepList : null,
              }] );
              setStreamingText('');
              setIsStreaming(false);
              setIsTyping(false);
              setCurrentSteps([]);
              setExpandedSteps(false);
              fullText = '';
            }

            if (event.type === 'error') {
              setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: event.content || 'Something went wrong. Please try again.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                steps: null,
              }] );
              setIsStreaming(false);
              setIsTyping(false);
              setStreamingText('');
              setCurrentSteps([]);
              setExpandedSteps(false);
            }
          } catch {
            // malformed JSON line — skip silently
          }
        }
      }

      // Fallback in case stream ended without explicit 'done' event
      if (fullText && fullText.trim()) {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content === fullText) {
            return prev;
          }
          return [...prev, {
            id: Date.now() + 1,
            role: 'assistant',
            content: fullText,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            steps: stepList.length > 0 ? stepList : null,
          }];
        });
        setStreamingText('');
        setIsStreaming(false);
        setIsTyping(false);
      }
    } catch (networkErr) {
       console.error('Network error:', networkErr);
       setIsTyping(false);
       setIsStreaming(false);
       setMessages(prev => [...prev, 
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'Could not connect to server: ' + (networkErr.message || ''),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          steps: null
        }
      ]);
      setStreamingText('');
      setCurrentSteps([]);
      setExpandedSteps(false);
    }
  };

  const handleQuickAction = (text) => {
    handleSend(null, text);
  };

  return (
    <div className="flex flex-col lg:flex-row h-full gap-6 pb-6">
      
      {/* LEFT — Chat Panel */}
      <Card className="flex-1 flex flex-col h-full bg-white relative overflow-hidden flex-shrink-0 lg:w-[60%]">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-[#E5E7EB] bg-white z-10">
          <h2 className="text-[18px] font-semibold text-[#111111]">FinSight AI</h2>
          <div className="flex items-center gap-2 bg-[#22C55E]/10 pl-2 pr-3 py-1 rounded-full">
            <div className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse"></div>
            <span className="text-[11px] font-semibold text-[#22C55E] uppercase tracking-[0.08em]">Live</span>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-full animate-in slide-in-from-bottom-2 fade-in duration-300 ease-out`}>
              
              {/* Agentic Steps for old messages (collapsed by default) */}
              {msg.role === 'assistant' && msg.steps && (
                <div className="mb-2 w-full max-w-[80%] flex flex-col gap-1 ml-10">
                  <div className="flex flex-wrap gap-1.5 opacity-60">
                    <Badge variant="neutral" className="!text-[10px] !px-1.5 !py-0.5">Compiled {msg.steps.length} steps</Badge>
                  </div>
                </div>
              )}

              <div className="flex gap-3 max-w-[80%]">
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-[#111111] flex flex-shrink-0 items-center justify-center mt-1">
                    <span className="text-white font-bold text-xs">F</span>
                  </div>
                )}
                
                <div className={`
                  px-4 py-3 text-[14px] leading-relaxed shadow-sm
                  ${msg.role === 'user' 
                    ? 'bg-[#111111] text-white rounded-[16px_16px_4px_16px]' 
                    : 'bg-[#F7F8F5] text-[#111111] rounded-[16px_16px_16px_4px] prose prose-sm max-w-none prose-headings:font-bold prose-headings:my-2 prose-p:my-1 prose-table:my-2 prose-th:p-2 prose-td:p-2 prose-table:border prose-th:border prose-td:border prose-th:bg-[#E5E7EB]'}
                `}>
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  )}
                </div>
              </div>
              
              <span className={`text-[11px] text-[#6B7280] mt-1.5 ${msg.role === 'assistant' ? 'ml-10' : ''}`}>
                {msg.timestamp}
              </span>
            </div>
          ))}

          {/* Active Thinking/Streaming state */}
          {isTyping && (
            <div className="flex flex-col items-start max-w-[80%] animate-in slide-in-from-bottom-2 fade-in duration-300">
              {currentSteps.length > 0 && (
                <div className="mb-3 w-full ml-10 flex flex-col gap-1.5 transition-all duration-300">
                  {currentSteps.map((step, i) => (
                    <div key={i} className="animate-in fade-in slide-in-from-left-2 duration-300">
                      <Badge variant="neutral" className="flex items-center gap-1.5 !bg-[#F3F4F6] !text-[#6B7280] !py-1 px-2.5">
                        <Activity className="w-3 h-3 animate-pulse" />
                        {step}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}

              {!streamingText && (
                <div className="flex gap-3 w-full">
                  <div className="w-7 h-7 rounded-full bg-[#111111] flex flex-shrink-0 items-center justify-center mt-1">
                    <span className="text-white font-bold text-xs">F</span>
                  </div>
                  <div className="px-5 py-4 bg-[#F7F8F5] rounded-[16px_16px_16px_4px] flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce"></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {isStreaming && streamingText && (
            <div className="flex flex-col items-start max-w-[80%] animate-in slide-in-from-bottom-2 fade-in duration-300">
              <div className="flex gap-3 w-full">
                <div className="w-7 h-7 rounded-full bg-[#111111] flex flex-shrink-0 items-center justify-center mt-1">
                  <span className="text-white font-bold text-xs">F</span>
                </div>
                <div className="px-4 py-3 text-[14px] leading-relaxed bg-[#F7F8F5] text-[#111111] rounded-[16px_16px_16px_4px] shadow-sm prose prose-sm max-w-none">
                  <ReactMarkdown>{streamingText}</ReactMarkdown>
                  <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-[#111111] animate-blink"></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} className="h-[2px] shrink-0" />
        </div>

        {/* Input Area */}
        <div className="px-6 py-5 bg-white border-t border-[#E5E7EB] z-10">
          <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-hide">
            {["NIFTY 50", "Top IPOs", "SIP advice", "Market mood"].map((pill) => (
              <button 
                key={pill}
                onClick={() => handleQuickAction(pill)}
                className="px-3 py-1.5 text-xs font-medium rounded-full border border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#111111] hover:text-white transition-all duration-200 whitespace-nowrap"
              >
                {pill}
              </button>
            ))}
          </div>
          
          <form onSubmit={handleSend} className="relative flex items-center">
            <Input 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about any stock, SIP, or IPO..."
              className="pr-12 text-[14px] bg-[#F7F8F5] transition-colors focus:bg-white focus:border-[#111111] py-3.5"
              autoFocus
            />
            <button 
              type="submit" 
              disabled={!inputValue.trim() || isTyping}
              className="absolute right-2 w-8 h-8 rounded-full bg-[#111111] flex items-center justify-center pr-0.5 text-white disabled:opacity-50 transition-opacity hover:opacity-85"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 5L19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </form>
        </div>
      </Card>

      {/* RIGHT — Market Context Panel */}
      <div className="lg:w-[40%] flex flex-col gap-6 overflow-y-auto pr-1 pb-6 hide-scrollbar flex-shrink-0">
        <StockCard 
          symbol="NIFTY 50" 
          name="Market Index" 
          price={marketData?.value ?? 22450.50} 
          change={marketData?.change_pct ?? 1.25} 
          isPositive={(marketData?.change_pct ?? 1.25) >= 0} 
        />
        <SentimentBar score={sentimentData ? ((sentimentData.overall_score + 1) / 2) * 100 : 68} />
        <NewsCard news={newsData} />
      </div>
    </div>
  );
}
