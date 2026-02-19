'use client';

import { useState, useEffect, useCallback } from "react";
import InputForm from "@/components/InputForm";
import ResultDashboard from "@/components/ResultDashboard";
import HistoryPanel from "@/components/HistoryPanel";
import AuthPage from "@/components/AuthPage";
import DailyFortune from "@/components/DailyFortune";
import {
  analyzeSaju,
  streamReading,
  streamChat,
  fetchHistory,
  fetchHistoryDetail,
  type AnalyzeRequest,
  type AnalysisData,
  type HistoryEntry,
} from "@/lib/api";
import type { Message } from "@/lib/history";
import { getCurrentUser, logout, isPremium, type SessionUser } from "@/lib/auth";
import { History, Plus, LogOut, Sun } from "lucide-react";

type Tab = "new" | "history" | "fortune";
type View = "home" | "result";

export default function Home() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [view, setView] = useState<View>("home");
  const [tab, setTab] = useState<Tab>("new");
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [analysisId, setAnalysisId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [historyList, setHistoryList] = useState<HistoryEntry[]>([]);
  const [currentRequest, setCurrentRequest] = useState<AnalyzeRequest | null>(null);

  useEffect(() => {
    setUser(getCurrentUser());
    setAuthChecked(true);
  }, []);

  const refreshHistory = useCallback(async () => {
    if (!user) return;
    const list = await fetchHistory(user.id);
    setHistoryList(list);
  }, [user]);

  useEffect(() => {
    if (user) refreshHistory();
  }, [refreshHistory, user]);

  const handleAnalyze = async (data: AnalyzeRequest) => {
    setIsLoading(true);
    setMessages([]);
    setAnalysis(null);
    setCurrentRequest(data);

    let analysisReceived = false;

    try {
      const response = await analyzeSaju({ ...data, user_id: user?.id || "" });
      setSessionId(response.session_id);
      setAnalysisId(response.analysis_id);
      setAnalysis(response.analysis);
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
      }, response.analysis_id);

      refreshHistory();
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
    if (!sessionId || !user) return;

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
      }, user.id, analysisId);
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
    setAnalysisId("");
    setCurrentRequest(null);
    refreshHistory();
  };

  const handleSelectHistory = async (entry: HistoryEntry) => {
    const detail = await fetchHistoryDetail(entry.id);
    const msgs = detail?.messages || [];
    setAnalysis(entry.analysis);
    setMessages(
      msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))
    );
    setSessionId("");
    setAnalysisId(entry.id);
    setCurrentRequest(entry.request);
    setView("result");
  };

  const handleAuth = (sessionUser: SessionUser) => {
    setUser(sessionUser);
  };

  const handleLogout = () => {
    logout();
    setUser(null);
    setView("home");
    setTab("new");
    setAnalysis(null);
    setMessages([]);
    setSessionId("");
    setAnalysisId("");
    setCurrentRequest(null);
    setHistoryList([]);
  };

  if (!authChecked) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen font-sans selection:bg-primary selection:text-white">
        <AuthPage onAuth={handleAuth} />
      </main>
    );
  }

  if (view === "result" && analysis) {
    return (
      <main className="min-h-screen font-sans selection:bg-primary selection:text-white">
        <ResultDashboard
          analysis={analysis}
          messages={messages}
          onSendMessage={handleChat}
          isLoading={isLoading}
          onGoBack={handleGoBack}
          canChat={isPremium(user)}
        />
      </main>
    );
  }

  return (
    <main className="min-h-screen font-sans selection:bg-primary selection:text-white flex flex-col">
      <div className="flex items-center justify-between px-6 pt-6 pb-1">
        <div className="flex items-center gap-2">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            <span className="font-semibold text-slate-700 dark:text-slate-200">{user.displayName}</span>님
          </p>
          {user.role === 'admin' && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">ADMIN</span>
          )}
          {user.role === 'user+' && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">USER+</span>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={14} />
          로그아웃
        </button>
      </div>

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
          {isPremium(user) && (
            <button
              onClick={() => { setTab("fortune"); refreshHistory(); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                tab === "fortune"
                  ? "bg-white dark:bg-slate-700 text-amber-500 shadow-sm"
                  : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              }`}
            >
              <Sun size={16} />
              오늘의 운세
            </button>
          )}
        </div>
      </div>

      {tab === "new" && (
        <InputForm onSubmit={handleAnalyze} isLoading={isLoading} />
      )}
      {tab === "history" && (
        <HistoryPanel
          history={historyList}
          onSelect={handleSelectHistory}
          onRefresh={refreshHistory}
          userId={user.id}
        />
      )}
      {tab === "fortune" && isPremium(user) && (
        <DailyFortune user={user} history={historyList} />
      )}
    </main>
  );
}
