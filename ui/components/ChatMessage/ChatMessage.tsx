import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import styles from './ChatMessage.module.css';

type ChatMessageProps = {
  message: string;
  isUser: boolean;
  timestamp?: Date;
};

/**
 * ChatMessage Component
 * Displays a single chat message with avatar and styling
 * based on whether it's from the user or AI
 */
export default function ChatMessage({ message, isUser, timestamp }: ChatMessageProps) {
  return (
    <Box className={`${styles.chatMessage} ${isUser ? styles.chatMessageUser : styles.chatMessageAi}`}>
      <Avatar 
        className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}
      >
        {isUser ? <PersonIcon /> : <SmartToyIcon />}
      </Avatar>
      <Box className={styles.content}>
        <Typography 
          variant="body2" 
          className={`${styles.sender} ${isUser ? styles.senderUser : styles.senderAi}`}
        >
          {isUser ? 'You' : 'Mental Coach'}
        </Typography>
        <Typography 
          variant="body1" 
          className={`${styles.text} ${isUser ? styles.textUser : styles.textAi}`}
        >
          {message}
        </Typography>
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
