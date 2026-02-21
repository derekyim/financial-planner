import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { APP_SHORT_NAME } from '@/constants';
import styles from './ThinkingBubble.module.css';

const ELLIPSIS_FRAMES = ['', '.', '..', '...'];

export default function ThinkingBubble({ text }: { text: string }) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setFrame((f) => (f + 1) % ELLIPSIS_FRAMES.length), 400);
    return () => clearInterval(id);
  }, []);

  return (
    <Box className={styles.wrapper}>
      <Avatar className={styles.avatar}>
        <SmartToyIcon />
      </Avatar>
      <Box className={styles.bubble}>
        <Typography variant="body2" className={styles.sender}>
          {APP_SHORT_NAME}
        </Typography>
        <Typography variant="body2" className={styles.text}>
          {text || 'Thinking'}{ELLIPSIS_FRAMES[frame]}
        </Typography>
      </Box>
    </Box>
  );
}
