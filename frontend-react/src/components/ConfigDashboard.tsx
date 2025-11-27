/**
 * Configuration Dashboard Component
 * Shows all collected parameters in real-time for validation
 */

import {
  makeStyles,
  tokens,
  Card,
  Text,
  Badge,
  Divider,
} from '@fluentui/react-components'
import {
  Checkmark20Regular,
  Warning20Regular,
  Info20Regular,
} from '@fluentui/react-icons'

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
    marginBottom: '8px',
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  paramRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
  },
  paramLabel: {
    fontWeight: 600,
    color: tokens.colorNeutralForeground2,
    minWidth: '200px',
  },
  paramValue: {
    fontFamily: 'monospace',
    backgroundColor: tokens.colorNeutralBackground2,
    padding: '4px 8px',
    borderRadius: '4px',
    flex: 1,
    marginLeft: '16px',
  },
  emptyValue: {
    color: tokens.colorNeutralForeground4,
    fontStyle: 'italic',
  },
})

interface ConfigDashboardProps {
  userData: Record<string, any>
  tfvarsReady: boolean
}

export default function ConfigDashboard({ userData, tfvarsReady }: ConfigDashboardProps) {
  const styles = useStyles()

  const environmentParams = {
    environment: 'Environment',
    location: 'Azure Region',
    network_logical_name: 'Network Name',
  }

  const sapSystemParams = {
    sid: 'SAP SID',
    database_sid: 'Database SID',
    database_platform: 'Database Platform',
  }

  const sizingParams = {
    database_size: 'Database Size',
    app_tier_sizing_dictionary_key: 'App Tier Sizing',
    purpose: 'Purpose',
  }

  const architectureParams = {
    architecture_type: 'Deployment Type',
    ha_enabled: 'High Availability',
    application_server_count: 'App Server Count',
    database_server_count: 'DB Server Count',
    scs_server_count: 'SCS Server Count',
    web_dispatcher_count: 'Web Dispatcher Count',
  }

  const networkParams = {
    network_type: 'Network Type',
    admin_subnet: 'Admin Subnet',
    db_subnet: 'DB Subnet',
    app_subnet: 'App Subnet',
  }

  const osParams = {
    os_type: 'OS Type',
    os_publisher: 'OS Image Publisher',
    os_offer: 'OS Image Offer',
    os_sku: 'OS Image SKU',
  }

  const renderSection = (title: string, params: Record<string, string>, icon: JSX.Element) => {
    const filledCount = Object.keys(params).filter(key => userData[key]).length
    const totalCount = Object.keys(params).length
    const isComplete = filledCount === totalCount

    return (
      <Card>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>
            {icon}
            <Text size={400} weight="semibold">
              {title}
            </Text>
            <Badge
              appearance={isComplete ? 'filled' : 'outline'}
              color={isComplete ? 'success' : 'warning'}
            >
              {filledCount}/{totalCount}
            </Badge>
          </div>
          <Divider />
          {Object.entries(params).map(([key, label]) => (
            <div key={key} className={styles.paramRow}>
              <Text className={styles.paramLabel}>{label}</Text>
              <Text className={userData[key] ? styles.paramValue : `${styles.paramValue} ${styles.emptyValue}`}>
                {userData[key] || '(not set)'}
              </Text>
            </div>
          ))}
        </div>
      </Card>
    )
  }

  const totalParams = 22 // Total number of parameters we track
  const filledParams = Object.keys(userData).filter(key => userData[key]).length
  const completionPercent = Math.round((filledParams / totalParams) * 100)

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div>
          <Text size={600} weight="bold">
            Configuration Dashboard
          </Text>
          <br />
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Review and validate your SAP deployment parameters
          </Text>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ textAlign: 'right' }}>
            <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
              Completion
            </Text>
            <br />
            <Text size={500} weight="bold" style={{
              color: tfvarsReady ? tokens.colorPaletteGreenForeground1 : tokens.colorBrandForeground1
            }}>
              {completionPercent}%
            </Text>
          </div>
          {tfvarsReady && (
            <Badge
              appearance="filled"
              color="success"
              size="extra-large"
              icon={<Checkmark20Regular />}
            >
              Ready
            </Badge>
          )}
        </div>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      {renderSection('Environment', environmentParams, <Info20Regular />)}
      {renderSection('SAP System', sapSystemParams, <Info20Regular />)}
      {renderSection('Sizing', sizingParams, <Info20Regular />)}
      {renderSection('Architecture', architectureParams, <Info20Regular />)}
      {renderSection('Network', networkParams, <Warning20Regular />)}
      {renderSection('Operating System', osParams, <Info20Regular />)}
    </div>
  )
}
