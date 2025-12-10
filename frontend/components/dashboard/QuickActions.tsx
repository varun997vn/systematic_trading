'use client';

import {
    Card,
    CardContent,
    Typography,
    Button,
    Box,
    Stack,
} from '@mui/material';
import {
    Add as AddIcon,
    Refresh as RefreshIcon,
    ShowChart as ChartIcon,
    Notifications as SignalIcon,
} from '@mui/icons-material';
import {useRouter} from 'next/navigation';

interface QuickActionsProps {
    onRefresh?: () => void;
}

export default function QuickActions({onRefresh}: QuickActionsProps) {
    const router = useRouter();

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>

                    Quick Actions
                </Typography>

                <Stack spacing={1.5} mt={2}>
                    <Button
                        variant="contained"
                        fullWidth
                        startIcon={<AddIcon/>}
                        onClick={() => router.push('/trades')}
                    >
                        Create Trade
                    </Button>

                    <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<SignalIcon/>}
                        onClick={() => router.push('/signals')}
                    >
                        Generate Signals
                    </Button>

                    <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<ChartIcon/>}
                        onClick={() => router.push('/charts')}
                    >
                        View Charts
                    </Button>

                    <Box pt={1}>
                        <Button
                            variant="text"
                            fullWidth
                            startIcon={<RefreshIcon/>}
                            onClick={onRefresh}
                        >
                            Refresh Dashboard
                        </Button>
                    </Box>
                </Stack>
            </CardContent>
        </Card>
    );
}
