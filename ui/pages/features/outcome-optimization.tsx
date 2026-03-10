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

const WORKFLOW_STEPS = [
  'Parse the user\'s goal into an objective metric, target value, and time period',
  'Look up the row and column for each Business Lever and Strategic Outcome',
  'Read current values to establish the baseline',
  'Define lever ranges (typically ±25–50% of current values)',
  'Call the HyperFormula calc engine optimizer with lever ranges, objective, and constraints',
  'The engine tests 500–800 scenarios via Latin hypercube sampling in ~150ms',
  'Present the top feasible solutions ranked by objective value',
];

export default function OutcomeOptimizationPage() {
  return (
    <>
      <Head>
        <title>{`Outcome Optimization | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Outcome Optimization
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Find the best combination of Business Levers to hit your Strategic Outcome targets
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Overview
          </Typography>
          <Typography className={styles.body}>
            The Goal Seek agent acts as a financial optimizer — similar to Excel&rsquo;s Solver but
            powered by an in-memory <strong>HyperFormula calculation engine</strong>. Given a target
            Strategic Outcome (e.g., &ldquo;$1M EBITDA by Dec 2027&rdquo;) and a set of Business
            Levers to vary (e.g., CaC, Ad Spend, AoV), it tests hundreds of scenarios in under a
            second and returns ranked solutions.
          </Typography>
          <Typography className={styles.body}>
            The optimizer runs entirely in memory using a copy of the spreadsheet&rsquo;s formula
            graph — <strong>no writes are made to the live Google Sheet</strong>. Changes are only
            applied when the user explicitly asks to implement a solution.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            How It Works
          </Typography>
          <ol className={styles.list}>
            {WORKFLOW_STEPS.map((step, i) => (
              <li key={i} className={styles.listItem}>{step}</li>
            ))}
          </ol>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Performance
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Aspect</TableCell>
                  <TableCell className={styles.tableHeadCell}>Before (Sheets API)</TableCell>
                  <TableCell className={styles.tableHeadCell}>After (HyperFormula)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[
                  ['Scenarios tested', '~15 (rate-limited)', '500–800 (in-memory)'],
                  ['Time per optimization', '30–60 seconds', '100–200ms'],
                  ['API calls', '~100 per request', '2–3 (one-time load)'],
                  ['Risk to live model', 'High (writes to sheet)', 'Zero (read-only copy)'],
                ].map(([aspect, before, after]) => (
                  <TableRow key={aspect}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500 }}>{aspect}</TableCell>
                    <TableCell className={styles.tableCell}>{before}</TableCell>
                    <TableCell className={styles.tableCell}>{after}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Example Solution Output
          </Typography>
          <Typography className={styles.body} sx={{ fontStyle: 'italic', mb: 2 }}>
            &ldquo;What combinations of CaC, Ad Spend, and AoV get me to $1M EBITDA by Dec 2027?&rdquo;
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Lever</TableCell>
                  <TableCell className={styles.tableHeadCell}>Solution 1</TableCell>
                  <TableCell className={styles.tableHeadCell}>Solution 2</TableCell>
                  <TableCell className={styles.tableHeadCell}>Solution 3</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[
                  ['CaC', '$39.15 (-10%)', '$41.33 (-5%)', '$43.50 (unchanged)'],
                  ['Ad Spend', '$132K (+10%)', '$120K (unchanged)', '$108K (-10%)'],
                  ['AoV', '$79.17 (+5%)', '$75.40 (unchanged)', '$86.71 (+15%)'],
                  ['EBITDA Result', '$1.61M', '$1.12M', '$1.45M'],
                ].map(([lever, s1, s2, s3]) => (
                  <TableRow key={lever}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500 }}>{lever}</TableCell>
                    <TableCell className={styles.tableCell}>{s1}</TableCell>
                    <TableCell className={styles.tableCell}>{s2}</TableCell>
                    <TableCell className={styles.tableCell}>{s3}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Example Prompts
          </Typography>
          <ul className={styles.list}>
            <li className={styles.listItem}>
              &ldquo;What combinations of CaC, Ad Spend, and AoV get me to $1M EBITDA by Dec 2027?&rdquo;
            </li>
            <li className={styles.listItem}>
              &ldquo;How can I increase Gross Sales by 20% while keeping Cash above $500K?&rdquo;
            </li>
            <li className={styles.listItem}>
              &ldquo;Optimize for maximum EBITDA by Q4 2026&rdquo;
            </li>
            <li className={styles.listItem}>
              &ldquo;Find the best lever combination to hit $2M revenue with CaC under $40&rdquo;
            </li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
