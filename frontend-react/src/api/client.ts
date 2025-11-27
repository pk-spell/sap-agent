/**
 * API Client for SAP Deployment Assistant Backend
 * Communicates with FastAPI backend on localhost:8000
 */

import type {
  Session,
  ChatResponse,
  SessionListResponse,
  CreateSessionResponse,
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
   * Returns blob and filename from Content-Disposition header
   */
  async downloadTfvars(sessionId: string): Promise<{ blob: Blob; filename: string }> {
    const response = await fetch(
      `${this.baseUrl}/api/sessions/${sessionId}/tfvars/download`
    )

    if (!response.ok) {
      throw new Error(`Failed to download TFVARS: ${response.statusText}`)
    }

    const blob = await response.blob()

    // Extract filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `sap-deployment-${sessionId.slice(0, 8)}.tfvars` // Fallback

    if (contentDisposition) {
      console.log('Content-Disposition:', contentDisposition) // Debug log

      // Try multiple patterns to extract filename
      // 1. RFC 6266 format: filename*=UTF-8''foo.txt
      let filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;\s]+)/i)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      } else {
        // 2. Quoted format: filename="foo.txt"
        filenameMatch = contentDisposition.match(/filename="([^"]+)"/i)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        } else {
          // 3. Unquoted format: filename=foo.txt
          filenameMatch = contentDisposition.match(/filename=([^;\s]+)/i)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1]
          }
        }
      }

      console.log('Extracted filename:', filename) // Debug log
    } else {
      console.warn('No Content-Disposition header found, using fallback filename')
    }

    return { blob, filename }
  }

  /**
   * Get TFVARS content as text (for preview)
   */
  async getTfvarsContent(sessionId: string): Promise<string> {
    const { blob } = await this.downloadTfvars(sessionId)
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

  /**
   * Export session configuration as JSON
   */
  async exportAsJSON(sessionId: string): Promise<any> {
    return this.fetchApi(`/api/sessions/${sessionId}/export/json`)
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for testing
export { ApiClient }
