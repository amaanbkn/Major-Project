import React, { useState, useRef, useEffect } from 'react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Input } from './ui/Input';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';
import { StockCard } from './StockCard';
import { SentimentBar } from './SentimentBar';
import { NewsCard } from './NewsCard';
import { streamChat } from '../api';

const initialMessages = [
  {
    id: 1,
    role: 'assistant',
    content: "Good morning. I'm FinSight AI, your personal market intelligence terminal. I can analyze stocks, track IPOs, or provide SIP recommendations based on current Indian market conditions. What would you like to explore?",
    timestamp: "09:15 AM",
    steps: null
  }
];

const mockStreamingResponse = "Reliance Industries is currently showing strong bullish momentum driven by robust quarterly earnings and strategic expansions in their retail sector. Key technical indicators point towards a potential breakout if it sustains above the ₹2,950 level.\n\nWould you like me to run a deeper technical analysis on the daily charts or look at their latest earnings report?";

const mockThinkingSteps = [
  "Fetching current price and volume data for RELIANCE...",
  "Analyzing latest news sentiment from 4 sources...",
  "Computing RSI, MACD, and moving averages...",
  "Synthesizing market context..."
];

export default function Chat() {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [currentSteps, setCurrentSteps] = useState([]);
  const [expandedSteps, setExpandedSteps] = useState(false);
  
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, currentSteps, expandedSteps]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || isTyping) return;
    
    // Add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, userMsg]);
    const currentInput = inputValue;
    setInputValue('');
    setIsTyping(true);
    setCurrentSteps([]);
    setExpandedSteps(true);
    setStreamingText('');

    try {
      let accumulatedText = '';
      let accumulatedSteps = [];
      const chatStream = streamChat(currentInput);
      
      for await (const data of chatStream) {
        if (data.type === 'step') {
          accumulatedSteps.push(data.content);
          setCurrentSteps([...accumulatedSteps]);
        } else if (data.type === 'chunk') {
          accumulatedText += data.content;
          setStreamingText(accumulatedText);
        } else if (data.type === 'error') {
          accumulatedText += "\n⚠️ " + data.content;
          setStreamingText(accumulatedText);
        }
      }

      setIsTyping(false);
      setMessages(prev => [
        ...prev, 
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: accumulatedText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          steps: accumulatedSteps.length > 0 ? accumulatedSteps : null
        }
      ]);
      setStreamingText('');
      setCurrentSteps([]);
      setExpandedSteps(false);
    } catch (error) {
       console.error("Stream failed:", error);
       setIsTyping(false);
       setMessages(prev => [
        ...prev, 
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: "I'm sorry, I am having trouble connecting to the backend. Please ensure the backend is running.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          steps: null
        }
      ]);
      setStreamingText('');
      setCurrentSteps([]);
    }
  };

  const handleQuickAction = (text) => {
    setInputValue(text);
    // Use a tiny timeout to ensure state updates before sending
    setTimeout(() => {
      handleSend();
    }, 10);
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
          {messages.map((msg, index) => (
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
                    : 'bg-[#F7F8F5] text-[#111111] rounded-[16px_16px_16px_4px]'}
                `}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
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
              
              {/* Active Agentic Steps */}
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

              <div className="flex gap-3 w-full">
                <div className="w-7 h-7 rounded-full bg-[#111111] flex flex-shrink-0 items-center justify-center mt-1">
                  <span className="text-white font-bold text-xs">F</span>
                </div>
                
                {streamingText ? (
                  <div className="px-4 py-3 text-[14px] leading-relaxed bg-[#F7F8F5] text-[#111111] rounded-[16px_16px_16px_4px] shadow-sm">
                    <p className="whitespace-pre-wrap">{streamingText}<span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-[#111111] animate-blink"></span></p>
                  </div>
                ) : (
                  <div className="px-5 py-4 bg-[#F7F8F5] rounded-[16px_16px_16px_4px] flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-1.5 h-1.5 bg-[#111111] rounded-full animate-bounce"></div>
                  </div>
                )}
              </div>
              
              {streamingText && (
                <span className="text-[11px] text-[#6B7280] mt-1.5 ml-10">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
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
        <StockCard />
        <SentimentBar score={68} />
        <NewsCard />
      </div>
    </div>
  );
}
