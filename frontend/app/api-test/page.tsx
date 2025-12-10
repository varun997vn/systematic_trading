/**
 * API Test Page Component
 * Interactive UI to test all backend API endpoints from Next.js
 *
 * Usage: Add this to your Next.js app at pages/api-test.tsx or app/api-test/page.tsx
 */

'use client'; // For Next.js 13+ App Router

import { useState } from 'react';
import api from '@/lib/api'; // Adjust path to your api.ts file

interface TestResult {
    name: string;
    status: 'pending' | 'success' | 'error';
    duration?: number;
    response?: string;
    error?: string;
}

export default function ApiTestPage() {
    const [results, setResults] = useState<TestResult[]>([]);
    const [testing, setTesting] = useState(false);
    const [filter, setFilter] = useState<'all' | 'success' | 'error'>('all');

    const updateResult = (name: string, update: Partial<TestResult>) => {
        setResults(prev => {
            const existing = prev.find(r => r.name === name);
            if (existing) {
                return prev.map(r => r.name === name ? { ...r, ...update } : r);
            }
            return [...prev, { name, status: 'pending', ...update }];
        });
    };

    const runTest = async (name: string, testFn: () => Promise<unknown>) => {
        const startTime = Date.now();
        updateResult(name, { status: 'pending' });

        try {
            const response = await testFn();
            const duration = Date.now() - startTime;
            updateResult(name, {
                status: 'success',
                duration,
                response: JSON.stringify(response, null, 2)
            });
        } catch (error) {
            const duration = Date.now() - startTime;
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            updateResult(name, {
                status: 'error',
                duration,
                error: errorMessage
            });
        }
    };

    const runAllTests = async () => {
        setTesting(true);
        setResults([]);

        const tests = [
            // ==========================================
            // Health & Info
            // ==========================================
            { name: '🏥 Root Endpoint', fn: () => api.root() },
            { name: '🏥 Health Check', fn: () => api.health() },

            // ==========================================
            // Config & Broker
            // ==========================================
            { name: '⚙️ Get Config', fn: () => api.config.get() },
            {
                name: '⚙️ Update Broker Config',
                fn: () => api.config.updateBroker({
                    broker_name: 'alpaca',
                    api_key: 'test_key',
                    api_secret: 'test_secret',
                    is_paper: true
                })
            },
            { name: '⚙️ Update Cash Balance', fn: () => api.config.updateCash(100000) },

            // ==========================================
            // Data Management
            // ==========================================
            { name: '📊 Get Available Tickers', fn: () => api.data.getTickers() },
            { name: '📊 Get Storage Info', fn: () => api.data.getStorageInfo() },
            {
                name: '📊 Download Ticker (AAPL)',
                fn: () => api.data.downloadTicker({
                    ticker: 'AAPL',
                    start_date: '2024-01-01',
                    end_date: '2024-12-31'
                })
            },
            {
                name: '📊 Download Multiple Tickers',
                fn: () => api.data.downloadMultiple({
                    tickers: ['AAPL', 'GOOGL', 'MSFT'],
                    start_date: '2024-01-01',
                    end_date: '2024-12-31'
                })
            },
            { name: '📊 Get Ticker Info (AAPL)', fn: () => api.data.getTickerInfo('AAPL') },
            { name: '📊 Get Ticker Data (AAPL)', fn: () => api.data.getTickerData('AAPL', undefined, undefined, 10) },

            // ==========================================
            // Strategy Management
            // ==========================================
            { name: '🎯 Get All Strategies', fn: () => api.strategies.getAll() },
            { name: '🎯 Get Active Strategies', fn: () => api.strategies.getActive() },
            { name: '🎯 Get Available Strategy Types', fn: () => api.strategies.getAvailableTypes() },
            {
                name: '🎯 Create Strategy (RSI)',
                fn: () => api.strategies.create({
                    name: 'Test RSI Strategy',
                    strategy_type: 'rsi_momentum',
                    parameters: { period: 14, overbought: 70, oversold: 30 },
                    status: 'active'
                })
            },

            // ==========================================
            // Trade Management
            // ==========================================
            { name: '💼 Get All Trades', fn: () => api.trades.getAll() },
            { name: '💼 Get Open Trades', fn: () => api.trades.getOpen() },
            {
                name: '💼 Create Trade',
                fn: () => api.trades.create({
                    strategy_id: 1,
                    symbol: 'AAPL',
                    side: 'buy',
                    quantity: 10,
                    signal_price: 150.00,
                    order_type: 'market',
                    notes: 'Test trade'
                })
            },

            // ==========================================
            // Position Management
            // ==========================================
            { name: '📈 Get All Positions', fn: () => api.positions.getAll() },
            { name: '📈 Get Position (AAPL)', fn: () => api.positions.getBySymbol('AAPL') },
            {
                name: '📈 Update Position',
                fn: () => api.positions.update({
                    symbol: 'AAPL',
                    quantity_change: 5,
                    price: 150.00
                })
            },

            // ==========================================
            // Portfolio
            // ==========================================
            { name: '💰 Get Portfolio Summary', fn: () => api.portfolio.getSummary() },

            // ==========================================
            // Trading Signals
            // ==========================================
            {
                name: '📡 Generate Signals (AAPL)',
                fn: () => api.signals.generate({
                    ticker: 'AAPL',
                    strategies: ['rsi_momentum', 'ma_crossover', 'macd'],
                    mode: 'aggregate',
                    start_date: '2024-01-01',
                    end_date: '2024-12-31'
                })
            },
            { name: '📡 Get Latest Signal (AAPL)', fn: () => api.signals.getLatest('AAPL') },
            { name: '📡 Get Signal History (AAPL)', fn: () => api.signals.getHistory('AAPL', 50) },
            { name: '📡 Get Buy/Sell Points (AAPL)', fn: () => api.signals.getBuySellPoints('AAPL', 10) },

            // ==========================================
            // Market Data
            // ==========================================
            {
                name: '📉 Get Market Data (AAPL)',
                fn: () => api.marketData.get('AAPL', '2024-01-01', '2024-12-31', '1d', 100)
            },
            { name: '📉 Get Latest Price (AAPL)', fn: () => api.marketData.getLatestPrice('AAPL') },

            // ==========================================
            // Market Status
            // ==========================================
            { name: '🏪 Get Market Status', fn: () => api.market.getStatus() },
        ];

        for (const test of tests) {
            await runTest(test.name, test.fn);
            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        setTesting(false);
    };

    const filteredResults = results.filter(r => {
        if (filter === 'all') return true;
        return r.status === filter;
    });

    const stats = {
        total: results.length,
        success: results.filter(r => r.status === 'success').length,
        error: results.filter(r => r.status === 'error').length,
        pending: results.filter(r => r.status === 'pending').length,
    };

    const clearResults = () => {
        setResults([]);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Trading System API Test Dashboard
                    </h1>
                    <p className="text-gray-600">
                        Test all backend API endpoints from your Next.js app
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                        Backend: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                    </p>
                </div>

                {/* Controls */}
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                    <div className="flex items-center justify-between">
                        <div className="flex gap-3">
                            <button
                                onClick={runAllTests}
                                disabled={testing}
                                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
                                    testing
                                        ? 'bg-gray-400 cursor-not-allowed'
                                        : 'bg-blue-600 hover:bg-blue-700'
                                }`}
                            >
                                {testing ? 'Testing...' : 'Run All Tests'}
                            </button>

                            {results.length > 0 && (
                                <button
                                    onClick={clearResults}
                                    disabled={testing}
                                    className="px-6 py-3 rounded-lg font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors disabled:opacity-50"
                                >
                                    Clear Results
                                </button>
                            )}
                        </div>

                        <div className="flex gap-2">
                            {(['all', 'success', 'error'] as const).map(f => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                        filter === f
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                                >
                                    {f.charAt(0).toUpperCase() + f.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Stats */}
                {results.length > 0 && (
                    <div className="grid grid-cols-4 gap-4 mb-6">
                        <StatCard label="Total" value={stats.total} color="gray" />
                        <StatCard label="Success" value={stats.success} color="green" />
                        <StatCard label="Error" value={stats.error} color="red" />
                        <StatCard label="Pending" value={stats.pending} color="yellow" />
                    </div>
                )}

                {/* Results */}
                <div className="space-y-4">
                    {filteredResults.length === 0 && !testing && (
                        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                            <p className="text-gray-500 text-lg">
                                Click &quot;Run All Tests&quot; to start testing your API endpoints
                            </p>
                        </div>
                    )}

                    {filteredResults.map((result, index) => (
                        <ResultCard key={index} result={result} />
                    ))}
                </div>

                {/* Legend */}
                {results.length > 0 && (
                    <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
                        <h3 className="font-semibold text-gray-900 mb-3">Test Categories</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div><span className="font-mono">🏥</span> Health & Info</div>
                            <div><span className="font-mono">⚙️</span> Config & Broker</div>
                            <div><span className="font-mono">📊</span> Data Management</div>
                            <div><span className="font-mono">🎯</span> Strategy Management</div>
                            <div><span className="font-mono">💼</span> Trade Management</div>
                            <div><span className="font-mono">📈</span> Position Management</div>
                            <div><span className="font-mono">💰</span> Portfolio</div>
                            <div><span className="font-mono">📡</span> Trading Signals</div>
                            <div><span className="font-mono">📉</span> Market Data</div>
                            <div><span className="font-mono">🏪</span> Market Status</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
    const colorClasses = {
        gray: 'bg-gray-100 text-gray-900',
        green: 'bg-green-100 text-green-900',
        red: 'bg-red-100 text-red-900',
        yellow: 'bg-yellow-100 text-yellow-900',
    }[color];

    return (
        <div className={`rounded-lg p-4 ${colorClasses}`}>
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-sm font-medium">{label}</div>
        </div>
    );
}

function ResultCard({ result }: { result: TestResult }) {
    const [expanded, setExpanded] = useState(false);

    const statusConfig = {
        pending: { icon: '⏳', color: 'bg-yellow-50 border-yellow-200', textColor: 'text-yellow-800' },
        success: { icon: '✅', color: 'bg-green-50 border-green-200', textColor: 'text-green-800' },
        error: { icon: '❌', color: 'bg-red-50 border-red-200', textColor: 'text-red-800' },
    }[result.status];

    return (
        <div className={`rounded-lg border-2 ${statusConfig.color} overflow-hidden`}>
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full p-4 text-left hover:bg-white/50 transition-colors"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">{statusConfig.icon}</span>
                        <div>
                            <h3 className={`font-semibold ${statusConfig.textColor}`}>
                                {result.name}
                            </h3>
                            {result.duration && (
                                <p className="text-sm text-gray-600">
                                    {result.duration}ms
                                </p>
                            )}
                        </div>
                    </div>
                    <span className="text-gray-400">
                        {expanded ? '▼' : '▶'}
                    </span>
                </div>
            </button>

            {expanded && (
                <div className="p-4 bg-white border-t">
                    {result.error && (
                        <div className="mb-4">
                            <h4 className="font-semibold text-red-900 mb-2">Error:</h4>
                            <pre className="bg-red-50 p-3 rounded text-sm text-red-800 overflow-x-auto">
                                {result.error}
                            </pre>
                        </div>
                    )}

                    {result.response && (
                        <div>
                            <h4 className="font-semibold text-gray-900 mb-2">Response:</h4>
                            <pre className="bg-gray-50 p-3 rounded text-sm text-gray-800 overflow-x-auto max-h-96">
                                {result.response}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}