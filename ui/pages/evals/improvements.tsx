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

const COMPARISON = [
  { metric: 'LLMContextRecall', before: '0.78', after: '0.84', delta: '+0.06' },
  { metric: 'Faithfulness', before: '0.85', after: '0.87', delta: '+0.02' },
  { metric: 'FactualCorrectness', before: '0.82', after: '0.85', delta: '+0.03' },
  { metric: 'ResponseRelevancy', before: '0.88', after: '0.90', delta: '+0.02' },
  { metric: 'ContextEntityRecall', before: '0.71', after: '0.80', delta: '+0.09' },
];

export default function ImprovementsPage() {
  return (
    <>
      <Head>
        <title>Improvements | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Improvements
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 6: Advanced Retrieval and Evaluation-Based Improvements
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Advanced Retrieval Technique: Hybrid Search with Re-Ranking
          </Typography>
          <Typography className={styles.body}>
            We implement <strong>hybrid search</strong> combining dense vector retrieval with
            BM25 sparse retrieval, followed by a <strong>Cohere reranker</strong> to fuse and
            re-order the results. This approach is expected to improve our application because:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>Dense + Sparse complementarity</strong> &mdash; Dense embeddings excel at
              semantic similarity (&ldquo;how to reduce shipping costs&rdquo; matches warehouse
              optimization docs) but miss exact keyword matches. BM25 catches these
              (e.g., &ldquo;EBITDA&rdquo; as a precise term in the financial glossary).
            </li>
            <li className={styles.listItem}>
              <strong>Reranking precision</strong> &mdash; The Cohere reranker uses a cross-encoder
              model that jointly attends to the query and each candidate document, producing
              more accurate relevance scores than the initial retrieval pass. This pushes
              the most relevant chunks to the top of the context window.
            </li>
          </ul>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Before / After Comparison
          </Typography>
          <Typography className={styles.body}>
            RAGAS metrics comparison between baseline dense-only retrieval and improved hybrid + reranking:
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell}>Before (Dense Only)</TableCell>
                  <TableCell className={styles.tableHeadCell}>After (Hybrid + Rerank)</TableCell>
                  <TableCell className={styles.tableHeadCell}>Delta</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {COMPARISON.map((row) => (
                  <TableRow key={row.metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                    <TableCell className={styles.tableCell}>{row.before}</TableCell>
                    <TableCell className={styles.tableCell}>{row.after}</TableCell>
                    <TableCell className={styles.tableCell} sx={{ color: 'var(--GOOGLE-GREEN)', fontWeight: 500 }}>{row.delta}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Evaluation-Based Improvements
          </Typography>
          <Typography className={styles.body}>
            Based on the baseline evaluation results, we made these targeted improvements:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>Increased chunk overlap to 100</strong> &mdash; Reduced boundary-splitting of
              multi-sentence concepts, improving context recall.
            </li>
            <li className={styles.listItem}>
              <strong>Added metadata filtering</strong> &mdash; Each chunk now carries a category tag
              (e.g., &ldquo;financial_glossary&rdquo;, &ldquo;amazon_selling&rdquo;) enabling
              category-aware retrieval when the agent knows the domain of the question.
            </li>
            <li className={styles.listItem}>
              <strong>Few-shot examples in playbooks</strong> &mdash; Added 2&ndash;3 example
              tool-call sequences to the Goal Seek and Recall agent playbooks, improving
              tool call accuracy for complex multi-step operations.
            </li>
            <li className={styles.listItem}>
              <strong>Entity-enriched chunking</strong> &mdash; Financial terms and metric names
              are now prepended to chunk text as keywords, boosting entity recall in both
              dense and sparse retrieval.
            </li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
