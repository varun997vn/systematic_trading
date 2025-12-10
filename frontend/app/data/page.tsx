'use client';

import { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    TextField,
    Grid,
    Card,
    CardContent,
    IconButton,
    Chip,
    LinearProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Alert,
    MenuItem,
    Autocomplete,
} from '@mui/material';
import {
    Delete as DeleteIcon,
    Download as DownloadIcon,
    Storage as StorageIcon,
    TrendingUp as TrendingUpIcon,
    Refresh as RefreshIcon,
    Info as InfoIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Types
interface TickerData {
    id: string;
    symbol: string;
    name: string;
    startDate: string;
    endDate: string;
    recordCount: number;
    lastUpdated: string;
    sizeKB: number;
    status: 'active' | 'stale' | 'error';
}

interface StorageStats {
    totalSizeKB: number;
    tickerCount: number;
    totalRecords: number;
}

// Popular tickers for autocomplete
const POPULAR_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
    'V', 'WMT', 'PG', 'JNJ', 'MA', 'HD', 'BAC', 'XOM', 'DIS', 'CSCO',
    'SPY', 'QQQ', 'IWM', 'DIA'
];

// API functions (you'll need to implement these)
const fetchTickerData = async (): Promise<TickerData[]> => {
    const response = await fetch('/api/data/tickers');
    if (!response.ok) throw new Error('Failed to fetch ticker data');
    return response.json();
};

const fetchStorageStats = async (): Promise<StorageStats> => {
    const response = await fetch('/api/data/storage-stats');
    if (!response.ok) throw new Error('Failed to fetch storage stats');
    return response.json();
};

const downloadTickerData = async (params: {
    symbol: string;
    startDate: Date;
    endDate: Date;
    interval: string;
}) => {
    const response = await fetch('/api/data/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Failed to download data');
    return response.json();
};

