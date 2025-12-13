import React, { useState } from 'react';
import { FileCode, Database, TrendingUp, Target, BarChart3, Shield, Package, ArrowRight, Play, CheckCircle2, Circle } from 'lucide-react';

// Module Card Component
const ModuleCard = ({ module, isSelected, onClick }) => {
    const Icon = module.icon;

    return (
        <div
            onClick={onClick}
            style={{
                position: 'relative',
                overflow: 'hidden',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                backgroundColor: isSelected ? module.bgColor.replace('0.1', '0.2') : module.bgColor,
                border: `2px solid ${isSelected ? module.color : 'transparent'}`,
                transform: isSelected ? 'scale(1.02)' : 'scale(1)',
            }}
            onMouseEnter={(e) => {
                if (!isSelected) {
                    e.currentTarget.style.backgroundColor = module.bgColor.replace('0.1', '0.15');
                    e.currentTarget.style.transform = 'scale(1.01)';
                }
            }}
            onMouseLeave={(e) => {
                if (!isSelected) {
                    e.currentTarget.style.backgroundColor = module.bgColor;
                    e.currentTarget.style.transform = 'scale(1)';
                }
            }}
        >
            <div style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <div
                        style={{
                            padding: '0.5rem',
                            borderRadius: '0.5rem',
                            marginRight: '0.75rem',
                            backgroundColor: module.color + '20'
                        }}
                    >
                        <Icon style={{ width: '1.5rem', height: '1.5rem', color: module.color }} />
                    </div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', color: 'white', margin: 0 }}>
                        {module.name}
                    </h3>
                </div>
                <p style={{ color: '#cbd5e1', fontSize: '0.875rem', lineHeight: '1.6', margin: 0 }}>
                    {module.description}
                </p>
            </div>
            {isSelected && (
                <div
                    style={{
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        width: '4rem',
                        height: '4rem',
                        background: `linear-gradient(135deg, transparent 50%, ${module.color}40 50%)`,
                    }}
                >
                    <CheckCircle2
                        style={{
                            position: 'absolute',
                            top: '0.5rem',
                            right: '0.5rem',
                            color: module.color,
                            width: '1.25rem',
                            height: '1.25rem'
                        }}
                    />
                </div>
            )}
        </div>
    );
};

// Module Details Component
const ModuleDetails = ({ module }) => {
    return (
        <div style={{
            backgroundColor: '#1e293b',
            borderRadius: '0.5rem',
            padding: '1.5rem',
            border: '2px solid #334155',
            animation: 'fadeIn 0.3s ease'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
                <div
                    style={{
                        padding: '0.75rem',
                        borderRadius: '0.5rem',
                        marginRight: '1rem',
                        backgroundColor: module.color + '20'
                    }}
                >
                    {React.createElement(module.icon, {
                        style: { width: '2rem', height: '2rem', color: module.color }
                    })}
                </div>
                <div>
                    <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: 'white', margin: 0 }}>
                        {module.name}
                    </h2>
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0 0' }}>Core Module</p>
                </div>
            </div>

            <p style={{ color: '#cbd5e1', marginBottom: '1.5rem', lineHeight: '1.6' }}>
                {module.details}
            </p>

            <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'white', marginBottom: '0.75rem' }}>
                    Key Components
                </h3>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '0.5rem'
                }}>
                    {module.components.map((component, idx) => (
                        <div
                            key={idx}
                            style={{
                                backgroundColor: '#334155',
                                borderRadius: '0.375rem',
                                padding: '0.75rem',
                                display: 'flex',
                                alignItems: 'center',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#475569'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#334155'}
                        >
                            <FileCode style={{ width: '1rem', height: '1rem', marginRight: '0.5rem', color: '#94a3b8' }} />
                            <code style={{ fontSize: '0.875rem', color: '#e2e8f0' }}>{component}</code>
                        </div>
                    ))}
                </div>
            </div>

            {module.example && (
                <div style={{
                    marginTop: '1.5rem',
                    backgroundColor: '#0f172a',
                    borderRadius: '0.5rem',
                    padding: '1rem',
                    border: '1px solid #334155'
                }}>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#94a3b8', marginBottom: '0.5rem' }}>
                        Example Usage
                    </h4>
                    <pre style={{
                        fontSize: '0.75rem',
                        color: '#cbd5e1',
                        overflowX: 'auto',
                        margin: 0,
                        fontFamily: 'monospace'
                    }}>
            {module.example}
          </pre>
                </div>
            )}
        </div>
    );
};

