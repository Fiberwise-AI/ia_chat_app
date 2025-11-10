import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Get ports from environment variables
const frontendPort = parseInt(process.env.FRONTEND_PORT || '5173')

export default defineConfig({
  plugins: [react()],
  server: {
    port: frontendPort,
    strictPort: false,
    host: '0.0.0.0',  // Listen on all interfaces for Docker
  }
})
