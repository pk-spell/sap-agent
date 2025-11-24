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
} from '@fluentui/react-components'
import {
  Chat24Regular,
  Settings24Filled,
  CloudArrowUp24Filled,
  Checkmark24Filled,
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
    backgroundColor: tokens.colorPaletteBlueBorder2,
    color: tokens.colorPaletteBlueForeground2,
  },
  greenIcon: {
    backgroundColor: tokens.colorPaletteGreenBorder2,
    color: tokens.colorPaletteGreenForeground2,
  },
  purpleIcon: {
    backgroundColor: tokens.colorPalettePurpleBorder2,
    color: tokens.colorPalettePurpleForeground2,
  },
  orangeIcon: {
    backgroundColor: tokens.colorPaletteOrangeBorder2,
    color: tokens.colorPaletteOrangeForeground2,
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
})

export default function LandingPage() {
  const styles = useStyles()
  const navigate = useNavigate()

  const handleStartChat = () => {
    navigate('/chat')
  }

  return (
    <div className={styles.root}>
      <div className={styles.container}>
        <div className={styles.header}>
          <Text className={styles.title}>SAP Deployment Assistant</Text>

          <Text className={styles.subtitle}>
            AI-powered conversational tool for generating SDAF-compliant Terraform configurations
          </Text>

          <Text className={styles.description}>
            This assistant helps you create production-ready <code>.tfvars</code> files for SAP deployments on Azure
            using the SAP Deployment Automation Framework (SDAF). Simply answer a few questions in natural language,
            and we'll generate the complete Terraform variable file for you.
          </Text>

          <div className={styles.buttonContainer}>
            <Button
              className={styles.ctaButton}
              appearance="primary"
              icon={<Chat24Regular />}
              onClick={handleStartChat}
              size="large"
            >
              Start Configuration Chat
            </Button>
          </div>

          <Text className={styles.footer}>
            Learn more about{' '}
            <Link
              href="https://learn.microsoft.com/en-us/azure/sap/automation/deployment-framework"
              target="_blank"
              className={styles.link}
            >
              SAP Deployment Automation Framework (SDAF)
            </Link>
          </Text>
        </div>
      </div>
    </div>
  )
}
