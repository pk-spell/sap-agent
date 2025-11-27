/**
 * Landing Page - Modern, creative entry point for SAP Deployment Assistant
 */

import { useNavigate } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Button,
  Text,
  Card,
  Link,
  Badge,
} from '@fluentui/react-components'
import {
  Chat24Regular,
  Settings24Filled,
  CloudArrowUp24Filled,
  Checkmark24Filled,
  Sparkle24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  root: {
    minHeight: '100vh',
    background: `linear-gradient(135deg, ${tokens.colorNeutralBackground1} 0%, ${tokens.colorNeutralBackground2} 100%)`,
    display: 'flex',
    flexDirection: 'column',
  },
  hero: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '80px 32px',
  },
  heroContent: {
    maxWidth: '1200px',
    width: '100%',
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '64px',
    alignItems: 'center',
  },
  leftColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '32px',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorNeutralForegroundOnBrand,
    borderRadius: '24px',
    fontSize: '14px',
    fontWeight: 600,
    width: 'fit-content',
  },
  title: {
    fontSize: '56px',
    fontWeight: 700,
    lineHeight: '1.1',
    color: tokens.colorNeutralForeground1,
    margin: 0,
  },
  gradient: {
    background: `linear-gradient(135deg, ${tokens.colorBrandForeground1} 0%, ${tokens.colorPaletteBlueForeground2} 100%)`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  subtitle: {
    fontSize: '20px',
    lineHeight: '1.6',
    color: tokens.colorNeutralForeground2,
    margin: 0,
  },
  ctaContainer: {
    display: 'flex',
    gap: '16px',
    alignItems: 'center',
  },
  ctaButton: {
    padding: '16px 32px',
    fontSize: '16px',
    height: 'auto',
    fontWeight: 600,
  },
  rightColumn: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  },
  featureCard: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    height: '100%',
  },
  featureIconContainer: {
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
  },
  blueIcon: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
  },
  greenIcon: {
    backgroundColor: tokens.colorPaletteGreenBackground2,
    color: tokens.colorPaletteGreenForeground2,
  },
  purpleIcon: {
    backgroundColor: tokens.colorPaletteMarigoldBackground2,
    color: tokens.colorPaletteMarigoldForeground2,
  },
  orangeIcon: {
    backgroundColor: tokens.colorPaletteDarkOrangeBackground2,
    color: tokens.colorPaletteDarkOrangeForeground2,
  },
  featureTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: tokens.colorNeutralForeground1,
  },
  featureDescription: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground3,
  },
  footer: {
    padding: '32px',
    textAlign: 'center',
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  footerText: {
    fontSize: '14px',
    color: tokens.colorNeutralForeground3,
  },
  link: {
    color: tokens.colorBrandForeground1,
    textDecorationLine: 'none',
    fontWeight: 600,
  },
  templatesSection: {
    padding: '64px 32px',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  templatesContent: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  templatesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    marginTop: '32px',
  },
  templateCard: {
    padding: '24px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: tokens.shadow16,
    },
  },
  templateHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px',
  },
})

