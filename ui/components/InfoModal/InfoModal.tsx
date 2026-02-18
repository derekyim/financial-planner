import { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import IconButton from '@mui/material/IconButton';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArchitectureIcon from '@mui/icons-material/AccountTree';
import StorageIcon from '@mui/icons-material/Storage';
import WebIcon from '@mui/icons-material/Web';
import BrushIcon from '@mui/icons-material/Brush';
import styles from './InfoModal.module.css';

type InfoModalProps = {
  open: boolean;
  onClose: () => void;
};

/**
 * InfoModal Component
 * Displays information about the application's architecture,
 * backend, frontend, and design in an accordion layout
 */
export default function InfoModal({ open, onClose }: InfoModalProps) {
  const [expanded, setExpanded] = useState<string | false>(false);

  function handleAccordionChange(panel: string) {
    return (_event: React.SyntheticEvent, isExpanded: boolean) => {
      setExpanded(isExpanded ? panel : false);
    };
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      className={styles.infoModalDialog}
    >
      <DialogTitle className={styles.infoModalTitle}>
        <Typography variant="h6" component="span">
          About This Application
        </Typography>
        <IconButton
          aria-label="close"
          onClick={onClose}
          className={styles.infoModalCloseButton}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent className={styles.infoModalContent}>
        <Accordion
          expanded={expanded === 'architecture'}
          onChange={handleAccordionChange('architecture')}
          className={styles.infoModalAccordion}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            className={styles.infoModalAccordionSummary}
          >
            <ArchitectureIcon className={styles.infoModalAccordionIcon} />
            <Typography>Architecture Overview</Typography>
          </AccordionSummary>
          <AccordionDetails className={styles.infoModalAccordionDetails}>
            <Typography>
            Welcome to the Mental Coach Chat!
              Why did I choose this topic?  Welp I asked Claude and this is what he wanted to build, perhaps its telling me something..
              <br /><br />
              This application uses a modern full-stack architecture with a 
              React/Next.js frontend and a FastAPI Python backend. <br /><br />The frontend 
              communicates with the backend via REST API calls, and the backend 
              integrates with OpenAI&apos;s GPT models for AI-powered responses.

          
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion
          expanded={expanded === 'backend'}
          onChange={handleAccordionChange('backend')}
          className={styles.infoModalAccordion}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            className={styles.infoModalAccordionSummary}
          >
            <StorageIcon className={styles.infoModalAccordionIcon} />
            <Typography>Backend</Typography>
          </AccordionSummary>
          <AccordionDetails className={styles.infoModalAccordionDetails}>
            <Typography>
              The backend is built with FastAPI, a modern Python web framework. <br /><br />
              It handles chat requests, integrates with the OpenAI API, and 
              provides health check endpoints. Environment variables are used 
              for secure API key management.
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion
          expanded={expanded === 'frontend'}
          onChange={handleAccordionChange('frontend')}
          className={styles.infoModalAccordion}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            className={styles.infoModalAccordionSummary}
          >
            <WebIcon className={styles.infoModalAccordionIcon} />
            <Typography>Frontend</Typography>
          </AccordionSummary>
          <AccordionDetails className={styles.infoModalAccordionDetails}>
            <Typography>
              The frontend is built with Next.js and React 18, using Material-UI 
              for components. <br /><br />
              It features a responsive chat interface with real-time 
              message updates, loading states, and error handling.<br /><br />
              The app is structured into a pages folder and a components folder to promote re-use and organization.<br /><br />
              Each Compnent and page consists of a .tsx file and a .module.css file.<br /><br />
              There is also a services layer and a utilities layer to promote re-use.
              
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Accordion
          expanded={expanded === 'design'}
          onChange={handleAccordionChange('design')}
          className={styles.infoModalAccordion}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            className={styles.infoModalAccordionSummary}
          >
            <BrushIcon className={styles.infoModalAccordionIcon} />
            <Typography>Design</Typography>
          </AccordionSummary>
          <AccordionDetails className={styles.infoModalAccordionDetails}>
            <Typography>

              The design follows Material Design principles with a 
              clean, accessible interface. <br /><br />
              The color palette uses Google&apos;s brand 
              colors, because why not :) <br /><br />The chat interface is 
              designed to feel welcoming and supportive.
              <br/> <br />
              I haven't added any of the things you may want to see, like file uploads, thumbs up/down or additional features.
              Those come next in a future revision.

              Thanks!
              
            </Typography>
          </AccordionDetails>
        </Accordion>
      </DialogContent>
    </Dialog>
  );
}
