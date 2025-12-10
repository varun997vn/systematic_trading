'use client';

import {useState, useEffect} from 'react';
import api from '@/lib/api';
import PortfolioSummary from '@/components/PortfolioSummary';
import SignalMonitor from '@/components/SignalMonitor';
import TickerSearch from '@/components/TickerSearch';

export default function DashboardPage() {
    const [portfolioData, setPortfolioData] = useState<any>(null);
    const [activeStrategies, setActiveStrategies] = useState<string[]>([]);
    const [marketStatus, setMarketStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [portfolio, strategies, market] = await Promise.all([
                api.portfolio.getSummary().catch(() => null),
                api.strategies.getActive().catch(() => ({strategies: [], count: 0})),
                api.market.getStatus().catch(() => null),
            ]);

            setPortfolioData(portfolio);
            setActiveStrategies(strategies.strategies);
            setMarketStatus(market);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    <p className="mt-4 text-gray-600">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Trading System</h1>
                            <p className="text-sm text-gray-500 mt-1">
                                Algorithmic Trading Dashboard
                            </p>
                        </div>
                        {marketStatus && (
                            <div className="flex items-center space-x-2">
                                <div
                                    className={`w-3 h-3 rounded-full ${marketStatus.is_open ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                <span className="text-sm font-medium text-gray-700">
                  Market {marketStatus.is_open ? 'Open' : 'Closed'}
                </span>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {error && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd"
                                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                          clipRule="evenodd"/>
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
                                <p className="text-sm text-red-700 mt-1">{error}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Quick Actions */}
                <div className="mb-8">
                    <TickerSearch/>
                </div>

                {/* Active Strategies */}
                {activeStrategies.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Strategies</h2>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex flex-wrap gap-2">
                                {activeStrategies.map((strategy) => (
                                    <span
                                        key={strategy}
                                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                                    >
                    {strategy}
                  </span>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Portfolio Summary */}
                {portfolioData && (
                    <div className="mb-8">
                        <PortfolioSummary data={portfolioData}/>
                    </div>
                )}

                {/* Signal Monitor */}
                <div className="mb-8">
                    <SignalMonitor/>
                </div>
            </main>
        </div>
    );
}
