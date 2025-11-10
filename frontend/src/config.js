// API configuration
// The browser always needs to use localhost (or the production URL)
// because it runs on the host machine, not inside Docker
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8091'
