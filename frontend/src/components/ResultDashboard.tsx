import React, { useState, useRef, useEffect } from 'react';
import { 
  User, 
  Send, 
  Sparkles, 
  Droplets, 
  Flame, 
  Mountain, 
  Circle, 
  Leaf,
  ArrowLeft,
  Lock
} from 'lucide-react';
import type { AnalysisData } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Props {
  analysis: AnalysisData;
  messages: { role: string; content: string }[];
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
  onGoBack: () => void;
  canChat?: boolean;
}

const ELEMENT_COLORS: Record<string, string> = {
  '목': 'text-emerald-500',
  '화': 'text-red-500',
  '토': 'text-amber-500',
  '금': 'text-slate-400',
  '수': 'text-blue-500',
};

const ELEMENT_BG_COLORS: Record<string, string> = {
  '목': 'bg-emerald-500',
  '화': 'bg-red-500',
  '토': 'bg-amber-500',
  '금': 'bg-slate-400',
  '수': 'bg-blue-500',
};

const ELEMENT_ICONS: Record<string, typeof Leaf> = {
  '목': Leaf,
  '화': Flame,
  '토': Mountain,
  '금': Circle,
  '수': Droplets,
};

export default function ResultDashboard({ analysis, messages, onSendMessage, isLoading, onGoBack, canChat = true }: Props) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput("");
  };

  const dayMaster = analysis.eight_characters.day_stem;
  const strength = analysis.strength_analysis;
  const elements = analysis.element_analysis.element_stats;
  const pillars = analysis.eight_characters.pillars;

  const pillarOrder = [
    { key: "time", label: "시주", data: pillars.time },
    { key: "day", label: "일주", data: pillars.day },
    { key: "month", label: "월주", data: pillars.month },
    { key: "year", label: "연주", data: pillars.year },
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background-light dark:bg-background-dark">
      {/* Header */}
      <header className="pt-8 px-6 pb-4 flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={onGoBack}
            className="w-10 h-10 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            title="되돌아가기"
          >
            <ArrowLeft className="text-slate-500 w-5 h-5" />
          </button>
          <div>
            <p className="text-xs font-bold text-slate-400 tracking-widest uppercase">Analysis Result</p>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">{analysis.eight_characters.name}님의 사주</h1>
          </div>
        </div>
        <div className="w-10 h-10 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm">
          <User className="text-slate-400 w-5 h-5" />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto pb-24 px-6 space-y-6">
        {/* Main Card (Day Master & Pillars) */}
        <div className="glass-card rounded-3xl p-6 relative overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-primary/20 blur-[80px] rounded-full pointer-events-none"></div>
          <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-400/10 blur-[80px] rounded-full pointer-events-none"></div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
                  Day Master
                </span>
                <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                  {dayMaster.element} ({dayMaster.stem_ko})
                </span>
              </div>
              <Sparkles className="text-primary w-5 h-5" />
            </div>

            <div className="grid grid-cols-4 gap-2 mb-8">
              {pillarOrder.map(({ key, label, data }) => (
                <div key={key} className="flex flex-col items-center gap-2">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">{label}</span>
                  <div className="flex flex-col gap-1 w-full">
                    <div className={`h-14 rounded-xl flex items-center justify-center bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 backdrop-blur-sm ${ELEMENT_COLORS[data.stem_element] || 'text-slate-500'}`}>
                      <span className="text-xl font-bold">{data.stem}</span>
                    </div>
                    <div className={`h-14 rounded-xl flex items-center justify-center bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 backdrop-blur-sm ${ELEMENT_COLORS[data.branch_element] || 'text-slate-500'}`}>
                      <span className="text-xl font-bold">{data.branch}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex items-center justify-between p-4 rounded-2xl bg-white/40 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 dark:text-slate-400 mb-1">신강/신약</span>
                <span className="font-bold text-sm text-slate-900 dark:text-white">{strength.strength_status}</span>
              </div>
              <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700"></div>
              <div className="flex flex-col items-end">
                <span className="text-xs text-slate-500 dark:text-slate-400 mb-1">용신 (Lucky Element)</span>
                <span className="font-bold text-sm text-emerald-500">{analysis.yong_shin_analysis.yong_shin}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Five Elements Chart */}
        <section>
          <div className="flex items-center justify-between mb-4 px-1">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">오행 분포</h2>
          </div>
          <div className="space-y-3">
            {Object.values(elements).map((el: { element: string; element_ko: string; element_en: string; count: number; score: number; ratio: number }) => {
              const Icon = ELEMENT_ICONS[el.element_ko] || Circle;
              const colorClass = ELEMENT_COLORS[el.element_ko] || 'text-slate-500';
              const bgClass = ELEMENT_BG_COLORS[el.element_ko] || 'bg-slate-500';
              
              return (
                <div key={el.element} className="glass-card p-3 rounded-2xl flex items-center gap-4 border border-slate-200 dark:border-slate-700 hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                    <Icon className={`w-5 h-5 ${colorClass}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between mb-1.5">
                      <span className="text-sm font-semibold text-slate-900 dark:text-white">{el.element_ko} <span className="text-slate-400 font-normal text-xs">({el.element})</span></span>
                      <span className="text-xs font-bold text-slate-900 dark:text-white">{Math.round(el.ratio)}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${bgClass}`} 
                        style={{ width: `${el.ratio}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Chat / Interpretation Section */}
        <section className="flex-1 flex flex-col min-h-[500px]">
          <div className="flex items-center justify-between mb-4 px-1">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">상세 해석 & 질문</h2>
          </div>
          
          <div className="glass-card rounded-3xl flex-1 flex flex-col overflow-hidden border border-slate-200 dark:border-slate-700 shadow-lg">
            <div className="flex-1 overflow-y-auto p-5 space-y-5" ref={scrollRef}>
              {messages.map((msg, idx) => {
                if (msg.role === 'assistant' && !msg.content) return null;
                return (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                      msg.role === 'user' 
                        ? 'bg-primary text-white rounded-br-none' 
                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-bl-none'
                    }`}>
                      {msg.role === 'user' ? (
                        <p>{msg.content}</p>
                      ) : (
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            strong: ({ children }) => <strong className="font-semibold text-slate-900 dark:text-white">{children}</strong>,
                            em: ({ children }) => <em className="italic">{children}</em>,
                            p: ({ children }) => <p className="mb-3 last:mb-0 leading-[1.8]">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc pl-4 my-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-4 my-2 space-y-1">{children}</ol>,
                            li: ({ children }) => <li className="leading-[1.8]">{children}</li>,
                            h1: ({ children }) => <p className="font-semibold text-slate-900 dark:text-white mb-3 mt-4">{children}</p>,
                            h2: ({ children }) => <p className="font-semibold text-slate-900 dark:text-white mb-3 mt-4">{children}</p>,
                            h3: ({ children }) => <p className="font-semibold text-slate-900 dark:text-white mb-2 mt-3">{children}</p>,
                            hr: () => <div className="my-4" />,
                            blockquote: ({ children }) => <div className="pl-3 border-l-2 border-slate-300 dark:border-slate-600 my-2 text-slate-500 dark:text-slate-400">{children}</div>,
                            code: ({ children }) => <span>{children}</span>,
                            a: ({ children, href }) => <a href={href} className="text-primary underline" target="_blank" rel="noopener noreferrer">{children}</a>,
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      )}
                    </div>
                  </div>
                );
              })}
              {isLoading && (messages.length === 0 || messages[messages.length - 1].role === 'user' || !messages[messages.length - 1].content) && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-bl-none p-4 flex gap-1.5">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-75"></span>
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-150"></span>
                  </div>
                </div>
              )}
            </div>

            {canChat ? (
              <form onSubmit={handleSubmit} className="p-4 border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
                <div className="relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="추가 질문을 입력하세요..."
                    className="w-full pl-4 pr-12 py-3.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 outline-none text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                    disabled={isLoading}
                  />
                  <button 
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-primary disabled:opacity-50 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </form>
            ) : (
              <div className="p-4 border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
                <div className="flex items-center justify-center gap-2 py-3 text-slate-400">
                  <Lock size={14} />
                  <span className="text-xs">추가 질문은 후원자(user+) 전용 기능입니다</span>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
