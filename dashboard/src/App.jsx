import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';

import NodeStatusCard from './components/NodeStatusCard';
import KeyValueForm from './components/KeyValueForm';
import KeyDistributionChart from './components/KeyDistributionChart';
import './App.css';

const NODES = [
  { id: 'node_1', port: 8000 },
  { id: 'node_2', port: 8001 },
  { id: 'node_3', port: 8002 }
];

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#0a1929',
      paper: '#1e2a3a',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const StyledHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(4),
  background: 'linear-gradient(45deg, #1e3c72 30%, #2a5298 90%)',
  color: theme.palette.common.white,
  marginBottom: theme.spacing(4),
}));

function App() {
  const [nodeStatuses, setNodeStatuses] = useState({});
  const [selectedNode, setSelectedNode] = useState(NODES[0]);

  const fetchNodeStatuses = async () => {
    const statuses = {};
    for (const node of NODES) {
      try {
        const response = await fetch(`http://localhost:${node.port}/status`);
        const data = await response.json();
        statuses[node.id] = data;
      } catch (error) {
        statuses[node.id] = { status: 'unhealthy', error: error.message };
      }
    }
    setNodeStatuses(statuses);
  };

  useEffect(() => {
    fetchNodeStatuses();
    const interval = setInterval(fetchNodeStatuses, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
        <StyledHeader>
          <Container maxWidth="lg">
            <Typography variant="h1" component="h1">
              Distributed Key-Value Store
            </Typography>
          </Container>
        </StyledHeader>

        <Container maxWidth="lg">
          <Grid container spacing={3}>
            {NODES.map(node => (
              <Grid item xs={12} md={4} key={node.id}>
                <NodeStatusCard
                  node={node}
                  status={nodeStatuses[node.id]}
                  isSelected={selectedNode.id === node.id}
                  onSelect={() => setSelectedNode(node)}
                />
              </Grid>
            ))}
          </Grid>

          <Grid container spacing={3} sx={{ mt: 3 }}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <KeyValueForm 
                  selectedNode={selectedNode} 
                  onOperationComplete={fetchNodeStatuses}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <KeyDistributionChart nodes={NODES} nodeStatuses={nodeStatuses} />
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App; 