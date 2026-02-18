import { useState, type ReactNode } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import MenuIcon from '@mui/icons-material/Menu';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import FlagIcon from '@mui/icons-material/Flag';
import BuildIcon from '@mui/icons-material/Build';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import DescriptionIcon from '@mui/icons-material/Description';
import StorageIcon from '@mui/icons-material/Storage';
import AssessmentIcon from '@mui/icons-material/Assessment';
import NextPlanIcon from '@mui/icons-material/NextPlan';
import DashboardIcon from '@mui/icons-material/Dashboard';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import BarChartIcon from '@mui/icons-material/BarChart';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { tourEngine } from '@/services/TourEngine';
import styles from './Layout.module.css';

const DRAWER_WIDTH = 260;

type NavItem = {
  label: string;
  href?: string;
  icon: ReactNode;
  children?: { label: string; href: string; icon: ReactNode }[];
};

const NAV_ITEMS: NavItem[] = [
  { label: 'Agent', href: '/', icon: <SmartToyIcon /> },
  { label: 'Idea', href: '/idea', icon: <LightbulbIcon /> },
  { label: 'Challenge', href: '/challenge', icon: <FlagIcon /> },
  { label: 'Solution', href: '/solution', icon: <BuildIcon /> },
  { label: 'Architecture', href: '/architecture', icon: <AccountTreeIcon /> },
  {
    label: 'Documentation',
    icon: <DescriptionIcon />,
    children: [
      { label: 'RAG Application', href: '/documentation/rag', icon: <StorageIcon /> },
      { label: 'Evals Approach', href: '/documentation/evals', icon: <AssessmentIcon /> },
      { label: 'Next Steps', href: '/documentation/next-steps', icon: <NextPlanIcon /> },
    ],
  },
  {
    label: 'Evals',
    icon: <BarChartIcon />,
    children: [
      { label: 'Dashboard', href: '/evals/dashboard', icon: <DashboardIcon /> },
      { label: 'Improvements', href: '/evals/improvements', icon: <TrendingUpIcon /> },
    ],
  },
];

export default function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    Documentation: true,
    Evals: true,
  });

  function handleToggleSection(label: string) {
    setOpenSections((prev) => ({ ...prev, [label]: !prev[label] }));
  }

  function isActive(href: string) {
    return router.pathname === href;
  }

  function isChildActive(children: NavItem['children']) {
    return children?.some((child) => router.pathname === child.href) ?? false;
  }

  function tourAttr(label: string): string {
    return `nav-${label.toLowerCase().replace(/\s+/g, '-')}`;
  }

  const drawerContent = (
    <Box className={styles.drawerInner} data-tour="nav-sidebar">
      <Box className={styles.drawerHeader}>
        <SmartToyIcon className={styles.drawerLogo} />
        <Typography variant="h6" className={styles.drawerTitle}>
          Dysprosium AI
        </Typography>
      </Box>
      <Divider />
      <List component="nav" className={styles.navList}>
        {NAV_ITEMS.map((item) => {
          if (item.children) {
            const sectionOpen = openSections[item.label] ?? false;
            const childActive = isChildActive(item.children);
            return (
              <Box key={item.label} data-tour={tourAttr(item.label)}>
                <ListItemButton
                  onClick={() => handleToggleSection(item.label)}
                  className={`${styles.navItem} ${childActive ? styles.navItemParentActive : ''}`}
                >
                  <ListItemIcon className={styles.navIcon}>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                  {sectionOpen ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
                <Collapse in={sectionOpen} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {item.children.map((child) => (
                      <Link href={child.href} key={child.href} passHref legacyBehavior>
                        <ListItemButton
                          component="a"
                          className={`${styles.navItemNested} ${isActive(child.href) ? styles.navItemActive : ''}`}
                        >
                          <ListItemIcon className={styles.navIconNested}>{child.icon}</ListItemIcon>
                          <ListItemText primary={child.label} primaryTypographyProps={{ variant: 'body2' }} />
                        </ListItemButton>
                      </Link>
                    ))}
                  </List>
                </Collapse>
              </Box>
            );
          }

          return (
            <Link href={item.href!} key={item.href} passHref legacyBehavior>
              <ListItemButton
                component="a"
                data-tour={tourAttr(item.label)}
                className={`${styles.navItem} ${isActive(item.href!) ? styles.navItemActive : ''}`}
              >
                <ListItemIcon className={styles.navIcon}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            </Link>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box className={styles.root}>
      <AppBar position="fixed" className={styles.appBar} elevation={0}>
        <Toolbar>
          <IconButton
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            className={styles.menuButton}
            aria-label="toggle navigation"
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap className={styles.appTitle} sx={{ flexGrow: 1 }}>
            Dysprosium Financial Planner
          </Typography>
          <IconButton
            onClick={() => {
              tourEngine.reset('main');
              window.dispatchEvent(new CustomEvent('start-tour'));
            }}
            aria-label="Take a tour"
            sx={{ color: 'var(--TEXT-SECONDARY)' }}
          >
            <HelpOutlineIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box component="nav" className={styles.drawerContainer}>
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: DRAWER_WIDTH },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box component="main" className={styles.main} sx={{ marginLeft: { md: `${DRAWER_WIDTH}px` } }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
