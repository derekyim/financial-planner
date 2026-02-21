import Head from 'next/head';
import Link from 'next/link';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import DashboardIcon from '@mui/icons-material/Dashboard';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { APP_NAME } from '@/constants';
import styles from '@/styles/content.module.css';

const SECTIONS = [
  {
    href: '/evals/dashboard',
    icon: <DashboardIcon />,
    title: 'Dashboard',
    description: 'RAGAS evaluation results, metrics tables, and LangSmith trace links.',
  },
  {
    href: '/evals/improvements',
    icon: <TrendingUpIcon />,
    title: 'Improvements',
    description: 'Advanced retrieval techniques and before/after performance comparisons.',
  },
];

export default function EvalsPage() {
  return (
    <>
      <Head>
        <title>{`Evals | ${APP_NAME}`}</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Evaluations
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Task 5 &amp; 6: Evaluation Results and Improvements
        </Typography>

        <Paper className={styles.card} elevation={0}>
          <List>
            {SECTIONS.map((section) => (
              <Link href={section.href} key={section.href} passHref legacyBehavior>
                <ListItemButton component="a" sx={{ borderRadius: 2, mb: 1 }}>
                  <ListItemIcon sx={{ color: 'var(--GOOGLE-BLUE)' }}>{section.icon}</ListItemIcon>
                  <ListItemText
                    primary={section.title}
                    secondary={section.description}
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItemButton>
              </Link>
            ))}
          </List>
        </Paper>
      </Box>
    </>
  );
}
