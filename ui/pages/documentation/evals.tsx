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
import styles from '@/styles/content.module.css';

const RAG_METRICS = [
  { metric: 'LLMContextRecall', description: 'Measures whether all relevant context was retrieved from the knowledge base.', range: '0.0 - 1.0' },
  { metric: 'Faithfulness', description: 'Checks if the generated response is factually grounded in the retrieved context.', range: '0.0 - 1.0' },
  { metric: 'FactualCorrectness', description: 'Validates the factual accuracy of claims made in the response.', range: '0.0 - 1.0' },
  { metric: 'ResponseRelevancy', description: 'Measures how well the response addresses the original question.', range: '0.0 - 1.0' },
  { metric: 'ContextEntityRecall', description: 'Entity-level recall: did we retrieve documents mentioning the key entities?', range: '0.0 - 1.0' },
];

const AGENT_METRICS = [
  { metric: 'ToolCallAccuracy', description: 'Evaluates if the agent called the correct tools with the correct arguments.', range: '0.0 - 1.0' },
  { metric: 'AgentGoalAccuracyWithReference', description: 'Binary metric: did the agent achieve the user\'s stated goal?', range: '0 or 1' },
  { metric: 'TopicAdherenceScore', description: 'Measures if the agent stayed on financial analysis topics throughout the conversation.', range: '0.0 - 1.0' },
];

export default function EvalsDocPage() {
  return (
    <>
      <Head>
        <title>Evals Approach | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Evals Approach
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 5: Evaluation Framework and Metrics
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Evaluation Strategy
          </Typography>
          <Typography className={styles.body}>
            We use the <strong>RAGAS</strong> (Retrieval-Augmented Generation Assessment) framework
            to evaluate both the RAG pipeline and the agent system. RAGAS provides standardized,
            LLM-powered metrics that can be run against a test dataset to produce quantitative
            quality scores.
          </Typography>
          <Typography className={styles.body}>
            The evaluation is split into two tiers: <strong>RAG metrics</strong> that assess
            retrieval and generation quality, and <strong>Agent metrics</strong> that assess
            tool usage, goal achievement, and topic adherence. Both tiers use GPT-4o-mini as the
            evaluation LLM for consistent, cost-effective scoring.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            RAG Evaluation Metrics
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '25%' }}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '60%' }}>Description</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '15%' }}>Range</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {RAG_METRICS.map((row) => (
                  <TableRow key={row.metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                    <TableCell className={styles.tableCell}>{row.description}</TableCell>
                    <TableCell className={styles.tableCell}>{row.range}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Agent Evaluation Metrics
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '30%' }}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '55%' }}>Description</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '15%' }}>Range</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {AGENT_METRICS.map((row) => (
                  <TableRow key={row.metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                    <TableCell className={styles.tableCell}>{row.description}</TableCell>
                    <TableCell className={styles.tableCell}>{row.range}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Test Dataset
          </Typography>
          <Typography className={styles.body}>
            The evaluation test set consists of two sources:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>Manual test cases</strong> (<code>backend/test_data/manual_test_cases.json</code>) &mdash;
              Hand-crafted question/answer/context triples covering all agent capabilities.
            </li>
            <li className={styles.listItem}>
              <strong>Synthetic test cases</strong> &mdash; Generated using RAGAS TestsetGenerator with
              a knowledge-graph approach over the business knowledge base documents.
            </li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
