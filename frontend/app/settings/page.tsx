'use client';

import {useState} from 'react';
import {
    Box,
    Paper,
    Typography,
    TextField,
    Button,
    Switch,
    FormControlLabel,
    Alert,
    Divider,
    Grid,
    Card,
    CardContent,
    CircularProgress,
    Chip,
    IconButton,
    InputAdornment,
    Tooltip,
    Stack,
} from '@mui/material';
import {
    Save as SaveIcon,
    Refresh as RefreshIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Visibility,
    VisibilityOff,
    AccountBalance as BrokerIcon,
    AttachMoney as CashIcon,
    Settings as SettingsIcon,
    HealthAndSafety as HealthIcon,
} from '@mui/icons-material';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {useForm, Controller} from 'react-hook-form';
import {zodResolver} from '@hookform/resolvers/zod';
import {z} from 'zod';
import api from '@/lib/api';

// ==========================================
// Validation Schemas
// ==========================================

const brokerConfigSchema = z.object({
    broker_name: z.string().min(1, 'Broker name is required'),
    api_key: z.string().min(1, 'API key is required'),
    api_secret: z.string().min(1, 'API secret is required'),
    is_paper: z.boolean(),
});

const cashBalanceSchema = z.object({
    cash_balance: z.number().min(0, 'Cash balance must be positive'),
});

type BrokerConfigForm = z.infer<typeof brokerConfigSchema>;
type CashBalanceForm = z.infer<typeof cashBalanceSchema>;

