/// <reference types="vite/client" />

// Global ambient types for environment variables
interface ImportMetaEnv {
  readonly VITE_OPENAI_API_BASE?: string
  readonly VITE_OPENAI_API_KEY?: string
  readonly VITE_GDRIVE_API_KEY?: string
  readonly VITE_GDRIVE_CLIENT_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
