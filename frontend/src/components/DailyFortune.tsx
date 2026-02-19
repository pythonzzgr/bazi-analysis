import React, { useState, useEffect } from 'react';
import { Sun, Heart, Briefcase, Activity, Palette, Hash, Gift, AlertTriangle, RefreshCw, Sparkles } from 'lucide-react';
import { getDailyFortune, type DailyFortuneData, type AnalyzeRequest, type HistoryEntry } from '@/lib/api';
import type { SessionUser } from '@/lib/auth';
import { hasProfile } from '@/lib/auth';

interface Props {
  user: SessionUser;
  history: HistoryEntry[];
}

const FORTUNE_CACHE_KEY = 'saju-daily-fortune';

function getCachedFortune(): DailyFortuneData | null {
  try {
    const raw = localStorage.getItem(FORTUNE_CACHE_KEY);
    if (!raw) return null;
    const cached = JSON.parse(raw);
    const today = new Date();
    const todayStr = `${today.getFullYear()}년 ${String(today.getMonth() + 1).padStart(2, '0')}월 ${String(today.getDate()).padStart(2, '0')}일`;
    if (cached.date === todayStr) return cached;
    return null;
  } catch {
    return null;
  }
}

function getLuckColor(index: number): string {
  if (index >= 80) return 'text-emerald-500';
  if (index >= 60) return 'text-blue-500';
  if (index >= 40) return 'text-amber-500';
  return 'text-red-400';
}

function getLuckBg(index: number): string {
  if (index >= 80) return 'from-emerald-500 to-teal-400';
  if (index >= 60) return 'from-blue-500 to-cyan-400';
  if (index >= 40) return 'from-amber-500 to-orange-400';
  return 'from-red-400 to-rose-400';
}

function getLuckLabel(index: number): string {
  if (index >= 80) return '대길';
  if (index >= 60) return '길';
  if (index >= 40) return '보통';
  return '주의';
}

function buildRequestFromProfile(user: SessionUser): (AnalyzeRequest & { user_id: string }) | null {
  if (!hasProfile(user)) return null;
  return {
    name: user.displayName,
    year: user.birthYear!,
    month: user.birthMonth!,
    day: user.birthDay!,
    hour: user.birthHour ?? 12,
    minute: user.birthMinute ?? 0,
    gender: user.gender!,
    is_lunar: user.isLunar ?? false,
    is_leap_month: user.isLeapMonth ?? false,
    user_id: user.id,
  };
}

