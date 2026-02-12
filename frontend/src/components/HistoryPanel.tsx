import React, { useState } from 'react';
import { Clock, Trash2, ChevronRight, AlertTriangle } from 'lucide-react';
import type { HistoryEntry } from '@/lib/history';
import { deleteHistoryEntry, clearHistory } from '@/lib/history';

interface Props {
  history: HistoryEntry[];
  onSelect: (entry: HistoryEntry) => void;
  onRefresh: () => void;
}

export default function HistoryPanel({ history, onSelect, onRefresh }: Props) {
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteHistoryEntry(id);
    onRefresh();
  };

  const handleClearAll = () => {
    clearHistory();
    onRefresh();
    setShowClearConfirm(false);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);

    if (diffMin < 1) return '방금 전';
    if (diffMin < 60) return `${diffMin}분 전`;
    if (diffHour < 24) return `${diffHour}시간 전`;
    if (diffDay < 7) return `${diffDay}일 전`;
    return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getGenderLabel = (gender: string) => gender === '남' ? '남성' : '여성';

  const getBirthInfo = (entry: HistoryEntry) => {
    const { year, month, day } = entry.request;
    const calType = entry.request.is_lunar ? '음력' : '양력';
    return `${year}.${String(month).padStart(2, '0')}.${String(day).padStart(2, '0')} (${calType})`;
  };

  if (history.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
          <Clock className="w-8 h-8 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">기록이 없습니다</h3>
        <p className="text-sm text-slate-400">사주 분석을 하면 자동으로 저장됩니다.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header Actions */}
      <div className="px-6 py-3 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium">{history.length}개의 기록</span>
        {!showClearConfirm ? (
          <button
            onClick={() => setShowClearConfirm(true)}
            className="text-xs text-red-400 hover:text-red-500 transition-colors font-medium"
          >
            전체 삭제
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs text-red-400 flex items-center gap-1">
              <AlertTriangle size={12} /> 정말 삭제?
            </span>
            <button
              onClick={handleClearAll}
              className="text-xs px-2 py-0.5 rounded bg-red-500 text-white font-medium hover:bg-red-600 transition-colors"
            >
              확인
            </button>
            <button
              onClick={() => setShowClearConfirm(false)}
              className="text-xs px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
            >
              취소
            </button>
          </div>
        )}
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-3">
        {history.map((entry) => {
          const dayMaster = entry.analysis.eight_characters.day_stem;
          const msgCount = entry.messages.length;

          return (
            <div
              key={entry.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(entry)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(entry); }}
              className="w-full text-left glass-card rounded-2xl p-4 border border-slate-200 dark:border-slate-700 hover:border-primary/40 hover:bg-white/50 dark:hover:bg-slate-800/50 transition-all group cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white truncate">
                      {entry.name}
                    </h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-semibold shrink-0">
                      {dayMaster.element} ({dayMaster.stem_ko})
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span>{getBirthInfo(entry)}</span>
                    <span>·</span>
                    <span>{getGenderLabel(entry.request.gender)}</span>
                    <span>·</span>
                    <span>대화 {msgCount}건</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1.5">{formatDate(entry.createdAt)}</p>
                </div>
                <div className="flex items-center gap-1 shrink-0 ml-3">
                  <button
                    onClick={(e) => handleDelete(e, entry.id)}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all opacity-0 group-hover:opacity-100"
                    title="삭제"
                  >
                    <Trash2 size={14} />
                  </button>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-primary transition-colors" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
