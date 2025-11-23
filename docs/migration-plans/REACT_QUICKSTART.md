# React + Fluent UI Quickstart Guide
## SAP Deployment Assistant - Production Frontend

**Ziel:** React-basiertes Frontend mit Microsoft Fluent UI für Production

---

## 🚀 Quick Setup (10 Minuten)

### 1. Create React Project

```bash
cd /home/kuschi/sap-agent

# Create React app with Vite + TypeScript
npm create vite@latest frontend-react -- --template react-ts

cd frontend-react
npm install
```

### 2. Install Fluent UI v9

```bash
# Fluent UI Components
npm install @fluentui/react-components @fluentui/react-icons

# State Management & API
npm install @tanstack/react-query axios

# Routing
npm install react-router-dom

# Dev Dependencies
npm install -D @types/node
```

### 3. Project Structure

```bash
mkdir -p src/{components/{Chat,Preview,Sidebar,Common},hooks,services,types,styles}
```

**Final Structure:**
```
frontend-react/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ProgressIndicator.tsx
│   │   ├── Preview/
│   │   │   ├── TFVarsPreview.tsx
│   │   │   └── PreviewButton.tsx
│   │   ├── Sidebar/
│   │   │   ├── SessionList.tsx
│   │   │   └── SessionCard.tsx
│   │   └── Common/
│   │       ├── Header.tsx
│   │       └── Layout.tsx
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useSessions.ts
│   │   └── usePreview.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── types/
│   │   ├── chat.ts
│   │   └── session.ts
│   ├── styles/
│   │   └── theme.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 📝 Code Templates

### src/main.tsx (Entry Point)

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { FluentProvider, webLightTheme, webDarkTheme } from '@fluentui/react-components';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/global.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <FluentProvider theme={webDarkTheme}>
        <App />
      </FluentProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

### src/App.tsx (Root Component)

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Common/Layout';
import { ChatWindow } from './components/Chat/ChatWindow';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<ChatWindow />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
```

### src/components/Common/Layout.tsx

```tsx
import {
  makeStyles,
  tokens,
  Title3,
  Button,
} from '@fluentui/react-components';
import { Settings24Regular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  root: {
    display: 'grid',
    gridTemplateRows: 'auto 1fr',
    height: '100vh',
    backgroundColor: tokens.colorNeutralBackground1,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: tokens.spacingVerticalL,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  content: {
    overflow: 'hidden',
  },
});

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const styles = useStyles();

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <Title3>⚙️ SAP Deployment Assistant</Title3>
        <Button
          icon={<Settings24Regular />}
          appearance="subtle"
        >
          Settings
        </Button>
      </header>
      <main className={styles.content}>{children}</main>
    </div>
  );
};
```

### src/components/Chat/ProgressIndicator.tsx (STICKY!)

```tsx
import {
  makeStyles,
  tokens,
  ProgressBar,
  Text,
} from '@fluentui/react-components';

const useStyles = makeStyles({
  container: {
    position: 'sticky',
    top: 0,
    zIndex: 1000,
    backgroundColor: tokens.colorNeutralBackground1,
    padding: tokens.spacingVerticalM,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
  },
  text: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
});

interface ProgressIndicatorProps {
  completion: number; // 0-100
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  completion,
}) => {
  const styles = useStyles();

  if (completion === 100) return null; // Hide when complete

  return (
    <div className={styles.container}>
      <Text className={styles.text}>
        Configuration Progress: {completion}%
      </Text>
      <ProgressBar value={completion / 100} />
    </div>
  );
};
```

### src/components/Chat/ChatWindow.tsx

```tsx
import { useState } from 'react';
import {
  makeStyles,
  tokens,
  Button,
} from '@fluentui/react-components';
import { DocumentRegular } from '@fluentui/react-icons';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ProgressIndicator } from './ProgressIndicator';
import { TFVarsPreview } from '../Preview/TFVarsPreview';
import { useChat } from '../../hooks/useChat';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  header: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: tokens.spacingVerticalM,
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: tokens.spacingVerticalL,
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
  },
});

export const ChatWindow = () => {
  const styles = useStyles();
  const { messages, sendMessage, completion, isLoading } = useChat();
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Button
          icon={<DocumentRegular />}
          appearance="subtle"
          onClick={() => setShowPreview(true)}
        >
          Preview TFVARS
        </Button>
      </div>

      <ProgressIndicator completion={completion} />

      <div className={styles.messages}>
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      <ChatInput onSend={sendMessage} disabled={isLoading} />

      {showPreview && (
        <TFVarsPreview onClose={() => setShowPreview(false)} />
      )}
    </div>
  );
};
```

