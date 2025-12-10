'use client';

import { useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    CardActions,
    Typography,
    Grid,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Switch,
    FormControlLabel,
    Chip,
    IconButton,
    Alert,
    CircularProgress,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Strategy type definition
interface Strategy {
    id: string;
    name: string;
    type: string;
    description: string;
    enabled: boolean;
    parameters: Record<string, any>;
    performance: {
        totalTrades: number;
        winRate: number;
        avgPnL: number;
        totalPnL: number;
    };
    createdAt: string;
    updatedAt: string;
}

// Available strategy types
const STRATEGY_TYPES = [
    { value: 'MEAN_REVERSION', label: 'Mean Reversion' },
    { value: 'MOMENTUM', label: 'Momentum' },
    { value: 'BREAKOUT', label: 'Breakout' },
    { value: 'TREND_FOLLOWING', label: 'Trend Following' },
    { value: 'CUSTOM', label: 'Custom' },
];

// Validation schema
const strategySchema = z.object({
    name: z.string().min(1, 'Name is required').max(100),
    type: z.string().min(1, 'Strategy type is required'),
    description: z.string().max(500).optional(),
    enabled: z.boolean().default(true),
    parameters: z.record(z.any()).optional(),
});

type StrategyFormData = z.infer<typeof strategySchema>;

export default function StrategiesPage() {
    const [openDialog, setOpenDialog] = useState(false);
    const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [strategyToDelete, setStrategyToDelete] = useState<string | null>(null);

    const queryClient = useQueryClient();

    // Fetch strategies
    const { data: strategies, isLoading, error } = useQuery<Strategy[]>({
        queryKey: ['strategies'],
        queryFn: async () => {
            const response = await fetch('/api/strategies');
            if (!response.ok) throw new Error('Failed to fetch strategies');
            return response.json();
        },
    });

    // Form setup
    const {
        control,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<StrategyFormData>({
        resolver: zodResolver(strategySchema),
        defaultValues: {
            name: '',
            type: '',
            description: '',
            enabled: true,
            parameters: {},
        },
    });

    // Create/Update mutation
    const saveMutation = useMutation({
        mutationFn: async (data: StrategyFormData) => {
            const url = editingStrategy
                ? `/api/strategies/${editingStrategy.id}`
                : '/api/strategies';
            const method = editingStrategy ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (!response.ok) throw new Error('Failed to save strategy');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
            handleCloseDialog();
        },
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            const response = await fetch(`/api/strategies/${id}`, {
                method: 'DELETE',
            });
            if (!response.ok) throw new Error('Failed to delete strategy');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
            setDeleteConfirmOpen(false);
            setStrategyToDelete(null);
        },
    });

    // Toggle enabled mutation
    const toggleEnabledMutation = useMutation({
        mutationFn: async ({ id, enabled }: { id: string; enabled: boolean }) => {
            const response = await fetch(`/api/strategies/${id}/toggle`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled }),
            });
            if (!response.ok) throw new Error('Failed to toggle strategy');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
        },
    });

    const handleOpenDialog = (strategy?: Strategy) => {
        if (strategy) {
            setEditingStrategy(strategy);
            reset({
                name: strategy.name,
                type: strategy.type,
                description: strategy.description,
                enabled: strategy.enabled,
                parameters: strategy.parameters,
            });
        } else {
            setEditingStrategy(null);
            reset({
                name: '',
                type: '',
                description: '',
                enabled: true,
                parameters: {},
            });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingStrategy(null);
        reset();
    };

    const onSubmit = (data: StrategyFormData) => {
        saveMutation.mutate(data);
    };

    const handleToggleEnabled = (strategy: Strategy) => {
        toggleEnabledMutation.mutate({
            id: strategy.id,
            enabled: !strategy.enabled,
        });
    };

    const handleDeleteClick = (id: string) => {
        setStrategyToDelete(id);
        setDeleteConfirmOpen(true);
    };

    const handleConfirmDelete = () => {
        if (strategyToDelete) {
            deleteMutation.mutate(strategyToDelete);
        }
    };

    if (isLoading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error">
                Error loading strategies: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
        );
    }

    return (
        <Box>
            {/* Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" fontWeight={600}>
                    Trading Strategies
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenDialog()}
                >
                    Create Strategy
                </Button>
            </Box>

            {/* Summary Stats */}
            {strategies && strategies.length > 0 && (
                <Grid container spacing={2} mb={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography color="textSecondary" gutterBottom>
                                    Total Strategies
                                </Typography>
                                <Typography variant="h4">{strategies.length}</Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography color="textSecondary" gutterBottom>
                                    Active Strategies
                                </Typography>
                                <Typography variant="h4">
                                    {strategies.filter((s) => s.enabled).length}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography color="textSecondary" gutterBottom>
                                    Total Trades
                                </Typography>
                                <Typography variant="h4">
                                    {strategies.reduce((sum, s) => sum + s.performance.totalTrades, 0)}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Typography color="textSecondary" gutterBottom>
                                    Avg Win Rate
                                </Typography>
                                <Typography variant="h4">
                                    {strategies.length > 0
                                        ? (
                                            strategies.reduce((sum, s) => sum + s.performance.winRate, 0) /
                                            strategies.length
                                        ).toFixed(1)
                                        : 0}
                                    %
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Strategy Cards */}
            {strategies && strategies.length > 0 ? (
                <Grid container spacing={3}>
                    {strategies.map((strategy) => (
                        <Grid item xs={12} md={6} lg={4} key={strategy.id}>
                            <Card>
                                <CardContent>
                                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                                        <Box>
                                            <Typography variant="h6" fontWeight={600}>
                                                {strategy.name}
                                            </Typography>
                                            <Chip
                                                label={
                                                    STRATEGY_TYPES.find((t) => t.value === strategy.type)?.label ||
                                                    strategy.type
                                                }
                                                size="small"
                                                sx={{ mt: 0.5 }}
                                            />
                                        </Box>
                                        <Chip
                                            label={strategy.enabled ? 'Active' : 'Disabled'}
                                            color={strategy.enabled ? 'success' : 'default'}
                                            size="small"
                                        />
                                    </Box>

                                    {strategy.description && (
                                        <Typography variant="body2" color="textSecondary" mb={2}>
                                            {strategy.description}
                                        </Typography>
                                    )}

                                    <Box mb={2}>
                                        <Grid container spacing={1}>
                                            <Grid item xs={6}>
                                                <Typography variant="caption" color="textSecondary">
                                                    Total Trades
                                                </Typography>
                                                <Typography variant="body2" fontWeight={600}>
                                                    {strategy.performance.totalTrades}
                                                </Typography>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Typography variant="caption" color="textSecondary">
                                                    Win Rate
                                                </Typography>
                                                <Typography variant="body2" fontWeight={600}>
                                                    {strategy.performance.winRate.toFixed(1)}%
                                                </Typography>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Typography variant="caption" color="textSecondary">
                                                    Avg P&L
                                                </Typography>
                                                <Typography
                                                    variant="body2"
                                                    fontWeight={600}
                                                    color={strategy.performance.avgPnL >= 0 ? 'success.main' : 'error.main'}
                                                >
                                                    ${strategy.performance.avgPnL.toFixed(2)}
                                                </Typography>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Typography variant="caption" color="textSecondary">
                                                    Total P&L
                                                </Typography>
                                                <Box display="flex" alignItems="center" gap={0.5}>
                                                    <Typography
                                                        variant="body2"
                                                        fontWeight={600}
                                                        color={
                                                            strategy.performance.totalPnL >= 0 ? 'success.main' : 'error.main'
                                                        }
                                                    >
                                                        ${strategy.performance.totalPnL.toFixed(2)}
                                                    </Typography>
                                                    {strategy.performance.totalPnL >= 0 ? (
                                                        <TrendingUpIcon fontSize="small" color="success" />
                                                    ) : (
                                                        <TrendingDownIcon fontSize="small" color="error" />
                                                    )}
                                                </Box>
                                            </Grid>
                                        </Grid>
                                    </Box>

                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={strategy.enabled}
                                                onChange={() => handleToggleEnabled(strategy)}
                                                disabled={toggleEnabledMutation.isPending}
                                            />
                                        }
                                        label="Enable Strategy"
                                    />
                                </CardContent>
                                <CardActions>
                                    <Button
                                        size="small"
                                        startIcon={<EditIcon />}
                                        onClick={() => handleOpenDialog(strategy)}
                                    >
                                        Edit
                                    </Button>
                                    <IconButton
                                        size="small"
                                        color="error"
                                        onClick={() => handleDeleteClick(strategy.id)}
                                    >
                                        <DeleteIcon />
                                    </IconButton>
                                </CardActions>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <Card>
                    <CardContent>
                        <Box textAlign="center" py={6}>
                            <Typography variant="h6" color="textSecondary" gutterBottom>
                                No strategies yet
                            </Typography>
                            <Typography variant="body2" color="textSecondary" mb={3}>
                                Create your first trading strategy to get started
                            </Typography>
                            <Button
                                variant="contained"
                                startIcon={<AddIcon />}
                                onClick={() => handleOpenDialog()}
                            >
                                Create Strategy
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            )}

            {/* Create/Edit Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle>{editingStrategy ? 'Edit Strategy' : 'Create Strategy'}</DialogTitle>
                <form onSubmit={handleSubmit(onSubmit)}>
                    <DialogContent>
                        <Box display="flex" flexDirection="column" gap={2}>
                            <Controller
                                name="name"
                                control={control}
                                render={({ field }) => (
                                    <TextField
                                        {...field}
                                        label="Strategy Name"
                                        fullWidth
                                        error={!!errors.name}
                                        helperText={errors.name?.message}
                                    />
                                )}
                            />

                            <Controller
                                name="type"
                                control={control}
                                render={({ field }) => (
                                    <FormControl fullWidth error={!!errors.type}>
                                        <InputLabel>Strategy Type</InputLabel>
                                        <Select {...field} label="Strategy Type">
                                            {STRATEGY_TYPES.map((type) => (
                                                <MenuItem key={type.value} value={type.value}>
                                                    {type.label}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                        {errors.type && (
                                            <Typography variant="caption" color="error">
                                                {errors.type.message}
                                            </Typography>
                                        )}
                                    </FormControl>
                                )}
                            />

                            <Controller
                                name="description"
                                control={control}
                                render={({ field }) => (
                                    <TextField
                                        {...field}
                                        label="Description"
                                        fullWidth
                                        multiline
                                        rows={3}
                                        error={!!errors.description}
                                        helperText={errors.description?.message}
                                    />
                                )}
                            />

                            <Controller
                                name="enabled"
                                control={control}
                                render={({ field }) => (
                                    <FormControlLabel
                                        control={<Switch {...field} checked={field.value} />}
                                        label="Enable strategy immediately"
                                    />
                                )}
                            />
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseDialog}>Cancel</Button>
                        <Button
                            type="submit"
                            variant="contained"
                            disabled={saveMutation.isPending}
                        >
                            {saveMutation.isPending ? 'Saving...' : editingStrategy ? 'Update' : 'Create'}
                        </Button>
                    </DialogActions>
                </form>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
                <DialogTitle>Delete Strategy</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to delete this strategy? This action cannot be undone.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
                    <Button
                        color="error"
                        variant="contained"
                        onClick={handleConfirmDelete}
                        disabled={deleteMutation.isPending}
                    >
                        {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}