const deleteTickerData = async (id: string) => {
    const response = await fetch(`/api/data/tickers/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete ticker data');
    return response.json();
};

export default function DataPage() {
    const queryClient = useQueryClient();
    const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [selectedTicker, setSelectedTicker] = useState<TickerData | null>(null);

    // Download form state
    const [symbol, setSymbol] = useState('');
    const [startDate, setStartDate] = useState<Date | null>(
        new Date(new Date().setFullYear(new Date().getFullYear() - 1))
    );
    const [endDate, setEndDate] = useState<Date | null>(new Date());
    const [interval, setInterval] = useState('1d');

    // Queries
    const { data: tickers = [], isLoading: tickersLoading, refetch: refetchTickers } = useQuery({
        queryKey: ['tickers'],
        queryFn: fetchTickerData,
    });

    const { data: storageStats, isLoading: statsLoading } = useQuery({
        queryKey: ['storageStats'],
        queryFn: fetchStorageStats,
    });

    // Mutations
    const downloadMutation = useMutation({
        mutationFn: downloadTickerData,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tickers'] });
            queryClient.invalidateQueries({ queryKey: ['storageStats'] });
            setDownloadDialogOpen(false);
            setSymbol('');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: deleteTickerData,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tickers'] });
            queryClient.invalidateQueries({ queryKey: ['storageStats'] });
            setDeleteDialogOpen(false);
            setSelectedTicker(null);
        },
    });

    // Handlers
    const handleDownload = () => {
        if (!symbol || !startDate || !endDate) return;
        downloadMutation.mutate({ symbol, startDate, endDate, interval });
    };

    const handleDeleteClick = (ticker: TickerData) => {
        setSelectedTicker(ticker);
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = () => {
        if (selectedTicker) {
            deleteMutation.mutate(selectedTicker.id);
        }
    };

    const formatBytes = (kb: number) => {
        if (kb < 1024) return `${kb.toFixed(2)} KB`;
        return `${(kb / 1024).toFixed(2)} MB`;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    // DataGrid columns
    const columns: GridColDef[] = [
        {
            field: 'symbol',
            headerName: 'Symbol',
            width: 120,
            renderCell: (params) => (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon sx={{ fontSize: 20, color: 'primary.main' }} />
                    <Typography variant="body2" fontWeight={600}>
                        {params.value}
                    </Typography>
                </Box>
            ),
        },
        {
            field: 'name',
            headerName: 'Name',
            width: 200,
            flex: 1,
        },
        {
            field: 'dateRange',
            headerName: 'Date Range',
            width: 220,
            valueGetter: (params, row) => `${formatDate(row.startDate)} - ${formatDate(row.endDate)}`,
        },
        {
            field: 'recordCount',
            headerName: 'Records',
            width: 120,
            align: 'right',
            headerAlign: 'right',
            valueFormatter: (params) => params.toLocaleString(),
        },
        {
            field: 'sizeKB',
            headerName: 'Size',
            width: 120,
            align: 'right',
            headerAlign: 'right',
            valueFormatter: (params) => formatBytes(params),
        },
        {
            field: 'status',
            headerName: 'Status',
            width: 120,
            renderCell: (params) => (
                <Chip
                    label={params.value}
                    size="small"
                    color={
                        params.value === 'active'
                            ? 'success'
                            : params.value === 'stale'
                            ? 'warning'
                            : 'error'
                    }
                />
            ),
        },
        {
            field: 'lastUpdated',
            headerName: 'Last Updated',
            width: 150,
            valueFormatter: (params) => formatDate(params),
        },
        {
            field: 'actions',
            type: 'actions',
            headerName: 'Actions',
            width: 100,
            getActions: (params) => [
                <GridActionsCellItem
                    key="delete"
                    icon={<DeleteIcon />}
                    label="Delete"
                    onClick={() => handleDeleteClick(params.row)}
                    showInMenu
                />,
            ],
        },
    ];

    const storagePercentage = storageStats
        ? Math.min((storageStats.totalSizeKB / (1024 * 1024)) * 100, 100)
        : 0;

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                        <Typography variant="h4" fontWeight={700} gutterBottom>
                            Market Data Management
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Download, manage, and monitor your historical market data
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={() => refetchTickers()}
                        >
                            Refresh
                        </Button>
                        <Button
                            variant="contained"
                            startIcon={<DownloadIcon />}
                            onClick={() => setDownloadDialogOpen(true)}
                        >
                            Download Data
                        </Button>
                    </Box>
                </Box>

                {/* Storage Stats Cards */}
                <Grid container spacing={3}>
                    <Grid item xs={12} md={4}>
                        <Card elevation={2}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                    <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="body2" color="text.secondary">
                                            Total Storage
                                        </Typography>
                                        <Typography variant="h5" fontWeight={700}>
                                            {storageStats
                                                ? formatBytes(storageStats.totalSizeKB)
                                                : '0 KB'}
                                        </Typography>
                                    </Box>
                                </Box>
                                <LinearProgress
                                    variant="determinate"
                                    value={storagePercentage}
                                    sx={{ height: 8, borderRadius: 1 }}
                                />
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                    {storagePercentage.toFixed(1)}% of 1 GB used
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card elevation={2}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main' }} />
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Tickers Stored
                                        </Typography>
                                        <Typography variant="h5" fontWeight={700}>
                                            {storageStats?.tickerCount ?? 0}
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card elevation={2}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <InfoIcon sx={{ fontSize: 40, color: 'info.main' }} />
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Total Records
                                        </Typography>
                                        <Typography variant="h5" fontWeight={700}>
                                            {storageStats?.totalRecords.toLocaleString() ?? 0}
                                        </Typography>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Data Table */}
                <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <DataGrid
                        rows={tickers}
                        columns={columns}
                        loading={tickersLoading}
                        pageSizeOptions={[10, 25, 50]}
                        initialState={{
                            pagination: { paginationModel: { pageSize: 10 } },
                        }}
                        disableRowSelectionOnClick
                        sx={{
                            border: 'none',
                            '& .MuiDataGrid-cell:focus': {
                                outline: 'none',
                            },
                        }}
                    />
                </Paper>

                {/* Download Dialog */}
                <Dialog
                    open={downloadDialogOpen}
                    onClose={() => setDownloadDialogOpen(false)}
                    maxWidth="sm"
                    fullWidth
                >
                    <DialogTitle>Download Market Data</DialogTitle>
                    <DialogContent>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
                            <Autocomplete
                                freeSolo
                                options={POPULAR_TICKERS}
                                value={symbol}
                                onInputChange={(_, newValue) => setSymbol(newValue.toUpperCase())}
                                renderInput={(params) => (
                                    <TextField
                                        {...params}
                                        label="Ticker Symbol"
                                        placeholder="Enter symbol (e.g., AAPL)"
                                        required
                                    />
                                )}
                            />

                            <DatePicker
                                label="Start Date"
                                value={startDate}
                                onChange={(date) => setStartDate(date)}
                                slotProps={{ textField: { fullWidth: true } }}
                            />

                            <DatePicker
                                label="End Date"
                                value={endDate}
                                onChange={(date) => setEndDate(date)}
                                slotProps={{ textField: { fullWidth: true } }}
                            />

                            <TextField
                                select
                                label="Interval"
                                value={interval}
                                onChange={(e) => setInterval(e.target.value)}
                                fullWidth
                            >
                                <MenuItem value="1m">1 Minute</MenuItem>
                                <MenuItem value="5m">5 Minutes</MenuItem>
                                <MenuItem value="15m">15 Minutes</MenuItem>
                                <MenuItem value="1h">1 Hour</MenuItem>
                                <MenuItem value="1d">1 Day</MenuItem>
                                <MenuItem value="1wk">1 Week</MenuItem>
                            </TextField>

                            {downloadMutation.isError && (
                                <Alert severity="error">
                                    {downloadMutation.error?.message || 'Failed to download data'}
                                </Alert>
                            )}
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setDownloadDialogOpen(false)}>Cancel</Button>
                        <Button
                            variant="contained"
                            onClick={handleDownload}
                            disabled={!symbol || !startDate || !endDate || downloadMutation.isPending}
                            startIcon={downloadMutation.isPending ? <RefreshIcon /> : <DownloadIcon />}
                        >
                            {downloadMutation.isPending ? 'Downloading...' : 'Download'}
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Delete Confirmation Dialog */}
                <Dialog
                    open={deleteDialogOpen}
                    onClose={() => setDeleteDialogOpen(false)}
                >
                    <DialogTitle>Delete Ticker Data</DialogTitle>
                    <DialogContent>
                        <Typography>
                            Are you sure you want to delete all data for{' '}
                            <strong>{selectedTicker?.symbol}</strong>? This action cannot be undone.
                        </Typography>
                        {deleteMutation.isError && (
                            <Alert severity="error" sx={{ mt: 2 }}>
                                {deleteMutation.error?.message || 'Failed to delete data'}
                            </Alert>
                            )}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                        <Button
                            variant="contained"
                            color="error"
                            onClick={handleDeleteConfirm}
                            disabled={deleteMutation.isPending}
                        >
                            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </LocalizationProvider>
    );
}