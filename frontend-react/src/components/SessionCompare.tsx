/**
 * Session Compare Component
 * Compare two sessions side-by-side
 */

import {
  makeStyles,
  tokens,
  Text,
  Badge,
  Divider,
} from '@fluentui/react-components'

const useStyles = makeStyles({
  root: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  compareGrid: {
    display: 'grid',
    gridTemplateColumns: '200px 1fr 1fr',
    gap: '12px',
    alignItems: 'center',
  },
  paramLabel: {
    fontWeight: 600,
    color: tokens.colorNeutralForeground2,
  },
  paramValue: {
    fontFamily: 'monospace',
    backgroundColor: tokens.colorNeutralBackground2,
    padding: '8px 12px',
    borderRadius: '4px',
  },
  different: {
    backgroundColor: tokens.colorPaletteYellowBackground2,
    borderLeft: `3px solid ${tokens.colorPaletteYellowBorder2}`,
  },
  same: {
    opacity: 0.7,
  },
  columnHeader: {
    fontWeight: 600,
    padding: '8px 12px',
    backgroundColor: tokens.colorBrandBackground2,
    borderRadius: '4px',
    textAlign: 'center',
  },
})

interface SessionCompareProps {
  session1Data: Record<string, any>
  session2Data: Record<string, any>
  session1Name: string
  session2Name: string
}

export default function SessionCompare({
  session1Data,
  session2Data,
  session1Name,
  session2Name,
}: SessionCompareProps) {
  const styles = useStyles()

  // Get all unique keys from both sessions
  const allKeys = Array.from(
    new Set([...Object.keys(session1Data), ...Object.keys(session2Data)])
  ).sort()

  const getDifferences = () => {
    return allKeys.filter(
      (key) => session1Data[key] !== session2Data[key]
    ).length
  }

  const renderValue = (value: any) => {
    if (value === null || value === undefined || value === '') {
      return <span style={{ color: tokens.colorNeutralForeground4, fontStyle: 'italic' }}>(not set)</span>
    }
    return String(value)
  }

  const isDifferent = (key: string) => {
    return session1Data[key] !== session2Data[key]
  }

  const differencesCount = getDifferences()
  const totalParams = allKeys.length

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div>
          <Text size={600} weight="bold">
            Configuration Comparison
          </Text>
          <br />
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Compare two session configurations side-by-side
          </Text>
        </div>
        <div style={{ textAlign: 'right' }}>
          <Badge
            appearance="filled"
            color={differencesCount === 0 ? 'success' : 'warning'}
            size="large"
          >
            {differencesCount} difference{differencesCount !== 1 ? 's' : ''}
          </Badge>
          <br />
          <Text size={200} style={{ color: tokens.colorNeutralForeground3, marginTop: '4px' }}>
            {totalParams - differencesCount} same / {totalParams} total
          </Text>
        </div>
      </div>

      <Divider />

      {/* Headers */}
      <div className={styles.compareGrid}>
        <div></div>
        <div className={styles.columnHeader}>
          <Text size={300} weight="semibold">
            {session1Name}
          </Text>
        </div>
        <div className={styles.columnHeader}>
          <Text size={300} weight="semibold">
            {session2Name}
          </Text>
        </div>
      </div>

      {/* Parameters */}
      {allKeys.map((key) => {
        const different = isDifferent(key)
        const value1 = session1Data[key]
        const value2 = session2Data[key]

        return (
          <div key={key} className={styles.compareGrid}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Text className={styles.paramLabel}>{key}</Text>
              {different && <Badge appearance="tint" color="warning" size="small">diff</Badge>}
            </div>
            <div className={`${styles.paramValue} ${different ? styles.different : styles.same}`}>
              {renderValue(value1)}
            </div>
            <div className={`${styles.paramValue} ${different ? styles.different : styles.same}`}>
              {renderValue(value2)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
