/**
 * ChatMessage Component
 * Displays a single message in the chat with different styling for user vs assistant
 */

import { makeStyles, tokens, Card, Text, Avatar, Button } from '@fluentui/react-components'
import { Bot24Regular, Person24Regular, Document24Regular } from '@fluentui/react-icons'
import { apiClient } from '../api/client'
import type { Message } from '../types'

const useStyles = makeStyles({
  messageContainer: {
    marginBottom: '16px',
    display: 'flex',
    gap: '12px',
  },
  userMessage: {
    flexDirection: 'row-reverse',
  },
  assistantMessage: {
    flexDirection: 'row',
  },
  avatar: {
    flexShrink: 0,
  },
  messageCard: {
    maxWidth: '70%',
    padding: '12px 16px',
  },
  userCard: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  assistantCard: {
    backgroundColor: tokens.colorNeutralBackground1,
  },
  messageContent: {
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  timestamp: {
    marginTop: '4px',
    opacity: 0.7,
  },
})

interface ChatMessageProps {
  message: Message
  sessionId?: string
}

export default function ChatMessage({ message, sessionId }: ChatMessageProps) {
  const styles = useStyles()
  const isUser = message.role === 'user'
  const isTfvarsDownload = message.content === '__TFVARS_DOWNLOAD__'

  const handleDownload = async () => {
    if (!sessionId) return

    try {
      const { blob, filename } = await apiClient.downloadTfvars(sessionId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Fehler beim Download der TFVARS Datei')
    }
  }

  return (
    <div
      className={`${styles.messageContainer} ${
        isUser ? styles.userMessage : styles.assistantMessage
      }`}
    >
      <Avatar
        className={styles.avatar}
        icon={isUser ? <Person24Regular /> : <Bot24Regular />}
        color={isUser ? 'brand' : 'colorful'}
        size={36}
      />

      <Card
        className={`${styles.messageCard} ${
          isUser ? styles.userCard : styles.assistantCard
        }`}
      >
        {isTfvarsDownload ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Text weight="semibold" size={400}>
              ✅ Konfiguration abgeschlossen!
            </Text>
            <Text>
              Deine TFVARS-Datei ist bereit zum Download. Klicke auf den Button unten, um sie herunterzuladen.
            </Text>
            <Button
              appearance="primary"
              icon={<Document24Regular />}
              onClick={handleDownload}
              style={{ width: 'fit-content' }}
            >
              TFVARS Datei herunterladen
            </Button>
          </div>
        ) : (
          <>
            <Text
              className={styles.messageContent}
              style={{ color: isUser ? tokens.colorNeutralForegroundOnBrand : undefined }}
            >
              {message.content}
            </Text>

            {message.timestamp && (
              <Text
                size={200}
                className={styles.timestamp}
                style={{ color: isUser ? tokens.colorNeutralForegroundOnBrand : undefined }}
              >
                {new Date(message.timestamp).toLocaleTimeString('de-DE', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </Text>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
