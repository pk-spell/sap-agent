import { useState, useEffect, useRef } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Card,
  CardHeader,
  Text,
  ProgressBar,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
} from '@fluentui/react-components'
import { Chat24Regular, Document24Regular } from '@fluentui/react-icons'
import ChatWindow from './components/ChatWindow'
import SessionList from './components/SessionList'
import { apiClient } from './api/client'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '100vh',
    backgroundColor: tokens.colorNeutralBackground2,
  },
  sidebar: {
    width: '280px',
    borderRight: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    display: 'flex',
    flexDirection: 'column',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '16px 24px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressContainer: {
    // STICKY PROGRESS BAR! (Das war dein Problem in Streamlit!)
    position: 'sticky',
    top: 0,
    zIndex: 1000,
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    padding: '12px 24px',
  },
  content: {
    flex: 1,
    overflow: 'auto',
  },
})

export default function App() {
  const styles = useStyles()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [sessionRefreshKey, setSessionRefreshKey] = useState(0)
  const creatingSessionRef = useRef(false)

  useEffect(() => {
    // Create initial session (with guard to prevent double-creation in React Strict Mode)
    if (!creatingSessionRef.current && !sessionId) {
      createNewSession()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const createNewSession = async () => {
    // Prevent multiple simultaneous session creations using ref
    if (creatingSessionRef.current) {
      console.log('Session creation already in progress, skipping...')
      return
    }

    creatingSessionRef.current = true
    try {
      const session = await apiClient.createSession()
      setSessionId(session.session_id)
      setProgress(0)
      // Trigger SessionList refresh
      setSessionRefreshKey(prev => prev + 1)
    } catch (error) {
      console.error('Failed to create session:', error)
    } finally {
      creatingSessionRef.current = false
    }
  }

  const handleSelectSession = async (newSessionId: string) => {
    // Reset state when switching sessions
    setSessionId(newSessionId)
    setProgress(0)

    // Check if the selected session has tfvars ready
    try {
      const data = await apiClient.loadChat(newSessionId)
      if (data.tfvars_ready) {
        setProgress(100)
      }
    } catch (error) {
      console.error('Failed to load session state:', error)
    }
  }

  const handleProgress = (step: number, total: number) => {
    setProgress((step / total) * 100)
  }

  const handleTfvarsReady = () => {
    setProgress(100)
  }

  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewContent, setPreviewContent] = useState('')

  const handlePreviewTfvars = async () => {
    if (!sessionId) return

    try {
      const content = await apiClient.getTfvarsContent(sessionId)
      setPreviewContent(content)
      setPreviewOpen(true)
    } catch (error) {
      console.error('Preview failed:', error)
      alert('Failed to load preview')
    }
  }

  const handleDownloadFromPreview = async () => {
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
    }
  }

  return (
    <div className={styles.root}>
      {/* Sidebar */}
      <div className={styles.sidebar}>
        <div style={{ padding: '16px' }}>
          <Card>
            <CardHeader
              image={<Chat24Regular />}
              header={<Text weight="semibold">SAP Assistant</Text>}
              description={<Text size={200}>V3 - Lokal mit Ollama</Text>}
            />
          </Card>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <SessionList
            key={sessionRefreshKey}
            currentSessionId={sessionId}
            onSelectSession={handleSelectSession}
          />
        </div>

        <div style={{ padding: '16px' }}>
          <Button
            appearance="primary"
            icon={<Chat24Regular />}
            onClick={createNewSession}
            disabled={creatingSessionRef.current}
            style={{ width: '100%' }}
          >
            New Session
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className={styles.main}>
        {/* Header */}
        <div className={styles.header}>
          <Text size={500} weight="semibold">
            SAP Deployment Configuration
          </Text>

          {sessionId && progress > 0 && (
            <Button
              appearance="secondary"
              icon={<Document24Regular />}
              onClick={handlePreviewTfvars}
            >
              Preview TFVARS
            </Button>
          )}
        </div>

        {/* STICKY PROGRESS BAR - FUNKTIONIERT! 🎉 */}
        {progress > 0 && progress < 100 && (
          <div className={styles.progressContainer}>
            <Text size={300} style={{ marginBottom: '8px' }}>
              Progress: {Math.round(progress)}%
            </Text>
            <ProgressBar value={progress / 100} />
          </div>
        )}

        {progress === 100 && (
          <div
            className={styles.progressContainer}
            style={{ backgroundColor: tokens.colorPaletteGreenBackground2 }}
          >
            <Text size={300} weight="semibold">
              ✅ Configuration completed!
            </Text>
          </div>
        )}

        {/* Chat Window */}
        <div className={styles.content}>
          {sessionId ? (
            <ChatWindow
              key={sessionId} // Force remount when sessionId changes
              sessionId={sessionId}
              onProgress={handleProgress}
              onTfvarsReady={handleTfvarsReady}
            />
          ) : (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
              }}
            >
              <Text>Loading Session...</Text>
            </div>
          )}
        </div>
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={(_, data) => setPreviewOpen(data.open)}>
        <DialogSurface style={{ maxWidth: '800px', maxHeight: '80vh' }}>
          <DialogBody>
            <DialogTitle>TFVARS Preview</DialogTitle>
            <DialogContent>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  whiteSpace: 'pre',
                  overflow: 'auto',
                  maxHeight: '500px',
                  padding: '12px',
                  backgroundColor: tokens.colorNeutralBackground2,
                  borderRadius: '4px',
                }}
              >
                {previewContent || 'Loading...'}
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setPreviewOpen(false)}>
                Close
              </Button>
              <Button appearance="primary" icon={<Document24Regular />} onClick={handleDownloadFromPreview}>
                Download
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
