'use client';

import {
    Card,
    CardContent,
    Typography,
    Grid,
    Box,
    Chip,
} from '@mui/material';
import {
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { PortfolioSummary } from '@/lib/api';

interface PortfolioSummaryCardProps {
    portfolio: PortfolioSummary | null;
}

export default function PortfolioSummaryCard({ portfolio }: PortfolioSummaryCardProps) {
    if (!portfolio) {
        return (
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Portfolio Summary
                    </Typography>
                    <Typography color="text.secondary">No portfolio data available</Typography>
                </CardContent>
            </Card>
        );
    }

    const totalPnL = portfolio.total_unrealized_pnl + portfolio.total_realized_pnl;
    const pnlPercentage = portfolio.total_value > 0
        ? ((totalPnL / (portfolio.total_value - totalPnL)) * 100)
        : 0;

const StatBox = ({ label, value, color, prefix = '$' }: { label: string; value: number | null | undefined; color?: string; prefix?: string }) => {
    const safeValue = typeof value === 'number' && !isNaN(value) ? value : 0;

    return (
        <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                {label}
            </Typography>
            <Typography variant="h5" fontWeight={600} color={color}>
                {prefix}{safeValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
        </Box>
    );
};


    return (
        <Card>
            <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                    <Typography variant="h6" fontWeight={600}>
                        Portfolio Summary
                    </Typography>
                    <Chip
                        icon={totalPnL >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                        label={`${totalPnL >= 0 ? '+' : ''}${pnlPercentage.toFixed(2)}%`}
                        color={totalPnL >= 0 ? 'success' : 'error'}
                        size="small"
                    />
                </Box>

                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <StatBox
                            label="Total Value"
                            value={portfolio.total_value}
                            color="primary.main"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <StatBox
                            label="Cash Balance"
                            value={portfolio.cash_balance}
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <StatBox
                            label="Positions Value"
                            value={portfolio.positions_value}
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <Box>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                Open Positions
                            </Typography>
                            <Typography variant="h5" fontWeight={600}>
                                {portfolio.num_positions}
                            </Typography>
                        </Box>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <StatBox
                            label="Unrealized P&L"
                            value={portfolio.total_unrealized_pnl}
                            color={portfolio.total_unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <StatBox
                            label="Realized P&L"
                            value={portfolio.total_realized_pnl}
                            color={portfolio.total_realized_pnl >= 0 ? 'success.main' : 'error.main'}
                        />
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
}