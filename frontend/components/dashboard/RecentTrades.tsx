'use client';

import {
    Card,
    CardContent,
    Typography,
    List,
    ListItem,
    ListItemText,
    Chip,
    Box,
    Button,
    Divider,
} from '@mui/material';
import { useRouter } from 'next/navigation';
import { TradeInfo } from '@/lib/api';
import { format } from 'date-fns';

interface RecentTradesProps {
    trades: TradeInfo[];
}

export default function RecentTrades({ trades }: RecentTradesProps) {
    const router = useRouter();

    const formatDate = (dateString: string) => {
        try {
            return format(new Date(dateString), 'MMM dd, HH:mm');
        } catch {
            return dateString;
        }
    };

    return (
        <Card>
            <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" fontWeight={600}>
                        Recent Trades
                    </Typography>
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={() => router.push('/trades')}
                    >
                        View All
                    </Button>
                </Box>

                {trades.length === 0 ? (
                    <Typography color="text.secondary" align="center" py={3}>
                        No recent trades
                    </Typography>
                ) : (
                    <List disablePadding>
                        {trades.map((trade, index) => (
                            <Box key={trade.id}>
                                {index > 0 && <Divider />}
                                <ListItem
                                    sx={{
                                        px: 0,
                                        py: 1.5,
                                        cursor: 'pointer',
                                        '&:hover': {
                                            bgcolor: 'action.hover',
                                        },
                                    }}
                                    onClick={() => router.push(`/trades?id=${trade.id}`)}
                                >
                                    <ListItemText
                                        primary={
                                            <Box display="flex" justifyContent="space-between" alignItems="center">
                                                <Box>
                                                    <Typography variant="body1" fontWeight={600}>
                                                        {trade.symbol}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {formatDate(trade.entry_time)}
                                                    </Typography>
                                                </Box>
                                                <Box display="flex" gap={1} alignItems="center">
                                                    <Chip
                                                        label={trade.side.toUpperCase()}
                                                        size="small"
                                                        color={trade.side === 'buy' ? 'success' : 'error'}
                                                        sx={{ minWidth: 50 }}
                                                    />
                                                    <Chip
                                                        label={trade.status.toUpperCase()}
                                                        size="small"
                                                        variant="outlined"
                                                        sx={{ minWidth: 60 }}
                                                    />
                                                </Box>
                                            </Box>
                                        }
                                        secondary={
                                            <Box mt={0.5}>
                                                <Typography variant="body2" component="span">
                                                    Qty: {trade.quantity} @ ${trade.entry_price.toFixed(2)}
                                                </Typography>
                                                {trade.pnl !== undefined && trade.pnl !== null && (
                                                    <Typography
                                                        variant="body2"
                                                        component="span"
                                                        ml={2}
                                                        color={trade.pnl >= 0 ? 'success.main' : 'error.main'}
                                                        fontWeight={600}
                                                    >
                                                        P&L: ${trade.pnl.toFixed(2)}
                                                    </Typography>
                                                )}
                                            </Box>
                                        }
                                    />
                                </ListItem>
                            </Box>
                        ))}
                    </List>
                )}
            </CardContent>
        </Card>
    );
}