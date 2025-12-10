'use client';

import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
} from '@mui/material';
import {
    Schedule as ClockIcon,
} from '@mui/icons-material';
import { MarketStatusResponse } from '@/lib/api';
import { format } from 'date-fns';

interface MarketStatusProps {
    status: MarketStatusResponse | null;
}

export default function MarketStatus({ status }: MarketStatusProps) {
    if (!status) {
        return null;
    }

    const formatTime = (dateString: string) => {
        try {
            return format(new Date(dateString), 'PPpp');
        } catch {
            return dateString;
        }
    };

    return (
        <Card sx={{ bgcolor: status.is_open ? 'success.light' : 'grey.100' }}>
            <CardContent sx={{ py: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box display="flex" alignItems="center" gap={2}>
                        <ClockIcon color="action" />
                        <Box>
                            <Typography variant="body2" fontWeight={600}>
                                Market Status
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                {formatTime(status.current_time)}
                            </Typography>
                        </Box>
                    </Box>

                    <Box display="flex" gap={1}>
                        <Chip
                            label={status.is_open ? 'OPEN' : 'CLOSED'}
                            color={status.is_open ? 'success' : 'default'}
                            size="small"
                        />
                        {status.is_trading_day && (
                            <Chip
                                label="TRADING DAY"
                                variant="outlined"
                                size="small"
                            />
                        )}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
}