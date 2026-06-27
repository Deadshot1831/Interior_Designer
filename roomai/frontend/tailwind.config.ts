import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#3B4A3F",
          light: "#5A6E5F",
          sand: "#E8E2D6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
