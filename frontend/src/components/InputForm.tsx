import React, { useState } from 'react';
import { User, Calendar, Clock, Moon, Sun, Check } from 'lucide-react';
import { getLeapMonth, type AnalyzeRequest } from '@/lib/api';

interface Props {
  onSubmit: (data: AnalyzeRequest) => void;
  isLoading: boolean;
}

const HOUR_OPTIONS = [
  { value: 0, label: "자시 (23:30~01:30)" },
  { value: 2, label: "축시 (01:30~03:30)" },
  { value: 4, label: "인시 (03:30~05:30)" },
  { value: 6, label: "묘시 (05:30~07:30)" },
  { value: 8, label: "진시 (07:30~09:30)" },
  { value: 10, label: "사시 (09:30~11:30)" },
  { value: 12, label: "오시 (11:30~13:30)" },
  { value: 14, label: "미시 (13:30~15:30)" },
  { value: 16, label: "신시 (15:30~17:30)" },
  { value: 18, label: "유시 (17:30~19:30)" },
  { value: 20, label: "술시 (19:30~21:30)" },
  { value: 22, label: "해시 (21:30~23:30)" },
];

export default function InputForm({ onSubmit, isLoading }: Props) {
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [hour, setHour] = useState(10);
  const [gender, setGender] = useState("남");
  const [isLunar, setIsLunar] = useState(false);
  const [isLeapMonth, setIsLeapMonth] = useState(false);
  const [leapMonthOfYear, setLeapMonthOfYear] = useState(0);

  const handleBirthDateChange = async (newDate: string) => {
    setBirthDate(newDate);
    setIsLeapMonth(false);

    if (isLunar && newDate) {
      const year = parseInt(newDate.split("-")[0], 10);
      if (year >= 1900 && year <= 2100) {
        try {
          const data = await getLeapMonth(year);
          setLeapMonthOfYear(data.leap_month);
        } catch {
          setLeapMonthOfYear(0);
        }
      } else {
        setLeapMonthOfYear(0);
      }
    } else {
      setLeapMonthOfYear(0);
    }
  };

  const handleLunarToggle = async () => {
    const newLunar = !isLunar;
    setIsLunar(newLunar);
    if (!newLunar) {
      setIsLeapMonth(false);
      setLeapMonthOfYear(0);
    } else if (birthDate) {
      const year = parseInt(birthDate.split("-")[0], 10);
      if (year >= 1900 && year <= 2100) {
        try {
          const data = await getLeapMonth(year);
          setLeapMonthOfYear(data.leap_month);
        } catch {
          setLeapMonthOfYear(0);
        }
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !birthDate) return;
    const [year, month, day] = birthDate.split("-").map(Number);
    const safeLeapMonth = isLunar && isLeapMonth && leapMonthOfYear === month;
    onSubmit({
      name,
      year,
      month,
      day,
      hour,
      minute: 0,
      gender,
      is_lunar: isLunar,
      is_leap_month: safeLeapMonth,
    });
  };

  return (
    <div className="flex-1 flex flex-col justify-center max-w-md mx-auto px-6 py-8">
      <header className="mb-8 text-center">
        <p className="text-sm font-semibold text-slate-400 tracking-widest uppercase mb-2">Destiny Compass</p>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">사주 분석</h1>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name Input */}
        <div className="glass-card rounded-2xl p-1 flex items-center transition-all focus-within:ring-2 focus-within:ring-primary">
          <div className="p-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
              <User size={20} />
            </div>
          </div>
          <div className="flex-1 pr-4">
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-0.5">이름</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="이름을 입력하세요"
              className="w-full bg-transparent border-none outline-none text-slate-900 dark:text-white text-base font-medium placeholder-slate-400 h-8"
              required
            />
          </div>
        </div>

        {/* Date & Time */}
        <div className="grid grid-cols-1 gap-4">
          <div className="glass-card rounded-2xl p-1 flex items-center transition-all focus-within:ring-2 focus-within:ring-emerald-500">
            <div className="p-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500">
                <Calendar size={20} />
              </div>
            </div>
            <div className="flex-1 pr-4">
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-0.5">생년월일</label>
              <input 
                type="date" 
                value={birthDate}
                onChange={(e) => handleBirthDateChange(e.target.value)}
                className="w-full bg-transparent border-none outline-none text-slate-900 dark:text-white text-base font-medium h-8"
                required
              />
            </div>
          </div>

          <div className="glass-card rounded-2xl p-1 flex items-center transition-all focus-within:ring-2 focus-within:ring-amber-500">
            <div className="p-4">
              <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-500">
                <Clock size={20} />
              </div>
            </div>
            <div className="flex-1 pr-4">
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-0.5">태어난 시간</label>
              <select 
                value={hour}
                onChange={(e) => setHour(Number(e.target.value))}
                className="w-full bg-transparent border-none outline-none text-slate-900 dark:text-white text-base font-medium appearance-none h-8"
              >
                {HOUR_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value} className="bg-white dark:bg-slate-800 text-slate-900 dark:text-white">
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Gender & Calendar Type */}
        <div className="grid grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => setGender(gender === "남" ? "여" : "남")}
            className={`p-4 rounded-2xl border transition-all flex flex-col items-center justify-center gap-2 h-24 ${
              gender === "남" 
                ? "bg-primary/20 border-primary text-primary shadow-[0_0_15px_rgba(19,127,236,0.3)]" 
                : "glass-card border-transparent text-slate-400 hover:bg-white/5"
            }`}
          >
            <span className="text-base font-bold">{gender === "남" ? "남성" : "여성"}</span>
          </button>

          <button
            type="button"
            onClick={handleLunarToggle}
            className={`p-4 rounded-2xl border transition-all flex flex-col items-center justify-center gap-2 h-24 ${
              isLunar
                ? "bg-blue-400/20 border-blue-400 text-blue-400 shadow-[0_0_15px_rgba(96,165,250,0.3)]" 
                : "glass-card border-transparent text-slate-400 hover:bg-white/5"
            }`}
          >
            <div className="flex items-center gap-2">
              {isLunar ? <Moon size={18} /> : <Sun size={18} />}
              <span className="text-base font-bold">{isLunar ? "음력" : "양력"}</span>
            </div>
          </button>
        </div>

        {isLunar && leapMonthOfYear > 0 && (
          <div 
            onClick={() => setIsLeapMonth(!isLeapMonth)}
            className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
              isLeapMonth
                ? "bg-amber-500/20 border-amber-500 text-amber-500"
                : "glass-card border-transparent text-slate-400 hover:bg-white/5"
            }`}
          >
            <span className="text-sm font-medium">윤달 적용 (윤{leapMonthOfYear}월)</span>
            {isLeapMonth && <Check size={18} />}
          </div>
        )}

        <button 
          type="submit" 
          disabled={isLoading}
          className="w-full h-14 rounded-2xl bg-primary text-white text-lg font-bold shadow-[0_10px_20px_-5px_rgba(19,127,236,0.5)] hover:bg-primary/90 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-8"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              분석 중...
            </span>
          ) : (
            "운세 확인하기"
          )}
        </button>
      </form>
    </div>
  );
}
