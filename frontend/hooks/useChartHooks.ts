import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type {
    MarketDataPoint,
    BuySellPoint,
    TradingSignal,
} from '@/lib/api';

// ============================================
// Hook for fetching chart data
// ============================================

export interface UseChartDataOptions {
    ticker: string;
    startDate?: Date | null;
    endDate?: Date | null;
    autoFetch?: boolean;
}

export interface ChartData {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume: number[];
}

export interface UseChartDataReturn {
    data: ChartData | null;
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export function useChartData({
                                 ticker,
                                 startDate,
                                 endDate,
                                 autoFetch = true,
                             }: UseChartDataOptions): UseChartDataReturn {
    const [data, setData] = useState<ChartData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!ticker) {
            setData(null);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const formatDate = (date: Date | null) =>
                date?.toISOString().split('T')[0];

            const response = await api.data.getTickerData(
                ticker,
                formatDate(startDate),
                formatDate(endDate)
            );

            const chartData: ChartData = {
                dates: response.data.map((d) => d.timestamp),
                open: response.data.map((d) => d.open),
                high: response.data.map((d) => d.high),
                low: response.data.map((d) => d.low),
                close: response.data.map((d) => d.close),
                volume: response.data.map((d) => d.volume),
            };

            setData(chartData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch data');
            setData(null);
        } finally {
            setLoading(false);
        }
    }, [ticker, startDate, endDate]);

    useEffect(() => {
        if (autoFetch) {
            fetchData();
        }
    }, [fetchData, autoFetch]);

    return { data, loading, error, refetch: fetchData };
}

// ============================================
// Hook for fetching trading signals
// ============================================

export interface UseSignalsOptions {
    ticker: string;
    minStrength?: number;
    autoFetch?: boolean;
}

export interface UseSignalsReturn {
    buySignals: BuySellPoint[];
    sellSignals: BuySellPoint[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
    generateSignals: () => Promise<void>;
}

export function useSignals({
                               ticker,
                               minStrength = 10,
                               autoFetch = true,
                           }: UseSignalsOptions): UseSignalsReturn {
    const [buySignals, setBuySignals] = useState<BuySellPoint[]>([]);
    const [sellSignals, setSellSignals] = useState<BuySellPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchSignals = useCallback(async () => {
        if (!ticker) {
            setBuySignals([]);
            setSellSignals([]);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await api.signals.getBuySellPoints(ticker, minStrength);
            setBuySignals(response.buy_points);
            setSellSignals(response.sell_points);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch signals');
            setBuySignals([]);
            setSellSignals([]);
        } finally {
            setLoading(false);
        }
    }, [ticker, minStrength]);

    const generateSignals = useCallback(async () => {
        if (!ticker) return;

        setLoading(true);
        setError(null);

        try {
            await api.signals.generate({ ticker });
            await fetchSignals();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate signals');
        } finally {
            setLoading(false);
        }
    }, [ticker, fetchSignals]);

    useEffect(() => {
        if (autoFetch) {
            fetchSignals();
        }
    }, [fetchSignals, autoFetch]);

    return {
        buySignals,
        sellSignals,
        loading,
        error,
        refetch: fetchSignals,
        generateSignals,
    };
}

// ============================================
// Hook for calculating chart statistics
// ============================================

export interface ChartStats {
    currentPrice: number;
    previousPrice: number;
    priceChange: number;
    priceChangePercent: number;
    highPrice: number;
    lowPrice: number;
    avgPrice: number;
    avgVolume: number;
    totalVolume: number;
}

export function useChartStats(data: ChartData | null): ChartStats {
    if (!data || data.close.length === 0) {
        return {
            currentPrice: 0,
            previousPrice: 0,
            priceChange: 0,
            priceChangePercent: 0,
            highPrice: 0,
            lowPrice: 0,
            avgPrice: 0,
            avgVolume: 0,
            totalVolume: 0,
        };
    }

    const prices = data.close;
    const volumes = data.volume;
    const currentPrice = prices[prices.length - 1];
    const previousPrice = prices[prices.length - 2] || currentPrice;
    const priceChange = currentPrice - previousPrice;
    const priceChangePercent = (priceChange / previousPrice) * 100;

    return {
        currentPrice,
        previousPrice,
        priceChange,
        priceChangePercent,
        highPrice: Math.max(...prices),
        lowPrice: Math.min(...prices),
        avgPrice: prices.reduce((a, b) => a + b, 0) / prices.length,
        avgVolume: volumes.reduce((a, b) => a + b, 0) / volumes.length,
        totalVolume: volumes.reduce((a, b) => a + b, 0),
    };
}

// ============================================
// Hook for managing multiple tickers
// ============================================

export interface UseTickersReturn {
    tickers: string[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export function useTickers(): UseTickersReturn {
    const [tickers, setTickers] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchTickers = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.data.getTickers();
            setTickers(response.tickers);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch tickers');
            setTickers([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTickers();
    }, [fetchTickers]);

    return { tickers, loading, error, refetch: fetchTickers };
}

// ============================================
// Hook for latest price updates
// ============================================

export interface UseLatestPriceOptions {
    symbol: string;
    interval?: number; // milliseconds
    enabled?: boolean;
}

export interface UseLatestPriceReturn {
    price: number | null;
    loading: boolean;
    error: string | null;
}

export function useLatestPrice({
                                   symbol,
                                   interval = 60000, // 1 minute default
                                   enabled = true,
                               }: UseLatestPriceOptions): UseLatestPriceReturn {
    const [price, setPrice] = useState<number | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!enabled || !symbol) return;

        const fetchPrice = async () => {
            try {
                setLoading(true);
                const response = await api.marketData.getLatestPrice(symbol);
                setPrice(response.price);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch price');
            } finally {
                setLoading(false);
            }
        };

        // Fetch immediately
        fetchPrice();

        // Set up interval
        const intervalId = setInterval(fetchPrice, interval);

        return () => clearInterval(intervalId);
    }, [symbol, interval, enabled]);

    return { price, loading, error };
}

export default {
    useChartData,
    useSignals,
    useChartStats,
    useTickers,
    useLatestPrice,
};