import Head from 'next/head';
import Link from 'next/link';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import StorageIcon from '@mui/icons-material/Storage';
import AssessmentIcon from '@mui/icons-material/Assessment';
import NextPlanIcon from '@mui/icons-material/NextPlan';
import styles from '@/styles/content.module.css';

const SECTIONS = [
  {
    href: '/documentation/rag',
    icon: <StorageIcon />,
    title: 'RAG Application',
    description: 'Data sources, chunking strategy, and how the internal RAG and Tavily search work together.',
  },
  {
    href: '/documentation/evals',
    icon: <AssessmentIcon />,
    title: 'Evals Approach',
    description: 'RAGAS evaluation framework, metrics used, and how we measure RAG and agent quality.',
  },
  {
    href: '/documentation/next-steps',
    icon: <NextPlanIcon />,
    title: 'Next Steps',
    description: 'Roadmap for Demo Day and future improvements to the application.',
  },
];

export default function DocumentationPage() {
  return (
    <>
      <Head>
        <title>Documentation | Dysprosium Financial Planner</title>
      </Head>
      <Box className={styles.page}>
        <Typography variant="h4" className={styles.pageTitle}>
          Documentation
        </Typography>
        <Typography variant="subtitle1" className={styles.pageSubtitle}>
          Technical documentation for the Dysprosium Financial Planner system
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
