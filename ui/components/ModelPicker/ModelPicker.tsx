import { useState, useEffect } from 'react';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import AddIcon from '@mui/icons-material/Add';
import NoteAddIcon from '@mui/icons-material/NoteAdd';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import CheckIcon from '@mui/icons-material/Check';
import TableChartIcon from '@mui/icons-material/TableChart';
import { DEFAULT_MODEL, MODELS_STORAGE_KEY, type SavedModel } from '@/constants';
import styles from './ModelPicker.module.css';

function loadSavedModels(): SavedModel[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(MODELS_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedModel[]) : [];
  } catch {
    return [];
  }
}

function persistModels(models: SavedModel[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(MODELS_STORAGE_KEY, JSON.stringify(models));
  } catch { /* storage unavailable */ }
}

type ModelPickerProps = {
  activeModel: SavedModel;
  onModelChange: (model: SavedModel) => void;
};

export default function ModelPicker({ activeModel, onModelChange }: ModelPickerProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [savedModels, setSavedModels] = useState<SavedModel[]>([]);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);
  const [newModelName, setNewModelName] = useState('');
  const [newModelUrl, setNewModelUrl] = useState('');

  useEffect(() => {
    setSavedModels(loadSavedModels());
  }, []);

  const menuOpen = Boolean(anchorEl);

  function handleMenuOpen(event: React.MouseEvent<HTMLElement>) {
    setAnchorEl(event.currentTarget);
  }

  function handleMenuClose() {
    setAnchorEl(null);
  }

  function handleAddNewClick() {
    handleMenuClose();
    setNewModelName('');
    setNewModelUrl('');
    setAddDialogOpen(true);
  }

  function handleLoadExistingClick() {
    handleMenuClose();
    setLoadDialogOpen(true);
  }

  function handleAddModelSubmit() {
    const url = newModelUrl.trim();
    if (!url) return;

    const name = newModelName.trim() || extractNameFromUrl(url);
    const model: SavedModel = { name, url };

    const exists = savedModels.some((m) => m.url === url);
    let updated: SavedModel[];
    if (exists) {
      updated = savedModels.map((m) => (m.url === url ? model : m));
    } else {
      updated = [...savedModels, model];
    }

    setSavedModels(updated);
    persistModels(updated);
    onModelChange(model);
    setAddDialogOpen(false);
  }

  function handleSelectModel(model: SavedModel) {
    onModelChange(model);
    setLoadDialogOpen(false);
  }

  function extractNameFromUrl(url: string): string {
    try {
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      return match ? `Sheet ${match[1].slice(0, 8)}…` : 'Untitled Model';
    } catch {
      return 'Untitled Model';
    }
  }

  const allModels: SavedModel[] = [DEFAULT_MODEL, ...savedModels.filter((m) => m.url !== DEFAULT_MODEL.url)];
  const isDefault = activeModel.url === DEFAULT_MODEL.url;

  return (
    <>
      <Box className={styles.wrapper}>
        <IconButton
          onClick={handleMenuOpen}
          className={styles.plusButton}
          aria-label="Model options"
          size="medium"
        >
          <AddIcon />
        </IconButton>

        <Chip
          icon={<TableChartIcon />}
          label={activeModel.name}
          size="small"
          variant="outlined"
          className={styles.activeChip}
          {...(!isDefault && { onDelete: () => onModelChange(DEFAULT_MODEL) })}
        />
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        slotProps={{ paper: { className: styles.menuPaper } }}
      >
        <MenuItem onClick={handleAddNewClick} className={styles.menuItem}>
          <ListItemIcon><NoteAddIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Add New Model</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLoadExistingClick} className={styles.menuItem}>
          <ListItemIcon><FolderOpenIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Load Existing Model</ListItemText>
        </MenuItem>
      </Menu>

      {/* Add New Model Dialog */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ className: styles.dialogPaper }}
      >
        <DialogTitle>Add New Model</DialogTitle>
        <DialogContent className={styles.dialogContent}>
          <TextField
            label="Model name (optional)"
            fullWidth
            variant="outlined"
            size="small"
            value={newModelName}
            onChange={(e) => setNewModelName(e.target.value)}
            placeholder="My Financial Model"
            className={styles.dialogField}
          />
          <TextField
            label="Model URL"
            fullWidth
            variant="outlined"
            size="small"
            value={newModelUrl}
            onChange={(e) => setNewModelUrl(e.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/..."
            required
            className={styles.dialogField}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddModelSubmit}
            variant="contained"
            disabled={!newModelUrl.trim()}
          >
            Add &amp; Load
          </Button>
        </DialogActions>
      </Dialog>

      {/* Load Existing Model Dialog */}
      <Dialog
        open={loadDialogOpen}
        onClose={() => setLoadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ className: styles.dialogPaper }}
      >
        <DialogTitle>Load Existing Model</DialogTitle>
        <DialogContent className={styles.dialogContent}>
          {allModels.map((model, idx) => (
            <Box key={model.url}>
              {idx > 0 && <Divider className={styles.modelDivider} />}
              <Box
                className={`${styles.modelRow} ${model.url === activeModel.url ? styles.modelRowActive : ''}`}
                onClick={() => handleSelectModel(model)}
              >
                <Box className={styles.modelInfo}>
                  <Typography variant="body1" className={styles.modelName}>
                    {model.name}
                    {model.url === DEFAULT_MODEL.url && (
                      <Chip label="default" size="small" className={styles.defaultBadge} />
                    )}
                  </Typography>
                  <Typography variant="caption" className={styles.modelUrl} noWrap>
                    {model.url}
                  </Typography>
                </Box>
                {model.url === activeModel.url && (
                  <CheckIcon className={styles.checkIcon} />
                )}
              </Box>
            </Box>
          ))}

          {allModels.length === 1 && (
            <Typography variant="body2" className={styles.emptyHint}>
              No custom models yet. Use &ldquo;Add New Model&rdquo; to add one.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoadDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