### src/components/Chat/ChatMessage.tsx

```tsx
import {
  makeStyles,
  tokens,
  Card,
  Text,
} from '@fluentui/react-components';
import { PersonRegular, BotRegular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  card: {
    padding: tokens.spacingVerticalM,
    display: 'flex',
    gap: tokens.spacingHorizontalM,
  },
  user: {
    backgroundColor: tokens.colorNeutralBackground3,
    borderLeft: `3px solid ${tokens.colorBrandBackground}`,
  },
  assistant: {
    backgroundColor: tokens.colorNeutralBackground2,
  },
  icon: {
    fontSize: '24px',
  },
  content: {
    flex: 1,
  },
});

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
  };
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const styles = useStyles();

  return (
    <Card
      className={`${styles.card} ${
        message.role === 'user' ? styles.user : styles.assistant
      }`}
    >
      <div className={styles.icon}>
        {message.role === 'user' ? <PersonRegular /> : <BotRegular />}
      </div>
      <div className={styles.content}>
        <Text>{message.content}</Text>
      </div>
    </Card>
  );
};
```

### src/components/Chat/ChatInput.tsx

```tsx
import { useState } from 'react';
import {
  makeStyles,
  tokens,
  Textarea,
  Button,
} from '@fluentui/react-components';
import { SendRegular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    padding: tokens.spacingVerticalL,
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  input: {
    flex: 1,
  },
});

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const styles = useStyles();
  const [value, setValue] = useState('');

  const handleSend = () => {
    if (value.trim()) {
      onSend(value);
      setValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.container}>
      <Textarea
        className={styles.input}
        placeholder="Type your answer here..."
        value={value}
        onChange={(_, data) => setValue(data.value)}
        onKeyDown={handleKeyPress}
        disabled={disabled}
        resize="vertical"
      />
      <Button
        icon={<SendRegular />}
        appearance="primary"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
      >
        Send
      </Button>
    </div>
  );
};
```

### src/components/Preview/TFVarsPreview.tsx (MODAL!)

```tsx
import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  Button,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { usePreview } from '../../hooks/usePreview';

const useStyles = makeStyles({
  code: {
    backgroundColor: tokens.colorNeutralBackground3,
    padding: tokens.spacingVerticalL,
    borderRadius: tokens.borderRadiusMedium,
    fontFamily: 'monospace',
    fontSize: tokens.fontSizeBase300,
    overflowX: 'auto',
    whiteSpace: 'pre',
  },
});

interface TFVarsPreviewProps {
  onClose: () => void;
}

export const TFVarsPreview: React.FC<TFVarsPreviewProps> = ({ onClose }) => {
  const styles = useStyles();
  const { preview, isLoading } = usePreview();

  return (
    <Dialog open onOpenChange={(_, data) => !data.open && onClose()}>
      <DialogSurface>
        <DialogTitle>TFVARS Preview</DialogTitle>
        <DialogBody>
          {isLoading ? (
            <p>Loading preview...</p>
          ) : (
            <pre className={styles.code}>{preview}</pre>
          )}
        </DialogBody>
        <DialogActions>
          <Button appearance="primary" onClick={onClose}>
            Close
          </Button>
        </DialogActions>
      </DialogSurface>
    </Dialog>
  );
};
```

### src/hooks/useChat.ts (State Management)

```tsx
import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useChat = (sessionId: string = 'default') => {
  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => api.getSession(sessionId),
    refetchInterval: 2000, // Auto-refresh every 2s
  });

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage(sessionId, message),
  });

  const sendMessage = useCallback(
    async (text: string) => {
      await sendMutation.mutateAsync(text);
    },
    [sendMutation]
  );

  return {
    messages: session?.messages ?? [],
    completion: session?.completion ?? 0,
    sendMessage,
    isLoading: sendMutation.isPending,
  };
};
```

### src/hooks/usePreview.ts

```tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const usePreview = (sessionId: string = 'default') => {
  const { data, isLoading } = useQuery({
    queryKey: ['preview', sessionId],
    queryFn: () => api.getPreview(sessionId),
  });

  return {
    preview: data?.preview ?? '',
    isLoading,
  };
};
```

### src/services/api.ts (Backend Communication)

