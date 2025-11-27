import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { FluentProvider, webLightTheme, webDarkTheme, Button, tokens } from '@fluentui/react-components'
import { WeatherMoon24Regular, WeatherSunny24Regular } from '@fluentui/react-icons'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LandingPage from './pages/LandingPage'
import ChatApp from './ChatApp'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  const [isDark, setIsDark] = useState(false)
  const [fontSize, setFontSize] = useState(100) // 100 = normal, 125 = large, 150 = extra large
  const [highContrast, setHighContrast] = useState(false)

  return (
    <FluentProvider theme={isDark ? webDarkTheme : webLightTheme}>
      <QueryClientProvider client={queryClient}>
        {/* Accessibility Controls */}
        <div style={{ position: 'fixed', top: '16px', right: '16px', zIndex: 9999, display: 'flex', gap: '8px', backgroundColor: tokens.colorNeutralBackground1, padding: '8px', borderRadius: '8px', boxShadow: tokens.shadow8 }}>
          <Button
            appearance="subtle"
            icon={isDark ? <WeatherSunny24Regular /> : <WeatherMoon24Regular />}
            onClick={() => setIsDark(!isDark)}
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
          />
          <Button
            appearance="subtle"
            onClick={() => setFontSize(fontSize === 100 ? 125 : fontSize === 125 ? 150 : 100)}
            aria-label="Change font size"
            title={`Font size: ${fontSize}%`}
          >
            A{fontSize > 100 ? '+' : ''}
          </Button>
          <Button
            appearance={highContrast ? 'primary' : 'subtle'}
            onClick={() => setHighContrast(!highContrast)}
            aria-label="Toggle high contrast"
            title="Toggle high contrast mode"
          >
            HC
          </Button>
        </div>

        {/* Apply global font size and high contrast */}
        <div
          style={{
            fontSize: `${fontSize}%`,
            filter: highContrast ? 'contrast(1.2) brightness(1.1)' : 'none',
          }}
        >
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/chat" element={<ChatApp />} />
            </Routes>
          </BrowserRouter>
        </div>
      </QueryClientProvider>
    </FluentProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
