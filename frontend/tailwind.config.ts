import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        vault: {
          950: "#07090e",
          900: "#0b0f19",
          850: "#111726",
          800: "#161f36",
          700: "#222f52",
          accent: "#06b6d4",
          neon: "#38bdf8",
          purple: "#818cf8",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "vault-glow":
          "radial-gradient(circle at 50% -20%, rgba(6, 182, 212, 0.15), transparent 70%)",
      },
    },
  },
  plugins: [],
};
export default config;
