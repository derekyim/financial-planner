import Head from 'next/head';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import styles from '@/styles/content.module.css';

export default function NextStepsPage() {
  return (
    <>
      <Head>
        <title>Next Steps | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Next Steps
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 7: Roadmap to Demo Day
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Keeping Dense Vector Retrieval?
          </Typography>
          <Typography className={styles.body}>
            <strong>Yes, with enhancements.</strong> The current dense vector retrieval with
            text-embedding-3-small and Qdrant provides a strong baseline for our business knowledge
            use case. The documents are domain-specific and well-structured, so dense embeddings
            capture semantic similarity effectively. However, for Demo Day we plan to add a
            hybrid retrieval layer that combines dense vectors with BM25 sparse retrieval to handle
            exact-match queries (e.g., specific financial terms, product names) that pure semantic
            search can miss.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Demo Day Roadmap
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              <strong>Hybrid Retrieval</strong> &mdash; Add BM25 sparse retrieval alongside dense vectors
              using Qdrant&apos;s built-in hybrid search. This will improve recall for exact-match
              queries and financial terminology lookups.
            </li>
            <li className={styles.listItem}>
              <strong>Persistent Vector Store</strong> &mdash; Move from in-memory Qdrant to hosted Qdrant Cloud
              for persistence across deployments and larger knowledge bases.
            </li>
            <li className={styles.listItem}>
              <strong>All 7 Sub-Agents</strong> &mdash; Complete implementation of Sensitivity Analysis,
              What-If, and Forecast Projection agents with full playbooks and tool sets.
            </li>
            <li className={styles.listItem}>
              <strong>Streaming Responses</strong> &mdash; Wire up the <code>chat_stream</code> function
              to deliver token-by-token responses in the UI for a more responsive experience.
            </li>
            <li className={styles.listItem}>
              <strong>Multi-Model Support</strong> &mdash; Allow connecting multiple Google Sheets
              financial models simultaneously for cross-brand analysis.
            </li>
            <li className={styles.listItem}>
              <strong>Expanded Knowledge Base</strong> &mdash; Ingest additional domain documents including
              TikTok Shop guides, retail expansion playbooks, and CPG-specific financial benchmarks.
            </li>
            <li className={styles.listItem}>
              <strong>Evaluation CI Pipeline</strong> &mdash; Integrate RAGAS evaluations into CI/CD so every
              code change is automatically tested against the golden dataset.
            </li>
            <li className={styles.listItem}>
              <strong>User Authentication</strong> &mdash; Add user accounts with per-user memory and
              conversation history persistence.
            </li>
          </ul>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Architecture Evolution
          </Typography>
          <Typography className={styles.body}>
            The current architecture is designed to be modular. Each sub-agent is a self-contained
            node in the LangGraph with its own tools, playbook, and memory access. Adding new agents
            requires only: (1) defining the playbook prompt, (2) binding the tools, (3) adding the node
            and edges to the graph, and (4) updating the supervisor&apos;s routing logic.
          </Typography>
          <Typography className={styles.body}>
            For Demo Day, the biggest structural change will be moving from Vercel serverless
            functions (which have execution time limits) to a dedicated backend service for
            long-running goal-seek optimizations that may take 30+ seconds.
          </Typography>
        </Paper>
      </Box>
    </>
  );
}
