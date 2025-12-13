import React, { useState } from 'react';
import { FileCode, Database, TrendingUp, Target, BarChart3, Shield, Package } from 'lucide-react';

const SystematicTradingArchitecture = () => {
    const [selectedModule, setSelectedModule] = useState(null);

    const modules = [
        {
            id: 'data',
            name: 'Data Management',
            icon: Database,
            color: '#3b82f6',
            bgColor: 'rgba(59, 130, 246, 0.1)',
            description: 'Handle price data, returns calculation, and data validation',
            components: ['PriceData', 'DataLoader', 'DataValidator', 'ReturnCalculator'],
            details: 'Manages all market data including OHLCV, handles missing data, calculates log returns and percentage returns.'
        },
        {
            id: 'forecast',
            name: 'Forecasting',
            icon: TrendingUp,
            color: '#10b981',
            bgColor: 'rgba(16, 185, 129, 0.1)',
            description: 'Trading rules that generate forecast signals',
            components: ['TrendFollowing', 'Carry', 'MeanReversion', 'ForecastScaler'],
            details: 'Implements various trading rules (EWMAC, carry, etc.) and scales forecasts to standard -20 to +20 range.'
        },
        {
            id: 'volatility',
            name: 'Volatility',
            icon: BarChart3,
            color: '#eab308',
            bgColor: 'rgba(234, 179, 8, 0.1)',
            description: 'Estimate and forecast instrument volatility',
            components: ['VolatilityEstimator', 'EWMAVolatility', 'VolatilityTargeting'],
            details: 'Calculates exponentially weighted moving average volatility for position sizing and risk management.'
        },
        {
            id: 'position',
            name: 'Position Sizing',
            icon: Target,
            color: '#a855f7',
            bgColor: 'rgba(168, 85, 247, 0.1)',
            description: 'Calculate optimal position sizes based on volatility and risk',
            components: ['PositionSizer', 'VolatilityScaling', 'InstrumentWeight'],
            details: 'Converts forecasts into positions using volatility targeting and risk-adjusted sizing.'
        },
        {
            id: 'portfolio',
            name: 'Portfolio',
            icon: Package,
            color: '#ec4899',
            bgColor: 'rgba(236, 72, 153, 0.1)',
            description: 'Combine forecasts and manage multiple instruments',
            components: ['ForecastCombiner', 'PortfolioOptimizer', 'DiversificationMultiplier'],
            details: 'Aggregates multiple trading rules and instruments into a coherent portfolio with proper diversification.'
        },
        {
            id: 'risk',
            name: 'Risk Management',
            icon: Shield,
            color: '#ef4444',
            bgColor: 'rgba(239, 68, 68, 0.1)',
            description: 'Monitor and control portfolio risk',
            components: ['RiskCalculator', 'CorrelationEstimator', 'CapitalAllocation'],
            details: 'Tracks portfolio volatility, correlations between instruments, and ensures risk targets are met.'
        }
    ];

    const stepColors = [
        '#3b82f6', // blue
        '#eab308', // yellow
        '#10b981', // green
        '#ec4899', // pink
        '#a855f7', // purple
        '#ef4444'  // red
    ];

    return (
        <div style={{
            width: '100%',
            minHeight: '100vh',
            background: 'linear-gradient(to bottom right, #0f172a, #1e293b)',
            padding: '2rem',
            overflowY: 'auto'
        }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <h1 style={{
                        fontSize: '2.5rem',
                        fontWeight: 'bold',
                        color: 'white',
                        marginBottom: '0.5rem'
                    }}>
                        Systematic Trading Framework
                    </h1>
                    <p style={{ color: '#cbd5e1', fontSize: '1.1rem' }}>
                        Based on Robert Carver's "Systematic Trading"
                    </p>
                </div>

                {/* Module Grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    {modules.map((module) => {
                        const Icon = module.icon;
                        const isSelected = selectedModule?.id === module.id;

                        return (
                            <div
                                key={module.id}
                                onClick={() => setSelectedModule(module)}
                                style={{
                                    backgroundColor: module.bgColor,
                                    border: `2px solid ${isSelected ? 'white' : 'transparent'}`,
                                    borderRadius: '0.5rem',
                                    padding: '1.5rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    transform: isSelected ? 'scale(1.02)' : 'scale(1)'
                                }}
                                onMouseEnter={(e) => {
                                    if (!isSelected) {
                                        e.currentTarget.style.backgroundColor = module.bgColor.replace('0.1', '0.2');
                                        e.currentTarget.style.transform = 'scale(1.02)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isSelected) {
                                        e.currentTarget.style.backgroundColor = module.bgColor;
                                        e.currentTarget.style.transform = 'scale(1)';
                                    }
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.75rem' }}>
                                    <Icon style={{ width: '2rem', height: '2rem', color: module.color, marginRight: '0.75rem' }} />
                                    <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'white', margin: 0 }}>
                                        {module.name}
                                    </h3>
                                </div>
                                <p style={{ color: '#cbd5e1', fontSize: '0.875rem', margin: 0 }}>
                                    {module.description}
                                </p>
                            </div>
                        );
                    })}
                </div>

                {/* Selected Module Details */}
                {selectedModule && (
                    <div style={{
                        backgroundColor: '#1e293b',
                        borderRadius: '0.5rem',
                        padding: '1.5rem',
                        border: '2px solid #334155',
                        marginBottom: '2rem',
                        animation: 'fadeIn 0.3s ease'
                    }}>
                        <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: 'white', marginBottom: '1rem' }}>
                            {selectedModule.name} Module
                        </h2>
                        <p style={{ color: '#cbd5e1', marginBottom: '1.5rem' }}>
                            {selectedModule.details}
                        </p>

                        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'white', marginBottom: '0.5rem' }}>
                            Key Components:
                        </h3>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '0.5rem'
                        }}>
                            {selectedModule.components.map((component, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        backgroundColor: '#334155',
                                        borderRadius: '0.25rem',
                                        padding: '0.5rem 0.75rem',
                                        color: '#e2e8f0',
                                        fontSize: '0.875rem',
                                        display: 'flex',
                                        alignItems: 'center'
                                    }}
                                >
                                    <FileCode style={{ width: '1rem', height: '1rem', marginRight: '0.5rem' }} />
                                    {component}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Data Flow */}
                <div style={{
                    backgroundColor: '#1e293b',
                    borderRadius: '0.5rem',
                    padding: '1.5rem',
                    border: '2px solid #334155'
                }}>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'white', marginBottom: '1rem' }}>
                        Data Flow
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', color: '#cbd5e1' }}>
                        {[
                            'Load and validate market data',
                            'Calculate volatility for each instrument',
                            'Generate forecasts from trading rules',
                            'Combine forecasts across rules and instruments',
                            'Size positions based on volatility and risk targets',
                            'Monitor portfolio risk and rebalance'
                        ].map((step, idx) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center' }}>
                                <div style={{
                                    width: '2rem',
                                    height: '2rem',
                                    borderRadius: '50%',
                                    backgroundColor: stepColors[idx],
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontWeight: 'bold',
                                    marginRight: '0.75rem',
                                    flexShrink: 0
                                }}>
                                    {idx + 1}
                                </div>
                                <span>{step}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
        </div>
    );
};

export default SystematicTradingArchitecture;