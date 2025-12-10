'use client';

import {useEffect, useState} from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Collapse,
} from '@mui/material';
import {
    AccessTime as AccessTimeIcon,
    FiberManualRecord as DotIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

interface MarketStatusResponse {
    // Your existing market status type
    isOpen?: boolean;
    nextOpen?: string;
    nextClose?: string;
}

interface GlobalMarket {
    name: string;
    region: string;
    timezone: string;
    openTime: string; // HH:MM format in local time
    closeTime: string; // HH:MM format in local time
    daysOpen: number[]; // 0-6, Sunday = 0
    symbol: string; // Exchange symbol
}

interface MarketStatusProps {
    status: MarketStatusResponse | null;
}

const GLOBAL_MARKETS: GlobalMarket[] = [
    {
        name: 'New York Stock Exchange',
        region: 'United States',
        timezone: 'America/New_York',
        openTime: '09:30',
        closeTime: '16:00',
        daysOpen: [1, 2, 3, 4, 5], // Monday to Friday
        symbol: 'NYSE',
    },
    {
        name: 'NASDAQ',
        region: 'United States',
        timezone: 'America/New_York',
        openTime: '09:30',
        closeTime: '16:00',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'NASDAQ',
    },
    {
        name: 'London Stock Exchange',
        region: 'United Kingdom',
        timezone: 'Europe/London',
        openTime: '08:00',
        closeTime: '16:30',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'LSE',
    },
    {
        name: 'Tokyo Stock Exchange',
        region: 'Japan',
        timezone: 'Asia/Tokyo',
        openTime: '09:00',
        closeTime: '15:00',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'TSE',
    },
    {
        name: 'Hong Kong Stock Exchange',
        region: 'Hong Kong',
        timezone: 'Asia/Hong_Kong',
        openTime: '09:30',
        closeTime: '16:00',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'HKEX',
    },
    {
        name: 'Shanghai Stock Exchange',
        region: 'China',
        timezone: 'Asia/Shanghai',
        openTime: '09:30',
        closeTime: '15:00',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'SSE',
    },
    {
        name: 'Frankfurt Stock Exchange',
        region: 'Germany',
        timezone: 'Europe/Berlin',
        openTime: '09:00',
        closeTime: '17:30',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'FRA',
    },
    {
        name: 'Singapore Exchange',
        region: 'Singapore',
        timezone: 'Asia/Singapore',
        openTime: '09:00',
        closeTime: '17:00',
        daysOpen: [1, 2, 3, 4, 5],
        symbol: 'SGX',
    },
];

interface MarketInfo {
    market: GlobalMarket;
    isOpen: boolean;
    nextChange: Date;
    nextChangeType: 'open' | 'close';
    localTime: Date;
}

function getMarketInfo(market: GlobalMarket): MarketInfo {
    const now = new Date();
    const localTime = new Date(now.toLocaleString('en-US', {timeZone: market.timezone}));

    const currentDay = localTime.getDay();
    const currentTime = localTime.getHours() * 60 + localTime.getMinutes();

    const [openHour, openMin] = market.openTime.split(':').map(Number);
    const [closeHour, closeMin] = market.closeTime.split(':').map(Number);
    const openMinutes = openHour * 60 + openMin;
    const closeMinutes = closeHour * 60 + closeMin;

    const isMarketDay = market.daysOpen.includes(currentDay);
    const isWithinHours = currentTime >= openMinutes && currentTime < closeMinutes;
    const isOpen = isMarketDay && isWithinHours;

    // Calculate next change time
    let nextChange = new Date(localTime);
    let nextChangeType: 'open' | 'close';

    if (isOpen) {
        // Market is open, next change is close
        nextChange.setHours(closeHour, closeMin, 0, 0);
        nextChangeType = 'close';
    } else if (isMarketDay && currentTime < openMinutes) {
        // Market day but before opening
        nextChange.setHours(openHour, openMin, 0, 0);
        nextChangeType = 'open';
    } else {
        // Find next market day
        let daysToAdd = 1;
        let nextDay = (currentDay + 1) % 7;

        while (!market.daysOpen.includes(nextDay) && daysToAdd < 7) {
            daysToAdd++;
            nextDay = (currentDay + daysToAdd) % 7;
        }

        nextChange = new Date(localTime);
        nextChange.setDate(nextChange.getDate() + daysToAdd);
        nextChange.setHours(openHour, openMin, 0, 0);
        nextChangeType = 'open';
    }

    return {
        market,
        isOpen,
        nextChange,
        nextChangeType,
        localTime,
    };
}

function formatTimeUntil(date: Date): string {
    const now = new Date();
    const diff = date.getTime() - now.getTime();

    if (diff < 0) return 'Now';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours === 0) {
        return `${minutes}m`;
    } else if (hours < 24) {
        return `${hours}h ${minutes}m`;
    } else {
        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;
        return `${days}d ${remainingHours}h`;
    }
}

function formatLocalTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });
}

export default function MarketStatus({status}: MarketStatusProps) {
    const [marketInfos, setMarketInfos] = useState<MarketInfo[]>([]);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [isExpanded, setIsExpanded] = useState(false);

    useEffect(() => {
        const updateMarkets = () => {
            setCurrentTime(new Date());
            const infos = GLOBAL_MARKETS.map(getMarketInfo);
            // Sort by open markets first, then by time until next change
            infos.sort((a, b) => {
                if (a.isOpen !== b.isOpen) return a.isOpen ? -1 : 1;
                return a.nextChange.getTime() - b.nextChange.getTime();
            });
            setMarketInfos(infos);
        };

        updateMarkets();
        const interval = setInterval(updateMarkets, 1000); // Update every second

        return () => clearInterval(interval);
    }, []);

    const openMarkets = marketInfos.filter(info => info.isOpen).length;

    return (
        <Card>
            <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2} flexWrap="wrap" gap={1}>
                    <Box display="flex" alignItems="center" gap={2}>
                        <Box display="flex" alignItems="center">
                            <AccessTimeIcon sx={{mr: 1}}/>
                            <Typography variant="h6" fontWeight={600}>
                                Global Markets
                            </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{fontFamily: 'monospace'}}>
                            {formatLocalTime(currentTime)}
                        </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                            label={`${openMarkets} Open`}
                            size="small"
                            color="success"
                            variant="outlined"
                        />
                        <Chip
                            label={`${marketInfos.length - openMarkets} Closed`}
                            size="small"
                            variant="outlined"
                        />
                        <IconButton
                            size="small"
                            onClick={() => setIsExpanded(!isExpanded)}
                            sx={{ml: 1}}
                        >
                            {isExpanded ? <ExpandLessIcon/> : <ExpandMoreIcon/>}
                        </IconButton>
                    </Box>
                </Box>

                <Collapse in={!isExpanded}>
                    <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                        {marketInfos.map((info) => (
                            <Chip
                                key={info.market.symbol}
                                label={info.market.symbol}
                                size="small"
                                icon={
                                    <DotIcon
                                        sx={{
                                            fontSize: 12,
                                            color: info.isOpen ? '#10B981' : '#94A3B8'
                                        }}
                                    />
                                }
                                sx={{
                                    bgcolor: info.isOpen ? 'rgba(16, 185, 129, 0.12)' : 'rgba(148, 163, 184, 0.12)',
                                    color: info.isOpen ? '#059669' : '#475569',
                                    borderColor: info.isOpen ? '#10B981' : '#CBD5E1',
                                    border: 1,
                                    fontWeight: 600,
                                    '& .MuiChip-label': {
                                        px: 1,
                                    },
                                }}
                            />
                        ))}
                    </Box>
                </Collapse>

                <Collapse in={isExpanded}>
                    <TableContainer>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Exchange</TableCell>
                                    <TableCell>Region</TableCell>
                                    <TableCell align="center">Status</TableCell>
                                    <TableCell>Local Time</TableCell>
                                    <TableCell>Next Change</TableCell>
                                    <TableCell>Hours</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {marketInfos.map((info) => (
                                    <TableRow
                                        key={info.market.symbol}
                                        sx={{
                                            '&:hover': {bgcolor: 'action.hover'},
                                            ...(info.isOpen && {bgcolor: 'success.lighter'})
                                        }}
                                    >
                                        <TableCell>
                                            <Box display="flex" alignItems="center" gap={1}>
                                                <DotIcon
                                                    sx={{
                                                        fontSize: 12,
                                                        color: info.isOpen ? 'success.main' : 'text.disabled'
                                                    }}
                                                />
                                                <Typography variant="body2" fontWeight={600}>
                                                    {info.market.symbol}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" color="text.secondary">
                                                {info.market.region}
                                            </Typography>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Chip
                                                label={info.isOpen ? 'Open' : 'Closed'}
                                                size="small"
                                                color={info.isOpen ? 'success' : 'default'}
                                                sx={{
                                                    minWidth: 70,
                                                    height: 24,
                                                    fontSize: '0.75rem'
                                                }}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" sx={{fontFamily: 'monospace'}}>
                                                {formatLocalTime(info.localTime)}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" color="primary" fontWeight={500}>
                                                {info.nextChangeType === 'open' ? 'Opens' : 'Closes'} in {formatTimeUntil(info.nextChange)}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                at {formatLocalTime(info.nextChange)}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="caption" color="text.secondary">
                                                {info.market.openTime} - {info.market.closeTime}
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Collapse>
            </CardContent>
        </Card>
    );
}