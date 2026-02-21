import { useState, useEffect, useRef } from 'react';
import Drawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import CloseIcon from '@mui/icons-material/Close';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import { logStore, type LogEntry } from '@/services/logStore';
import styles from './DebugPane.module.css';

export const DEBUG_PANE_WIDTH = 420;

export default function DebugPane({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLogs(logStore.getAll());
    const unsub = logStore.subscribe(() => setLogs(logStore.getAll()));
    return unsub;
  }, []);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs, open]);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      variant="persistent"
      sx={{ '& .MuiDrawer-paper': { width: DEBUG_PANE_WIDTH, top: 64, height: 'calc(100% - 64px)' } }}
    >
      <Box className={styles.header}>
        <Typography variant="subtitle1" className={styles.title}>
          Agent Activity
        </Typography>
        <Box>
          <Tooltip title="Clear logs">
            <IconButton size="small" onClick={() => logStore.clear()}>
              <DeleteSweepIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      <Box className={styles.logContainer}>
        {logs.length === 0 && (
          <Typography variant="body2" className={styles.empty}>
            No logs yet. Send a message to see agent activity.
          </Typography>
        )}
        {logs.map((entry) => (
          <Box key={entry.id} className={styles.logEntry}>
            <Typography variant="caption" className={styles.logMeta}>
              <span className={entry.source === 'SERVER' ? styles.sourceServer : styles.sourceUi}>
                {entry.source}
              </span>
              <span className={styles.logTime}>
                {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </Typography>
            <Typography variant="body2" component="pre" className={styles.logText}>
              {entry.text}
            </Typography>
          </Box>
        ))}
        <div ref={bottomRef} />
      </Box>
    </Drawer>
  );
}
