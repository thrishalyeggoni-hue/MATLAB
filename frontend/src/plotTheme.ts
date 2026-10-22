import type { Layout } from "plotly.js";
export const BASE_LAYOUT: Partial<Layout> = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "#161a20",
  font: { family: "Arial, sans-serif", color: "#aab2c0", size: 11 },
  margin: { l: 58, r: 25, t: 20, b: 45 },
  hovermode: "x unified",
  legend: { orientation: "h", x: 0, y: 1.2 },
  xaxis: {
    gridcolor: "#2b3039",
    zerolinecolor: "#343b46",
    title: { text: "DISTANCE (m)" },
  },
  yaxis: { gridcolor: "#2b3039", zerolinecolor: "#343b46" },
  autosize: true,
};
