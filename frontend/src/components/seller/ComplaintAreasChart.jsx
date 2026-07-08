import {
  Bar,
  BarChart,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts'
import { VIZ } from './vizTheme'

// Share of fit complaints by garment area. Single series, so one sequential
// hue for every bar (never darker-where-bigger on nominal categories) and
// no legend — the title names the series. Every bar is direct-labeled, so
// no value hides behind a tooltip.
export default function ComplaintAreasChart({ areas }) {
  const data = (areas ?? []).map((a) => ({
    area: a.area,
    pct: Math.round(a.pct * 100),
  }))
  // Container sized to content so labels never get clipped by a fixed height.
  const height = data.length * 40 + 8

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 8 }}>
        <XAxis type="number" domain={[0, 'dataMax']} hide />
        <YAxis
          type="category"
          dataKey="area"
          width={110}
          axisLine={false}
          tickLine={false}
          tick={{ fill: VIZ.inkSecondary, fontSize: 13 }}
        />
        <Bar dataKey="pct" fill={VIZ.bar} barSize={14} radius={[0, 4, 4, 0]} isAnimationActive={false}>
          <LabelList
            dataKey="pct"
            position="right"
            formatter={(v) => `${v}%`}
            style={{ fill: VIZ.ink, fontSize: 13, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
