import Head from 'next/head';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { APP_NAME, EMBEDDING_MODEL, EMBEDDING_DIMS, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K, SUPERVISOR_MODEL, AGENT_MODEL } from '@/constants';
import styles from '@/styles/content.module.css';

const TOOLING_CHOICES = [
  { component: 'LLM (Supervisor)', choice: SUPERVISOR_MODEL, reason: 'Best reasoning for complex routing decisions and structured output.' },
  { component: 'LLM (Agents)', choice: AGENT_MODEL, reason: 'Cost-effective for tool-calling agents that follow structured playbooks.' },
  { component: 'Agent Orchestration', choice: 'LangGraph', reason: 'Native support for cyclic tool-calling loops, checkpointing, and memory stores.' },
  { component: 'Tools', choice: 'Google Sheets API (gspread)', reason: 'Direct programmatic access to read/write cells, formulas, and ranges.' },
  { component: 'Embedding Model', choice: EMBEDDING_MODEL, reason: `Production OpenAI embedding model; ${EMBEDDING_DIMS} dims, good cost/quality tradeoff.` },
  { component: 'Vector Database', choice: 'Qdrant (in-memory)', reason: 'Lightweight, no infrastructure needed; easy to swap to hosted Qdrant later.' },
  { component: 'Monitoring', choice: 'LangSmith', reason: 'First-party LangGraph tracing; shows full agent execution traces and tool calls.' },
  { component: 'Evaluation', choice: 'RAGAS', reason: 'Standard framework for RAG evaluation with faithfulness, recall, and relevancy metrics.' },
  { component: 'User Interface', choice: 'Next.js + MUI', reason: 'React-based with server-side rendering; Material-UI for consistent component library.' },
  { component: 'Deployment', choice: 'Vercel', reason: 'Integrated Next.js hosting with Python serverless functions for the backend.' },
  { component: 'Web Search', choice: 'Tavily', reason: 'Purpose-built search API for AI agents; returns structured, citation-ready results.' },
];

export default function SolutionPage() {
  return (
    <>
      <Head>
        <title>{`Solution | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Proposed Solution
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 2: Solution Architecture and Tooling Choices
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Solution Overview
          </Typography>
          <Typography className={styles.body}>
            The solution is a <strong>multi-agent financial analysis system</strong> built on
            LangGraph that connects to Google Sheets financial models via API. A supervisor/planner
            agent receives natural-language queries and routes them to specialist sub-agents &mdash;
            each with a dedicated playbook, tool set, and memory context. The user interacts through
            a React/Next.js chat interface that communicates with a FastAPI backend deployed on Vercel.
          </Typography>
          <Typography className={styles.body}>
            To the user, it feels like chatting with a senior FP&amp;A analyst who has instant recall
            of every formula, can run hundreds of scenarios in seconds, and brings strategic industry
            knowledge from a curated knowledge base. The system combines <strong>Agentic RAG</strong> (retrieval-augmented
            generation over business strategy documents and Tavily web search) with <strong>tool-using agents</strong> that
            can read, write, and analyze live spreadsheet data.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Tooling Choices
          </Typography>
          <Typography className={styles.body}>
            Each choice is driven by the need for a production-grade, extensible stack
            that supports multi-agent orchestration with tool calling:
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '20%' }}>Component</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '22%' }}>Choice</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '58%' }}>Rationale</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {TOOLING_CHOICES.map((row) => (
                  <TableRow key={row.component}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500 }}>{row.component}</TableCell>
                    <TableCell className={styles.tableCell}>{row.choice}</TableCell>
                    <TableCell className={styles.tableCell}>{row.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            RAG and Agent Components
          </Typography>
          <Typography className={styles.body}>
            <strong>RAG components:</strong> The Strategic Guidance sub-agent uses a Qdrant vector store
            loaded with business knowledge documents (financial glossaries, Amazon/Shopify strategies,
            advertising playbooks, warehouse optimization guides). Documents are chunked with
            RecursiveCharacterTextSplitter ({CHUNK_SIZE} chars, {CHUNK_OVERLAP} overlap) and embedded with
            {EMBEDDING_MODEL}. On query, the top {RETRIEVAL_K} relevant chunks are retrieved and injected
            into the agent&apos;s system prompt as grounding context. An advanced hybrid retrieval mode
            (BM25 + dense with Reciprocal Rank Fusion) is available via the <code>ADVANCED_RETRIEVAL</code> flag.
          </Typography>
          <Typography className={styles.body}>
            <strong>Agent components:</strong> The supervisor routes to specialist agents (Recall, Goal Seek,
            Strategic, with Sensitivity, What-If, and Forecast planned for Demo Day) each backed by
            LangChain tools bound to the LLM. Tool-calling agents can read/write cells, trace formula
            chains, run sensitivity tables, and log to audit trails. Memory is managed across 5 types:
            short-term (conversation via LangGraph checkpointer), long-term (cross-session facts in
            InMemoryStore), semantic (embedding-indexed knowledge), episodic (timestamped past
            interactions), and procedural (agent playbooks).
          </Typography>
        </Paper>
      </Box>
    </>
  );
}