export default function DailyFortune({ user, history }: Props) {
  const [fortune, setFortune] = useState<DailyFortuneData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [useProfile, setUseProfile] = useState(hasProfile(user));

  useEffect(() => {
    const cached = getCachedFortune();
    if (cached) setFortune(cached);
  }, []);

  const fetchFortune = async () => {
    setIsLoading(true);
    setError('');

    try {
      let req: AnalyzeRequest & { user_id: string };

      if (useProfile && hasProfile(user)) {
        req = buildRequestFromProfile(user)!;
      } else if (history.length > 0) {
        const entry = history[selectedIdx];
        if (!entry) return;
        req = { ...entry.request, user_id: user.id };
      } else {
        setError('프로필에 생년월일을 설정하거나, 사주 분석을 먼저 진행해주세요.');
        return;
      }

      const data = await getDailyFortune(req);
      setFortune(data);
      localStorage.setItem(FORTUNE_CACHE_KEY, JSON.stringify(data));
    } catch (e) {
      setError(e instanceof Error ? e.message : '운세 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const noSource = !hasProfile(user) && history.length === 0;

  if (noSource) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 text-center">
        <Sun className="w-12 h-12 text-slate-300 mb-4" />
        <p className="text-sm text-slate-400">사주 분석을 먼저 진행해주세요.</p>
        <p className="text-xs text-slate-300 mt-1">분석 기록 또는 프로필 생년월일을 기반으로 오늘의 운세를 생성합니다.</p>
      </div>
    );
  }

  if (!fortune && !isLoading) {
    return (
      <div className="flex-1 flex flex-col px-6 py-6">
        <div className="glass-card rounded-3xl p-6 border border-slate-200 dark:border-slate-700 shadow-lg">
          <div className="flex items-center gap-2 mb-5">
            <Sun className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">오늘의 운세</h3>
          </div>

          {hasProfile(user) && history.length > 0 && (
            <div className="mb-4 flex gap-2">
              <button
                onClick={() => setUseProfile(true)}
                className={`flex-1 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  useProfile
                    ? 'bg-primary/10 border-primary text-primary border'
                    : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500'
                }`}
              >
                내 프로필
              </button>
              <button
                onClick={() => setUseProfile(false)}
                className={`flex-1 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  !useProfile
                    ? 'bg-primary/10 border-primary text-primary border'
                    : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500'
                }`}
              >
                분석 기록
              </button>
            </div>
          )}

          {useProfile && hasProfile(user) ? (
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              <span className="font-semibold text-slate-700 dark:text-slate-200">{user.displayName}</span>님의
              프로필 ({user.birthYear}.{user.birthMonth}.{user.birthDay})로 운세를 확인합니다.
            </p>
          ) : (
            <>
              {history.length > 1 && (
                <div className="mb-4">
                  <p className="text-xs text-slate-400 mb-2">운세를 볼 사주를 선택하세요</p>
                  <div className="space-y-2">
                    {history.slice(0, 5).map((entry, idx) => (
                      <button
                        key={entry.id}
                        onClick={() => setSelectedIdx(idx)}
                        className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all ${
                          selectedIdx === idx
                            ? 'bg-primary/10 border-primary text-primary font-semibold border'
                            : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300'
                        }`}
                      >
                        {entry.name} ({entry.request.year}.{entry.request.month}.{entry.request.day})
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {history.length === 1 && (
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                  <span className="font-semibold text-slate-700 dark:text-slate-200">{history[0].name}</span>님의 사주로 오늘의 운세를 확인해보세요.
                </p>
              )}
            </>
          )}

          {error && <p className="text-xs text-red-500 mb-3">{error}</p>}

          <button
            onClick={fetchFortune}
            disabled={isLoading}
            className="w-full h-12 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-bold shadow-[0_8px_16px_-4px_rgba(245,158,11,0.4)] hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles size={16} />
                오늘의 운세 보기
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm text-slate-400">운세를 생성하고 있습니다...</p>
      </div>
    );
  }

  if (!fortune) return null;

  const luckColor = getLuckColor(fortune.luck_index);
  const luckBg = getLuckBg(fortune.luck_index);
  const luckLabel = getLuckLabel(fortune.luck_index);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 pb-24">
      <div className="glass-card rounded-3xl p-6 border border-slate-200 dark:border-slate-700 shadow-lg relative overflow-hidden">
        <div className="absolute -top-16 -right-16 w-48 h-48 bg-amber-400/20 blur-[60px] rounded-full pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-slate-400">{fortune.date} {fortune.weekday}요일</p>
            <button
              onClick={fetchFortune}
              disabled={isLoading}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="새로고침"
            >
              <RefreshCw size={14} className="text-slate-400" />
            </button>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
            {fortune.name}님의 오늘의 운세
          </h3>

          <div className="flex items-center gap-4 mb-5">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" className="text-slate-100 dark:text-slate-800" strokeWidth="8" />
                <circle
                  cx="40" cy="40" r="34" fill="none"
                  className={luckColor}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${(fortune.luck_index / 100) * 213.6} 213.6`}
                  stroke="currentColor"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-xl font-black ${luckColor}`}>{fortune.luck_index}</span>
              </div>
            </div>
            <div>
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${luckBg}`}>
                {luckLabel}
              </span>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">{fortune.fortune}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {fortune.love && (
          <div className="glass-card rounded-2xl p-4 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-pink-50 dark:bg-pink-900/20 flex items-center justify-center shrink-0">
              <Heart className="w-4 h-4 text-pink-500" />
            </div>
            <div>
              <p className="text-xs font-semibold text-pink-500 mb-0.5">연애 / 대인관계</p>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{fortune.love}</p>
            </div>
          </div>
        )}

        {fortune.work && (
          <div className="glass-card rounded-2xl p-4 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0">
              <Briefcase className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <p className="text-xs font-semibold text-blue-500 mb-0.5">직업 / 학업</p>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{fortune.work}</p>
            </div>
          </div>
        )}

        {fortune.health && (
          <div className="glass-card rounded-2xl p-4 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4 text-emerald-500" />
            </div>
            <div>
              <p className="text-xs font-semibold text-emerald-500 mb-0.5">건강</p>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{fortune.health}</p>
            </div>
          </div>
        )}

        {fortune.warning && (
          <div className="glass-card rounded-2xl p-4 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-4 h-4 text-red-400" />
            </div>
            <div>
              <p className="text-xs font-semibold text-red-400 mb-0.5">오늘의 주의사항</p>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{fortune.warning}</p>
            </div>
          </div>
        )}
      </div>

      <div className="glass-card rounded-2xl p-5 border border-slate-200 dark:border-slate-700">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Today&apos;s Lucky</p>
        <div className="grid grid-cols-3 gap-3">
          {fortune.lucky_color && (
            <div className="flex flex-col items-center gap-1.5 py-2">
              <Palette className="w-5 h-5 text-violet-500" />
              <span className="text-[10px] text-slate-400">행운 색상</span>
              <span className="text-sm font-bold text-slate-900 dark:text-white">{fortune.lucky_color}</span>
            </div>
          )}
          {fortune.lucky_number > 0 && (
            <div className="flex flex-col items-center gap-1.5 py-2">
              <Hash className="w-5 h-5 text-blue-500" />
              <span className="text-[10px] text-slate-400">행운 숫자</span>
              <span className="text-sm font-bold text-slate-900 dark:text-white">{fortune.lucky_number}</span>
            </div>
          )}
          {fortune.lucky_item && (
            <div className="flex flex-col items-center gap-1.5 py-2">
              <Gift className="w-5 h-5 text-amber-500" />
              <span className="text-[10px] text-slate-400">행운 아이템</span>
              <span className="text-sm font-bold text-slate-900 dark:text-white">{fortune.lucky_item}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
