// Authentication utilities for WebSocket and API connections

interface AuthToken {
  token: string;
  expiresAt: number;
  refreshToken?: string;
}

export class AuthManager {
  private static TOKEN_KEY = 'authToken';
  private static REFRESH_TOKEN_KEY = 'refreshToken';
  private static TOKEN_EXPIRY_KEY = 'tokenExpiry';

  static saveToken(authData: AuthToken): void {
    localStorage.setItem(this.TOKEN_KEY, authData.token);
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, authData.expiresAt.toString());
    
    if (authData.refreshToken) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, authData.refreshToken);
    }
  }

  static getToken(): string | null {
    const token = localStorage.getItem(this.TOKEN_KEY);
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    if (!token || !expiry) {
      return null;
    }
    
    // Check if token is expired
    if (Date.now() > parseInt(expiry, 10)) {
      this.clearToken();
      return null;
    }
    
    return token;
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static clearToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
  }

  static isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  static async refreshAuthToken(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Failed to refresh token');
      }

      const data = await response.json();
      this.saveToken({
        token: data.access_token,
        expiresAt: Date.now() + (data.expires_in * 1000),
        refreshToken: data.refresh_token || refreshToken,
      });

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearToken();
      return false;
    }
  }

  static async ensureValidToken(): Promise<string | null> {
    let token = this.getToken();
    
    if (!token) {
      // Try to refresh if we have a refresh token
      const refreshed = await this.refreshAuthToken();
      if (refreshed) {
        token = this.getToken();
      }
    }
    
    return token;
  }
}

// WebSocket authentication header generator
export function getWSAuthHeaders(): Record<string, string> {
  const token = AuthManager.getToken();
  if (!token) {
    return {};
  }
  
  return {
    'Authorization': `Bearer ${token}`,
  };
}

// API request interceptor for axios
export function setupAuthInterceptor(axiosInstance: any): void {
  // Request interceptor
  axiosInstance.interceptors.request.use(
    async (config: any) => {
      const token = await AuthManager.ensureValidToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: any) => Promise.reject(error)
  );

  // Response interceptor for handling 401s
  axiosInstance.interceptors.response.use(
    (response: any) => response,
    async (error: any) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        const refreshed = await AuthManager.refreshAuthToken();
        if (refreshed) {
          const token = AuthManager.getToken();
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return axiosInstance(originalRequest);
        }
      }

      return Promise.reject(error);
    }
  );
}