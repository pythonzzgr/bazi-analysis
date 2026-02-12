'use client';

import { useState, useEffect, useCallback } from "react";
import InputForm from "@/components/InputForm";
import ResultDashboard from "@/components/ResultDashboard";
import HistoryPanel from "@/components/HistoryPanel";
import {
  analyzeSaju,
  chatWithAgent,
  type AnalyzeRequest,
  type AnalysisData,
} from "@/lib/api";
import {
  getHistory,
  saveHistory,
  updateHistoryMessages,
  type HistoryEntry,
  type Message,
} from "@/lib/history";
import { History, Plus } from "lucide-react";

type Tab = "new" | "history";
type View = "home" | "result";

export default function Home() {
  const [view, setView] = useState<View>("home");
  const [tab, setTab] = useState<Tab>("new");
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [historyList, setHistoryList] = useState<HistoryEntry[]>([]);
  const [currentHistoryId, setCurrentHistoryId] = useState<string | null>(null);
  const [currentRequest, setCurrentRequest] = useState<AnalyzeRequest | null>(null);

  // 히스토리 로드
  const refreshHistory = useCallback(() => {
    setHistoryList(getHistory());
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  // 메시지가 변경될 때 히스토리 업데이트
  useEffect(() => {
    if (currentHistoryId && messages.length > 0) {
      updateHistoryMessages(currentHistoryId, messages);
    }
  }, [messages, currentHistoryId]);

  const handleAnalyze = async (data: AnalyzeRequest) => {
    setIsLoading(true);
    setMessages([]);
    setAnalysis(null);
    setCurrentRequest(data);

    try {
      const response = await analyzeSaju(data);
      setSessionId(response.session_id);
      setAnalysis(response.analysis);

      const initialMessages: Message[] = [
        { role: "assistant", content: response.interpretation },
      ];
      setMessages(initialMessages);

      // 히스토리에 저장
      const historyId = crypto.randomUUID();
      setCurrentHistoryId(historyId);
      const entry: HistoryEntry = {
        id: historyId,
        name: data.name,
        createdAt: new Date().toISOString(),
        request: data,
        analysis: response.analysis,
        messages: initialMessages,
        sessionId: response.session_id,
      };
      saveHistory(entry);
      refreshHistory();

      setView("result");
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
      alert(`오류가 발생했습니다: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChat = async (message: string) => {
    if (!sessionId) return;
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    
    setIsLoading(true);

    try {
      const response = await chatWithAgent(sessionId, message);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.reply },
      ]);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `오류: ${errorMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    setView("home");
    setAnalysis(null);
    setMessages([]);
    setSessionId("");
    setCurrentHistoryId(null);
    setCurrentRequest(null);
    refreshHistory();
  };

  const handleSelectHistory = (entry: HistoryEntry) => {
    setAnalysis(entry.analysis);
    setMessages(entry.messages);
    setSessionId(entry.sessionId);
    setCurrentHistoryId(entry.id);
    setCurrentRequest(entry.request);
    setView("result");
  };

  // 결과 화면
  if (view === "result" && analysis) {
    return (
      <main className="min-h-screen font-sans selection:bg-primary selection:text-white">
        <ResultDashboard 
          analysis={analysis} 
          messages={messages} 
          onSendMessage={handleChat}
          isLoading={isLoading}
          onGoBack={handleGoBack}
        />
      </main>
    );
  }

  // 홈 화면 (탭: 새 분석 / 기록)
  return (
    <main className="min-h-screen font-sans selection:bg-primary selection:text-white flex flex-col">
      {/* Tab Navigation */}
      <div className="pt-8 px-6 pb-2 shrink-0">
        <div className="flex gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/50">
          <button
            onClick={() => setTab("new")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              tab === "new"
                ? "bg-white dark:bg-slate-700 text-primary shadow-sm"
                : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            }`}
          >
            <Plus size={16} />
            새 분석
          </button>
          <button
            onClick={() => { setTab("history"); refreshHistory(); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              tab === "history"
                ? "bg-white dark:bg-slate-700 text-primary shadow-sm"
                : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            }`}
          >
            <History size={16} />
            기록
            {historyList.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-bold">
                {historyList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {tab === "new" ? (
        <InputForm onSubmit={handleAnalyze} isLoading={isLoading} />
      ) : (
        <HistoryPanel
          history={historyList}
          onSelect={handleSelectHistory}
          onRefresh={refreshHistory}
        />
      )}
    </main>
  );
}
