import { createTheme } from '@mui/material/styles';

/**
 * Official Google Color Palette Theme
 * Following the brand guidelines for consistent UI
 */
const theme = createTheme({
  palette: {
    primary: {
      main: '#4285F4', // Google Blue
      light: '#669DF6',
      dark: '#1967D2',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#5F6368', // Google Gray
      light: '#80868B',
      dark: '#3C4043',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#EA4335', // Google Red
      light: '#F28B82',
      dark: '#C5221F',
    },
    warning: {
      main: '#FBBC05', // Google Yellow
      light: '#FDD663',
      dark: '#F29900',
    },
    success: {
      main: '#34A853', // Google Green
      light: '#81C995',
      dark: '#188038',
    },
    background: {
      default: '#FFFFFF',
      paper: '#F8F9FA',
    },
    text: {
      primary: '#202124',
      secondary: '#5F6368',
    },
    divider: '#DADCE0',
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 500,
      color: '#202124',
    },
    h2: {
      fontWeight: 500,
      color: '#202124',
    },
    h3: {
      fontWeight: 500,
      color: '#202124',
    },
    body1: {
      color: '#202124',
    },
    body2: {
      color: '#5F6368',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        },
      },
    },
  },
});

export default theme;

