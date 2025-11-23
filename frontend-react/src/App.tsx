import { useState, useEffect } from 'react'
import {
  makeStyles,
  tokens,
  Button,
  Card,
  CardHeader,
  Text,
  ProgressBar,
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
  const [tfvarsReady, setTfvarsReady] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // Create initial session
    createNewSession()
  }, [])

  const createNewSession = async () => {
    try {
      const session = await apiClient.createSession()
      setSessionId(session.session_id)
      setTfvarsReady(false)
      setProgress(0)
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handleProgress = (step: number, total: number) => {
    setProgress((step / total) * 100)
  }

  const handleTfvarsReady = () => {
    setTfvarsReady(true)
    setProgress(100)
  }

  const handleDownloadTfvars = async () => {
    if (!sessionId) return

    try {
      const blob = await apiClient.downloadTfvars(sessionId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sap_${sessionId.slice(0, 8)}.tfvars`
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
            currentSessionId={sessionId}
            onSelectSession={setSessionId}
          />
        </div>

        <div style={{ padding: '16px' }}>
          <Button
            appearance="primary"
            icon={<Chat24Regular />}
            onClick={createNewSession}
            style={{ width: '100%' }}
          >
            Neue Session
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className={styles.main}>
        {/* Header */}
        <div className={styles.header}>
          <Text size={500} weight="semibold">
            SAP Deployment Konfiguration
          </Text>

          {tfvarsReady && (
            <Button
              appearance="primary"
              icon={<Document24Regular />}
              onClick={handleDownloadTfvars}
            >
              TFVARS Herunterladen
            </Button>
          )}
        </div>

        {/* STICKY PROGRESS BAR - FUNKTIONIERT! 🎉 */}
        {progress > 0 && progress < 100 && (
          <div className={styles.progressContainer}>
            <Text size={300} style={{ marginBottom: '8px' }}>
              Fortschritt: {Math.round(progress)}%
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
              ✅ Konfiguration abgeschlossen!
            </Text>
          </div>
        )}

        {/* Chat Window */}
        <div className={styles.content}>
          {sessionId ? (
            <ChatWindow
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
              <Text>Lade Session...</Text>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