export default function LandingPage() {
  const styles = useStyles()
  const navigate = useNavigate()

  const handleStartChat = () => {
    navigate('/chat')
  }

  return (
    <div className={styles.root}>
      <div className={styles.hero}>
        <div className={styles.heroContent}>
          {/* Left Column - Main Content */}
          <div className={styles.leftColumn}>
            <div className={styles.badge}>
              <Checkmark24Filled />
              <span>AI-Powered Configuration</span>
            </div>

            <h1 className={styles.title}>
              SAP Deployment{' '}
              <span className={styles.gradient}>Assistant</span>
            </h1>

            <p className={styles.subtitle}>
              Generate production-ready Terraform configurations for SAP on Azure
              through natural language conversations. Powered by SDAF best practices.
            </p>

            <div className={styles.ctaContainer}>
              <Button
                className={styles.ctaButton}
                appearance="primary"
                icon={<Chat24Regular />}
                onClick={handleStartChat}
                size="large"
              >
                Start Chat
              </Button>
              <Link
                href="https://learn.microsoft.com/en-us/azure/sap/automation/deployment-framework"
                target="_blank"
                className={styles.link}
              >
                Learn about SDAF →
              </Link>
            </div>
          </div>

          {/* Right Column - Feature Cards */}
          <div className={styles.rightColumn}>
            <Card className={styles.featureCard}>
              <div className={`${styles.featureIconContainer} ${styles.blueIcon}`}>
                <Chat24Regular />
              </div>
              <Text className={styles.featureTitle}>Conversational Flow</Text>
              <Text className={styles.featureDescription}>
                Answer simple questions in natural language - no complex forms or technical jargon required
              </Text>
            </Card>

            <Card className={styles.featureCard}>
              <div className={`${styles.featureIconContainer} ${styles.greenIcon}`}>
                <Checkmark24Filled />
              </div>
              <Text className={styles.featureTitle}>SDAF Validated</Text>
              <Text className={styles.featureDescription}>
                All configurations follow SAP Deployment Automation Framework best practices and standards
              </Text>
            </Card>

            <Card className={styles.featureCard}>
              <div className={`${styles.featureIconContainer} ${styles.purpleIcon}`}>
                <Settings24Filled />
              </div>
              <Text className={styles.featureTitle}>180+ Parameters</Text>
              <Text className={styles.featureDescription}>
                Comprehensive configuration coverage with intelligent defaults for rapid deployment
              </Text>
            </Card>

            <Card className={styles.featureCard}>
              <div className={`${styles.featureIconContainer} ${styles.orangeIcon}`}>
                <CloudArrowUp24Filled />
              </div>
              <Text className={styles.featureTitle}>Production Ready</Text>
              <Text className={styles.featureDescription}>
                Export complete .tfvars files ready for immediate use with Terraform and Azure
              </Text>
            </Card>
          </div>
        </div>
      </div>

      {/* Quick Start Templates */}
      <div className={styles.templatesSection}>
        <div className={styles.templatesContent}>
          <div style={{ textAlign: 'center', marginBottom: '16px' }}>
            <Text size={600} weight="bold">
              Quick Start Templates
            </Text>
            <br />
            <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
              Start with a pre-configured template for common scenarios
            </Text>
          </div>

          <div className={styles.templatesGrid}>
            <Card className={styles.templateCard} onClick={handleStartChat}>
              <div className={styles.templateHeader}>
                <Sparkle24Regular style={{ color: tokens.colorPaletteBlueForeground2 }} />
                <Text size={400} weight="semibold">
                  S/4HANA Development
                </Text>
                <Badge appearance="tint" color="success">Popular</Badge>
              </div>
              <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
                Standard dev environment with demo sizing, single instance, no HA
              </Text>
            </Card>

            <Card className={styles.templateCard} onClick={handleStartChat}>
              <div className={styles.templateHeader}>
                <Settings24Filled style={{ color: tokens.colorPalettePurpleForeground2 }} />
                <Text size={400} weight="semibold">
                  Production HA Setup
                </Text>
              </div>
              <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
                High-availability production deployment with distributed architecture
              </Text>
            </Card>

            <Card className={styles.templateCard} onClick={handleStartChat}>
              <div className={styles.templateHeader}>
                <Chat24Regular style={{ color: tokens.colorPaletteGreenForeground2 }} />
                <Text size={400} weight="semibold">
                  QA Environment
                </Text>
              </div>
              <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
                Quality assurance environment with medium sizing, no HA
              </Text>
            </Card>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <Text className={styles.footerText}>
          Built for SAP on Azure deployments using the{' '}
          <Link
            href="https://learn.microsoft.com/en-us/azure/sap/automation/deployment-framework"
            target="_blank"
            className={styles.link}
          >
            SAP Deployment Automation Framework
          </Link>
        </Text>
      </footer>
    </div>
  )
}
