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
import { APP_NAME } from '@/constants';
import styles from '@/styles/content.module.css';

const COMPARISON = [
  { metric: 'LLMContextRecall', before: '0.55', after: '0.60', delta: '+0.06' },
  { metric: 'LLMContextPrecision', before: '0.85', after: '0.90', delta: '+0.05' },
  { metric: 'Faithfulness', before: '0.55', after: '0.55', delta: '0.00' },
  { metric: 'FactualCorrectness', before: '1.00', after: '1.00', delta: '0.00' },
  { metric: 'ResponseRelevancy', before: '0.79', after: '0.79', delta: '0.00' },
  { metric: 'ContextEntityRecall', before: '0.37', after: '0.40', delta: '+0.03' },
  { metric: 'NoiseSensitivity', before: '0.00', after: '0.07', delta: '+0.07' },
];

export default function ImprovementsPage() {
  return (
    <>
      <Head>
        <title>{`Improvements | ${APP_NAME}`}</title>
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
            Advanced Retrieval Technique: Hybrid Search with Reciprocal Rank Fusion
          </Typography>
          <Typography className={styles.body}>
            We implement <strong>hybrid search</strong> combining dense vector retrieval (Qdrant
            cosine similarity) with <strong>BM25 sparse retrieval</strong>, fused using
            <strong> Reciprocal Rank Fusion (RRF)</strong> with three key improvements over naive
            hybrid search. The retrieval mode is controlled by the <code>ADVANCED_RETRIEVAL</code>
            environment variable, enabling A/B evaluation between baseline dense-only and the
            improved hybrid pipeline.
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>NLTK tokenization</strong> &mdash; Instead of naive whitespace splitting,
              BM25 uses regex-based tokenization with Porter stemming and English stop-word removal.
              This lets &ldquo;optimize&rdquo; and &ldquo;optimization&rdquo; match correctly
              and prevents common words from flooding BM25 scores in a domain-specific financial corpus.
            </li>
            <li className={styles.listItem}>
              <strong>BM25 score thresholding</strong> &mdash; Only BM25 candidates scoring above
              mean + 1 standard deviation are included, filtering out low-quality keyword matches
              that would otherwise dilute precision.
            </li>
            <li className={styles.listItem}>
              <strong>Asymmetric RRF (dense 1.5&times;)</strong> &mdash; Dense retrieval scores
              are weighted 1.5&times; in the RRF fusion, reflecting that semantic similarity is
              the stronger signal for this domain. BM25 supplements rather than competes.
            </li>
          </ul>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Before / After Comparison
          </Typography>
          <Typography className={styles.body}>
            RAGAS metrics comparison between baseline dense-only retrieval and improved hybrid (BM25 + Dense + RRF):
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell}>Before (Dense Only)</TableCell>
                  <TableCell className={styles.tableHeadCell}>After (Hybrid + RRF)</TableCell>
                  <TableCell className={styles.tableHeadCell}>Delta</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {COMPARISON.map((row) => {
                  const numDelta = parseFloat(row.delta);
                  const lowerIsBetter = row.metric === 'NoiseSensitivity';
                  const isPositive = lowerIsBetter ? numDelta <= 0 : numDelta >= 0;
                  const deltaColor = numDelta === 0
                    ? 'inherit'
                    : isPositive ? 'var(--GOOGLE-GREEN)' : 'var(--GOOGLE-RED, #d32f2f)';
                  return (
                    <TableRow key={row.metric}>
                      <TableCell className={styles.tableCell} sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{row.metric}</TableCell>
                      <TableCell className={styles.tableCell}>{row.before}</TableCell>
                      <TableCell className={styles.tableCell}>{row.after}</TableCell>
                      <TableCell className={styles.tableCell} sx={{ color: deltaColor, fontWeight: 500 }}>{row.delta}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Implementation Details
          </Typography>
          <Typography className={styles.body}>
            The hybrid retrieval is implemented in <code>backend/agents/rag_pipeline.py</code> and
            controlled by the <code>ADVANCED_RETRIEVAL</code> environment variable:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>BM25 index</strong> &mdash; Built over the same chunked documents during
              ingestion using <code>rank_bm25.BM25Okapi</code> with NLTK-powered tokenization
              (Porter stemmer, English stop-word removal, regex punctuation stripping).
            </li>
            <li className={styles.listItem}>
              <strong>Score-gated candidates</strong> &mdash; BM25 candidates below mean + 1&sigma;
              are filtered out. Dense retrieves 2&times;k candidates; only high-scoring BM25
              results are fused, preventing low-quality keyword matches from diluting precision.
            </li>
            <li className={styles.listItem}>
              <strong>Asymmetric RRF (k=60, dense&times;1.5)</strong> &mdash; Dense scores are
              multiplied by 1.5 in the RRF formula, giving semantic similarity the dominant weight
              while BM25 acts as a precision supplement for exact-term matches.
            </li>
            <li className={styles.listItem}>
              <strong>A/B toggle</strong> &mdash; Set <code>ADVANCED_RETRIEVAL=true</code> to
              enable improved hybrid mode, or <code>false</code> for baseline dense-only. Each
              evaluation run is registered as a unique LangSmith experiment for traceability.
            </li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
