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
import Button from '@mui/material/Button';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { APP_NAME } from '@/constants';
import styles from '@/styles/content.module.css';

const RAG_RESULTS = [
  { metric: 'LLMContextRecall', baseline: '0.55', description: 'Relevant context retrieved' },
  { metric: 'LLMContextPrecision', baseline: '0.85', description: 'Retrieved context is precise and relevant' },
  { metric: 'Faithfulness', baseline: '0.55', description: 'Response grounded in context' },
  { metric: 'FactualCorrectness', baseline: '1.00', description: 'Facts are accurate' },
  { metric: 'ResponseRelevancy', baseline: '0.79', description: 'Response addresses the question' },
  { metric: 'ContextEntityRecall', baseline: '0.37', description: 'Key entities in retrieved docs' },
  { metric: 'NoiseSensitivity', baseline: '0.00', description: 'Robustness to irrelevant context' },
];

const AGENT_RESULTS = [
  { metric: 'ToolCallAccuracy', baseline: '0.90', description: 'Correct tool + correct arguments' },
  { metric: 'AgentGoalAccuracy', baseline: '0.80', description: 'User goal achieved' },
  { metric: 'TopicAdherenceScore', baseline: '0.95', description: 'Stayed on financial topics' },
];

export default function DashboardPage() {
  return (
    <>
      <Head>
        <title>{`Evals Dashboard | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Evals Dashboard
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 5: RAGAS Evaluation Results
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            RAG Pipeline Metrics
          </Typography>
          <Typography className={styles.body}>
            Baseline evaluation over the manual test dataset using RAGAS framework with GPT-4o-mini
            as the evaluator LLM:
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell}>Score</TableCell>
                  <TableCell className={styles.tableHeadCell}>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {RAG_RESULTS.map((row) => (
                  <TableRow key={row.metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                    <TableCell className={styles.tableCell}>{row.baseline}</TableCell>
                    <TableCell className={styles.tableCell}>{row.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Agent Metrics
          </Typography>
          <Typography className={styles.body}>
            Agent-level evaluation using RAGAS multi-turn metrics over traced agent conversations:
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell}>Score</TableCell>
                  <TableCell className={styles.tableHeadCell}>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {AGENT_RESULTS.map((row) => (
                  <TableRow key={row.metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                    <TableCell className={styles.tableCell}>{row.baseline}</TableCell>
                    <TableCell className={styles.tableCell}>{row.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Conclusions
          </Typography>
          <Typography className={styles.body}>
            The baseline results on 5,087 chunks across 9 documents show perfect factual correctness
            (1.00) and strong context precision (0.85). Context recall (0.55) and faithfulness (0.55)
            reveal room for improvement &mdash; the harder multi-hop and diagnostic questions pull down
            these averages because relevant information is spread across multiple chunks. Context entity
            recall (0.37) is a weaker metric, reflecting the challenge of surfacing all domain-specific
            entities from a large corpus. Noise sensitivity is 0.00, indicating the baseline is fully
            robust against irrelevant context. Agent tool call accuracy is high (0.90), confirming the
            playbook-driven approach effectively guides tool selection.
          </Typography>
          <Typography className={styles.body}>
            The test set includes both easy definitional questions (samples 1&ndash;10) and harder
            diagnostic/multi-step questions (samples 11&ndash;20), giving a realistic picture of
            production performance. The hybrid retrieval experiment (see Improvements) tests whether
            improved BM25 with NLTK tokenization, score thresholding, and asymmetric RRF weighting
            can improve retrieval on the harder questions.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            LangSmith Traces
          </Typography>
          <Typography className={styles.body}>
            Full agent execution traces are available in LangSmith, showing every LLM call,
            tool invocation, and routing decision:
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              endIcon={<OpenInNewIcon />}
              href="https://smith.langchain.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              Open LangSmith Dashboard
            </Button>
          </Box>
        </Paper>
      </Box>
    </>
  );
}
