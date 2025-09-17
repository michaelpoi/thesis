import React, { useMemo } from "react";

/**
 * Speedometer
 * - Renders a semicircle gauge with tick marks, labels, and a needle.
 * - Smoothly animates to the latest `speed`.
 *
 * Props:
 *  speed: number            // current speed (same units as max)
 *  max: number              // max speed displayed (e.g., 200)
 *  units?: string           // label, e.g., "km/h" or "mph"
 *  majorTicks?: number      // number of major ticks (including 0 & max)
 *  minorPerMajor?: number   // minor ticks between majors
 *  color?: string           // accent color for arc and needle
 *  background?: string      // gauge background
 *  width?: number           // px; height auto = width/2
 */
export default function Speedometer({
  speed,
  max,
  units = "km/h",
  majorTicks = 5,
  minorPerMajor = 4,
  color = "#4F46E5",
  background = "#0d0f13",
  width = 360,
}) {
  const clamped = Math.max(0, Math.min(speed, max));
  const value = clamped / max; // 0..1

  // SVG viewbox is 0..100 x 0..50 (semicircle). We then scale to "width".
  const vbWidth = 100;
  const vbHeight = 55; // a little padding below for labels
  const cx = 50;
  const cy = 50; // center of the full circle would be y=50; we draw upper half
  const r = 45;

  // Angle mapping: value=0 -> 180deg (left), value=1 -> 0deg (right)
  const angle = useMemo(() => {
    const deg = 180 - value * 180; // 180..0
    return (deg * Math.PI) / 180;
  }, [value]);

  const needleX = cx + r * Math.cos(angle);
  const needleY = cy - r * Math.sin(angle);

  // Build ticks
  const majors = Array.from({ length: majorTicks }, (_, i) => i);
  const minorsTotal = (majorTicks - 1) * minorPerMajor + 1;
  const minorStep = 1 / (minorsTotal - 1);
  const minorValues = Array.from({ length: minorsTotal }, (_, i) => i * minorStep);

  const labelFor = (v) => Math.round(v * max);

  // Arc path for nice background & value arc
 const arcPath = (fromValue, toValue) => {
   // map 0..1 to π..0 (left to right)
   const a0 = Math.PI * (1 - fromValue);
   const a1 = Math.PI * (1 - toValue);
   const x0 = cx + r * Math.cos(a0);
   const y0 = cy - r * Math.sin(a0);
   const x1 = cx + r * Math.cos(a1);
   const y1 = cy - r * Math.sin(a1);
   const largeArcFlag = toValue - fromValue > 0.5 ? 1 : 0;
   const sweepFlag = 1; // <-- clockwise (left -> right)
   return `M ${x0} ${y0} A ${r} ${r} 0 ${largeArcFlag} ${sweepFlag} ${x1} ${y1}`;
 };

  return (
    <div
      style={{
        width,
        height: Math.round(width / 2),
        background,
        borderRadius: 12,
        display: "grid",
        placeItems: "center",
      }}
    >
      <svg
        viewBox={`0 0 ${vbWidth} ${vbHeight}`}
        style={{ width: "95%", height: "auto", overflow: "visible" }}
      >
        {/* Shadow / base arc */}
        <path
          d={arcPath(0, 1)}
          stroke="#1f2430"
          strokeWidth="10"
          fill="none"
          strokeLinecap="round"
        />

        {/* Value arc */}
        <path
          d={arcPath(0, value)}
          stroke={color}
          strokeWidth="10"
          fill="none"
          strokeLinecap="round"
          style={{ filter: "drop-shadow(0 0 2px rgba(79,70,229,0.6))" }}
        />

        {/* Minor ticks */}
        {minorValues.map((v, i) => {
          const a = (Math.PI * (180 - v * 180)) / 180;
          const outer = r;
          const inner = r - 2.6; // minor tick length
          const x1 = cx + outer * Math.cos(a);
          const y1 = cy - outer * Math.sin(a);
          const x2 = cx + inner * Math.cos(a);
          const y2 = cy - inner * Math.sin(a);
          return (
            <line
              key={`minor-${i}`}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#2c3342"
              strokeWidth="0.8"
            />
          );
        })}

        {/* Major ticks + labels */}
        {majors.map((i) => {
          const v = i / (majorTicks - 1);
          const a = (Math.PI * (180 - v * 180)) / 180;
          const outer = r;
          const inner = r - 5; // major tick length
          const x1 = cx + outer * Math.cos(a);
          const y1 = cy - outer * Math.sin(a);
          const x2 = cx + inner * Math.cos(a);
          const y2 = cy - inner * Math.sin(a);

          const labelR = r - 10.5;
          const lx = cx + labelR * Math.cos(a);
          const ly = cy - labelR * Math.sin(a);

          return (
            <g key={`major-${i}`}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#9aa0a6" strokeWidth="1.4" />
              <text
                x={lx}
                y={ly}
                fill="#c7ccd6"
                fontSize="4"
                textAnchor="middle"
                dominantBaseline="middle"
                style={{ userSelect: "none" }}
              >
                {labelFor(v)}
              </text>
            </g>
          );
        })}

        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needleX}
          y2={needleY}
          stroke={color}
          strokeWidth="2.8"
          strokeLinecap="round"
          style={{
            transformOrigin: "center",
            transition: "x2 300ms ease, y2 300ms ease",
            filter: "drop-shadow(0 0 2px rgba(79,70,229,0.7))",
          }}
        />
        {/* Needle hub */}
        <circle cx={cx} cy={cy} r="3" fill="#e5e7eb" />

        {/* Label */}
        <text
          x={cx}
          y={cy + 3}
          fill="#e5e7eb"
          fontSize="5"
          textAnchor="middle"
          dominantBaseline="hanging"
          style={{ userSelect: "none" }}
        >
          {Math.round(clamped)} {units}
        </text>
      </svg>
    </div>
  );
}
