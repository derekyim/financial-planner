import { useState, useRef, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { APP_NAME, DEFAULT_MODEL, type SavedModel } from '@/constants';
import ChatMessage from '@/components/ChatMessage/ChatMessage';
import ThinkingBubble from '@/components/ThinkingBubble/ThinkingBubble';
import ModelPicker from '@/components/ModelPicker/ModelPicker';
import { chatService } from '@/services/chatService';
import { logStore } from '@/services/logStore';
import { chatSessionStore, type ChatSession } from '@/services/chatSessionStore';
import styles from './index.module.css';

type Message = {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
};

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState<SavedModel>(DEFAULT_MODEL);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessions(chatSessionStore.getAll());
    const unsub = chatSessionStore.subscribe(() => setSessions(chatSessionStore.getAll()));
    return unsub;
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinkingText]);

  const loadSession = useCallback((sessionId: string) => {
    const session = chatSessionStore.get(sessionId);
    if (session) {
      setActiveSessionId(sessionId);
      setMessages(session.messages);
    }
  }, []);

  useEffect(() => {
    function handleSelectChat(e: Event) {
      const sessionId = (e as CustomEvent<string>).detail;
      loadSession(sessionId);
    }
    function handleNewChat() {
      setActiveSessionId(null);
      setMessages([]);
      setError(null);
      setThinkingText(null);
    }
    window.addEventListener('select-chat', handleSelectChat);
    window.addEventListener('new-chat', handleNewChat);
    return () => {
      window.removeEventListener('select-chat', handleSelectChat);
      window.removeEventListener('new-chat', handleNewChat);
    };
  }, [loadSession]);

  function persistMessages(sessionId: string, msgs: Message[]) {
    const title = msgs.find((m) => m.isUser)?.text.slice(0, 60) || 'New Chat';
    chatSessionStore.save({ id: sessionId, title, messages: msgs, updatedAt: new Date() });
  }

  async function handleSendMessage() {
    if (!inputValue.trim() || isLoading) return;

    const sessionId = activeSessionId || generateId();
    if (!activeSessionId) setActiveSessionId(sessionId);

    const userMessage: Message = {
      id: generateId(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue('');
    setIsLoading(true);
    setError(null);
    setThinkingText(null);

    logStore.add('UI', `User sent: "${userMessage.text}"`);

    try {
      const reply = await chatService.sendMessageStream(
        userMessage.text,
        {
          onThinking: (text) => {
            setThinkingText(text);
            logStore.add('SERVER', `[Thinking] ${text}`);
          },
          onLog: (text) => {
            logStore.add('SERVER', text);
          },
          onError: (text) => {
            setError(text);
            logStore.add('SERVER', `[ERROR] ${text}`);
          },
        },
        sessionId,
      );

      setThinkingText(null);

      if (reply) {
        const aiMessage: Message = {
          id: generateId(),
          text: reply,
          isUser: false,
          timestamp: new Date(),
        };
        const finalMessages = [...updatedMessages, aiMessage];
        setMessages(finalMessages);
        persistMessages(sessionId, finalMessages);
        logStore.add('UI', 'Agent response received');
      }
    } catch (err) {
      setThinkingText(null);
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong';
      setError(errorMessage);
      logStore.add('UI', `Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyPress(event: React.KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }

  return (
    <>
      <Head>
        <title>{APP_NAME}</title>
        <meta name="description" content="Multi-agent financial analysis powered by AI" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <Box className={styles.container}>
        <Container maxWidth="md" className={styles.messagesContainer}>
          <Box className={styles.messages}>
            {messages.length === 0 && !thinkingText ? (
              <Box className={styles.welcome}>
                <SmartToyIcon className={styles.welcomeIcon} />
                <Typography variant="h6" className={styles.welcomeTitle}>
                  {APP_NAME}
                </Typography>
                <Typography variant="body1" className={styles.welcomeText}>
                  Ask me any finance question.  I can answer general questions, or look for industry trends.  If you upload your financial model I can recall metrics, run goal-seek optimizations,
                  provide strategic guidance, and analyze business scenarios.  I can also help you understand your financial model and the data in it.
                </Typography>
              </Box>
            ) : (
              messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message.text}
                  isUser={message.isUser}
                  timestamp={message.timestamp}
                />
              ))
            )}
            {thinkingText !== null && <ThinkingBubble text={thinkingText} />}
            {error && (
              <Alert severity="error" className={styles.error}>
                {error}
              </Alert>
            )}
            <div ref={messagesEndRef} />
          </Box>
        </Container>

        <Paper className={styles.inputContainer} elevation={3}>
          <Container maxWidth="md" className={styles.inputWrapper}>
            <ModelPicker activeModel={activeModel} onModelChange={setActiveModel} />
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Ask about your financial model..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className={styles.inputField}
              variant="outlined"
              size="medium"
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={styles.sendButton}
            >
              <SendIcon />
            </IconButton>
          </Container>
        </Paper>
      </Box>
    </>
  );
}
