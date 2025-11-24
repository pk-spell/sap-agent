/**
 * SessionList Component
 * Displays list of chat sessions in the sidebar with selection capability
 */

import { useState, useEffect } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Text,
  Spinner,
} from '@fluentui/react-components'
import { Chat20Regular, CheckmarkCircle20Regular, Delete20Regular } from '@fluentui/react-icons'
import { apiClient } from '../api/client'
import type { Session } from '../types'

const useStyles = makeStyles({
  container: {
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  header: {
    marginBottom: '8px',
  },
  sessionItem: {
    width: '100%',
    justifyContent: 'flex-start',
    padding: '12px',
    paddingRight: '40px', // Space for delete button
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: '4px',
    textAlign: 'left',
    position: 'relative',
  },
  sessionItemWrapper: {
    position: 'relative',
    width: '100%',
    '&:hover': {
      '& .deleteButton': {
        opacity: '1 !important',
      },
    },
  },
  deleteButton: {
    position: 'absolute',
    right: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    opacity: 0,
    transition: 'opacity 0.2s ease-in-out',
    minWidth: '28px',
    height: '28px',
    padding: '4px',
    zIndex: 10,
    backgroundColor: tokens.colorNeutralBackground1,
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  deleteButtonVisible: {
    opacity: 1,
  },
  activeSession: {
    backgroundColor: tokens.colorBrandBackground2,
    borderLeft: `3px solid ${tokens.colorBrandBackground}`,
  },
  sessionName: {
    fontWeight: 600,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    width: '100%',
  },
  sessionDate: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground3,
  },
  emptyState: {
    textAlign: 'center',
    padding: '24px 16px',
    color: tokens.colorNeutralForeground3,
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '24px',
  },
})

interface SessionListProps {
  currentSessionId: string | null
  onSelectSession: (sessionId: string) => void
}

export default function SessionList({
  currentSessionId,
  onSelectSession,
}: SessionListProps) {
  const styles = useStyles()
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    setIsLoading(true)
    try {
      const sessionList = await apiClient.getSessions()
      // Sort by created_at descending (newest first)
      const sorted = sessionList.sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setSessions(sorted)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    // Format based on time difference
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

    // Otherwise show date
    return date.toLocaleDateString('en-US', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    })
  }

  const getSessionName = (session: Session): string => {
    if (session.name) return session.name

    // Generate name from session_id and date
    const shortId = session.session_id.slice(0, 8)
    const date = new Date(session.created_at).toLocaleDateString('en-US', {
      day: '2-digit',
      month: '2-digit',
    })
    return `Session ${date} (${shortId})`
  }

  const handleDeleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent session selection when clicking delete

    if (!confirm('Do you really want to delete this session?')) {
      return
    }

    try {
      await apiClient.deleteSession(sessionId)
      // Remove from local state
      setSessions(sessions.filter(s => s.session_id !== sessionId))

      // If we deleted the current session, notify parent
      if (sessionId === currentSessionId) {
        // Parent should handle creating a new session
        onSelectSession('')
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session')
    }
  }

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="medium" />
      </div>
    )
  }

  if (sessions.length === 0) {
    return (
      <div className={styles.emptyState}>
        <Text size={300}>No sessions available</Text>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <Text className={styles.header} weight="semibold" size={300}>
        Sessions
      </Text>

      {sessions.map((session) => {
        const isActive = session.session_id === currentSessionId

        return (
          <div
            key={session.session_id}
            className={styles.sessionItemWrapper}
          >
            <Button
              appearance="subtle"
              className={`${styles.sessionItem} ${
                isActive ? styles.activeSession : ''
              }`}
              onClick={() => onSelectSession(session.session_id)}
              icon={
                isActive ? <CheckmarkCircle20Regular /> : <Chat20Regular />
              }
            >
              <Text className={styles.sessionName} size={300}>
                {getSessionName(session)}
              </Text>
              <Text className={styles.sessionDate}>
                {formatDate(session.created_at)}
              </Text>
            </Button>

            <Button
              appearance="subtle"
              className={`deleteButton ${styles.deleteButton}`}
              icon={<Delete20Regular />}
              onClick={(e) => handleDeleteSession(session.session_id, e)}
              aria-label="Delete session"
            />
          </div>
        )
      })}
    </div>
  )
}
