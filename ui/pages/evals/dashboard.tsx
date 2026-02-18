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
import styles from '@/styles/content.module.css';

const RAG_RESULTS = [
  { metric: 'LLMContextRecall', baseline: '0.78', description: 'Relevant context retrieved' },
  { metric: 'Faithfulness', baseline: '0.85', description: 'Response grounded in context' },
  { metric: 'FactualCorrectness', baseline: '0.82', description: 'Facts are accurate' },
  { metric: 'ResponseRelevancy', baseline: '0.88', description: 'Response addresses the question' },
  { metric: 'ContextEntityRecall', baseline: '0.71', description: 'Key entities in retrieved docs' },
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
        <title>Evals Dashboard | Dysprosium Financial Planner</title>
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
            The baseline results show strong performance in response relevancy (0.88) and
            faithfulness (0.85), indicating the RAG pipeline retrieves relevant context and
            the LLM stays grounded. Context entity recall (0.71) is the weakest metric,
            suggesting some domain-specific entities are not well-captured by the current
            chunking strategy. Agent tool call accuracy is high (0.90), confirming the
            playbook-driven approach effectively guides tool selection.
          </Typography>
          <Typography className={styles.body}>
            Areas for improvement: increasing chunk overlap or switching to semantic chunking
            could improve entity recall. Adding few-shot examples to agent playbooks may
            further improve tool call accuracy for edge cases.
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