```tsx
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Get session
  async getSession(sessionId: string) {
    const { data } = await client.get(`/sessions/${sessionId}`);
    return data;
  },

  // Send message
  async sendMessage(sessionId: string, message: string) {
    const { data } = await client.post(`/sessions/${sessionId}/chat`, {
      message,
    });
    return data;
  },

  // Get preview
  async getPreview(sessionId: string) {
    const { data } = await client.get(`/sessions/${sessionId}/preview`);
    return data;
  },

  // Create new session
  async createSession() {
    const { data } = await client.post('/sessions/new');
    return data;
  },

  // List all sessions
  async listSessions() {
    const { data } = await client.get('/sessions');
    return data.sessions;
  },
};
```

### src/types/chat.ts

```tsx
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Session {
  session_id: string;
  messages: Message[];
  completion: number;
  current_prompt: number;
  tfvars_ready: boolean;
  tfvars_content?: string;
  user_data: Record<string, any>;
}
```

### .env.local

```bash
VITE_API_URL=http://localhost:8000
```

---

## 🎨 Elex Clerics Theme (Custom)

### src/styles/theme.ts

```tsx
import { createLightTheme, createDarkTheme } from '@fluentui/react-components';

// Elex Clerics inspired colors
const elexColors = {
  primary: '#7a8591',      // Muted steel
  secondary: '#9da8b5',    // Light steel
  highlight: '#b8c5d4',    // Highlight steel
  background: '#1a1d23',   // Dark metal
  surface: '#252930',      // Surface metal
  card: '#323640',         // Card background
};

export const elexTheme = createDarkTheme({
  colorBrandBackground: elexColors.primary,
  colorBrandBackgroundHover: elexColors.secondary,
  colorBrandBackgroundPressed: elexColors.highlight,
  colorNeutralBackground1: elexColors.background,
  colorNeutralBackground2: elexColors.surface,
  colorNeutralBackground3: elexColors.card,
});
```

**Verwendung:**
```tsx
// In main.tsx
<FluentProvider theme={elexTheme}>
  <App />
</FluentProvider>
```

---

## 🚀 Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📦 Deployment (Azure Static Web Apps)

### 1. Build App

```bash
npm run build
# → Erstellt ./dist Ordner
```

### 2. Deploy to Azure

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Create Static Web App
az staticwebapp create \
  --name sdaf-assistant \
  --resource-group rg-sdaf-assistant \
  --source ./dist \
  --location westeurope \
  --branch main \
  --app-location "/frontend-react" \
  --api-location "" \
  --output-location "dist"
```

### 3. CI/CD (GitHub Actions)

```yaml
# .github/workflows/azure-static-web-app.yml
name: Azure Static Web Apps CI/CD

on:
  push:
    branches:
      - main

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build
        run: |
          cd frontend-react
          npm ci
          npm run build

      - name: Deploy
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          action: 'upload'
          app_location: '/frontend-react'
          output_location: 'dist'
```

---

## ✅ Checklist

### Initial Setup
- [ ] Create Vite project
- [ ] Install Fluent UI v9
- [ ] Setup folder structure
- [ ] Configure TypeScript

### Components
- [ ] Layout + Header
- [ ] ChatWindow
- [ ] ChatMessage (User/Assistant)
- [ ] ChatInput (Textarea + Send)
- [ ] ProgressIndicator (Sticky!)
- [ ] TFVarsPreview (Modal Dialog)

### Hooks & Services
- [ ] useChat (message management)
- [ ] usePreview (preview data)
- [ ] api.ts (backend communication)

### Styling
- [ ] Elex Clerics theme
- [ ] Responsive design
- [ ] Dark mode

### Testing
- [ ] Test with local backend (localhost:8000)
- [ ] Test progress bar (sticky!)
- [ ] Test preview modal
- [ ] Test mobile view

### Deployment
- [ ] Build production bundle
- [ ] Deploy to Azure Static Web Apps
- [ ] Setup CI/CD

---

## 🎯 Expected Result

**After following this guide:**
- ✅ React app läuft auf http://localhost:5173
- ✅ Fluent UI Components funktionieren
- ✅ Sticky Progress Bar (nicht wie Streamlit!)
- ✅ Preview Modal (echtes Popup!)
- ✅ Elex Clerics Design (muted metallics)
- ✅ TypeScript fully typed
- ✅ Production-ready

**Migration Zeit:** ~2 Wochen bei 4h/Tag

---

**Next:** Siehe `AZURE_AI_MIGRATION_PLAN.md` für Backend-Migration!
