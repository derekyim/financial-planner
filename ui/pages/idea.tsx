import Head from 'next/head';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Chip from '@mui/material/Chip';
import { APP_NAME, PROJECT_NAME, PROJECT_SUBTITLE } from '@/constants';
import styles from '@/styles/content.module.css';

const SUB_AGENTS = [
  'Strategic Guidance (RAG)',
  'Current Trends (Tavily)',
  'Information Recall',
  'Forecast Projection',
  'Sensitivity Analysis',
  'What-If Analysis',
  'Goal Seek Optimization',
];

export default function IdeaPage() {
  return (
    <>
      <Head>
        <title>{`Project Idea | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Project Idea
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          {PROJECT_SUBTITLE}
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            {PROJECT_NAME} &mdash; Financial Model AI Agent
          </Typography>
          <Typography className={styles.body}>
            {PROJECT_NAME} is a direct-to-consumer ecommerce brand selling powdered drink mixes
            across Shopify, Amazon, and wholesale channels. Like most emerging CPG brands, the business
            relies on a complex Google Sheets financial model to plan ad spend, forecast revenue,
            manage cash flow, and optimize for profitability.
          </Typography>
          <Typography className={styles.body}>
            The goal of this project is to build an AI-powered multi-agent system that can
            deeply analyze these financial models using natural language. Instead of manually
            tracing formulas across dozens of spreadsheet tabs, an FP&amp;A analyst can ask the
            agent questions like &ldquo;What happens to my EBITDA if I raise prices by $5 in Q3?&rdquo;
            or &ldquo;Find me three scenarios to hit 10% gross sales growth while keeping cash
            above $1M.&rdquo;
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Multi-Agent Architecture
          </Typography>
          <Typography className={styles.body}>
            The system uses a supervisor/planner agent that routes user requests to
            seven specialist sub-agents, each with a dedicated playbook:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {SUB_AGENTS.map((agent) => (
              <Chip key={agent} label={agent} variant="outlined" color="primary" className={styles.chip} />
            ))}
          </Box>
          <Typography className={styles.body}>
            Each agent has access to specific tools for reading and writing to Google Sheets,
            tracing formula chains, performing sensitivity analyses, and retrieving strategic
            business knowledge from a RAG-powered knowledge base.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Key Capabilities
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>Read and understand complex multi-tab financial models with 170+ rows</li>
            <li className={styles.listItem}>Trace formula chains to explain how any Key Result is calculated</li>
            <li className={styles.listItem}>Run goal-seek optimization using Latin hypercube sampling</li>
            <li className={styles.listItem}>Perform 1- and 2-variable sensitivity analyses</li>
            <li className={styles.listItem}>Provide strategic guidance via RAG over business knowledge base</li>
            <li className={styles.listItem}>Search current trends using Tavily web search</li>
            <li className={styles.listItem}>Maintain conversation context using 5 memory types</li>
            <li className={styles.listItem}>Log all actions to an audit trail in the spreadsheet</li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
