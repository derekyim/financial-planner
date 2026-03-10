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
import { APP_NAME } from '@/constants';
import styles from '@/styles/content.module.css';

const MODELS = [
  { name: 'Budget', key: 'budget' },
  { name: 'Base Case', key: 'base_case' },
  { name: 'Growth Case', key: 'growth_case' },
  { name: 'Cost Reduction', key: 'cost_reduction_case' },
  { name: 'Board Plan', key: 'board_plan' },
];

const WORKFLOW_STEPS = [
  'Read the Variance tab template from the current model to identify metric names and layout',
  'Gather 2026 values for each metric from the current model\'s operations tab',
  'Switch to the comparison model and gather the same 2026 values',
  'Switch back to the current model',
  'Write values to column E ("This Model") of the Variance tab',
  'Calculate dollar and percentage variances, and write analysis notes',
  'Log the action to the AuditLog',
];

export default function VarianceAnalysisPage() {
  return (
    <>
      <Head>
        <title>{`Variance Analysis | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Multi-Model Variance Analysis
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Compare the Budget against any production model and populate a YTD 2026 Variance Report
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Overview
          </Typography>
          <Typography className={styles.body}>
            The Variance Analysis agent compares two financial models side-by-side. Starting from the
            Budget model (or whichever model is active), it reads 2026 data from both models and
            populates the existing <strong>Variance</strong> tab with actual values, computed
            variances, and written analysis notes — producing a standard YTD Financial Variance Report.
          </Typography>
          <Typography className={styles.body}>
            The agent uses <code>switch_model</code> to temporarily read from the comparison model,
            then switches back to write results. All model URLs are looked up by name via
            the <code>get_model_url</code> tool, so users simply say
            &ldquo;run variance analysis vs Growth Case&rdquo;.
          </Typography>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Production Models
          </Typography>
          <Typography className={styles.body}>
            Five production models are pre-loaded in the UI&rsquo;s Model Picker and registered
            in the backend&rsquo;s model registry:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {MODELS.map((m) => (
              <Chip key={m.key} label={m.name} variant="outlined" className={styles.chip} />
            ))}
          </Box>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Agent Workflow
          </Typography>
          <Typography className={styles.body}>
            When the supervisor routes a variance request, the Variance agent follows these steps:
          </Typography>
          <ol className={styles.list}>
            {WORKFLOW_STEPS.map((step, i) => (
              <li key={i} className={styles.listItem}>{step}</li>
            ))}
          </ol>
        </Paper>

        <Paper className={styles.card} elevation={0}>
          <Typography variant="h6" className={styles.sectionTitle}>
            Example Output
          </Typography>
          <TableContainer className={styles.table}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell className={styles.tableHeadCell}>Metric</TableCell>
                  <TableCell className={styles.tableHeadCell}>Budget</TableCell>
                  <TableCell className={styles.tableHeadCell}>Growth Case</TableCell>
                  <TableCell className={styles.tableHeadCell}>Variance</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[
                  ['Gross Sales', '$39.9M', '$62.8M', '+$22.9M (+57%)'],
                  ['Net Revenue', '$36.1M', '$56.7M', '+$20.5M (+57%)'],
                  ['Gross Profit', '$30.3M', '$50.8M', '+$20.5M (+68%)'],
                  ['EBITDA', '-$1.2M', '$15.0M', '+$16.2M'],
                  ['Orders', '284K', '425K', '+141K (+50%)'],
                ].map(([metric, budget, growth, variance]) => (
                  <TableRow key={metric}>
                    <TableCell className={styles.tableCell} sx={{ fontWeight: 500 }}>{metric}</TableCell>
                    <TableCell className={styles.tableCell}>{budget}</TableCell>
                    <TableCell className={styles.tableCell}>{growth}</TableCell>
                    <TableCell className={styles.tableCell}>{variance}</TableCell>
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
            <li className={styles.listItem}>&ldquo;Run a variance analysis vs Growth Case&rdquo;</li>
            <li className={styles.listItem}>&ldquo;Compare budget against the Board Plan&rdquo;</li>
            <li className={styles.listItem}>&ldquo;How does the budget compare to the cost reduction case?&rdquo;</li>
            <li className={styles.listItem}>&ldquo;Fill in the Variance tab comparing to base case&rdquo;</li>
          </ul>
        </Paper>
      </Box>
    </>
  );
}