// Execution Flow Step Component
const FlowStep = ({ step, index, isActive, isCompleted, color }) => {
    return (
        <div style={{ display: 'flex', alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: '1rem' }}>
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '50%',
                        transition: 'all 0.3s ease',
                        width: '3rem',
                        height: '3rem',
                        backgroundColor: isCompleted || isActive ? color : '#475569',
                        boxShadow: isActive ? `0 0 20px ${color}80` : 'none',
                    }}
                >
                    {isCompleted ? (
                        <CheckCircle2 style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
                    ) : isActive ? (
                        <Play style={{ width: '1.25rem', height: '1.25rem', color: 'white' }} />
                    ) : (
                        <Circle style={{ width: '1.25rem', height: '1.25rem', color: '#94a3b8' }} />
                    )}
                </div>
                {index < 5 && (
                    <div
                        style={{
                            width: '2px',
                            height: '4rem',
                            marginTop: '0.5rem',
                            transition: 'all 0.3s ease',
                            backgroundColor: isCompleted ? color : '#475569',
                        }}
                    />
                )}
            </div>

            <div style={{ flex: 1, paddingBottom: '2rem' }}>
                <h4 style={{ color: 'white', fontWeight: '600', marginBottom: '0.25rem' }}>{step.title}</h4>
                <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{step.description}</p>
                {step.outputs && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                        {step.outputs.map((output, idx) => (
                            <span
                                key={idx}
                                style={{
                                    fontSize: '0.75rem',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '0.25rem',
                                    backgroundColor: color + '20',
                                    color: color,
                                }}
                            >
                {output}
              </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

// Main Component
const SystematicTradingArchitecture = () => {
    const [selectedModule, setSelectedModule] = useState(null);
    const [activeFlow, setActiveFlow] = useState(0);
    const [view, setView] = useState('modules');

    const modules = [
        {
            id: 'data',
            name: 'Data Management',
            icon: Database,
            color: '#3b82f6',
            bgColor: 'rgba(59, 130, 246, 0.1)',
            description: 'Handle price data, returns calculation, and data validation',
            components: ['PriceData', 'DataLoader', 'DataValidator', 'ReturnCalculator'],
            details: 'Manages all market data including OHLCV, handles missing data, calculates log returns and percentage returns. This is the foundation of the entire system.',
            example: `data = DataLoader.load_csv('prices.csv')
validated = DataValidator.check(data)
returns = ReturnCalculator.log_returns(validated)`
        },
        {
            id: 'volatility',
            name: 'Volatility',
            icon: BarChart3,
            color: '#eab308',
            bgColor: 'rgba(234, 179, 8, 0.1)',
            description: 'Estimate and forecast instrument volatility',
            components: ['VolatilityEstimator', 'EWMAVolatility', 'VolatilityTargeting'],
            details: 'Calculates exponentially weighted moving average volatility for position sizing and risk management. Uses configurable span for EWMA calculation.',
            example: `vol_estimator = EWMAVolatility(span=36)
daily_vol = vol_estimator.calculate(returns)
annual_vol = daily_vol * sqrt(256)`
        },
        {
            id: 'forecast',
            name: 'Forecasting',
            icon: TrendingUp,
            color: '#10b981',
            bgColor: 'rgba(16, 185, 129, 0.1)',
            description: 'Trading rules that generate forecast signals',
            components: ['TrendFollowing', 'Carry', 'MeanReversion', 'ForecastScaler'],
            details: 'Implements various trading rules (EWMAC, carry, etc.) and scales forecasts to standard -20 to +20 range for consistent risk allocation.',
            example: `ewmac = TrendFollowing.ewmac(fast=16, slow=64)
forecast = ForecastScaler.scale(ewmac, target=10)
# Output range: -20 to +20`
        },
        {
            id: 'position',
            name: 'Position Sizing',
            icon: Target,
            color: '#a855f7',
            bgColor: 'rgba(168, 85, 247, 0.1)',
            description: 'Calculate optimal position sizes based on volatility and risk',
            components: ['PositionSizer', 'VolatilityScaling', 'InstrumentWeight'],
            details: 'Converts forecasts into positions using volatility targeting and risk-adjusted sizing. Ensures consistent risk across instruments.',
            example: `position = PositionSizer.calculate(
  forecast=10,
  volatility=0.15,
  capital=100000,
  target_risk=0.20
)`
        },
        {
            id: 'portfolio',
            name: 'Portfolio',
            icon: Package,
            color: '#ec4899',
            bgColor: 'rgba(236, 72, 153, 0.1)',
            description: 'Combine forecasts and manage multiple instruments',
            components: ['ForecastCombiner', 'PortfolioOptimizer', 'DiversificationMultiplier'],
            details: 'Aggregates multiple trading rules and instruments into a coherent portfolio with proper diversification. Applies diversification multiplier.',
            example: `combined = ForecastCombiner.weighted_average(
  forecasts={'ewmac_16_64': 10, 'carry': 5},
  weights={'ewmac_16_64': 0.6, 'carry': 0.4}
)`
        },
        {
            id: 'risk',
            name: 'Risk Management',
            icon: Shield,
            color: '#ef4444',
            bgColor: 'rgba(239, 68, 68, 0.1)',
            description: 'Monitor and control portfolio risk',
            components: ['RiskCalculator', 'CorrelationEstimator', 'CapitalAllocation'],
            details: 'Tracks portfolio volatility, correlations between instruments, and ensures risk targets are met. Implements position limits and drawdown controls.',
            example: `risk = RiskCalculator.portfolio_risk(
  positions=positions,
  correlations=corr_matrix,
  volatilities=vols
)`
        }
    ];

    const executionFlow = [
        {
            title: '1. Data Ingestion & Validation',
            description: 'Load historical price data, validate for completeness, and calculate returns',
            color: '#3b82f6',
            outputs: ['OHLCV Data', 'Log Returns', 'Percentage Returns']
        },
        {
            title: '2. Volatility Estimation',
            description: 'Calculate EWMA volatility for each instrument to normalize risk',
            color: '#eab308',
            outputs: ['Daily Volatility', 'Annual Volatility', 'Vol Forecast']
        },
        {
            title: '3. Forecast Generation',
            description: 'Apply trading rules (trend, carry, mean reversion) to generate signals',
            color: '#10b981',
            outputs: ['Raw Forecasts', 'Scaled Forecasts (-20 to +20)']
        },
        {
            title: '4. Forecast Combination',
            description: 'Combine multiple forecasts using weighted averaging or optimization',
            color: '#ec4899',
            outputs: ['Combined Forecast', 'Diversification Multiplier']
        },
        {
            title: '5. Position Sizing',
            description: 'Convert forecasts to positions using volatility targeting',
            color: '#a855f7',
            outputs: ['Target Positions', 'Risk-Adjusted Sizes', 'Capital Allocation']
        },
        {
            title: '6. Risk Management & Execution',
            description: 'Apply risk limits, calculate portfolio metrics, and execute trades',
            color: '#ef4444',
            outputs: ['Final Positions', 'Portfolio Risk', 'Trade Orders']
        }
    ];

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(to bottom right, #0f172a, #1e293b)',
            padding: '1.5rem'
        }}>
            <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <h1 style={{
                        fontSize: 'clamp(2rem, 5vw, 3rem)',
                        fontWeight: 'bold',
                        color: 'white',
                        marginBottom: '0.75rem'
                    }}>
                        Systematic Trading Framework
                    </h1>
                    <p style={{ color: '#cbd5e1', fontSize: '1.125rem', marginBottom: '1.5rem' }}>
                        Based on Robert Carver's "Systematic Trading"
                    </p>

                    {/* View Toggle */}
                    <div style={{
                        display: 'inline-flex',
                        borderRadius: '0.5rem',
                        backgroundColor: '#1e293b',
                        padding: '0.25rem'
                    }}>
                        <button
                            onClick={() => setView('modules')}
                            style={{
                                padding: '0.5rem 1.5rem',
                                borderRadius: '0.375rem',
                                transition: 'all 0.2s',
                                backgroundColor: view === 'modules' ? '#3b82f6' : 'transparent',
                                color: view === 'modules' ? 'white' : '#94a3b8',
                                border: 'none',
                                cursor: 'pointer',
                                fontWeight: '500'
                            }}
                        >
                            Module Overview
                        </button>
                        <button
                            onClick={() => setView('flow')}
                            style={{
                                padding: '0.5rem 1.5rem',
                                borderRadius: '0.375rem',
                                transition: 'all 0.2s',
                                backgroundColor: view === 'flow' ? '#3b82f6' : 'transparent',
                                color: view === 'flow' ? 'white' : '#94a3b8',
                                border: 'none',
                                cursor: 'pointer',
                                fontWeight: '500'
                            }}
                        >
                            Execution Flow
                        </button>
                    </div>
                </div>

                {/* Module View */}
                {view === 'modules' && (
                    <>
                        {/* Module Grid */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                            gap: '1rem',
                            marginBottom: '2rem'
                        }}>
                            {modules.map((module) => (
                                <ModuleCard
                                    key={module.id}
                                    module={module}
                                    isSelected={selectedModule?.id === module.id}
                                    onClick={() => setSelectedModule(module)}
                                />
                            ))}
                        </div>

                        {/* Selected Module Details */}
                        {selectedModule && (
                            <ModuleDetails module={selectedModule} />
                        )}
                    </>
                )}

                {/* Flow View */}
                {view === 'flow' && (
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                        gap: '2rem'
                    }}>
                        {/* Flow Steps */}
                        <div style={{
                            backgroundColor: '#1e293b',
                            borderRadius: '0.5rem',
                            padding: '1.5rem',
                            border: '2px solid #334155'
                        }}>
                            <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: 'white', marginBottom: '1.5rem' }}>
                                Execution Pipeline
                            </h2>
                            <div style={{ marginBottom: '1.5rem' }}>
                                {executionFlow.map((step, index) => (
                                    <FlowStep
                                        key={index}
                                        step={step}
                                        index={index}
                                        isActive={activeFlow === index}
                                        isCompleted={activeFlow > index}
                                        color={step.color}
                                    />
                                ))}
                            </div>

                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                                <button
                                    onClick={() => setActiveFlow(Math.max(0, activeFlow - 1))}
                                    disabled={activeFlow === 0}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        backgroundColor: '#334155',
                                        color: 'white',
                                        borderRadius: '0.375rem',
                                        border: 'none',
                                        cursor: activeFlow === 0 ? 'not-allowed' : 'pointer',
                                        opacity: activeFlow === 0 ? 0.5 : 1,
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (activeFlow !== 0) e.currentTarget.style.backgroundColor = '#475569';
                                    }}
                                    onMouseLeave={(e) => {
                                        if (activeFlow !== 0) e.currentTarget.style.backgroundColor = '#334155';
                                    }}
                                >
                                    Previous
                                </button>
                                <button
                                    onClick={() => setActiveFlow(Math.min(5, activeFlow + 1))}
                                    disabled={activeFlow === 5}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        backgroundColor: '#3b82f6',
                                        color: 'white',
                                        borderRadius: '0.375rem',
                                        border: 'none',
                                        cursor: activeFlow === 5 ? 'not-allowed' : 'pointer',
                                        opacity: activeFlow === 5 ? 0.5 : 1,
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (activeFlow !== 5) e.currentTarget.style.backgroundColor = '#2563eb';
                                    }}
                                    onMouseLeave={(e) => {
                                        if (activeFlow !== 5) e.currentTarget.style.backgroundColor = '#3b82f6';
                                    }}
                                >
                                    Next
                                </button>
                                <button
                                    onClick={() => setActiveFlow(0)}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        backgroundColor: '#334155',
                                        color: 'white',
                                        borderRadius: '0.375rem',
                                        border: 'none',
                                        cursor: 'pointer',
                                        marginLeft: 'auto',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#475569'}
                                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#334155'}
                                >
                                    Reset
                                </button>
                            </div>
                        </div>

                        {/* Flow Visualization */}
                        <div style={{
                            backgroundColor: '#1e293b',
                            borderRadius: '0.5rem',
                            padding: '1.5rem',
                            border: '2px solid #334155'
                        }}>
                            <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: 'white', marginBottom: '1.5rem' }}>
                                Data Flow Diagram
                            </h2>
                            <div style={{ marginBottom: '1.5rem' }}>
                                {[
                                    { from: 'Market Data', to: 'Data Module', active: activeFlow >= 0 },
                                    { from: 'Data Module', to: 'Volatility Module', active: activeFlow >= 1 },
                                    { from: 'Data Module', to: 'Forecast Module', active: activeFlow >= 2 },
                                    { from: 'Forecast Module', to: 'Portfolio Module', active: activeFlow >= 3 },
                                    { from: 'Volatility Module', to: 'Position Module', active: activeFlow >= 4 },
                                    { from: 'Portfolio Module', to: 'Position Module', active: activeFlow >= 4 },
                                    { from: 'Position Module', to: 'Risk Module', active: activeFlow >= 5 },
                                    { from: 'Risk Module', to: 'Trade Execution', active: activeFlow >= 5 },
                                ].map((edge, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            padding: '1rem',
                                            borderRadius: '0.5rem',
                                            marginBottom: '0.5rem',
                                            transition: 'all 0.3s',
                                            backgroundColor: edge.active ? '#1e40af20' : '#47556920',
                                            borderLeft: `4px solid ${edge.active ? '#3b82f6' : '#475569'}`,
                                        }}
                                    >
                    <span style={{
                        color: '#cbd5e1',
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        flex: 1
                    }}>
                      {edge.from}
                    </span>
                                        <ArrowRight
                                            style={{
                                                margin: '0 1rem',
                                                color: edge.active ? '#3b82f6' : '#475569',
                                                width: '1.5rem',
                                                height: '1.5rem'
                                            }}
                                        />
                                        <span style={{
                                            color: '#cbd5e1',
                                            fontFamily: 'monospace',
                                            fontSize: '0.875rem',
                                            flex: 1,
                                            textAlign: 'right'
                                        }}>
                      {edge.to}
                    </span>
                                    </div>
                                ))}
                            </div>

                            <div style={{
                                padding: '1rem',
                                backgroundColor: '#0f172a',
                                borderRadius: '0.5rem',
                                border: '1px solid #334155'
                            }}>
                                <h3 style={{
                                    fontSize: '0.875rem',
                                    fontWeight: '600',
                                    color: '#94a3b8',
                                    marginBottom: '0.5rem'
                                }}>
                                    Current Step Details
                                </h3>
                                <p style={{ color: '#cbd5e1', fontSize: '0.875rem', margin: 0 }}>
                                    {executionFlow[activeFlow].description}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Stats */}
                <div style={{
                    marginTop: '2rem',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                    gap: '1rem'
                }}>
                    {[
                        { label: 'Total Modules', value: '6' },
                        { label: 'Components', value: '24' },
                        { label: 'Pipeline Steps', value: '6' },
                        { label: 'Integration Points', value: '8' }
                    ].map((stat, idx) => (
                        <div key={idx} style={{
                            backgroundColor: '#1e293b',
                            borderRadius: '0.5rem',
                            padding: '1rem',
                            border: '1px solid #334155'
                        }}>
                            <div style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                                {stat.label}
                            </div>
                            <div style={{ color: 'white', fontSize: '1.875rem', fontWeight: 'bold' }}>
                                {stat.value}
                            </div>
                        </div>
                    ))}
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