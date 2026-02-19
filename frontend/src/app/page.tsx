'use client';

import { useState, useEffect, useCallback } from "react";
import InputForm from "@/components/InputForm";
import ResultDashboard from "@/components/ResultDashboard";
import HistoryPanel from "@/components/HistoryPanel";
import AuthPage from "@/components/AuthPage";
import {
  analyzeSaju,
  streamReading,
  streamChat,
  type AnalyzeRequest,
  type AnalysisData,
} from "@/lib/api";
import {
  getHistory,
  saveHistory,
  updateHistoryMessages,
  migrateMatchingHistory,
  type HistoryEntry,
  type Message,
} from "@/lib/history";
import { getCurrentUser, logout, type SessionUser } from "@/lib/auth";
import { History, Plus, LogOut } from "lucide-react";

type Tab = "new" | "history";
type View = "home" | "result";

export default function Home() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [view, setView] = useState<View>("home");
  const [tab, setTab] = useState<Tab>("new");
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [historyList, setHistoryList] = useState<HistoryEntry[]>([]);
  const [currentHistoryId, setCurrentHistoryId] = useState<string | null>(null);
  const [currentRequest, setCurrentRequest] = useState<AnalyzeRequest | null>(null);

  // 인증 상태 확인
  useEffect(() => {
    setUser(getCurrentUser());
    setAuthChecked(true);
  }, []);

  // 히스토리 로드
  const refreshHistory = useCallback(() => {
    setHistoryList(getHistory());
  }, []);

  useEffect(() => {
    if (user) refreshHistory();
  }, [refreshHistory, user]);

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

    let analysisReceived = false;

    try {
      const response = await analyzeSaju(data);
      setSessionId(response.session_id);
      setAnalysis(response.analysis);

      const historyId = crypto.randomUUID();
      setCurrentHistoryId(historyId);
      const entry: HistoryEntry = {
        id: historyId,
        name: data.name,
        createdAt: new Date().toISOString(),
        request: data,
        analysis: response.analysis,
        messages: [],
        sessionId: response.session_id,
      };
      saveHistory(entry);
      refreshHistory();

      analysisReceived = true;
      setView("result");
      setMessages([{ role: "assistant", content: "" }]);

      await streamReading(response.session_id, (delta) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = { ...last, content: last.content + delta };
          return updated;
        });
      });
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
      if (!analysisReceived) {
        alert(`오류가 발생했습니다: ${errorMsg}`);
      } else {
        setMessages((prev) => {
          const updated = prev.filter((m) => m.content !== "");
          return [...updated, { role: "assistant", content: `오류: ${errorMsg}` }];
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChat = async (message: string) => {
    if (!sessionId) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: message },
      { role: "assistant", content: "" },
    ]);
    setIsLoading(true);

    try {
      await streamChat(sessionId, message, (delta) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = { ...last, content: last.content + delta };
          return updated;
        });
      });
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (updated[lastIdx].content === "") {
          updated[lastIdx] = { role: "assistant", content: `오류: ${errorMsg}` };
        } else {
          updated.push({ role: "assistant", content: `오류: ${errorMsg}` });
        }
        return updated;
      });
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

  const handleAuth = (sessionUser: SessionUser) => {
    setUser(sessionUser);
    // 기존 히스토리 중 가입자 이름과 일치하는 항목 이전
    migrateMatchingHistory(sessionUser.displayName);
  };

  const handleLogout = () => {
    logout();
    setUser(null);
    setView("home");
    setTab("new");
    setAnalysis(null);
    setMessages([]);
    setSessionId("");
    setCurrentHistoryId(null);
    setCurrentRequest(null);
    setHistoryList([]);
  };

  // 인증 상태 확인 중
  if (!authChecked) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  // 로그인 페이지
  if (!user) {
    return (
      <main className="min-h-screen font-sans selection:bg-primary selection:text-white">
        <AuthPage onAuth={handleAuth} />
      </main>
    );
  }

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
      {/* User Header */}
      <div className="flex items-center justify-between px-6 pt-6 pb-1">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          <span className="font-semibold text-slate-700 dark:text-slate-200">{user.displayName}</span>님, 환영합니다
        </p>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={14} />
          로그아웃
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="pt-2 px-6 pb-2 shrink-0">
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
