import React, { useState } from 'react';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import { styled } from '@mui/material/styles';
import GetAppIcon from '@mui/icons-material/GetApp';
import PublishIcon from '@mui/icons-material/Publish';
import DeleteIcon from '@mui/icons-material/Delete';

const StyledPre = styled('pre')(({ theme }) => ({
  background: theme.palette.background.default,
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  overflowX: 'auto',
  margin: theme.spacing(2, 0),
  '&::-webkit-scrollbar': {
    height: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: theme.palette.background.paper,
  },
  '&::-webkit-scrollbar-thumb': {
    background: theme.palette.primary.main,
    borderRadius: '4px',
  },
}));

function KeyValueForm({ selectedNode, onOperationComplete }) {
  const [key, setKey] = useState('');
  const [value, setValue] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (action) => {
    setLoading(true);
    setResult(null);
    
    try {
      let response;
      const url = `http://localhost:${selectedNode.port}/store/${key}`;
      
      switch (action) {
        case 'get':
          response = await fetch(url);
          break;
        case 'put':
          response = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value })
          });
          break;
        case 'delete':
          response = await fetch(url, { method: 'DELETE' });
          break;
        default:
          throw new Error('Invalid action');
      }

      const data = await response.json();
      setResult({
        success: response.ok,
        data: data
      });

      // If operation was successful and it was a PUT or DELETE, refresh the stats
      if (response.ok && (action === 'put' || action === 'delete')) {
        // Wait a short moment for replication
        await new Promise(resolve => setTimeout(resolve, 500));
        onOperationComplete();
        
        // Clear form after successful PUT
        if (action === 'put') {
          setKey('');
          setValue('');
        }
      }
    } catch (error) {
      setResult({
        success: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Key-Value Operations
      </Typography>
      
      <Stack spacing={3}>
        <TextField
          label="Key"
          variant="outlined"
          fullWidth
          value={key}
          onChange={(e) => setKey(e.target.value)}
          disabled={loading}
        />
        
        <TextField
          label="Value"
          variant="outlined"
          fullWidth
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
          multiline
          rows={2}
        />
        
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            onClick={() => handleSubmit('get')}
            disabled={loading || !key}
            startIcon={<GetAppIcon />}
          >
            Get
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleSubmit('put')}
            disabled={loading || !key || !value}
            startIcon={<PublishIcon />}
          >
            Put
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleSubmit('delete')}
            disabled={loading || !key}
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </Stack>
        
        {loading && (
          <Box display="flex" justifyContent="center">
            <CircularProgress />
          </Box>
        )}
        
        {result && (
          <Box>
            {result.success ? (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  Operation completed successfully
                </Alert>
                <StyledPre>
                  {JSON.stringify(result.data, null, 2)}
                </StyledPre>
              </Box>
            ) : (
              <Alert severity="error">
                {result.error}
              </Alert>
            )}
          </Box>
        )}
      </Stack>
    </Box>
  );
}

export default KeyValueForm; 