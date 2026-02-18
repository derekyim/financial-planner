import Head from 'next/head';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Chip from '@mui/material/Chip';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import styles from '@/styles/content.module.css';
import archStyles from './architecture.module.css';

type DiagramBoxProps = {
  label: string;
  color?: string;
  small?: boolean;
};

function DiagramBox({ label, color = 'var(--GOOGLE-BLUE)', small }: DiagramBoxProps) {
  return (
    <Box
      className={small ? archStyles.boxSmall : archStyles.box}
      sx={{ borderColor: color, color }}
    >
      <Typography variant={small ? 'caption' : 'body2'} sx={{ fontWeight: 500 }}>
        {label}
      </Typography>
    </Box>
  );
}

function Arrow() {
  return (
    <Box className={archStyles.arrow}>
      <ArrowDownwardIcon sx={{ fontSize: 20, color: 'var(--TEXT-DISABLED)' }} />
    </Box>
  );
}

export default function ArchitecturePage() {
  return (
    <>
      <Head>
        <title>Architecture | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Architecture
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 2: Infrastructure Diagram
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            System Architecture
          </Typography>
          <Typography className={styles.body}>
            The diagram below shows the full stack: the Next.js/React UI communicates via REST API
            with a FastAPI backend deployed on Vercel. The backend runs a LangGraph supervisor that
            routes to specialist agents, each with access to specific tools and knowledge sources.
          </Typography>

          <Box id="architecture-diagram" className={archStyles.diagram}>
            {/* UI Layer */}
            <Box className={archStyles.layer}>
              <Chip label="UI Layer" size="small" className={archStyles.layerLabel} />
              <DiagramBox label="Next.js / React" />
            </Box>

            <Arrow />

            {/* API Layer */}
            <Box className={archStyles.layer}>
              <Chip label="API Layer" size="small" className={archStyles.layerLabel} />
              <DiagramBox label="FastAPI on Vercel" color="var(--GOOGLE-GREEN)" />
            </Box>

            <Arrow />

            {/* Agent Orchestration */}
            <Box className={archStyles.layer}>
              <Chip label="Agent Orchestration (LangGraph)" size="small" className={archStyles.layerLabel} />
              <DiagramBox label="Supervisor / Planner" color="var(--GOOGLE-RED)" />
              <Box className={archStyles.agentRow}>
                <DiagramBox label="Recall" small />
                <DiagramBox label="Goal Seek" small />
                <DiagramBox label="Strategic" small color="var(--GOOGLE-GREEN)" />
                <DiagramBox label="What-If" small />
                <DiagramBox label="Sensitivity" small />
                <DiagramBox label="Forecast" small />
              </Box>
            </Box>

            <Arrow />

            {/* Tools + Data row */}
            <Box className={archStyles.splitRow}>
              <Box className={archStyles.layer}>
                <Chip label="Tools" size="small" className={archStyles.layerLabel} />
                <DiagramBox label="Google Sheets API" small color="var(--GOOGLE-GREEN-DARK)" />
                <DiagramBox label="Tavily Web Search" small color="var(--GOOGLE-GREEN-DARK)" />
              </Box>

              <Box className={archStyles.layer}>
                <Chip label="Data / Knowledge" size="small" className={archStyles.layerLabel} />
                <DiagramBox label="Qdrant Vector Store" small color="var(--GOOGLE-YELLOW-DARK)" />
                <DiagramBox label="OpenAI Embeddings" small color="var(--GOOGLE-YELLOW-DARK)" />
                <DiagramBox label="Knowledge Base (5 categories)" small color="var(--GOOGLE-YELLOW-DARK)" />
              </Box>

              <Box className={archStyles.layer}>
                <Chip label="Monitoring & Evals" size="small" className={archStyles.layerLabel} />
                <DiagramBox label="LangSmith" small color="var(--GOOGLE-RED-DARK)" />
                <DiagramBox label="RAGAS Framework" small color="var(--GOOGLE-RED-DARK)" />
              </Box>
            </Box>
          </Box>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Agent Flow
          </Typography>
          <Typography className={styles.body}>
            Every request follows this path:
          </Typography>
          <ol className={styles.list}>
            <li className={styles.listItem}>
              <strong>Model Documentation Reader</strong> &mdash; Reads and caches the financial model&apos;s
              documentation tab on first interaction.
            </li>
            <li className={styles.listItem}>
              <strong>Supervisor / Planner</strong> &mdash; Analyzes the user&apos;s question using structured output
              to decide which specialist agent should handle it.
            </li>
            <li className={styles.listItem}>
              <strong>Specialist Agent</strong> &mdash; Executes the appropriate playbook. Tool-using agents
              (Recall, Goal Seek) enter a tool-call loop, calling Google Sheets tools and returning results
              until the task is complete.
            </li>
            <li className={styles.listItem}>
              <strong>Response</strong> &mdash; The final agent response is returned through the API to the UI.
            </li>
          </ol>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Memory Architecture
          </Typography>
          <Typography className={styles.body}>
            The system uses five memory types for comprehensive context management:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}><strong>Short-Term Memory</strong> &mdash; Conversation history via LangGraph checkpointer (MemorySaver).</li>
            <li className={styles.listItem}><strong>Long-Term Memory</strong> &mdash; Cross-session facts stored in InMemoryStore, persisted across threads.</li>
            <li className={styles.listItem}><strong>Semantic Memory</strong> &mdash; Embedding-indexed knowledge with text-embedding-3-small for similarity search.</li>
            <li className={styles.listItem}><strong>Episodic Memory</strong> &mdash; Timestamped records of past agent interactions and outcomes.</li>
            <li className={styles.listItem}><strong>Procedural Memory</strong> &mdash; Agent playbooks and standard operating procedures for each task type.</li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
