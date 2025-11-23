/**
 * ChatMessage Component
 * Displays a single message in the chat with different styling for user vs assistant
 */

import { makeStyles, tokens, Card, Text, Avatar } from '@fluentui/react-components'
import { Bot24Regular, Person24Regular } from '@fluentui/react-icons'
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
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const styles = useStyles()
  const isUser = message.role === 'user'

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
      </Card>
    </div>
  )
}
