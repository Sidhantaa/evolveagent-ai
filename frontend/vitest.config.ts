import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Standalone Vitest config. Includes the React plugin (for JSX/TSX transform in
// component tests) but NOT the Tailwind plugin, which is ESM-only and can't be
// loaded by Vitest's config loader.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./src/test-setup.ts'],
  },
})
