import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          navy: '#0E1F3D',
          navyDark: '#091429',
          navyLight: '#1a3358',
          gold: '#C08B3A',
          goldLight: '#D4A254',
          goldDark: '#A07230',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '70ch',
          },
        },
      },
    },
  },
  plugins: [
    typography,
  ],
};
