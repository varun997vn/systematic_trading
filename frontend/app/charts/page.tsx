'use client';

import React, {useState, useEffect, useCallback} from 'react';
import {
    Box,
    Container,
    Paper,
    Typography,
    Grid,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Slider,
    Chip,
    Button,
    CircularProgress,
    Alert,
    IconButton,
    Tooltip,
    Stack,
    Divider,
} from '@mui/material';
import {
    Download as DownloadIcon,
    Refresh as RefreshIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import {LocalizationProvider, DatePicker} from '@mui/x-date-pickers';
import {AdapterDateFns} from '@mui/x-date-pickers/AdapterDateFns';
import dynamic from 'next/dynamic';
import {api, type TradingSignal, type MarketDataPoint, type BuySellPoint} from '@/lib/api';

// Dynamic import to avoid SSR issues with Plotly
const Plot = dynamic(() => import('react-plotly.js'), {ssr: false});

interface ChartData {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume: number[];
}

export default function ChartsPage() {
    // State management
    const [tickers, setTickers] = useState<string[]>([]);
    const [selectedTicker, setSelectedTicker] = useState<string>('');
    const [startDate, setStartDate] = useState<Date | null>(
        new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) // 90 days ago
    );
    const [endDate, setEndDate] = useState<Date | null>(new Date());
    const [signalStrength, setSignalStrength] = useState<number>(10);
    const [chartData, setChartData] = useState<ChartData | null>(null);
    const [buyPoints, setBuyPoints] = useState<BuySellPoint[]>([]);
    const [sellPoints, setSellPoints] = useState<BuySellPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState({
        currentPrice: 0,
        priceChange: 0,
        priceChangePercent: 0,
        highPrice: 0,
        lowPrice: 0,
        avgVolume: 0,
    });

    // Fetch available tickers on mount
    useEffect(() => {
        const fetchTickers = async () => {
            try {
                const response = await api.data.getTickers();
                setTickers(response.tickers);
                if (response.tickers.length > 0) {
                    setSelectedTicker(response.tickers[0]);
                }
            } catch (err) {
                setError('Failed to load tickers');
                console.error(err);
            }
        };
        fetchTickers();
    }, []);

    // Fetch chart data when ticker or dates change
    const fetchChartData = useCallback(async () => {
        if (!selectedTicker) return;

        setLoading(true);
        setError(null);

        try {
            const formatDate = (date: Date | null) =>
                date?.toISOString().split('T')[0] || '';

            // Fetch market data
            const dataResponse = await api.data.getTickerData(
                selectedTicker,
                formatDate(startDate),
                formatDate(endDate)
            );

            // Transform data for Plotly
            const chartData: ChartData = {
                dates: dataResponse.data.map((d) => d.timestamp),
                open: dataResponse.data.map((d) => d.open),
                high: dataResponse.data.map((d) => d.high),
                low: dataResponse.data.map((d) => d.low),
                close: dataResponse.data.map((d) => d.close),
                volume: dataResponse.data.map((d) => d.volume),
            };

            setChartData(chartData);

            // Calculate stats
            const prices = chartData.close;
            const volumes = chartData.volume;
            const currentPrice = prices[prices.length - 1] || 0;
            const previousPrice = prices[prices.length - 2] || currentPrice;
            const priceChange = currentPrice - previousPrice;
            const priceChangePercent = ((priceChange / previousPrice) * 100);

            setStats({
                currentPrice,
                priceChange,
                priceChangePercent,
                highPrice: Math.max(...prices),
                lowPrice: Math.min(...prices),
                avgVolume: volumes.reduce((a, b) => a + b, 0) / volumes.length,
            });

            // Fetch buy/sell signals
            const signalsResponse = await api.signals.getBuySellPoints(
                selectedTicker,
                signalStrength
            );

            setBuyPoints(signalsResponse.buy_points);
            setSellPoints(signalsResponse.sell_points);
        } catch (err) {
            setError('Failed to load chart data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [selectedTicker, startDate, endDate, signalStrength]);

    useEffect(() => {
        if (selectedTicker) {
            fetchChartData();
        }
    }, [selectedTicker, fetchChartData]);

    // Generate signals for the current ticker
    const handleGenerateSignals = async () => {
        if (!selectedTicker) return;

        setLoading(true);
        try {
            await api.signals.generate({
                ticker: selectedTicker,
                start_date: startDate?.toISOString().split('T')[0],
                end_date: endDate?.toISOString().split('T')[0],
            });
            await fetchChartData();
        } catch (err) {
            setError('Failed to generate signals');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Prepare Plotly data
    const getPlotlyData = () => {
        if (!chartData) return [];

        const data: any[] = [
            // Candlestick chart
            {
                type: 'candlestick',
                x: chartData.dates,
                open: chartData.open,
                high: chartData.high,
                low: chartData.low,
                close: chartData.close,
                name: selectedTicker,
                increasing: {line: {color: '#10b981'}},
                decreasing: {line: {color: '#ef4444'}},
                yaxis: 'y',
                xaxis: 'x',
            },
        ];

        // Add buy signals
        if (buyPoints.length > 0) {
            data.push({
                type: 'scatter',
                mode: 'markers',
                x: buyPoints.map((p) => p.date),
                y: buyPoints.map((p) => p.price),
                name: 'Buy Signal',
                marker: {
                    color: '#10b981',
                    size: 12,
                    symbol: 'triangle-up',
                    line: {color: '#065f46', width: 2},
                },
                yaxis: 'y',
                xaxis: 'x',
            });
        }

        // Add sell signals
        if (sellPoints.length > 0) {
            data.push({
                type: 'scatter',
                mode: 'markers',
                x: sellPoints.map((p) => p.date),
                y: sellPoints.map((p) => p.price),
                name: 'Sell Signal',
                marker: {
                    color: '#ef4444',
                    size: 12,
                    symbol: 'triangle-down',
                    line: {color: '#991b1b', width: 2},
                },
                yaxis: 'y',
                xaxis: 'x',
            });
        }

        // Volume bars
        data.push({
            type: 'bar',
            x: chartData.dates,
            y: chartData.volume,
            name: 'Volume',
            yaxis: 'y2',
            xaxis: 'x',
            marker: {
                color: chartData.close.map((close, i) =>
                    i === 0 || close >= chartData.close[i - 1]
                        ? 'rgba(16, 185, 129, 0.3)'
                        : 'rgba(239, 68, 68, 0.3)'
                ),
            },
        });

        return data;
    };

    const plotlyLayout = {
        autosize: true,
        height: 700,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: {color: '#94a3b8', family: 'Inter, sans-serif'},
        xaxis: {
            domain: [0, 1],
            rangeslider: {visible: false},
            gridcolor: '#334155',
            showgrid: true,
        },
        yaxis: {
            domain: [0.25, 1],
            gridcolor: '#334155',
            showgrid: true,
        },
        yaxis2: {
            domain: [0, 0.2],
            gridcolor: '#334155',
            showgrid: false,
        },
        margin: {l: 60, r: 40, t: 40, b: 40},
        legend: {
            x: 0,
            y: 1.1,
            orientation: 'h',
        },
        hovermode: 'x unified',
    };

    const plotlyConfig = {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Container maxWidth="xl" sx={{py: 4}}>
                {/* Header */}
                <Box sx={{mb: 4}}>
                    <Typography variant="h4" fontWeight={700} gutterBottom>
                        Chart Analysis
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Visualize price action and trading signals
                    </Typography>
                </Box>

                {/* Controls */}
                <Paper elevation={0} sx={{p: 3, mb: 3, bgcolor: 'background.paper'}}>
                    <Grid container spacing={3}>
                        {/* Ticker Selection */}
                        <Grid item xs={12} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>Ticker</InputLabel>
                                <Select
                                    value={selectedTicker}
                                    label="Ticker"
                                    onChange={(e) => setSelectedTicker(e.target.value)}
                                >
                                    {tickers.map((ticker) => (
                                        <MenuItem key={ticker} value={ticker}>
                                            {ticker}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>

                        {/* Date Range */}
                        <Grid item xs={12} md={3}>
                            <DatePicker
                                label="Start Date"
                                value={startDate}
                                onChange={setStartDate}
                                slotProps={{textField: {fullWidth: true}}}
                            />
                        </Grid>
                        <Grid item xs={12} md={3}>
                            <DatePicker
                                label="End Date"
                                value={endDate}
                                onChange={setEndDate}
                                slotProps={{textField: {fullWidth: true}}}
                            />
                        </Grid>

                        {/* Actions */}
                        <Grid item xs={12} md={3}>
                            <Stack direction="row" spacing={1}>
                                <Tooltip title="Refresh Data">
                                    <IconButton
                                        onClick={fetchChartData}
                                        disabled={loading}
                                        color="primary"
                                    >
                                        <RefreshIcon/>
                                    </IconButton>
                                </Tooltip>
                                <Button
                                    variant="contained"
                                    onClick={handleGenerateSignals}
                                    disabled={loading}
                                    fullWidth
                                    startIcon={<ShowChartIcon/>}
                                >
                                    Generate Signals
                                </Button>
                            </Stack>
                        </Grid>

                        {/* Signal Strength Slider */}
                        <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                Signal Strength Threshold: {signalStrength}
                            </Typography>
                            <Slider
                                value={signalStrength}
                                onChange={(_, value) => setSignalStrength(value as number)}
                                onChangeCommitted={fetchChartData}
                                min={1}
                                max={100}
                                valueLabelDisplay="auto"
                                marks={[
                                    {value: 1, label: 'Weak'},
                                    {value: 50, label: 'Medium'},
                                    {value: 100, label: 'Strong'},
                                ]}
                            />
                        </Grid>
                    </Grid>
                </Paper>

                {/* Stats Cards */}
                {chartData && (
                    <Grid container spacing={2} sx={{mb: 3}}>
                        <Grid item xs={6} md={2.4}>
                            <Paper elevation={0} sx={{p: 2, bgcolor: 'background.paper'}}>
                                <Typography variant="caption" color="text.secondary">
                                    Current Price
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    ${stats.currentPrice.toFixed(2)}
                                </Typography>
                            </Paper>
                        </Grid>
                        <Grid item xs={6} md={2.4}>
                            <Paper elevation={0} sx={{p: 2, bgcolor: 'background.paper'}}>
                                <Typography variant="caption" color="text.secondary">
                                    Change
                                </Typography>
                                <Stack direction="row" alignItems="center" spacing={0.5}>
                                    {stats.priceChange >= 0 ? (
                                        <TrendingUpIcon fontSize="small" color="success"/>
                                    ) : (
                                        <TrendingDownIcon fontSize="small" color="error"/>
                                    )}
                                    <Typography
                                        variant="h6"
                                        fontWeight={600}
                                        color={stats.priceChange >= 0 ? 'success.main' : 'error.main'}
                                    >
                                        {stats.priceChangePercent.toFixed(2)}%
                                    </Typography>
                                </Stack>
                            </Paper>
                        </Grid>
                        <Grid item xs={6} md={2.4}>
                            <Paper elevation={0} sx={{p: 2, bgcolor: 'background.paper'}}>
                                <Typography variant="caption" color="text.secondary">
                                    High
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    ${stats.highPrice.toFixed(2)}
                                </Typography>
                            </Paper>
                        </Grid>
                        <Grid item xs={6} md={2.4}>
                            <Paper elevation={0} sx={{p: 2, bgcolor: 'background.paper'}}>
                                <Typography variant="caption" color="text.secondary">
                                    Low
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    ${stats.lowPrice.toFixed(2)}
                                </Typography>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={2.4}>
                            <Paper elevation={0} sx={{p: 2, bgcolor: 'background.paper'}}>
                                <Typography variant="caption" color="text.secondary">
                                    Avg Volume
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    {(stats.avgVolume / 1000000).toFixed(2)}M
                                </Typography>
                            </Paper>
                        </Grid>
                    </Grid>
                )}

                {/* Signal Summary */}
                {(buyPoints.length > 0 || sellPoints.length > 0) && (
                    <Paper elevation={0} sx={{p: 2, mb: 3, bgcolor: 'background.paper'}}>
                        <Stack direction="row" spacing={2} alignItems="center">
                            <Typography variant="body2" color="text.secondary">
                                Signals:
                            </Typography>
                            <Chip
                                label={`${buyPoints.length} Buy`}
                                color="success"
                                size="small"
                                icon={<TrendingUpIcon/>}
                            />
                            <Chip
                                label={`${sellPoints.length} Sell`}
                                color="error"
                                size="small"
                                icon={<TrendingDownIcon/>}
                            />
                        </Stack>
                    </Paper>
                )}

                {/* Error Alert */}
                {error && (
                    <Alert severity="error" sx={{mb: 3}} onClose={() => setError(null)}>
                        {error}
                    </Alert>
                )}

                {/* Chart */}
                <Paper elevation={0} sx={{p: 3, bgcolor: 'background.paper'}}>
                    {loading ? (
                        <Box
                            display="flex"
                            justifyContent="center"
                            alignItems="center"
                            height={700}
                        >
                            <CircularProgress/>
                        </Box>
                    ) : chartData ? (
                        <Plot
                            data={getPlotlyData()}
                            layout={plotlyLayout}
                            config={plotlyConfig}
                            style={{width: '100%'}}
                            useResizeHandler
                        />
                    ) : (
                        <Box
                            display="flex"
                            justifyContent="center"
                            alignItems="center"
                            height={700}
                        >
                            <Typography variant="body1" color="text.secondary">
                                Select a ticker to view chart
                            </Typography>
                        </Box>
                    )}
                </Paper>
            </Container>
        </LocalizationProvider>
    );
}