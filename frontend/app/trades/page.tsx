'use client';

import { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Grid,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    IconButton,
    Stack,
} from '@mui/material';
import {
    DataGrid,
    GridColDef,
    GridRenderCellParams,
    GridToolbar,
} from '@mui/x-data-grid';
import {
    Add as AddIcon,
    Close as CloseIcon,
    TrendingUp as ProfitIcon,
    TrendingDown as LossIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Types
interface Trade {
    id: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    quantity: number;
    entryPrice: number;
    exitPrice: number | null;
    status: 'OPEN' | 'CLOSED';
    strategy: string;
    pnl: number | null;
    pnlPercent: number | null;
    entryDate: string;
    exitDate: string | null;
}

interface PerformanceMetrics {
    totalTrades: number;
    openTrades: number;
    closedTrades: number;
    winRate: number;
    avgPnl: number;
    totalPnl: number;
}

// Zod schema for trade form
const tradeSchema = z.object({
    symbol: z.string().min(1, 'Symbol is required'),
    side: z.enum(['BUY', 'SELL']),
    quantity: z.number().min(1, 'Quantity must be at least 1'),
    entryPrice: z.number().min(0.01, 'Entry price must be greater than 0'),
    strategy: z.string().min(1, 'Strategy is required'),
});

type TradeFormData = z.infer<typeof tradeSchema>;

export default function TradesPage() {
    const [filterStatus, setFilterStatus] = useState<string>('ALL');
    const [filterStrategy, setFilterStrategy] = useState<string>('ALL');
    const [filterSymbol, setFilterSymbol] = useState<string>('');
    const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [isDetailsDialogOpen, setIsDetailsDialogOpen] = useState(false);

    // React Hook Form
    const {
        control,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<TradeFormData>({
        resolver: zodResolver(tradeSchema),
        defaultValues: {
            symbol: '',
            side: 'BUY',
            quantity: 100,
            entryPrice: 0,
            strategy: '',
        },
    });

    // Fetch trades
    const { data: trades = [], isLoading: tradesLoading } = useQuery<Trade[]>({
        queryKey: ['trades', filterStatus, filterStrategy, filterSymbol],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (filterStatus !== 'ALL') params.append('status', filterStatus);
            if (filterStrategy !== 'ALL') params.append('strategy', filterStrategy);
            if (filterSymbol) params.append('symbol', filterSymbol);

            const response = await fetch(`/api/trades?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch trades');
            return response.json();
        },
    });

    // Fetch performance metrics
    const { data: metrics } = useQuery<PerformanceMetrics>({
        queryKey: ['trades-metrics'],
        queryFn: async () => {
            const response = await fetch('/api/trades/metrics');
            if (!response.ok) throw new Error('Failed to fetch metrics');
            return response.json();
        },
    });

    // Fetch available strategies
    const { data: strategies = [] } = useQuery<string[]>({
        queryKey: ['strategies-list'],
        queryFn: async () => {
            const response = await fetch('/api/strategies/list');
            if (!response.ok) throw new Error('Failed to fetch strategies');
            return response.json();
        },
    });

    // Handle create trade
    const onSubmit = async (data: TradeFormData) => {
        try {
            const response = await fetch('/api/trades', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (!response.ok) throw new Error('Failed to create trade');

            setIsCreateDialogOpen(false);
            reset();
            // Refetch trades would happen automatically with React Query
        } catch (error) {
            console.error('Error creating trade:', error);
        }
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'symbol',
            headerName: 'Symbol',
            width: 100,
            renderCell: (params: GridRenderCellParams) => (
                <Typography fontWeight={600}>{params.value}</Typography>
            ),
        },
        {
            field: 'side',
            headerName: 'Side',
            width: 80,
            renderCell: (params: GridRenderCellParams) => (
                <Chip
                    label={params.value}
                    color={params.value === 'BUY' ? 'success' : 'error'}
                    size="small"
                />
            ),
        },
        {
            field: 'quantity',
            headerName: 'Quantity',
            width: 100,
            type: 'number',
        },
        {
            field: 'entryPrice',
            headerName: 'Entry Price',
            width: 120,
            type: 'number',
            valueFormatter: (params) => `$${params.toFixed(2)}`,
        },
        {
            field: 'exitPrice',
            headerName: 'Exit Price',
            width: 120,
            type: 'number',
            valueFormatter: (params) => (params ? `$${params.toFixed(2)}` : '-'),
        },
        {
            field: 'pnl',
            headerName: 'P&L',
            width: 120,
            type: 'number',
            renderCell: (params: GridRenderCellParams) => {
                if (params.value === null) return '-';
                const pnl = params.value as number;
                return (
                    <Box display="flex" alignItems="center" gap={0.5}>
                        {pnl >= 0 ? (
                            <ProfitIcon fontSize="small" color="success" />
                        ) : (
                            <LossIcon fontSize="small" color="error" />
                        )}
                        <Typography
                            color={pnl >= 0 ? 'success.main' : 'error.main'}
                            fontWeight={600}
                        >
                            ${Math.abs(pnl).toFixed(2)}
                        </Typography>
                    </Box>
                );
            },
        },
        {
            field: 'pnlPercent',
            headerName: 'P&L %',
            width: 100,
            type: 'number',
            renderCell: (params: GridRenderCellParams) => {
                if (params.value === null) return '-';
                const pct = params.value as number;
                return (
                    <Typography
                        color={pct >= 0 ? 'success.main' : 'error.main'}
                        fontWeight={600}
                    >
                        {pct >= 0 ? '+' : ''}
                        {pct.toFixed(2)}%
                    </Typography>
                );
            },
        },
        {
            field: 'strategy',
            headerName: 'Strategy',
            width: 150,
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 100,
            renderCell: (params: GridRenderCellParams) => (
                <Chip
                    label={params.value}
                    color={params.value === 'OPEN' ? 'primary' : 'default'}
                    size="small"
                    variant="outlined"
                />
            ),
        },
        {
            field: 'entryDate',
            headerName: 'Entry Date',
            width: 180,
            valueFormatter: (params) => new Date(params).toLocaleString(),
        },
        {
            field: 'actions',
            headerName: 'Actions',
            width: 120,
            sortable: false,
            renderCell: (params: GridRenderCellParams) => (
                <Button
                    size="small"
                    variant="outlined"
                    onClick={() => {
                        setSelectedTrade(params.row as Trade);
                        setIsDetailsDialogOpen(true);
                    }}
                >
                    Details
                </Button>
            ),
        },
    ];

    return (
        <Box>
            {/* Page Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" fontWeight={700}>
                    Trades
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setIsCreateDialogOpen(true)}
                >
                    Create Trade
                </Button>
            </Box>

            {/* Performance Metrics */}
            {metrics && (
                <Grid container spacing={2} mb={3}>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Total Trades
                                </Typography>
                                <Typography variant="h5" fontWeight={700}>
                                    {metrics.totalTrades}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Open
                                </Typography>
                                <Typography variant="h5" fontWeight={700} color="primary">
                                    {metrics.openTrades}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Closed
                                </Typography>
                                <Typography variant="h5" fontWeight={700}>
                                    {metrics.closedTrades}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Win Rate
                                </Typography>
                                <Typography
                                    variant="h5"
                                    fontWeight={700}
                                    color={metrics.winRate >= 50 ? 'success.main' : 'error.main'}
                                >
                                    {metrics.winRate.toFixed(1)}%
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Avg P&L
                                </Typography>
                                <Typography
                                    variant="h5"
                                    fontWeight={700}
                                    color={metrics.avgPnl >= 0 ? 'success.main' : 'error.main'}
                                >
                                    ${metrics.avgPnl.toFixed(2)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                        <Card>
                            <CardContent>
                                <Typography color="text.secondary" variant="body2">
                                    Total P&L
                                </Typography>
                                <Typography
                                    variant="h5"
                                    fontWeight={700}
                                    color={metrics.totalPnl >= 0 ? 'success.main' : 'error.main'}
                                >
                                    ${metrics.totalPnl.toFixed(2)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Filters */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={6} md={3}>
                        <TextField
                            fullWidth
                            label="Search Symbol"
                            value={filterSymbol}
                            onChange={(e) => setFilterSymbol(e.target.value)}
                            placeholder="e.g., AAPL"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <FormControl fullWidth>
                            <InputLabel>Status</InputLabel>
                            <Select
                                value={filterStatus}
                                label="Status"
                                onChange={(e) => setFilterStatus(e.target.value)}
                            >
                                <MenuItem value="ALL">All</MenuItem>
                                <MenuItem value="OPEN">Open</MenuItem>
                                <MenuItem value="CLOSED">Closed</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <FormControl fullWidth>
                            <InputLabel>Strategy</InputLabel>
                            <Select
                                value={filterStrategy}
                                label="Strategy"
                                onChange={(e) => setFilterStrategy(e.target.value)}
                            >
                                <MenuItem value="ALL">All</MenuItem>
                                {strategies.map((strategy) => (
                                    <MenuItem key={strategy} value={strategy}>
                                        {strategy}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Button
                            fullWidth
                            variant="outlined"
                            onClick={() => {
                                setFilterStatus('ALL');
                                setFilterStrategy('ALL');
                                setFilterSymbol('');
                            }}
                        >
                            Clear Filters
                        </Button>
                    </Grid>
                </Grid>
            </Paper>

            {/* Trades Table */}
            <Paper sx={{ height: 600, width: '100%' }}>
                <DataGrid
                    rows={trades}
                    columns={columns}
                    loading={tradesLoading}
                    pageSizeOptions={[10, 25, 50, 100]}
                    initialState={{
                        pagination: { paginationModel: { pageSize: 25 } },
                    }}
                    slots={{ toolbar: GridToolbar }}
                    slotProps={{
                        toolbar: {
                            showQuickFilter: true,
                        },
                    }}
                    disableRowSelectionOnClick
                />
            </Paper>

            {/* Create Trade Dialog */}
            <Dialog
                open={isCreateDialogOpen}
                onClose={() => setIsCreateDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    Create New Trade
                    <IconButton
                        onClick={() => setIsCreateDialogOpen(false)}
                        sx={{ position: 'absolute', right: 8, top: 8 }}
                    >
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <form onSubmit={handleSubmit(onSubmit)}>
                    <DialogContent>
                        <Stack spacing={2}>
                            <Controller
                                name="symbol"
                                control={control}
                                render={({ field }) => (
                                    <TextField
                                        {...field}
                                        label="Symbol"
                                        fullWidth
                                        error={!!errors.symbol}
                                        helperText={errors.symbol?.message}
                                    />
                                )}
                            />

                            <Controller
                                name="side"
                                control={control}
                                render={({ field }) => (
                                    <FormControl fullWidth error={!!errors.side}>
                                        <InputLabel>Side</InputLabel>
                                        <Select {...field} label="Side">
                                            <MenuItem value="BUY">BUY</MenuItem>
                                            <MenuItem value="SELL">SELL</MenuItem>
                                        </Select>
                                    </FormControl>
                                )}
                            />

                            <Controller
                                name="quantity"
                                control={control}
                                render={({ field: { onChange, ...field } }) => (
                                    <TextField
                                        {...field}
                                        label="Quantity"
                                        type="number"
                                        fullWidth
                                        onChange={(e) => onChange(Number(e.target.value))}
                                        error={!!errors.quantity}
                                        helperText={errors.quantity?.message}
                                    />
                                )}
                            />

                            <Controller
                                name="entryPrice"
                                control={control}
                                render={({ field: { onChange, ...field } }) => (
                                    <TextField
                                        {...field}
                                        label="Entry Price"
                                        type="number"
                                        fullWidth
                                        onChange={(e) => onChange(Number(e.target.value))}
                                        error={!!errors.entryPrice}
                                        helperText={errors.entryPrice?.message}
                                        InputProps={{
                                            startAdornment: '$',
                                        }}
                                    />
                                )}
                            />

                            <Controller
                                name="strategy"
                                control={control}
                                render={({ field }) => (
                                    <FormControl fullWidth error={!!errors.strategy}>
                                        <InputLabel>Strategy</InputLabel>
                                        <Select {...field} label="Strategy">
                                            {strategies.map((strategy) => (
                                                <MenuItem key={strategy} value={strategy}>
                                                    {strategy}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                )}
                            />
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setIsCreateDialogOpen(false)}>Cancel</Button>
                        <Button type="submit" variant="contained">
                            Create Trade
                        </Button>
                    </DialogActions>
                </form>
            </Dialog>

            {/* Trade Details Dialog */}
            <Dialog
                open={isDetailsDialogOpen}
                onClose={() => setIsDetailsDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    Trade Details
                    <IconButton
                        onClick={() => setIsDetailsDialogOpen(false)}
                        sx={{ position: 'absolute', right: 8, top: 8 }}
                    >
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <DialogContent>
                    {selectedTrade && (
                        <Grid container spacing={2} sx={{ mt: 1 }}>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Symbol
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    {selectedTrade.symbol}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Side
                                </Typography>
                                <Chip
                                    label={selectedTrade.side}
                                    color={selectedTrade.side === 'BUY' ? 'success' : 'error'}
                                />
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Quantity
                                </Typography>
                                <Typography variant="body1">{selectedTrade.quantity}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Strategy
                                </Typography>
                                <Typography variant="body1">{selectedTrade.strategy}</Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Entry Price
                                </Typography>
                                <Typography variant="body1">
                                    ${selectedTrade.entryPrice.toFixed(2)}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Exit Price
                                </Typography>
                                <Typography variant="body1">
                                    {selectedTrade.exitPrice
                                        ? `$${selectedTrade.exitPrice.toFixed(2)}`
                                        : '-'}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    P&L
                                </Typography>
                                <Typography
                                    variant="h6"
                                    color={
                                        selectedTrade.pnl && selectedTrade.pnl >= 0
                                            ? 'success.main'
                                            : 'error.main'
                                    }
                                    fontWeight={600}
                                >
                                    {selectedTrade.pnl ? `$${selectedTrade.pnl.toFixed(2)}` : '-'}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    P&L %
                                </Typography>
                                <Typography
                                    variant="h6"
                                    color={
                                        selectedTrade.pnlPercent && selectedTrade.pnlPercent >= 0
                                            ? 'success.main'
                                            : 'error.main'
                                    }
                                    fontWeight={600}
                                >
                                    {selectedTrade.pnlPercent
                                        ? `${selectedTrade.pnlPercent >= 0 ? '+' : ''}${selectedTrade.pnlPercent.toFixed(2)}%`
                                        : '-'}
                                </Typography>
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body2" color="text.secondary">
                                    Status
                                </Typography>
                                <Chip
                                    label={selectedTrade.status}
                                    color={selectedTrade.status === 'OPEN' ? 'primary' : 'default'}
                                    variant="outlined"
                                />
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Entry Date
                                </Typography>
                                <Typography variant="body1">
                                    {new Date(selectedTrade.entryDate).toLocaleString()}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="text.secondary">
                                    Exit Date
                                </Typography>
                                <Typography variant="body1">
                                    {selectedTrade.exitDate
                                        ? new Date(selectedTrade.exitDate).toLocaleString()
                                        : '-'}
                                </Typography>
                            </Grid>
                        </Grid>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setIsDetailsDialogOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}