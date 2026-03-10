import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import PersonIcon from '@mui/icons-material/Person';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { APP_SHORT_NAME } from '@/constants';
import styles from './ChatMessage.module.css';

type ChatMessageProps = {
  message: string;
  isUser: boolean;
  timestamp?: Date;
};

const PRESENTATION_URL_PATTERN = /\[PRESENTATION_URL:(https:\/\/docs\.google\.com\/presentation\/d\/[^\]]+)\]/g;

function extractPresentationUrl(text: string): { cleanText: string; url: string | null } {
  const match = PRESENTATION_URL_PATTERN.exec(text);
  PRESENTATION_URL_PATTERN.lastIndex = 0;
  if (!match) return { cleanText: text, url: null };
  const cleanText = text.replace(PRESENTATION_URL_PATTERN, '').trim();
  return { cleanText, url: match[1] };
}

/**
 * ChatMessage Component
 * Displays a single chat message with avatar and styling
 * based on whether it's from the user or AI.
 * AI messages are rendered as Markdown; user messages as plain text.
 * Detects [PRESENTATION_URL:...] markers and renders an "Open Presentation" button.
 */
export default function ChatMessage({ message, isUser, timestamp }: ChatMessageProps) {
  const { cleanText, url: presentationUrl } = isUser
    ? { cleanText: message, url: null }
    : extractPresentationUrl(message);

  return (
    <Box className={`${styles.chatMessage} ${isUser ? styles.chatMessageUser : styles.chatMessageAi}`}>
      <Avatar 
        className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}
      >
        {isUser ? <PersonIcon /> : <Box sx={{ fontFamily: "'Georgia', serif", fontWeight: 700, fontSize: 14 }}>Dy</Box>}
      </Avatar>
      <Box className={styles.content}>
        <Typography 
          variant="body2" 
          className={`${styles.sender} ${isUser ? styles.senderUser : styles.senderAi}`}
        >
          {isUser ? 'You' : APP_SHORT_NAME}
        </Typography>
        {isUser ? (
          <Typography 
            variant="body1" 
            className={`${styles.text} ${styles.textUser}`}
          >
            {cleanText}
          </Typography>
        ) : (
          <Box className={`${styles.text} ${styles.textAi} ${styles.markdown}`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{cleanText}</ReactMarkdown>
          </Box>
        )}
        {presentationUrl && (
          <Button
            variant="contained"
            startIcon={<OpenInNewIcon />}
            href={presentationUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.presentationButton}
          >
            Open Presentation
          </Button>
        )}
        {timestamp && (
          <Typography 
            variant="caption" 
            className={`${styles.timestamp} ${isUser ? styles.timestampUser : styles.timestampAi}`}
          >
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
