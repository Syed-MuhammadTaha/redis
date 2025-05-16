import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { styled } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import StorageIcon from '@mui/icons-material/Storage';
import RouterIcon from '@mui/icons-material/Router';

const StyledCard = styled(Card)(({ theme, isselected, ishealthy }) => ({
  cursor: 'pointer',
  transition: 'transform 0.2s, box-shadow 0.2s',
  border: isselected === 'true' ? `2px solid ${theme.palette.primary.main}` : 'none',
  background: ishealthy === 'true' 
    ? 'linear-gradient(45deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%)'
    : 'linear-gradient(45deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%)',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const StatusIndicator = styled(Box)(({ theme, ishealthy }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  color: ishealthy === 'true' ? theme.palette.success.main : theme.palette.error.main,
  marginBottom: theme.spacing(2),
}));

const DetailRow = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginTop: theme.spacing(1),
  color: theme.palette.text.secondary,
}));

function NodeStatusCard({ node, status, isSelected, onSelect }) {
  const isHealthy = status?.status === 'healthy';

  return (
    <StyledCard 
      isselected={isSelected.toString()} 
      ishealthy={isHealthy.toString()}
      onClick={onSelect}
      elevation={isSelected ? 8 : 2}
    >
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          {node.id}
        </Typography>

        <StatusIndicator ishealthy={isHealthy.toString()}>
          {isHealthy ? <CheckCircleIcon /> : <ErrorIcon />}
          <Typography variant="body1">
            {isHealthy ? 'Healthy' : 'Unhealthy'}
          </Typography>
        </StatusIndicator>

        {status && !status.error && (
          <Box sx={{ mt: 2 }}>
            <DetailRow>
              <AccessTimeIcon fontSize="small" />
              <Typography variant="body2">
                Uptime: {status.uptime}
              </Typography>
            </DetailRow>
            <DetailRow>
              <StorageIcon fontSize="small" />
              <Typography variant="body2">
                Keys: {status.key_count}
              </Typography>
            </DetailRow>
            <DetailRow>
              <RouterIcon fontSize="small" />
              <Typography variant="body2">
                Port: {node.port}
              </Typography>
            </DetailRow>
          </Box>
        )}

        {status?.error && (
          <Typography 
            color="error" 
            variant="body2" 
            sx={{ mt: 2 }}
          >
            {status.error}
          </Typography>
        )}
      </CardContent>
    </StyledCard>
  );
}

export default NodeStatusCard; 