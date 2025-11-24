/**
 * ChatWindow Component
 * Main chat interface with message list, input field, and auto-scroll
 */

import { useState, useEffect, useRef } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Input,
  Spinner,
  Text,
} from '@fluentui/react-components'
import { Send24Regular } from '@fluentui/react-icons'
import ChatMessage from './ChatMessage'
import { apiClient } from '../api/client'
import type { Message, ChatResponse } from '../types'

const useStyles = makeStyles({
  chatContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: tokens.colorNeutralBackground2,
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
  },
  inputContainer: {
    padding: '16px 24px',
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    gap: '16px',
    color: tokens.colorNeutralForeground3,
  },
  loadingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px',
    marginBottom: '16px',
  },
})

interface ChatWindowProps {
  sessionId: string
  onProgress?: (step: number, total: number) => void
  onTfvarsReady?: () => void
}

export default function ChatWindow({
  sessionId,
  onProgress,
  onTfvarsReady,
}: ChatWindowProps) {
  const styles = useStyles()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingSession, setLoadingSession] = useState(true)
  const [tfvarsAdded, setTfvarsAdded] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load session history when sessionId changes
  useEffect(() => {
    setTfvarsAdded(false) // Reset on session change
    loadSessionHistory()
  }, [sessionId])

  const loadSessionHistory = async () => {
    setLoadingSession(true)
    try {
      const data = await apiClient.loadChat(sessionId)
      setMessages(data.messages || [])

      // If TFVARS already ready, notify parent and add download message
      if (data.tfvars_ready) {
        onTfvarsReady?.()
        onProgress?.(6, 6) // Assuming 6 total steps
        setTfvarsAdded(true) // Mark as added so we don't add it again
      }
    } catch (error) {
      console.error('Failed to load session:', error)
      // Start with welcome message if session is new
      setMessages([
        {
          role: 'assistant',
          content:
            'Willkommen beim SAP Deployment Assistant! Ich helfe dir, eine Terraform-Konfiguration für deine SAP-Umgebung zu erstellen.\n\nLass uns mit der Umgebungskonfiguration beginnen. Welche Azure Region möchtest du verwenden? (z.B. westeurope, northeurope)',
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setLoadingSession(false)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    // Add user message to UI immediately
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response: ChatResponse = await apiClient.sendMessage(
        sessionId,
        userMessage.content
      )

      // Add assistant response
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // Update progress if provided
      if (response.current_step && response.total_steps) {
        onProgress?.(response.current_step, response.total_steps)
      }

      // Notify if TFVARS ready and add download message
      if (response.tfvars_ready && !tfvarsAdded) {
        onTfvarsReady?.()
        setTfvarsAdded(true)

        // Add download message to chat
        const downloadMessage: Message = {
          role: 'assistant',
          content: '__TFVARS_DOWNLOAD__', // Special marker for ChatMessage component
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, downloadMessage])
      }
    } catch (error) {
      console.error('Failed to send message:', error)

      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: `Fehler: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (loadingSession) {
    return (
      <div className={styles.emptyState}>
        <Spinner size="large" />
        <Text>Session wird geladen...</Text>
      </div>
    )
  }

  return (
    <div className={styles.chatContainer}>
      {/* Messages */}
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <Text size={500}>Keine Nachrichten</Text>
            <Text size={300}>
              Starte eine Konversation, um deine SAP-Konfiguration zu erstellen
            </Text>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} sessionId={sessionId} />
            ))}

            {isLoading && (
              <div className={styles.loadingIndicator}>
                <Spinner size="small" />
                <Text size={300}>Assistent antwortet...</Text>
              </div>
            )}

            {/* Auto-scroll anchor */}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className={styles.inputContainer}>
        <Input
          className={styles.input}
          placeholder="Nachricht eingeben... (Enter zum Senden, Shift+Enter für neue Zeile)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
          size="large"
        />
        <Button
          appearance="primary"
          icon={<Send24Regular />}
          onClick={handleSendMessage}
          disabled={!input.trim() || isLoading}
          size="large"
        >
          Senden
        </Button>
      </div>
    </div>
  )
}
