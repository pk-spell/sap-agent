import { useState, useRef, useEffect } from 'react'
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
import { Chat24Regular, Document24Regular, Copy24Regular, ArrowDownload24Regular, Info24Regular } from '@fluentui/react-icons'
import ChatWindow from './components/ChatWindow'
import SessionList from './components/SessionList'
import ConfigDashboard from './components/ConfigDashboard'
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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K: New Session
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        createNewSession()
      }
      // Ctrl+P: Preview TFVARS (if session exists)
      else if ((e.ctrlKey || e.metaKey) && e.key === 'p' && sessionId) {
        e.preventDefault()
        handlePreviewTfvars()
      }
      // Ctrl+D: Download (if TFVARS ready)
      else if ((e.ctrlKey || e.metaKey) && e.key === 'd' && sessionId && progress === 100) {
        e.preventDefault()
        handleDownloadFromPreview()
      }
      // Ctrl+I: View Config Dashboard (if session exists)
      else if ((e.ctrlKey || e.metaKey) && e.key === 'i' && sessionId) {
        e.preventDefault()
        handleOpenDashboard()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [sessionId, progress]) // Re-attach when sessionId or progress changes

  // Don't create session automatically on mount anymore
  // User must explicitly click "New Session" or start typing

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

    // Load session state and calculate progress
    try {
      const data = await apiClient.loadChat(newSessionId)

      if (data.tfvars_ready) {
        setProgress(100)
      } else if (data.current_prompt !== undefined) {
        // Calculate progress based on current_prompt (0-5 = 6 total steps)
        const totalSteps = 6
        const currentStep = data.current_prompt
        setProgress((currentStep / totalSteps) * 100)
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
  const [dashboardOpen, setDashboardOpen] = useState(false)
  const [userData, setUserData] = useState<Record<string, any>>({})
  const [tfvarsReady, setTfvarsReady] = useState(false)

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

  const handleCopyToClipboard = async () => {
    if (!previewContent) return

    try {
      await navigator.clipboard.writeText(previewContent)
      alert('TFVARS copied to clipboard!')
    } catch (error) {
      console.error('Copy failed:', error)
      alert('Failed to copy to clipboard')
    }
  }

  const handleExportAsJSON = async () => {
    if (!sessionId) return

    try {
      const jsonData = await apiClient.exportAsJSON(sessionId)
      const jsonString = JSON.stringify(jsonData, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sap-config-${sessionId.slice(0, 8)}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('JSON export failed:', error)
      alert('Failed to export as JSON')
    }
  }

  const handleOpenDashboard = async () => {
    if (!sessionId) return

    try {
      const data = await apiClient.loadChat(sessionId)
      const jsonData = await apiClient.exportAsJSON(sessionId)
      setUserData(jsonData.configuration || {})
      setTfvarsReady(data.tfvars_ready || false)
      setDashboardOpen(true)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      alert('Failed to load configuration data')
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

          {sessionId && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Button
                appearance="secondary"
                icon={<Info24Regular />}
                onClick={handleOpenDashboard}
              >
                View Config
              </Button>
              <Button
                appearance="secondary"
                icon={<ArrowDownload24Regular />}
                onClick={handleExportAsJSON}
              >
                Export JSON
              </Button>
              <Button
                appearance="secondary"
                icon={<Document24Regular />}
                onClick={handlePreviewTfvars}
              >
                Preview TFVARS
              </Button>
            </div>
          )}
        </div>

        {/* ENHANCED PROGRESS INDICATOR */}
        {progress > 0 && progress < 100 && (
          <div className={styles.progressContainer}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <Text size={300} weight="semibold">
                Configuration in Progress
              </Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                {Math.round(progress)}% Complete
              </Text>
            </div>
            <ProgressBar value={progress / 100} thickness="large" />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
              {['Environment', 'SAP System', 'Sizing', 'Architecture', 'Network', 'OS'].map((step, idx) => {
                const stepProgress = ((idx + 1) / 6) * 100
                const isCompleted = progress >= stepProgress
                const isCurrent = progress >= (idx / 6) * 100 && progress < stepProgress
                return (
                  <div key={idx} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    flex: 1,
                    opacity: isCompleted || isCurrent ? 1 : 0.4
                  }}>
                    <div style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: isCompleted ? tokens.colorPaletteGreenBackground3 : isCurrent ? tokens.colorBrandBackground : tokens.colorNeutralBackground3,
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      marginBottom: '4px'
                    }}>
                      {isCompleted ? '✓' : idx + 1}
                    </div>
                    <Text size={100} style={{
                      color: isCurrent ? tokens.colorBrandForeground1 : tokens.colorNeutralForeground3,
                      fontWeight: isCurrent ? 600 : 400,
                      textAlign: 'center'
                    }}>
                      {step}
                    </Text>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {progress === 100 && (
          <div
            className={styles.progressContainer}
            style={{ backgroundColor: tokens.colorPaletteGreenBackground2 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: tokens.colorPaletteGreenForeground1,
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                fontWeight: 'bold'
              }}>
                ✓
              </div>
              <div>
                <Text size={400} weight="semibold" style={{ color: tokens.colorPaletteGreenForeground1 }}>
                  Configuration Complete!
                </Text>
                <br />
                <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                  Your TFVARS file is ready to download
                </Text>
              </div>
            </div>
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
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                gap: '24px',
                padding: '48px',
                textAlign: 'center',
              }}
            >
              <Text size={800} weight="semibold">
                Welcome to SAP Deployment Assistant
              </Text>
              <Text size={400} style={{ maxWidth: '600px', color: tokens.colorNeutralForeground3 }}>
                I'll help you create Terraform configurations for your SAP environment on Azure using the SAP Deployment Automation Framework (SDAF).
              </Text>
              <Text size={300} style={{ maxWidth: '600px', color: tokens.colorNeutralForeground3 }}>
                Start a new chat to begin, or select an existing session from the sidebar.
              </Text>
              <Button
                appearance="primary"
                icon={<Chat24Regular />}
                onClick={createNewSession}
                disabled={creatingSessionRef.current}
                size="large"
              >
                Start New Chat
              </Button>
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
                  whiteSpace: 'pre-wrap',
                  overflow: 'auto',
                  maxHeight: '500px',
                  padding: '12px',
                  backgroundColor: tokens.colorNeutralBackground2,
                  borderRadius: '4px',
                  border: `1px solid ${tokens.colorNeutralStroke1}`,
                }}
              >
                {previewContent ? (
                  <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '12px' }}>
                    {previewContent.split('\n').map((line, idx) => (
                      <div key={idx} style={{ display: 'flex', gap: '12px' }}>
                        <span style={{
                          color: tokens.colorNeutralForeground3,
                          userSelect: 'none',
                          minWidth: '40px',
                          textAlign: 'right'
                        }}>
                          {idx + 1}
                        </span>
                        <span>{line}</span>
                      </div>
                    ))}
                  </pre>
                ) : (
                  'Loading...'
                )}
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setPreviewOpen(false)}>
                Close
              </Button>
              <Button appearance="secondary" icon={<Copy24Regular />} onClick={handleCopyToClipboard}>
                Copy to Clipboard
              </Button>
              <Button appearance="primary" icon={<Document24Regular />} onClick={handleDownloadFromPreview}>
                Download
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      {/* Configuration Dashboard Dialog */}
      <Dialog open={dashboardOpen} onOpenChange={(_, data) => setDashboardOpen(data.open)}>
        <DialogSurface style={{ maxWidth: '900px', maxHeight: '90vh' }}>
          <DialogBody>
            <DialogTitle>Configuration Dashboard</DialogTitle>
            <DialogContent style={{ overflowY: 'auto', maxHeight: '70vh' }}>
              <ConfigDashboard userData={userData} tfvarsReady={tfvarsReady} />
            </DialogContent>
            <DialogActions>
              <Button appearance="secondary" onClick={() => setDashboardOpen(false)}>
                Close
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}
