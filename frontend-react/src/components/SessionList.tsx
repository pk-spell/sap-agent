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
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Input,
} from '@fluentui/react-components'
import { Chat20Regular, CheckmarkCircle20Regular, Delete20Regular, Warning20Regular, Share20Regular, Search20Regular, Dismiss20Regular } from '@fluentui/react-icons'
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
      '& .actionButton': {
        opacity: '1 !important',
      },
    },
  },
  actionButton: {
    position: 'absolute',
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
  shareButton: {
    right: '44px',
  },
  deleteButton: {
    right: '8px',
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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredSessions, setFilteredSessions] = useState<Session[]>([])

  useEffect(() => {
    loadSessions()
  }, [])

  // Filter sessions based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredSessions(sessions)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = sessions.filter(session => {
      const name = getSessionName(session).toLowerCase()
      const sessionId = session.session_id.toLowerCase()
      const date = formatDate(session.created_at).toLowerCase()

      return name.includes(query) || sessionId.includes(query) || date.includes(query)
    })

    setFilteredSessions(filtered)
  }, [searchQuery, sessions])

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

  const handleDeleteClick = (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent session selection when clicking delete
    setSessionToDelete(sessionId)
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return

    try {
      await apiClient.deleteSession(sessionToDelete)
      // Remove from local state
      setSessions(sessions.filter(s => s.session_id !== sessionToDelete))

      // If we deleted the current session, notify parent
      if (sessionToDelete === currentSessionId) {
        // Parent should handle creating a new session
        onSelectSession('')
      }

      // Close dialog and reset
      setDeleteDialogOpen(false)
      setSessionToDelete(null)
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session')
      setDeleteDialogOpen(false)
    }
  }

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false)
    setSessionToDelete(null)
  }

  const handleShareSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation()

    try {
      await navigator.clipboard.writeText(sessionId)
      alert(`Session ID copied to clipboard!\n\nSession ID: ${sessionId}`)
    } catch (error) {
      console.error('Share failed:', error)
      alert(`Session ID: ${sessionId}\n\nCopy this ID manually.`)
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

      {/* Search Input */}
      <div style={{ marginBottom: '12px' }}>
        <Input
          placeholder="Search sessions..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          contentBefore={<Search20Regular />}
          contentAfter={
            searchQuery && (
              <Button
                appearance="subtle"
                icon={<Dismiss20Regular />}
                size="small"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search"
              />
            )
          }
          size="small"
          style={{ width: '100%' }}
        />
        {searchQuery && (
          <Text size={200} style={{ color: tokens.colorNeutralForeground3, marginTop: '4px', display: 'block' }}>
            {filteredSessions.length} result{filteredSessions.length !== 1 ? 's' : ''}
          </Text>
        )}
      </div>

      {filteredSessions.map((session) => {
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
              className={`actionButton ${styles.actionButton} ${styles.shareButton}`}
              icon={<Share20Regular />}
              onClick={(e) => handleShareSession(session.session_id, e)}
              aria-label="Share session"
            />

            <Button
              appearance="subtle"
              className={`actionButton ${styles.actionButton} ${styles.deleteButton}`}
              icon={<Delete20Regular />}
              onClick={(e) => handleDeleteClick(session.session_id, e)}
              aria-label="Delete session"
            />
          </div>
        )
      })}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={(_, data) => setDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Delete Session?</DialogTitle>
            <DialogContent>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Warning20Regular style={{ color: tokens.colorPaletteRedForeground1, fontSize: '24px' }} />
                <div>
                  <Text>
                    Are you sure you want to delete this session?
                  </Text>
                  <br />
                  <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                    This action cannot be undone.
                  </Text>
                </div>
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={handleCancelDelete}>
                Cancel
              </Button>
              <Button appearance="primary" style={{
                backgroundColor: tokens.colorPaletteRedBackground3,
                color: 'white'
              }} onClick={handleConfirmDelete}>
                Delete
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
