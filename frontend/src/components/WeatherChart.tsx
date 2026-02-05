// frontend/src/components/WeatherChart.tsx
"use client";

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { DailyWeatherSummary, StationWeatherComparison } from "@/lib/types";

// ============================================
// 溫度趨勢圖
// ============================================

interface TemperatureChartProps {
  data: DailyWeatherSummary[];
  height?: number;
}

export function TemperatureChart({ data, height = 300 }: TemperatureChartProps) {
  const chartData = data.map((d) => ({
    date: d.month_day.split("-")[1] + "日",
    平均溫度: d.temp_avg ? parseFloat(d.temp_avg.toFixed(1)) : null,
    最高溫: d.temp_max ? parseFloat(d.temp_max.toFixed(1)) : null,
    最低溫: d.temp_min ? parseFloat(d.temp_min.toFixed(1)) : null,
  }));

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">溫度趨勢</h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis
            unit="°C"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="最高溫"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: "#ef4444", r: 3 }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="平均溫度"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ fill: "#f97316", r: 3 }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="最低溫"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: "#3b82f6", r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================
// 降雨機率圖
// ============================================

interface PrecipChartProps {
  data: DailyWeatherSummary[];
  height?: number;
}

export function PrecipChart({ data, height = 250 }: PrecipChartProps) {
  const chartData = data.map((d) => ({
    date: d.month_day.split("-")[1] + "日",
    降雨機率: d.precip_prob ? parseFloat((d.precip_prob * 100).toFixed(0)) : 0,
    晴天率: d.sunny_rate ? parseFloat((d.sunny_rate * 100).toFixed(0)) : 0,
  }));

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">降雨與晴天機率</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis
            unit="%"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar dataKey="晴天率" fill="#fbbf24" radius={[4, 4, 0, 0]} />
          <Bar dataKey="降雨機率" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================
// 天氣傾向圓餅圖
// ============================================

interface TendencyPieChartProps {
  sunny: number;
  cloudy: number;
  rainy: number;
  size?: number;
}

const TENDENCY_COLORS = ["#fbbf24", "#94a3b8", "#3b82f6"];

export function TendencyPieChart({
  sunny,
  cloudy,
  rainy,
  size = 200
}: TendencyPieChartProps) {
  const data = [
    { name: "晴天", value: parseFloat((sunny * 100).toFixed(0)) },
    { name: "陰天", value: parseFloat((cloudy * 100).toFixed(0)) },
    { name: "雨天", value: parseFloat((rainy * 100).toFixed(0)) },
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">天氣傾向</h3>
      <ResponsiveContainer width="100%" height={size}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={size * 0.25}
            outerRadius={size * 0.4}
            paddingAngle={2}
            dataKey="value"
            label={({ name, value }) => `${name} ${value}%`}
            labelLine={false}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={TENDENCY_COLORS[index % TENDENCY_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================
// 多站點比較柱狀圖
// ============================================

interface StationCompareChartProps {
  data: StationWeatherComparison[];
  metric: "sunny_rate" | "precip_prob" | "temp_avg";
  height?: number;
}

const METRIC_CONFIG = {
  sunny_rate: {
    label: "晴天率",
    color: "#fbbf24",
    unit: "%",
    transform: (v: number | null) => v ? parseFloat((v * 100).toFixed(0)) : 0,
  },
  precip_prob: {
    label: "降雨機率",
    color: "#3b82f6",
    unit: "%",
    transform: (v: number | null) => v ? parseFloat((v * 100).toFixed(0)) : 0,
  },
  temp_avg: {
    label: "平均溫度",
    color: "#f97316",
    unit: "°C",
    transform: (v: number | null) => v ? parseFloat(v.toFixed(1)) : 0,
  },
};

export function StationCompareChart({
  data,
  metric,
  height = 250
}: StationCompareChartProps) {
  const config = METRIC_CONFIG[metric];

  const chartData = data.map((d) => ({
    name: d.station.name,
    [config.label]: config.transform(d[metric]),
  }));

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        {config.label}比較
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 50, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            unit={config.unit}
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            domain={metric === "temp_avg" ? ['auto', 'auto'] : [0, 100]}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            width={60}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Bar
            dataKey={config.label}
            fill={config.color}
            radius={[0, 4, 4, 0]}
            barSize={30}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
