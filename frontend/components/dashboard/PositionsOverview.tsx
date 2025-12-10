'use client';

import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  Button,
} from '@mui/material';
import { useRouter } from 'next/navigation';
import { PositionInfo } from '@/lib/api';

interface PositionsOverviewProps {
  positions: PositionInfo[];
  onRefresh?: () => void;
}

export default function PositionsOverview({ positions, onRefresh }: PositionsOverviewProps) {
  const router = useRouter();

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" fontWeight={600}>
            Open Positions
          </Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={() => router.push('/positions')}
          >
            View All
          </Button>
        </Box>

        {positions.length === 0 ? (
          <Typography color="text.secondary" align="center" py={3}>
            No open positions
          </Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Symbol</strong></TableCell>
                  <TableCell align="right"><strong>Quantity</strong></TableCell>
                  <TableCell align="right"><strong>Avg Price</strong></TableCell>
                  <TableCell align="right"><strong>Current</strong></TableCell>
                  <TableCell align="right"><strong>Value</strong></TableCell>
                  <TableCell align="right"><strong>P&L</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {positions.map((position) => (
                  <TableRow
                    key={position.symbol}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => router.push(`/positions?symbol=${position.symbol}`)}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {position.symbol}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{position.quantity}</TableCell>
                    <TableCell align="right">
                      ${position.avg_price.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      ${position.current_price.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      ${position.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell align="right">
                      <Box display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color={position.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                        >
                          ${position.unrealized_pnl.toFixed(2)}
                        </Typography>
                        <Chip
                          label={`${position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl_pct.toFixed(2)}%`}
                          size="small"
                          color={position.unrealized_pnl >= 0 ? 'success' : 'error'}
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
}