import { theme } from './src/utils/theme';

/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          background: theme.colors.background,
          'text-dark': theme.colors.textDark,
          button: theme.colors.button,
        },
      },
    },
    plugins: [],
  }