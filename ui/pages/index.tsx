import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import SendIcon from '@mui/icons-material/Send';
import PsychologyIcon from '@mui/icons-material/Psychology';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import ChatMessage from '@/components/ChatMessage/ChatMessage';
import InfoModal from '@/components/InfoModal/InfoModal';
import { chatService } from '@/services/chatService';
import styles from './index.module.css';

type Message = {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
};

/**
 * Home Page - Main Chat Interface
 * A supportive mental coach chat application
 */
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isApiHealthy, setIsApiHealthy] = useState<boolean | null>(null);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check API health on mount
  useEffect(() => {
    async function checkApiHealth() {
      const healthy = await chatService.checkHealth();
      setIsApiHealthy(healthy);
    }
    checkApiHealth();
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  async function handleSendMessage() {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const reply = await chatService.sendMessage(userMessage.text);
      const aiMessage: Message = {
        id: generateId(),
        text: reply,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong';
      setError(errorMessage);
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
        <title>Mental Coach Chat</title>
        <meta name="description" content="A supportive mental coach to help with stress, motivation, and confidence" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Box className={styles.container}>
        {/* Header */}
        <Paper className={styles.header} elevation={0}>
          <PsychologyIcon className={styles.headerIcon} />
          <Box className={styles.headerContent}>
            <Typography variant="h5" className={styles.headerTitle}>
              Mental Coach
            </Typography>
            <Typography variant="body2" className={styles.headerSubtitle}>
              Your supportive AI companion for stress, motivation & confidence
            </Typography>
          </Box>
          {/* {isApiHealthy === false && (
            <Alert severity="warning" className={styles.apiWarning}>
              API is offline. Please start the backend server.
            </Alert>
          )} */}
          <IconButton
            onClick={() => setIsInfoModalOpen(true)}
            className={styles.infoButton}
            aria-label="Application information"
          >
            <LightbulbIcon />
          </IconButton>
        </Paper>

        {/* Info Modal */}
        <InfoModal
          open={isInfoModalOpen}
          onClose={() => setIsInfoModalOpen(false)}
        />

        {/* Chat Messages Area */}
        <Container maxWidth="md" className={styles.messagesContainer}>
          <Box className={styles.messages}>
            {messages.length === 0 ? (
              <Box className={styles.welcome}>
                <PsychologyIcon className={styles.welcomeIcon} />
                <Typography variant="h6" className={styles.welcomeTitle}>
                  Welcome to Mental Coach
                </Typography>
                <Typography variant="body1" className={styles.welcomeText}>
                  I'm here to help you with stress, motivation, habits, and building confidence.
                  Feel free to share what's on your mind!
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
            {isLoading && (
              <Box className={styles.loading}>
                <CircularProgress size={24} />
                <Typography variant="body2">Thinking...</Typography>
              </Box>
            )}
            {error && (
              <Alert severity="error" className={styles.error}>
                {error}
              </Alert>
            )}
            <div ref={messagesEndRef} />
          </Box>
        </Container>

        {/* Input Area */}
        <Paper className={styles.inputContainer} elevation={3}>
          <Container maxWidth="md" className={styles.inputWrapper}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Type your message..."
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
