'use client';

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  CircularProgress,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridRenderCellParams,
  GridToolbar,
} from '@mui/x-data-grid';
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api, { PositionInfo } from '@/lib/api';

// ==========================================
// Validation Schemas
// ==========================================

const closePositionSchema = z.object({
  price: z.number().positive('Price must be positive'),
});

type ClosePositionFormData = z.infer<typeof closePositionSchema>;

const updatePositionSchema = z.object({
  quantity_change: z.number().refine(val => val !== 0, {
    message: 'Quantity change cannot be zero',
  }),
  price: z.number().positive('Price must be positive'),
});

type UpdatePositionFormData = z.infer<typeof updatePositionSchema>;

// ==========================================
// Helper Functions
// ==========================================

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
};

const formatNumber = (value: number, decimals: number = 2): string => {
  return value.toFixed(decimals);
};

// ==========================================
// Close Position Dialog
// ==========================================

interface ClosePositionDialogProps {
  open: boolean;
  position: PositionInfo | null;
  onClose: () => void;
  onSuccess: () => void;
}

const ClosePositionDialog: React.FC<ClosePositionDialogProps> = ({
  open,
  position,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ClosePositionFormData>({
    resolver: zodResolver(closePositionSchema),
    defaultValues: {
      price: position?.current_price || 0,
    },
  });

  const closeMutation = useMutation({
    mutationFn: (data: ClosePositionFormData) =>
      api.positions.close(position!.symbol, data.price),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      reset();
      onSuccess();
      onClose();
    },
  });

  const onSubmit = (data: ClosePositionFormData) => {
    closeMutation.mutate(data);
  };

  React.useEffect(() => {
    if (position) {
      reset({ price: position.current_price });
    }
  }, [position, reset]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Close Position: {position?.symbol}
      </DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Stack spacing={2}>
            {closeMutation.isError && (
              <Alert severity="error">
                {closeMutation.error instanceof Error
                  ? closeMutation.error.message
                  : 'Failed to close position'}
              </Alert>
            )}

            {position && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Current Position
                </Typography>
                <Typography variant="body1">
                  Quantity: {formatNumber(position.quantity, 0)} shares
                </Typography>
                <Typography variant="body1">
                  Avg Price: {formatCurrency(position.avg_price)}
                </Typography>
                <Typography variant="body1">
                  Current Price: {formatCurrency(position.current_price)}
                </Typography>
                <Typography
                  variant="body1"
                  color={position.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                >
                  Unrealized P&L: {formatCurrency(position.unrealized_pnl)} (
                  {formatPercent(position.unrealized_pnl_pct)})
                </Typography>
              </Box>
            )}

            <Controller
              name="price"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Exit Price"
                  type="number"
                  fullWidth
                  required
                  error={!!errors.price}
                  helperText={errors.price?.message}
                  inputProps={{ step: 0.01 }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value))}
                />
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            color="error"
            disabled={closeMutation.isPending}
          >
            {closeMutation.isPending ? 'Closing...' : 'Close Position'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

// ==========================================
// Update Position Dialog
// ==========================================

interface UpdatePositionDialogProps {
  open: boolean;
  position: PositionInfo | null;
  onClose: () => void;
  onSuccess: () => void;
}

const UpdatePositionDialog: React.FC<UpdatePositionDialogProps> = ({
  open,
  position,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UpdatePositionFormData>({
    resolver: zodResolver(updatePositionSchema),
    defaultValues: {
      quantity_change: 0,
      price: position?.current_price || 0,
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: UpdatePositionFormData) =>
      api.positions.update({
        symbol: position!.symbol,
        quantity_change: data.quantity_change,
        price: data.price,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      reset();
      onSuccess();
      onClose();
    },
  });

  const onSubmit = (data: UpdatePositionFormData) => {
    updateMutation.mutate(data);
  };

  React.useEffect(() => {
    if (position) {
      reset({ quantity_change: 0, price: position.current_price });
    }
  }, [position, reset]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Update Position: {position?.symbol}
      </DialogTitle>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Stack spacing={2}>
            {updateMutation.isError && (
              <Alert severity="error">
                {updateMutation.error instanceof Error
                  ? updateMutation.error.message
                  : 'Failed to update position'}
              </Alert>
            )}

            {position && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Current Position
                </Typography>
                <Typography variant="body1">
                  Quantity: {formatNumber(position.quantity, 0)} shares
                </Typography>
                <Typography variant="body1">
                  Avg Price: {formatCurrency(position.avg_price)}
                </Typography>
              </Box>
            )}

            <Controller
              name="quantity_change"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Quantity Change"
                  type="number"
                  fullWidth
                  required
                  error={!!errors.quantity_change}
                  helperText={
                    errors.quantity_change?.message ||
                    'Positive to add shares, negative to reduce shares'
                  }
                  inputProps={{ step: 1 }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value))}
                />
              )}
            />

            <Controller
              name="price"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Transaction Price"
                  type="number"
                  fullWidth
                  required
                  error={!!errors.price}
                  helperText={errors.price?.message}
                  inputProps={{ step: 0.01 }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value))}
                />
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Updating...' : 'Update Position'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

// ==========================================
// Main Positions Page Component
// ==========================================

const PositionsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedPosition, setSelectedPosition] = useState<PositionInfo | null>(null);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);

  // Fetch positions
  const {
    data: positionsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['positions'],
    queryFn: () => api.positions.getAll(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const positions = positionsData?.positions || [];

  // Calculate summary metrics
  const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
  const totalPnL = positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);
  const totalPnLPct = totalValue > 0 ? (totalPnL / (totalValue - totalPnL)) * 100 : 0;

  // Define table columns
  const columns: GridColDef<PositionInfo>[] = [
    {
      field: 'symbol',
      headerName: 'Symbol',
      width: 120,
      renderCell: (params: GridRenderCellParams<PositionInfo>) => (
        <Typography variant="body2" fontWeight="600">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'quantity',
      headerName: 'Quantity',
      width: 120,
      type: 'number',
      valueFormatter: (value) => formatNumber(value, 0),
    },
    {
      field: 'avg_price',
      headerName: 'Avg Price',
      width: 120,
      type: 'number',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'current_price',
      headerName: 'Current Price',
      width: 130,
      type: 'number',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'market_value',
      headerName: 'Market Value',
      width: 140,
      type: 'number',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'unrealized_pnl',
      headerName: 'Unrealized P&L',
      width: 150,
      type: 'number',
      renderCell: (params: GridRenderCellParams<PositionInfo>) => {
        const value = params.value as number;
        const isPositive = value >= 0;
        return (
          <Box display="flex" alignItems="center" gap={0.5}>
            {isPositive ? (
              <TrendingUpIcon fontSize="small" color="success" />
            ) : (
              <TrendingDownIcon fontSize="small" color="error" />
            )}
            <Typography
              variant="body2"
              color={isPositive ? 'success.main' : 'error.main'}
              fontWeight="600"
            >
              {formatCurrency(value)}
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'unrealized_pnl_pct',
      headerName: 'P&L %',
      width: 120,
      type: 'number',
      renderCell: (params: GridRenderCellParams<PositionInfo>) => {
        const value = params.value as number;
        const isPositive = value >= 0;
        return (
          <Chip
            label={formatPercent(value)}
            color={isPositive ? 'success' : 'error'}
            size="small"
            variant="outlined"
          />
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 180,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams<PositionInfo>) => (
        <Stack direction="row" spacing={1}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => {
              setSelectedPosition(params.row);
              setUpdateDialogOpen(true);
            }}
          >
            Update
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => {
              setSelectedPosition(params.row);
              setCloseDialogOpen(true);
            }}
          >
            Close
          </Button>
        </Stack>
      ),
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Page Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="600">
          Positions
        </Typography>
        <Tooltip title={isLoading ? 'Loading...' : 'Refresh positions'}>
          <span>
            <IconButton onClick={() => refetch()} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {/* Summary Cards */}
      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={2} mb={3}>
        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Positions
            </Typography>
            <Typography variant="h5" fontWeight="600">
              {positions.length}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Market Value
            </Typography>
            <Typography variant="h5" fontWeight="600">
              {formatCurrency(totalValue)}
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Unrealized P&L
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography
                variant="h5"
                fontWeight="600"
                color={totalPnL >= 0 ? 'success.main' : 'error.main'}
              >
                {formatCurrency(totalPnL)}
              </Typography>
              <Chip
                label={formatPercent(totalPnLPct)}
                color={totalPnL >= 0 ? 'success' : 'error'}
                size="small"
              />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Positions Table */}
      <Card>
        <CardContent>
          {isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error instanceof Error ? error.message : 'Failed to load positions'}
            </Alert>
          )}

          {isLoading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
              <CircularProgress />
            </Box>
          ) : positions.length === 0 ? (
            <Box
              display="flex"
              flexDirection="column"
              justifyContent="center"
              alignItems="center"
              minHeight={400}
            >
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Open Positions
              </Typography>
              <Typography variant="body2" color="text.secondary">
                You don't have any open positions at the moment.
              </Typography>
            </Box>
          ) : (
            <DataGrid
              rows={positions}
              columns={columns}
              getRowId={(row) => row.symbol}
              initialState={{
                pagination: { paginationModel: { pageSize: 10 } },
                sorting: {
                  sortModel: [{ field: 'market_value', sort: 'desc' }],
                },
              }}
              pageSizeOptions={[5, 10, 25, 50]}
              disableRowSelectionOnClick
              slots={{ toolbar: GridToolbar }}
              slotProps={{
                toolbar: {
                  showQuickFilter: true,
                  quickFilterProps: { debounceMs: 500 },
                },
              }}
              sx={{
                minHeight: 400,
                '& .MuiDataGrid-cell:focus': {
                  outline: 'none',
                },
                '& .MuiDataGrid-row:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      <ClosePositionDialog
        open={closeDialogOpen}
        position={selectedPosition}
        onClose={() => {
          setCloseDialogOpen(false);
          setSelectedPosition(null);
        }}
        onSuccess={() => {
          // Optional: Show success message
        }}
      />

      <UpdatePositionDialog
        open={updateDialogOpen}
        position={selectedPosition}
        onClose={() => {
          setUpdateDialogOpen(false);
          setSelectedPosition(null);
        }}
        onSuccess={() => {
          // Optional: Show success message
        }}
      />
    </Box>
  );
};

export default PositionsPage;