// ==========================================
// Settings Page Component
// ==========================================

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const [showApiKey, setShowApiKey] = useState(false);
    const [showApiSecret, setShowApiSecret] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // ==========================================
    // Queries
    // ==========================================

    const {data: config, isLoading: configLoading} = useQuery({
        queryKey: ['config'],
        queryFn: api.config.get,
    });

    const {data: health, isLoading: healthLoading, refetch: refetchHealth} = useQuery({
        queryKey: ['health'],
        queryFn: api.health,
        refetchInterval: 30000, // Refetch every 30 seconds
    });

    // ==========================================
    // Forms
    // ==========================================

    const {
        control: brokerControl,
        handleSubmit: handleBrokerSubmit,
        formState: {errors: brokerErrors},
        reset: resetBrokerForm,
    } = useForm<BrokerConfigForm>({
        resolver: zodResolver(brokerConfigSchema),
        defaultValues: {
            broker_name: config?.broker_name || '',
            api_key: '',
            api_secret: '',
            is_paper: config?.is_paper ?? true,
        },
    });

    const {
        control: cashControl,
        handleSubmit: handleCashSubmit,
        formState: {errors: cashErrors},
        reset: resetCashForm,
    } = useForm<CashBalanceForm>({
        resolver: zodResolver(cashBalanceSchema),
        defaultValues: {
            cash_balance: config?.cash_balance || 0,
        },
    });

    // Update form defaults when config loads
    useState(() => {
        if (config) {
            resetBrokerForm({
                broker_name: config.broker_name,
                api_key: '',
                api_secret: '',
                is_paper: config.is_paper,
            });
            resetCashForm({
                cash_balance: config.cash_balance,
            });
        }
    });

    // ==========================================
    // Mutations
    // ==========================================

    const brokerMutation = useMutation({
        mutationFn: api.config.updateBroker,
        onSuccess: (data) => {
            queryClient.invalidateQueries({queryKey: ['config']});
            setSuccessMessage(`Broker configuration updated: ${data.broker_name} (${data.is_paper ? 'Paper' : 'Live'} trading)`);
            setErrorMessage(null);
            setTimeout(() => setSuccessMessage(null), 5000);
        },
        onError: (error: Error) => {
            setErrorMessage(`Failed to update broker configuration: ${error.message}`);
            setSuccessMessage(null);
        },
    });

    const cashMutation = useMutation({
        mutationFn: (cashBalance: number) => api.config.updateCash(cashBalance),
        onSuccess: (data) => {
            queryClient.invalidateQueries({queryKey: ['config']});
            queryClient.invalidateQueries({queryKey: ['portfolio']});
            setSuccessMessage(`Cash balance updated: $${data.cash_balance.toLocaleString()}`);
            setErrorMessage(null);
            setTimeout(() => setSuccessMessage(null), 5000);
        },
        onError: (error: Error) => {
            setErrorMessage(`Failed to update cash balance: ${error.message}`);
            setSuccessMessage(null);
        },
    });

    // ==========================================
    // Handlers
    // ==========================================

    const onBrokerSubmit = (data: BrokerConfigForm) => {
        brokerMutation.mutate(data);
    };

    const onCashSubmit = (data: CashBalanceForm) => {
        cashMutation.mutate(data.cash_balance);
    };

    const handleRefreshHealth = () => {
        refetchHealth();
    };

    // ==========================================
    // Health Status Component
    // ==========================================

    const ServiceStatus = ({name, status}: { name: string; status: boolean }) => (
        <Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1}}>
            <Typography variant="body2" color="text.secondary">
                {name}
            </Typography>
            <Chip
                size="small"
                icon={status ? <CheckCircleIcon/> : <ErrorIcon/>}
                label={status ? 'Operational' : 'Down'}
                color={status ? 'success' : 'error'}
                sx={{minWidth: 110}}
            />
        </Box>
    );

    // ==========================================
    // Render
    // ==========================================

    if (configLoading) {
        return (
            <Box sx={{display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh'}}>
                <CircularProgress/>
            </Box>
        );
    }

    return (
        <Box>
            {/* Header */}
            <Box sx={{mb: 4}}>
                <Typography variant="h4" fontWeight={700} gutterBottom>
                    Settings
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Configure your trading system, broker connection, and account settings
                </Typography>
            </Box>

            {/* Success/Error Messages */}
            {successMessage && (
                <Alert severity="success" sx={{mb: 3}} onClose={() => setSuccessMessage(null)}>
                    {successMessage}
                </Alert>
            )}

            {errorMessage && (
                <Alert severity="error" sx={{mb: 3}} onClose={() => setErrorMessage(null)}>
                    {errorMessage}
                </Alert>
            )}

            <Grid container spacing={3}>
                {/* Broker Configuration */}
                <Grid item xs={12} lg={8}>
                    <Paper sx={{p: 3}}>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 3}}>
                            <BrokerIcon sx={{mr: 1.5, color: 'primary.main'}}/>
                            <Typography variant="h6" fontWeight={600}>
                                Broker Configuration
                            </Typography>
                        </Box>

                        <form onSubmit={handleBrokerSubmit(onBrokerSubmit)}>
                            <Stack spacing={3}>
                                <Controller
                                    name="broker_name"
                                    control={brokerControl}
                                    render={({field}) => (
                                        <TextField
                                            {...field}
                                            label="Broker Name"
                                            placeholder="e.g., alpaca, interactive_brokers"
                                            error={!!brokerErrors.broker_name}
                                            helperText={brokerErrors.broker_name?.message}
                                            fullWidth
                                        />
                                    )}
                                />

                                <Controller
                                    name="api_key"
                                    control={brokerControl}
                                    render={({field}) => (
                                        <TextField
                                            {...field}
                                            label="API Key"
                                            type={showApiKey ? 'text' : 'password'}
                                            error={!!brokerErrors.api_key}
                                            helperText={brokerErrors.api_key?.message}
                                            fullWidth
                                            InputProps={{
                                                endAdornment: (
                                                    <InputAdornment position="end">
                                                        <IconButton
                                                            onClick={() => setShowApiKey(!showApiKey)}
                                                            edge="end"
                                                        >
                                                            {showApiKey ? <VisibilityOff/> : <Visibility/>}
                                                        </IconButton>
                                                    </InputAdornment>
                                                ),
                                            }}
                                        />
                                    )}
                                />

                                <Controller
                                    name="api_secret"
                                    control={brokerControl}
                                    render={({field}) => (
                                        <TextField
                                            {...field}
                                            label="API Secret"
                                            type={showApiSecret ? 'text' : 'password'}
                                            error={!!brokerErrors.api_secret}
                                            helperText={brokerErrors.api_secret?.message}
                                            fullWidth
                                            InputProps={{
                                                endAdornment: (
                                                    <InputAdornment position="end">
                                                        <IconButton
                                                            onClick={() => setShowApiSecret(!showApiSecret)}
                                                            edge="end"
                                                        >
                                                            {showApiSecret ? <VisibilityOff/> : <Visibility/>}
                                                        </IconButton>
                                                    </InputAdornment>
                                                ),
                                            }}
                                        />
                                    )}
                                />

                                <Controller
                                    name="is_paper"
                                    control={brokerControl}
                                    render={({field}) => (
                                        <FormControlLabel
                                            control={
                                                <Switch
                                                    checked={field.value}
                                                    onChange={(e) => field.onChange(e.target.checked)}
                                                    color="primary"
                                                />
                                            }
                                            label={
                                                <Box>
                                                    <Typography variant="body2" fontWeight={500}>
                                                        Paper Trading Mode
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        Enable to use simulated trading (recommended for testing)
                                                    </Typography>
                                                </Box>
                                            }
                                        />
                                    )}
                                />

                                <Box sx={{display: 'flex', gap: 2, pt: 1}}>
                                    <Button
                                        type="submit"
                                        variant="contained"
                                        startIcon={<SaveIcon/>}
                                        disabled={brokerMutation.isPending}
                                    >
                                        {brokerMutation.isPending ? 'Saving...' : 'Save Broker Config'}
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        onClick={() => resetBrokerForm()}
                                        disabled={brokerMutation.isPending}
                                    >
                                        Reset
                                    </Button>
                                </Box>
                            </Stack>
                        </form>
                    </Paper>

                    {/* Cash Balance Management */}
                    <Paper sx={{p: 3, mt: 3}}>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 3}}>
                            <CashIcon sx={{mr: 1.5, color: 'success.main'}}/>
                            <Typography variant="h6" fontWeight={600}>
                                Cash Balance Management
                            </Typography>
                        </Box>

                        <form onSubmit={handleCashSubmit(onCashSubmit)}>
                            <Stack spacing={3}>
                                <Box>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Current Cash Balance
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700} color="success.main">
                                        ${config?.cash_balance.toLocaleString(undefined, {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    })}
                                    </Typography>
                                </Box>

                                <Divider/>

                                <Controller
                                    name="cash_balance"
                                    control={cashControl}
                                    render={({field}) => (
                                        <TextField
                                            {...field}
                                            label="New Cash Balance"
                                            type="number"
                                            error={!!cashErrors.cash_balance}
                                            helperText={cashErrors.cash_balance?.message || 'Update your available cash balance'}
                                            fullWidth
                                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                                            InputProps={{
                                                startAdornment: <InputAdornment position="start">$</InputAdornment>,
                                            }}
                                        />
                                    )}
                                />

                                <Box sx={{display: 'flex', gap: 2}}>
                                    <Button
                                        type="submit"
                                        variant="contained"
                                        startIcon={<SaveIcon/>}
                                        disabled={cashMutation.isPending}
                                    >
                                        {cashMutation.isPending ? 'Updating...' : 'Update Cash Balance'}
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        onClick={() => resetCashForm()}
                                        disabled={cashMutation.isPending}
                                    >
                                        Reset
                                    </Button>
                                </Box>
                            </Stack>
                        </form>
                    </Paper>
                </Grid>

                {/* System Health & Info */}
                <Grid item xs={12} lg={4}>
                    {/* System Health */}
                    <Paper sx={{p: 3, mb: 3}}>
                        <Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2}}>
                            <Box sx={{display: 'flex', alignItems: 'center'}}>
                                <HealthIcon sx={{mr: 1.5, color: 'info.main'}}/>
                                <Typography variant="h6" fontWeight={600}>
                                    System Health
                                </Typography>
                            </Box>
                            <Tooltip title="Refresh health status">
                                <IconButton onClick={handleRefreshHealth} size="small">
                                    <RefreshIcon/>
                                </IconButton>
                            </Tooltip>
                        </Box>

                        {healthLoading ? (
                            <Box sx={{display: 'flex', justifyContent: 'center', py: 3}}>
                                <CircularProgress size={24}/>
                            </Box>
                        ) : health ? (
                            <Stack spacing={2}>
                                <Box>
                                    <Typography variant="caption" color="text.secondary" gutterBottom>
                                        Overall Status
                                    </Typography>
                                    <Chip
                                        label={health.status.toUpperCase()}
                                        color={health.status === 'healthy' ? 'success' : 'error'}
                                        sx={{fontWeight: 600}}
                                    />
                                </Box>

                                <Divider/>

                                <Box>
                                    <Typography variant="caption" color="text.secondary" gutterBottom>
                                        Services
                                    </Typography>
                                    <ServiceStatus name="Data Manager" status={health.services.data_manager}/>
                                    <ServiceStatus name="Trader" status={health.services.trader}/>
                                    <ServiceStatus name="Database" status={health.services.database}/>
                                </Box>

                                <Divider/>

                                <Box>
                                    <Typography variant="caption" color="text.secondary">
                                        Last Updated
                                    </Typography>
                                    <Typography variant="body2">
                                        {new Date(health.timestamp).toLocaleString()}
                                    </Typography>
                                </Box>
                            </Stack>
                        ) : (
                            <Alert severity="warning">Failed to load health status</Alert>
                        )}
                    </Paper>

                    {/* Account Information */}
                    <Paper sx={{p: 3}}>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 2}}>
                            <SettingsIcon sx={{mr: 1.5, color: 'primary.main'}}/>
                            <Typography variant="h6" fontWeight={600}>
                                Account Info
                            </Typography>
                        </Box>

                        <Stack spacing={2}>
                            <Box>
                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                    Initial Capital
                                </Typography>
                                <Typography variant="h6" fontWeight={600}>
                                    ${config?.initial_capital.toLocaleString(undefined, {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                })}
                                </Typography>
                            </Box>

                            <Divider/>

                            <Box>
                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                    Broker
                                </Typography>
                                <Typography variant="body1" fontWeight={500}>
                                    {config?.broker_name || 'Not configured'}
                                </Typography>
                            </Box>

                            <Box>
                                <Typography variant="caption" color="text.secondary" gutterBottom>
                                    Trading Mode
                                </Typography>
                                <Chip
                                    label={config?.is_paper ? 'Paper Trading' : 'Live Trading'}
                                    color={config?.is_paper ? 'info' : 'warning'}
                                    size="small"
                                />
                            </Box>
                        </Stack>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}