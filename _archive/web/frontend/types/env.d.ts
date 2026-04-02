declare namespace NodeJS {
  interface ProcessEnv {
    // WebSocket Configuration
    NEXT_PUBLIC_WS_URL: string;
    NEXT_PUBLIC_API_URL: string;
    
    // Authentication
    NEXT_PUBLIC_AUTH_ENABLED: string;
    
    // Feature Flags
    NEXT_PUBLIC_ENABLE_MEV: string;
    NEXT_PUBLIC_ENABLE_SOCIAL_SIGNALS: string;
    NEXT_PUBLIC_ENABLE_CLONE_SPAWNING: string;
    
    // Trading Configuration
    NEXT_PUBLIC_MAX_CLONES: string;
    NEXT_PUBLIC_MIN_CLONE_CAPITAL: string;
    NEXT_PUBLIC_SPAWN_THRESHOLD: string;
    
    // Display Configuration
    NEXT_PUBLIC_CHART_UPDATE_INTERVAL: string;
    NEXT_PUBLIC_PERFORMANCE_HISTORY_HOURS: string;
  }
}