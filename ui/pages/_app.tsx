import type { AppProps } from 'next/app';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from '@/theme/theme';
import Layout from '@/components/Layout/Layout';
import ProductTour from '@/components/ProductTour/ProductTour';
import '@/colors.css';
import '@/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <ProductTour />
        <Component {...pageProps} />
      </Layout>
    </ThemeProvider>
  );
}
