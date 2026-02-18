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
import Chip from '@mui/material/Chip';
import styles from '@/styles/content.module.css';

const DATA_SOURCES = [
  { category: 'Financial Glossary', description: 'Business and financial terms (SBA, Investopedia)', file: 'data/financial_glossary/' },
  { category: 'Amazon Selling', description: 'Account setup, listing optimization, FBA/FBM strategies', file: 'data/amazon_selling/' },
  { category: 'Shopify Strategy', description: 'Store optimization, apps, marketing for DTC', file: 'data/shopify_strategy/' },
  { category: 'Advertising', description: 'Meta, Google, TikTok campaign strategies and ROI optimization', file: 'data/advertising/' },
  { category: 'Operations', description: 'Warehouse optimization, shipping cost reduction, inventory', file: 'data/operations/' },
];

export default function RagDocPage() {
  return (
    <>
      <Head>
        <title>RAG Application | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          RAG Application
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 3: Data Sources, Chunking Strategy, and Retrieval Architecture
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Chunking Strategy
          </Typography>
          <Typography className={styles.body}>
            We use <strong>RecursiveCharacterTextSplitter</strong> with a chunk size of 500 characters
            and 50-character overlap. This was chosen because:
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              Business knowledge documents contain short, self-contained paragraphs and bullet points &mdash;
              500 characters captures a complete concept without splitting mid-sentence.
            </li>
            <li className={styles.listItem}>
              The 50-character overlap ensures continuity at chunk boundaries, preventing loss of
              context when a concept spans two chunks.
            </li>
            <li className={styles.listItem}>
              RecursiveCharacterTextSplitter tries paragraph, sentence, then word boundaries in order,
              producing cleaner chunks than a fixed-length splitter.
            </li>
          </ul>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            <Chip label="chunk_size=500" variant="outlined" size="small" />
            <Chip label="chunk_overlap=50" variant="outlined" size="small" />
            <Chip label="k=5 retrieval" variant="outlined" size="small" />
          </Box>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Internal Knowledge Base (RAG)
          </Typography>
          <Typography className={styles.body}>
            The internal knowledge base is a collection of curated documents organized by category.
            These are embedded using <strong>text-embedding-3-small</strong> (OpenAI, 1536 dimensions)
            and stored in a <strong>Qdrant</strong> in-memory vector store.
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Category</TableCell>
                  <TableCell className={styles.tableHeadCell}>Description</TableCell>
                  <TableCell className={styles.tableHeadCell}>Path</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {DATA_SOURCES.map((src) => (
                  <TableRow key={src.category}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500 }}>{src.category}</TableCell>
                    <TableCell className={styles.tableCell}>{src.description}</TableCell>
                    <TableCell className={styles.tableCell}><code>{src.file}</code></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            External API: Tavily Web Search
          </Typography>
          <Typography className={styles.body}>
            For questions about current market trends, competitor activity, or recent industry news,
            the system uses <strong>Tavily</strong> &mdash; a search API purpose-built for AI agents.
            Tavily returns structured, citation-ready results from the web.
          </Typography>
          <Typography className={styles.body}>
            <strong>Interaction during usage:</strong> When the supervisor routes a query to the
            Strategic Guidance or Current Trends agent, the agent first checks the internal RAG
            knowledge base for relevant context. If the question is about current events or data
            not in the knowledge base, Tavily is called to supplement with live web results.
            Both sources are combined in the agent&apos;s context window before generating a response,
            with source attribution for each piece of information.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Retrieval Pipeline
          </Typography>
          <ol className={styles.list}>
            <li className={styles.listItem}>User asks a strategic or knowledge question</li>
            <li className={styles.listItem}>Supervisor routes to the Strategic Guidance agent</li>
            <li className={styles.listItem}>Agent calls <code>retrieve_context(query, k=5)</code> on Qdrant</li>
            <li className={styles.listItem}>Top 5 chunks are injected into the system prompt as grounding context</li>
            <li className={styles.listItem}>If needed, Tavily web search provides supplementary current data</li>
            <li className={styles.listItem}>Agent generates a response citing retrieved sources</li>
          </ol>
        </Paper>
      </Box>
    </>
  );
}
