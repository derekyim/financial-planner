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
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ChatMessage from '@/components/ChatMessage/ChatMessage';
import { chatService } from '@/services/chatService';
import styles from './index.module.css';

type Message = {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
        <title>Dysprosium Financial Planner</title>
        <meta name="description" content="Multi-agent financial analysis powered by AI" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <Box className={styles.container}>
        <Container maxWidth="md" className={styles.messagesContainer}>
          <Box className={styles.messages}>
            {messages.length === 0 ? (
              <Box className={styles.welcome}>
                <SmartToyIcon className={styles.welcomeIcon} />
                <Typography variant="h6" className={styles.welcomeTitle}>
                  Dysprosium Financial Planner
                </Typography>
                <Typography variant="body1" className={styles.welcomeText}>
                  Ask me about your financial model. I can recall metrics, run goal-seek optimizations,
                  provide strategic guidance, and analyze business scenarios.
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

        <Paper className={styles.inputContainer} elevation={3}>
          <Container maxWidth="md" className={styles.inputWrapper}>
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
