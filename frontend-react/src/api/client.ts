/**
 * API Client for SAP Deployment Assistant Backend
 * Communicates with FastAPI backend on localhost:8000
 */

import type {
  Session,
  Message,
  ChatResponse,
  SessionListResponse,
  CreateSessionResponse,
  SendMessageRequest,
  LoadChatResponse,
  ApiError,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async fetchApi<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const error: ApiError = await response
          .json()
          .catch(() => ({ detail: 'Unknown error occurred' }))
        throw new Error(error.detail || `HTTP ${response.status}`)
      }

      return response.json()
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Network error occurred')
    }
  }

  /**
   * Health check endpoint
   */
  async checkHealth(): Promise<{ status: string }> {
    return this.fetchApi('/health')
  }

  /**
   * Create a new chat session
   */
  async createSession(): Promise<Session> {
    const response = await this.fetchApi<CreateSessionResponse>('/api/sessions', {
      method: 'POST',
    })
    return {
      session_id: response.session_id,
      name: response.name,
      created_at: response.created_at,
    }
  }

  /**
   * Send a message in a chat session
   */
  async sendMessage(
    sessionId: string,
    message: string
  ): Promise<ChatResponse> {
    const payload = { message }

    return this.fetchApi<ChatResponse>(`/api/sessions/${sessionId}/chat`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  /**
   * Get list of all chat sessions
   */
  async getSessions(): Promise<Session[]> {
    const response = await this.fetchApi<SessionListResponse>('/api/sessions')
    return response.sessions
  }

  /**
   * Load a specific chat session with its history
   */
  async loadChat(sessionId: string): Promise<LoadChatResponse> {
    return this.fetchApi<LoadChatResponse>(`/api/sessions/${sessionId}`)
  }

  /**
   * Download TFVARS file for a session
   */
  async downloadTfvars(sessionId: string): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/tfvars/download`
    )

    if (!response.ok) {
      throw new Error(`Failed to download TFVARS: ${response.statusText}`)
    }

    return response.blob()
  }

  /**
   * Get TFVARS content as text (for preview)
   */
  async getTfvarsContent(sessionId: string): Promise<string> {
    const blob = await this.downloadTfvars(sessionId)
    return blob.text()
  }

  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.fetchApi(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for testing
export { ApiClient }
