import pako from "pako";
import type { AnalysisData, DailyFortuneData } from "./api";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://sajugo.shop";

function compressAndEncode(data: object): string {
  const json = JSON.stringify(data);
  const compressed = pako.deflate(new TextEncoder().encode(json));
  let base64 = btoa(String.fromCharCode(...compressed));
  base64 = base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return base64;
}

export function buildAnalysisShareUrl(
  analysis: AnalysisData,
  messages: { role: string; content: string }[],
): string {
  const pillars = analysis.eight_characters.pillars;
  const elements = Object.values(analysis.element_analysis.element_stats).map((e) => ({
    name: e.element_ko,
    hanja: e.element,
    ratio: Math.round(e.ratio),
  }));

  const reading = messages
    .filter((m) => m.role === "assistant" && m.content)
    .map((m) => m.content)
    .join("\n\n");

  const data = {
    type: "analysis",
    title: `${analysis.eight_characters.name}님의 사주`,
    dayMaster: `${analysis.eight_characters.day_stem.element} (${analysis.eight_characters.day_stem.stem_ko})`,
    strength: analysis.strength_analysis.strength_status,
    yongShin: `${analysis.yong_shin_analysis.yong_shin} (${analysis.yong_shin_analysis.yong_shin_ko})`,
    pillars: {
      time: { stem: pillars.time.stem, branch: pillars.time.branch },
      day: { stem: pillars.day.stem, branch: pillars.day.branch },
      month: { stem: pillars.month.stem, branch: pillars.month.branch },
      year: { stem: pillars.year.stem, branch: pillars.year.branch },
    },
    elements,
    reading,
    ogDescription: `${analysis.eight_characters.day_stem.element} 일간 | ${analysis.strength_analysis.strength_status} | 용신: ${analysis.yong_shin_analysis.yong_shin_ko}`,
  };

  return `${APP_URL}/share?d=${compressAndEncode(data)}`;
}

export function buildFortuneShareUrl(fortune: DailyFortuneData): string {
  const data = {
    type: "fortune",
    title: `${fortune.name}님의 오늘의 운세`,
    fortune: {
      date: fortune.date,
      weekday: fortune.weekday,
      luck_index: fortune.luck_index,
      fortune: fortune.fortune,
      love: fortune.love,
      work: fortune.work,
      health: fortune.health,
      warning: fortune.warning,
      lucky_color: fortune.lucky_color,
      lucky_number: fortune.lucky_number,
      lucky_item: fortune.lucky_item,
    },
    ogDescription: `행운지수 ${fortune.luck_index}점 | ${fortune.fortune.slice(0, 50)}...`,
  };

  return `${APP_URL}/share?d=${compressAndEncode(data)}`;
}

export function buildChatShareUrl(
  name: string,
  messages: { role: string; content: string }[],
): string {
  const data = {
    type: "chat",
    title: `${name}님의 사주 상담`,
    subtitle: `대화 ${messages.length}건`,
    messages: messages.filter((m) => m.content).map((m) => ({
      role: m.role,
      content: m.content.slice(0, 2000),
    })),
    ogDescription: `${name}님의 사주 상담 내역 (${messages.length}건)`,
  };

  return `${APP_URL}/share?d=${compressAndEncode(data)}`;
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
