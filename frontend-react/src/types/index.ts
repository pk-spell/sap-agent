/**
 * TypeScript type definitions for SAP Deployment Assistant
 */

export interface Session {
  session_id: string
  created_at: string
  updated_at?: string
  name?: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatResponse {
  reply: string
  block?: string
  tfvars_ready?: boolean
  current_step?: number
  total_steps?: number
}

export interface SessionListResponse {
  sessions: Session[]
}

export interface CreateSessionResponse {
  session_id: string
  name: string
  created_at: string
}

export interface SendMessageRequest {
  session_id: string
  message: string
}

export interface LoadChatResponse {
  session_id: string
  messages: Message[]
  tfvars_content?: string
  tfvars_ready?: boolean
}

export interface ApiError {
  detail: string
  status?: number
}
