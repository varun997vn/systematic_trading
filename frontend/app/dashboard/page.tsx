'use client';

import { useEffect, useState } from 'react';
import {
    Box,
    Grid,
    Container,
    Typography,
    Alert,
    CircularProgress,
} from '@mui/material';
import PortfolioSummaryCard from '@/components/dashboard/PortfolioSummaryCard';
import PositionsOverview from '@/components/dashboard/PositionsOverview';
import RecentTrades from '@/components/dashboard/RecentTrades';
import MarketStatus from '@/components/dashboard/MarketStatus';
import QuickActions from '@/components/dashboard/QuickActions';
import api, { PortfolioSummary, PositionInfo, TradeInfo, MarketStatusResponse } from '@/lib/api';

export default function DashboardPage() {
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [positions, setPositions] = useState<PositionInfo[]>([]);
    const [recentTrades, setRecentTrades] = useState<TradeInfo[]>([]);
    const [marketStatus, setMarketStatus] = useState<MarketStatusResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load all dashboard data in parallel
            const [portfolioRes, positionsRes, tradesRes, marketRes] = await Promise.all([
                api.portfolio.getSummary().catch(() => null),
                api.positions.getAll().catch(() => ({ positions: [], count: 0 })),
                api.trades.getAll(undefined, undefined, undefined).catch(() => ({ trades: [], count: 0 })),
                api.market.getStatus().catch(() => null),
            ]);

            setPortfolio(portfolioRes);
            setPositions(positionsRes.positions);

            // Get only the 5 most recent trades
            setRecentTrades(tradesRes.trades.slice(0, 5));
            setMarketStatus(marketRes);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Typography variant="h4" gutterBottom fontWeight={600}>
                Dashboard
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            <Grid container spacing={3}>
                {/* Market Status */}
                <Grid item xs={12}>
                    <MarketStatus status={marketStatus} />
                </Grid>

                {/* Portfolio Summary */}
                <Grid item xs={12} md={8}>
                    <PortfolioSummaryCard portfolio={portfolio} />
                </Grid>

                {/* Quick Actions */}
                <Grid item xs={12} md={4}>
                    <QuickActions onRefresh={loadDashboardData} />
                </Grid>

                {/* Open Positions */}
                <Grid item xs={12} lg={7}>
                    <PositionsOverview positions={positions} onRefresh={loadDashboardData} />
                </Grid>

                {/* Recent Trades */}
                <Grid item xs={12} lg={5}>
                    <RecentTrades trades={recentTrades} />
                </Grid>
            </Grid>
        </Container>
    );
}