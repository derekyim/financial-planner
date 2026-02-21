import { useState, useEffect, type ReactNode } from 'react';
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
import Tooltip from '@mui/material/Tooltip';
import Badge from '@mui/material/Badge';
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
import BugReportIcon from '@mui/icons-material/BugReport';
import ChatIcon from '@mui/icons-material/Chat';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { tourEngine } from '@/services/TourEngine';
import { chatSessionStore, type ChatSession } from '@/services/chatSessionStore';
import { logStore } from '@/services/logStore';
import { APP_NAME, APP_SHORT_NAME } from '@/constants';
import DebugPane, { DEBUG_PANE_WIDTH } from '@/components/DebugPane/DebugPane';
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
    Chats: true,
  });
  const [debugOpen, setDebugOpen] = useState(false);
  const [logCount, setLogCount] = useState(0);
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  const isAgentPage = router.pathname === '/';

  useEffect(() => {
    setLogCount(logStore.getAll().length);
    const unsub = logStore.subscribe(() => {
      setLogCount(logStore.getAll().length);
    });
    return unsub;
  }, []);

  useEffect(() => {
    setSessions(chatSessionStore.getAll());
    const unsub = chatSessionStore.subscribe(() => setSessions(chatSessionStore.getAll()));
    return unsub;
  }, []);

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

  function handleSelectChat(sessionId: string) {
    if (router.pathname !== '/') {
      router.push('/');
    }
    setTimeout(() => window.dispatchEvent(new CustomEvent('select-chat', { detail: sessionId })), 50);
  }

  function handleNewChat() {
    if (router.pathname !== '/') {
      router.push('/');
    }
    setTimeout(() => window.dispatchEvent(new CustomEvent('new-chat')), 50);
  }

  function handleDeleteChat(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    chatSessionStore.remove(sessionId);
  }

  const drawerContent = (
    <Box className={styles.drawerInner} data-tour="nav-sidebar">
      <Box className={styles.drawerHeader}>
        <SmartToyIcon className={styles.drawerLogo} />
        <Typography variant="h6" className={styles.drawerTitle}>
          {APP_SHORT_NAME}
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

      <Divider sx={{ mt: 1, mb: 0.5 }} />

      {/* Chats section */}
      <Box data-tour="nav-chats">
        <ListItemButton
          onClick={() => handleToggleSection('Chats')}
          className={styles.navItem}
        >
          <ListItemIcon className={styles.navIcon}><ChatIcon /></ListItemIcon>
          <ListItemText primary="Chats" />
          <Tooltip title="New chat">
            <IconButton
              size="small"
              onClick={(e) => { e.stopPropagation(); handleNewChat(); }}
              sx={{ mr: -0.5 }}
            >
              <AddIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {openSections.Chats ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        <Collapse in={openSections.Chats ?? false} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {sessions.length === 0 && (
              <Typography variant="caption" className={styles.chatEmpty}>
                No conversations yet
              </Typography>
            )}
            {sessions.map((session) => (
              <ListItemButton
                key={session.id}
                className={styles.navItemNested}
                onClick={() => handleSelectChat(session.id)}
              >
                <ListItemText
                  primary={session.title}
                  primaryTypographyProps={{
                    variant: 'body2',
                    noWrap: true,
                    sx: { maxWidth: 160 },
                  }}
                />
                <IconButton
                  size="small"
                  onClick={(e) => handleDeleteChat(e, session.id)}
                  className={styles.chatDeleteBtn}
                >
                  <DeleteOutlineIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </ListItemButton>
            ))}
          </List>
        </Collapse>
      </Box>
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
            {APP_NAME}
          </Typography>

          {isAgentPage && (
            <Tooltip title="Agent Activity">
              <IconButton
                onClick={() => setDebugOpen((prev) => !prev)}
                aria-label="Toggle debug pane"
                sx={{ color: debugOpen ? 'var(--GOOGLE-BLUE)' : 'var(--TEXT-SECONDARY)' }}
              >
                <Badge
                  badgeContent={debugOpen ? 0 : logCount}
                  color="primary"
                  max={99}
                  sx={{ '& .MuiBadge-badge': { fontSize: '0.6rem', minWidth: 16, height: 16 } }}
                >
                  <BugReportIcon />
                </Badge>
              </IconButton>
            </Tooltip>
          )}

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

      <Box
        component="main"
        className={styles.main}
        sx={{
          marginLeft: { md: `${DRAWER_WIDTH}px` },
          marginRight: isAgentPage && debugOpen ? `${DEBUG_PANE_WIDTH}px` : 0,
          transition: 'margin-right 225ms cubic-bezier(0, 0, 0.2, 1)',
        }}
      >
        <Toolbar />
        {children}
      </Box>

      {isAgentPage && <DebugPane open={debugOpen} onClose={() => setDebugOpen(false)} />}
    </Box>
  );
}
