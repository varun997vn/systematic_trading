'use client';

import { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    CircularProgress,
    Alert,
    Card,
    CardContent,
    Grid,
    IconButton,
    Tooltip,
    SelectChangeEvent,
} from '@mui/material';
import {
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    Timeline as TimelineIcon,
    Refresh as RefreshIcon,
    FilterList as FilterIcon,
    ShowChart as ChartIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';

// Types
interface Signal {
    id: string;
    ticker: string;
    signal: 'BUY' | 'SELL' | 'HOLD';
    strength: number;
    price: number;
    strategy: string;
    timestamp: string;
    indicators?: Record<string, number>;
}

interface GenerateSignalsRequest {
    tickers: string[];
    strategies?: string[];
}

// API Functions
async function fetchSignals(): Promise<Signal[]> {
    const response = await fetch('/api/signals');
    if (!response.ok) throw new Error('Failed to fetch signals');
    return response.json();
}

async function generateSignals(data: GenerateSignalsRequest): Promise<Signal[]> {
    const response = await fetch('/api/signals/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to generate signals');
    return response.json();
}

async function fetchAvailableTickers(): Promise<string[]> {
    const response = await fetch('/api/tickers');
    if (!response.ok) throw new Error('Failed to fetch tickers');
    return response.json();
}

async function fetchAvailableStrategies(): Promise<string[]> {
    const response = await fetch('/api/strategies');
    if (!response.ok) throw new Error('Failed to fetch strategies');
    const strategies = await response.json();
    return strategies.map((s: any) => s.name);
}

// Helper functions
function getSignalColor(signal: string): 'success' | 'error' | 'default' {
    if (signal === 'BUY') return 'success';
    if (signal === 'SELL') return 'error';
    return 'default';
}

function getStrengthLabel(strength: number): string {
    if (strength >= 0.8) return 'Very Strong';
    if (strength >= 0.6) return 'Strong';
    if (strength >= 0.4) return 'Moderate';
    if (strength >= 0.2) return 'Weak';
    return 'Very Weak';
}

export default function SignalsPage() {
    const router = useRouter();
    const queryClient = useQueryClient();

    const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
    const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
    const [signalFilter, setSignalFilter] = useState<string>('ALL');

    // Queries
    const { data: signals = [], isLoading: signalsLoading, error: signalsError } = useQuery({
        queryKey: ['signals'],
        queryFn: fetchSignals,
    });

    const { data: availableTickers = [] } = useQuery({
        queryKey: ['available-tickers'],
        queryFn: fetchAvailableTickers,
    });

    const { data: availableStrategies = [] } = useQuery({
        queryKey: ['available-strategies'],
        queryFn: fetchAvailableStrategies,
    });

    // Mutations
    const generateMutation = useMutation({
        mutationFn: generateSignals,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['signals'] });
        },
    });

    // Handlers
    const handleGenerateSignals = () => {
        if (selectedTickers.length === 0) return;

        generateMutation.mutate({
            tickers: selectedTickers,
            strategies: selectedStrategies.length > 0 ? selectedStrategies : undefined,
        });
    };

    const handleTickerChange = (event: SelectChangeEvent<string[]>) => {
        const value = event.target.value;
        setSelectedTickers(typeof value === 'string' ? value.split(',') : value);
    };

    const handleStrategyChange = (event: SelectChangeEvent<string[]>) => {
        const value = event.target.value;
        setSelectedStrategies(typeof value === 'string' ? value.split(',') : value);
    };

    const handleViewChart = (ticker: string) => {
        router.push(`/charts?ticker=${ticker}`);
    };

    // Filter signals
    const filteredSignals = signals.filter((signal) => {
        if (signalFilter === 'ALL') return true;
        return signal.signal === signalFilter;
    });

    // Calculate summary stats
    const buySignals = signals.filter((s) => s.signal === 'BUY').length;
    const sellSignals = signals.filter((s) => s.signal === 'SELL').length;
    const holdSignals = signals.filter((s) => s.signal === 'HOLD').length;
    const avgStrength = signals.length > 0
        ? signals.reduce((sum, s) => sum + s.strength, 0) / signals.length
        : 0;

    return (
        <Box>
            {/* Page Header */}
            <Box
                sx={{
                    mb: 4,
                    pb: 3,
                    borderBottom: '3px solid',
                    borderImage: 'linear-gradient(90deg, #2196f3 0%, #00bcd4 100%) 1',
                }}
            >
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 800,
                        letterSpacing: '-0.02em',
                        background: 'linear-gradient(135deg, #2196f3 0%, #00bcd4 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        mb: 1,
                    }}
                >
                    Trading Signals
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Generate and analyze trading signals from your strategies
                </Typography>
            </Box>

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        sx={{
                            background: 'linear-gradient(135deg, #4caf50 0%, #66bb6a 100%)',
                            color: 'white',
                            boxShadow: '0 8px 24px rgba(76, 175, 80, 0.3)',
                        }}
                    >
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <TrendingUpIcon sx={{ mr: 1, fontSize: 28 }} />
                                <Typography variant="h6" fontWeight={700}>
                                    Buy Signals
                                </Typography>
                            </Box>
                            <Typography variant="h3" fontWeight={800}>
                                {buySignals}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        sx={{
                            background: 'linear-gradient(135deg, #f44336 0%, #ef5350 100%)',
                            color: 'white',
                            boxShadow: '0 8px 24px rgba(244, 67, 54, 0.3)',
                        }}
                    >
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <TrendingDownIcon sx={{ mr: 1, fontSize: 28 }} />
                                <Typography variant="h6" fontWeight={700}>
                                    Sell Signals
                                </Typography>
                            </Box>
                            <Typography variant="h3" fontWeight={800}>
                                {sellSignals}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        sx={{
                            background: 'linear-gradient(135deg, #ff9800 0%, #ffa726 100%)',
                            color: 'white',
                            boxShadow: '0 8px 24px rgba(255, 152, 0, 0.3)',
                        }}
                    >
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <TimelineIcon sx={{ mr: 1, fontSize: 28 }} />
                                <Typography variant="h6" fontWeight={700}>
                                    Hold Signals
                                </Typography>
                            </Box>
                            <Typography variant="h3" fontWeight={800}>
                                {holdSignals}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        sx={{
                            background: 'linear-gradient(135deg, #9c27b0 0%, #ab47bc 100%)',
                            color: 'white',
                            boxShadow: '0 8px 24px rgba(156, 39, 176, 0.3)',
                        }}
                    >
                        <CardContent>
                            <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
                                Avg Strength
                            </Typography>
                            <Typography variant="h3" fontWeight={800}>
                                {(avgStrength * 100).toFixed(0)}%
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                                {getStrengthLabel(avgStrength)}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Generate Signals Section */}
            <Paper
                sx={{
                    p: 3,
                    mb: 4,
                    background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)',
                    border: '2px solid #e3f2fd',
                }}
            >
                <Typography variant="h6" fontWeight={700} sx={{ mb: 3 }}>
                    Generate New Signals
                </Typography>

                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={4}>
                        <FormControl fullWidth>
                            <InputLabel>Select Tickers</InputLabel>
                            <Select
                                multiple
                                value={selectedTickers}
                                onChange={handleTickerChange}
                                renderValue={(selected) => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {selected.map((value) => (
                                            <Chip key={value} label={value} size="small" />
                                        ))}
                                    </Box>
                                )}
                            >
                                {availableTickers.map((ticker) => (
                                    <MenuItem key={ticker} value={ticker}>
                                        {ticker}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <FormControl fullWidth>
                            <InputLabel>Select Strategies (Optional)</InputLabel>
                            <Select
                                multiple
                                value={selectedStrategies}
                                onChange={handleStrategyChange}
                                renderValue={(selected) => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {selected.map((value) => (
                                            <Chip key={value} label={value} size="small" />
                                        ))}
                                    </Box>
                                )}
                            >
                                {availableStrategies.map((strategy) => (
                                    <MenuItem key={strategy} value={strategy}>
                                        {strategy}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Button
                            fullWidth
                            variant="contained"
                            size="large"
                            onClick={handleGenerateSignals}
                            disabled={selectedTickers.length === 0 || generateMutation.isPending}
                            startIcon={generateMutation.isPending ? <CircularProgress size={20} /> : <RefreshIcon />}
                            sx={{
                                height: 56,
                                fontWeight: 700,
                                background: 'linear-gradient(135deg, #2196f3 0%, #00bcd4 100%)',
                                '&:hover': {
                                    background: 'linear-gradient(135deg, #1976d2 0%, #0097a7 100%)',
                                },
                            }}
                        >
                            {generateMutation.isPending ? 'Generating...' : 'Generate Signals'}
                        </Button>
                    </Grid>
                </Grid>

                {generateMutation.isError && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        Failed to generate signals. Please try again.
                    </Alert>
                )}

                {generateMutation.isSuccess && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                        Successfully generated {generateMutation.data?.length || 0} signals!
                    </Alert>
                )}
            </Paper>

            {/* Signals Table */}
            <Paper sx={{ mb: 4 }}>
                <Box
                    sx={{
                        p: 2,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        borderBottom: '1px solid #e0e0e0',
                    }}
                >
                    <Typography variant="h6" fontWeight={700}>
                        Signal History
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                            variant={signalFilter === 'ALL' ? 'contained' : 'outlined'}
                            size="small"
                            onClick={() => setSignalFilter('ALL')}
                        >
                            All
                        </Button>
                        <Button
                            variant={signalFilter === 'BUY' ? 'contained' : 'outlined'}
                            size="small"
                            color="success"
                            onClick={() => setSignalFilter('BUY')}
                        >
                            Buy
                        </Button>
                        <Button
                            variant={signalFilter === 'SELL' ? 'contained' : 'outlined'}
                            size="small"
                            color="error"
                            onClick={() => setSignalFilter('SELL')}
                        >
                            Sell
                        </Button>
                        <Button
                            variant={signalFilter === 'HOLD' ? 'contained' : 'outlined'}
                            size="small"
                            onClick={() => setSignalFilter('HOLD')}
                        >
                            Hold
                        </Button>
                    </Box>
                </Box>

                {signalsLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress />
                    </Box>
                ) : signalsError ? (
                    <Alert severity="error" sx={{ m: 2 }}>
                        Failed to load signals. Please try again.
                    </Alert>
                ) : filteredSignals.length === 0 ? (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                        <Typography variant="body1" color="text.secondary">
                            No signals found. Generate signals to get started.
                        </Typography>
                    </Box>
                ) : (
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                                    <TableCell sx={{ fontWeight: 700 }}>Ticker</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>Signal</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>Strength</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>Price</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>Strategy</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                                    <TableCell sx={{ fontWeight: 700 }} align="right">
                                        Actions
                                    </TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredSignals.map((signal) => (
                                    <TableRow
                                        key={signal.id}
                                        sx={{
                                            '&:hover': { backgroundColor: '#fafafa' },
                                            transition: 'background-color 0.2s',
                                        }}
                                    >
                                        <TableCell>
                                            <Typography fontWeight={700}>{signal.ticker}</Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={signal.signal}
                                                color={getSignalColor(signal.signal)}
                                                size="small"
                                                sx={{ fontWeight: 700 }}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Box
                                                    sx={{
                                                        width: 100,
                                                        height: 8,
                                                        backgroundColor: '#e0e0e0',
                                                        borderRadius: 4,
                                                        overflow: 'hidden',
                                                    }}
                                                >
                                                    <Box
                                                        sx={{
                                                            width: `${signal.strength * 100}%`,
                                                            height: '100%',
                                                            background:
                                                                signal.strength >= 0.7
                                                                    ? 'linear-gradient(90deg, #4caf50, #66bb6a)'
                                                                    : signal.strength >= 0.4
                                                                        ? 'linear-gradient(90deg, #ff9800, #ffa726)'
                                                                        : 'linear-gradient(90deg, #f44336, #ef5350)',
                                                        }}
                                                    />
                                                </Box>
                                                <Typography variant="body2" fontWeight={600}>
                                                    {(signal.strength * 100).toFixed(0)}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>${signal.price.toFixed(2)}</TableCell>
                                        <TableCell>
                                            <Chip label={signal.strategy} size="small" variant="outlined" />
                                        </TableCell>
                                        <TableCell>
                                            {new Date(signal.timestamp).toLocaleString()}
                                        </TableCell>
                                        <TableCell align="right">
                                            <Tooltip title="View Chart">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => handleViewChart(signal.ticker)}
                                                    sx={{
                                                        color: '#2196f3',
                                                        '&:hover': { backgroundColor: '#e3f2fd' },
                                                    }}
                                                >
                                                    <ChartIcon />
                                                </IconButton>
                                            </Tooltip>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                )}
            </Paper>
        </Box>
    );
}