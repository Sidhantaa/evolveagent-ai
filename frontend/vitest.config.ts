import { defineConfig } from 'vitest/config'

// Standalone Vitest config (does NOT load the Tailwind/React vite plugins, which
// are ESM-only and can't be required by Vitest's esbuild loader). Tests exercise
// the data-layer mappers, so no CSS/JSX transform is needed here.
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
