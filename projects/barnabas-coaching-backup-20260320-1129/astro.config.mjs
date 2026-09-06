import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://barnabas.coach',
  integrations: [
    tailwind(),
  ],
  output: 'static',
});
