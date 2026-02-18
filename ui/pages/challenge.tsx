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

const EVAL_PAIRS = [
  {
    input: 'What is EBITDA and how is it calculated in this model?',
    expectedOutput: 'Explains EBITDA = EBIT + Depreciation + Amortization, references M - Monthly row 194.',
  },
  {
    input: 'What are the Key Drivers for this business?',
    expectedOutput: 'Lists Orders, AoV, CaC, Orders Per Customer, Repeat Purchase Rate, Discounts %, Refunds %, Shipping Income %.',
  },
  {
    input: 'I want to increase EBITDA by 10% while keeping cash above $1M. What should I change?',
    expectedOutput: 'Runs goal-seek with 3 scenario combinations adjusting Key Drivers, returns ranked solutions.',
  },
  {
    input: 'What if I raised product prices by $5 starting in June 2025?',
    expectedOutput: 'Traces the AoV impact through Gross Sales, Net Revenue, Gross Profit, and EBITDA formulas.',
  },
  {
    input: 'How should I optimize my Amazon ad spend for a powdered drink brand?',
    expectedOutput: 'Retrieves strategic guidance from RAG knowledge base on Amazon advertising strategy.',
  },
  {
    input: 'What are the latest trends in DTC ecommerce for CPG brands?',
    expectedOutput: 'Uses Tavily to search current web sources for DTC ecommerce trends and summarizes findings.',
  },
  {
    input: 'Run a sensitivity analysis on Ad Spend vs Product Price impact on Gross Profit.',
    expectedOutput: 'Generates a 2-variable sensitivity table showing Gross Profit at different Ad Spend and Price levels.',
  },
  {
    input: 'What is my current cash position and forecast?',
    expectedOutput: 'Reads cash row from M - Monthly, returns current Actual and Forecast values.',
  },
];

export default function ChallengePage() {
  return (
    <>
      <Head>
        <title>Challenge | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          The Challenge
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 1: Defining Problem, Audience, and Scope
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Problem Statement
          </Typography>
          <Box className={styles.infoBox}>
            <Typography variant="body1" sx={{ fontWeight: 500, color: 'var(--TEXT-PRIMARY)' }}>
              Ecommerce FP&amp;A teams spend hours manually navigating complex, multi-tab financial models
              in Google Sheets to answer strategic business questions, trace formula dependencies,
              and run scenario analyses &mdash; work that is tedious, error-prone, and impossible to
              scale across multiple brands or models.
            </Typography>
          </Box>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Audience
          </Typography>
          <Typography className={styles.body}>
            The primary user is an <strong>FP&amp;A Analyst or CFO</strong> at a mid-market ecommerce
            company (typically $5M&ndash;$100M revenue) who manages financial planning across
            direct-to-consumer (Shopify), marketplace (Amazon), and wholesale channels.
          </Typography>
          <Typography className={styles.body}>
            Their job function involves building and maintaining financial models, running
            scenario analyses for board decks, forecasting cash flow, and recommending
            strategic changes to ad spend, pricing, and channel mix. The part of their job
            we are automating is the <strong>formula-chain tracing, sensitivity analysis,
            and goal-seek optimization</strong> that currently requires deep manual spreadsheet work.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Evaluation Questions (Input / Expected Output)
          </Typography>
          <Typography className={styles.body}>
            These question-answer pairs form the basis for evaluating the agent&apos;s capabilities:
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '45%' }}>User Input</TableCell>
                  <TableCell className={styles.tableHeadCell} sx={{ width: '55%' }}>Expected Output</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {EVAL_PAIRS.map((pair, idx) => (
                  <TableRow key={idx}>
                    <TableCell className={styles.tableCell}>{pair.input}</TableCell>
                    <TableCell className={styles.tableCell}>{pair.expectedOutput}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>
    </>
  );
}
