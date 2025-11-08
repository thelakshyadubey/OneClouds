import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1C2541', // oc-navy
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#5BC0BE', // oc-teal
      contrastText: '#0B132B',
    },
    background: {
      default: '#F7FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0B132B', // oc-dark
      secondary: '#3A506B', // oc-steel
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Optional: For a consistent baseline style across browsers */}
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
