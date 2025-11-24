/**
 * PreviewModal Component
 * Modal dialog for previewing and downloading TFVARS content
 * Uses Fluent UI Dialog with syntax highlighting
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  makeStyles,
  tokens,
  Spinner,
  Text,
} from '@fluentui/react-components'
import {
  Dismiss24Regular,
  Copy24Regular,
  DocumentArrowDown24Regular,
  Checkmark24Regular,
} from '@fluentui/react-icons'
import { apiClient } from '../api/client'

const useStyles = makeStyles({
  dialogSurface: {
    maxWidth: '900px',
    width: '90vw',
    maxHeight: '90vh',
  },
  codeContainer: {
    backgroundColor: tokens.colorNeutralBackground3,
    borderRadius: tokens.borderRadiusMedium,
    padding: '16px',
    overflowX: 'auto',
    fontFamily: 'monospace',
    fontSize: '13px',
    lineHeight: '1.6',
    marginTop: '16px',
    maxHeight: '60vh',
    overflowY: 'auto',
    border: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  codeContent: {
    whiteSpace: 'pre',
    margin: 0,
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '48px',
    gap: '12px',
  },
  errorContainer: {
    padding: '24px',
    color: tokens.colorPaletteRedForeground1,
    backgroundColor: tokens.colorPaletteRedBackground1,
    borderRadius: tokens.borderRadiusMedium,
    marginTop: '16px',
  },
  actions: {
    display: 'flex',
    gap: '8px',
  },
})

interface PreviewModalProps {
  sessionId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function PreviewModal({
  sessionId,
  open,
  onOpenChange,
}: PreviewModalProps) {
  const styles = useStyles()
  const [content, setContent] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (open) {
      loadContent()
    }
  }, [open, sessionId])

  const loadContent = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const tfvarsContent = await apiClient.getTfvarsContent(sessionId)
      setContent(tfvarsContent)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Fehler beim Laden der TFVARS'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = async () => {
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
    } catch (err) {
      console.error('Download failed:', err)
      setError('Download fehlgeschlagen')
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => onOpenChange(data.open)}>
      <DialogSurface className={styles.dialogSurface}>
        <DialogBody>
          <DialogTitle
            action={
              <DialogTrigger action="close">
                <Button
                  appearance="subtle"
                  aria-label="close"
                  icon={<Dismiss24Regular />}
                />
              </DialogTrigger>
            }
          >
            TFVARS Vorschau
          </DialogTitle>

          <DialogContent>
            {isLoading ? (
              <div className={styles.loadingContainer}>
                <Spinner size="large" />
                <Text>Lade TFVARS...</Text>
              </div>
            ) : error ? (
              <div className={styles.errorContainer}>
                <Text weight="semibold">Fehler:</Text>
                <Text>{error}</Text>
              </div>
            ) : (
              <>
                <Text size={300} style={{ display: 'block', marginBottom: '8px' }}>
                  Terraform-Variablendatei für Session:{' '}
                  <code>{sessionId.slice(0, 8)}</code>
                </Text>

                <div className={styles.codeContainer}>
                  <pre className={styles.codeContent}>{content}</pre>
                </div>
              </>
            )}
          </DialogContent>

          <DialogActions className={styles.actions}>
            <DialogTrigger disableButtonEnhancement>
              <Button appearance="secondary">Schließen</Button>
            </DialogTrigger>

            {!isLoading && !error && (
              <>
                <Button
                  appearance="secondary"
                  icon={copied ? <Checkmark24Regular /> : <Copy24Regular />}
                  onClick={handleCopy}
                >
                  {copied ? 'Kopiert!' : 'Kopieren'}
                </Button>

                <Button
                  appearance="primary"
                  icon={<DocumentArrowDown24Regular />}
                  onClick={handleDownload}
                >
                  Herunterladen
                </Button>
              </>
            )}
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
