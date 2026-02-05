// frontend/src/components/DateRangePicker.tsx
"use client";

import { useState, useCallback } from "react";

interface DateRangePickerProps {
  onRangeSelect: (startDate: string, endDate: string) => void;
  disabled?: boolean;
}

const MONTHS = [
  "一月", "二月", "三月", "四月", "五月", "六月",
  "七月", "八月", "九月", "十月", "十一月", "十二月"
];

const DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

export function DateRangePicker({ onRangeSelect, disabled }: DateRangePickerProps) {
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [startDay, setStartDay] = useState<number | null>(null);
  const [endDay, setEndDay] = useState<number | null>(null);

  const handleDayClick = useCallback((day: number) => {
    if (startDay === null || endDay !== null) {
      // 開始新的選擇
      setStartDay(day);
      setEndDay(null);
    } else {
      // 完成選擇
      const start = Math.min(startDay, day);
      const end = Math.max(startDay, day);
      setStartDay(start);
      setEndDay(end);

      // 格式化日期並回調
      const month = String(selectedMonth + 1).padStart(2, "0");
      const startDate = `${month}-${String(start).padStart(2, "0")}`;
      const endDate = `${month}-${String(end).padStart(2, "0")}`;
      onRangeSelect(startDate, endDate);
    }
  }, [startDay, endDay, selectedMonth, onRangeSelect]);

  const isInRange = (day: number) => {
    if (startDay === null) return false;
    if (endDay === null) return day === startDay;
    return day >= startDay && day <= endDay;
  };

  const isStart = (day: number) => day === startDay;
  const isEnd = (day: number) => day === endDay;

  const daysCount = DAYS_IN_MONTH[selectedMonth];
  const days = Array.from({ length: daysCount }, (_, i) => i + 1);

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      {/* 月份選擇 */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setSelectedMonth((m) => (m - 1 + 12) % 12)}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          disabled={disabled}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h3 className="text-lg font-semibold text-gray-800">
          {MONTHS[selectedMonth]}
        </h3>
        <button
          onClick={() => setSelectedMonth((m) => (m + 1) % 12)}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          disabled={disabled}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* 星期標題 */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {["日", "一", "二", "三", "四", "五", "六"].map((d) => (
          <div key={d} className="text-center text-xs text-gray-500 py-1">
            {d}
          </div>
        ))}
      </div>

      {/* 日期網格 */}
      <div className="grid grid-cols-7 gap-1">
        {/* 填充月初空白 */}
        {Array.from({ length: new Date(2000, selectedMonth, 1).getDay() }).map((_, i) => (
          <div key={`empty-${i}`} className="h-8" />
        ))}

        {/* 日期按鈕 */}
        {days.map((day) => (
          <button
            key={day}
            onClick={() => handleDayClick(day)}
            disabled={disabled}
            className={`
              h-8 rounded-lg text-sm font-medium transition-all
              ${isInRange(day)
                ? isStart(day) || isEnd(day)
                  ? "bg-blue-500 text-white"
                  : "bg-blue-100 text-blue-700"
                : "hover:bg-gray-100 text-gray-700"
              }
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
          >
            {day}
          </button>
        ))}
      </div>

      {/* 選擇提示 */}
      <div className="mt-4 text-center text-sm text-gray-500">
        {startDay === null
          ? "點選起始日期"
          : endDay === null
          ? "點選結束日期"
          : `已選擇: ${startDay} 日 ~ ${endDay} 日`}
      </div>
    </div>
  );
}
