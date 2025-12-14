import React, { useState } from 'react';
import { FileCode, Database, TrendingUp, Target, BarChart3, Shield, Package, ArrowRight, Play, CheckCircle2, Circle, Briefcase } from 'lucide-react';

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
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0.25rem 0 0 0' }}>
                        {module.import}
                    </p>
                </div>
            </div>

            <p style={{ color: '#cbd5e1', marginBottom: '1.5rem', lineHeight: '1.6' }}>
                {module.details}
            </p>

            <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'white', marginBottom: '0.75rem' }}>
                    Key Classes
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
                {index < 7 && (
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
            name: 'Data',
            icon: Database,
            color: '#3b82f6',
            bgColor: 'rgba(59, 130, 246, 0.1)',
            import: 'from st.data import DataManager, PriceData',
            description: 'OHLCV data ingestion, validation, and return calculation',
            components: ['DataManager', 'DataLoader', 'PriceData', 'DataValidator', 'ReturnCalculator'],
            details: 'Handles market data loading from CSV or Yahoo Finance, validates data completeness, and calculates log/percentage returns. Uses Pydantic for data validation and pandas for time series operations.',
            example: `from st.data import DataManager

dm = DataManager()
price_data = dm.get_data("AAPL",
                         start_date="2020-01-01",
                         validate=True)
returns = dm.get_returns("AAPL",
                         return_type="log")`
        },
        {
            id: 'volatility',
            name: 'Volatility',
            icon: BarChart3,
            color: '#eab308',
            bgColor: 'rgba(234, 179, 8, 0.1)',
            import: 'from st.volatility import VolatilityManager',
            description: 'EWMA volatility estimation and targeting for position sizing',
            components: ['VolatilityManager', 'EWMAVolatility', 'VolatilityTargeter', 'VolatilityConfig'],
            details: 'Calculates exponentially weighted moving average (EWMA) volatility with configurable span (Carver recommends 32-36). Converts daily volatility to annual using sqrt(256). Provides volatility targeting scalars for position sizing.',
            example: `from st.volatility import VolatilityManager

vm = VolatilityManager(target_vol=0.20)
vol_result = vm.estimate_from_prices(
    prices, ticker="AAPL"
)
scalar = vm.get_position_scalar(vol_result)
# scalar = target_vol / current_vol`
        },
        {
            id: 'forecast',
            name: 'Forecast',
            icon: TrendingUp,
            color: '#10b981',
            bgColor: 'rgba(16, 185, 129, 0.1)',
            import: 'from st.forecast import ForecastManager',
            description: 'Trading rules (EWMAC, carry, mean reversion) and forecast scaling',
            components: ['ForecastManager', 'EWMAC', 'ForecastScaler', 'ForecastCombiner'],
            details: 'Implements Carver\'s trading rules, primarily EWMAC (Exponentially Weighted Moving Average Crossover). Scales raw forecasts to standardized -20 to +20 range with target absolute forecast of 10. Combines multiple forecasts using weighted averaging with FDM (Forecast Diversification Multiplier).',
            example: `from st.forecast import ForecastManager

fm = ForecastManager()
# Generate EWMAC(16,64) forecast
raw = fm.ewmac(prices, fast=16, slow=64)
scaled = fm.scale_forecast(raw, target=10)

# Combine multiple forecasts
combined = fm.combine_forecasts({
    'ewmac_16_64': forecast1,
    'ewmac_32_128': forecast2
}, weights={'ewmac_16_64': 0.5, ...})`
        },
        {
            id: 'position',
            name: 'Position',
            icon: Target,
            color: '#a855f7',
            bgColor: 'rgba(168, 85, 247, 0.1)',
            import: 'from st.position import PositionManager',
            description: 'Volatility-targeted position sizing and buffering',
            components: ['PositionManager', 'PositionSizer', 'PositionBuffer', 'Position'],
            details: 'Converts forecasts to positions using Carver\'s position sizing formula: Position = (Capital × Vol_Target × IDM × Weight × Forecast) / (10 × Instrument_Vol). Applies position buffering (10% buffer width) to reduce turnover from small position changes.',
            example: `from st.position import PositionManager

pm = PositionManager(
    volatility_target=0.20,
    max_leverage=2.0
)
position_set = pm.calculate_positions(
    forecasts=combined_forecasts,
    volatilities=vol_results,
    capital=100_000,
    weights=portfolio_weights
)
# Returns Position objects with buffering`
        },
        {
            id: 'portfolio',
            name: 'Portfolio',
            icon: Package,
            color: '#ec4899',
            bgColor: 'rgba(236, 72, 153, 0.1)',
            import: 'from st.portfolio import PortfolioManager',
            description: 'Multi-instrument weights and IDM calculation',
            components: ['PortfolioManager', 'PortfolioOptimizer', 'PortfolioWeights', 'IDMCalculator'],
            details: 'Manages portfolio-level weights across multiple instruments using equal weighting, inverse volatility, or risk parity. Calculates IDM (Instrument Diversification Multiplier) to scale positions based on correlation structure. Applies capital allocation per instrument.',
            example: `from st.portfolio import PortfolioManager

portfolio = PortfolioManager()
weights = portfolio.calculate_weights(
    volatilities=vol_dict,
    method="risk_parity"  # or "equal"
)
idm = portfolio.calculate_idm(
    correlations=corr_matrix
)
# Typical IDM: 1.5-2.5 for diversified`
        },
        {
            id: 'risk',
            name: 'Risk',
            icon: Shield,
            color: '#ef4444',
            bgColor: 'rgba(239, 68, 68, 0.1)',
            import: 'from st.risk import RiskManager',
            description: 'Portfolio risk monitoring and leverage controls',
            components: ['RiskManager', 'RiskCalculator', 'CorrelationEstimator', 'LeverageController'],
            details: 'Monitors portfolio-level risk metrics including total volatility, leverage, and correlation-adjusted risk. Enforces maximum leverage limits (default 2.0x) and scales positions proportionally if exceeded. Validates volatility ranges and risk parameters.',
            example: `from st.risk import RiskManager

rm = RiskManager(max_leverage=2.0)
risk_check = rm.check_portfolio_risk(
    positions=position_set,
    volatilities=vol_dict,
    correlations=corr_matrix
)
# Scales positions if leverage > max
final_positions = rm.apply_risk_limits(
    position_set
)`
        },
        {
            id: 'trader',
            name: 'Trader',
            icon: Briefcase,
            color: '#06b6d4',
            bgColor: 'rgba(6, 182, 212, 0.1)',
            import: 'from st.trader import Trader',
            description: 'Complete pipeline orchestration and trade generation',
            components: ['Trader', 'TradeSet', 'Trade', 'TradingPipeline'],
            details: 'Orchestrates the complete systematic trading pipeline in generate_trades() method. Coordinates all modules from data loading through trade execution. Stores comprehensive pipeline output for analysis. Handles incremental position updates and trade buffering.',
            example: `from st.trader import Trader

trader = Trader(
    tickers=["AAPL", "MSFT", "GOOGL"],
    capital=100_000
)
trade_set = trader.generate_trades(
    start_date="2020-01-01",
    ewmac_pairs=[(16,64), (32,128)],
    portfolio_weights_method="risk_parity"
)
# Returns TradeSet with Trade objects`
        }
    ];

    const executionFlow = [
        {
            title: '1. Data Ingestion & Validation',
            description: 'DataManager loads OHLCV data via DataLoader, validates completeness with DataValidator, calculates log returns',
            color: '#3b82f6',
            outputs: ['PriceData', 'Log Returns', 'Validated Series']
        },
        {
            title: '2. Volatility Estimation (EWMA)',
            description: 'VolatilityManager calculates EWMA volatility with span=36, annualizes to 256 trading days',
            color: '#eab308',
            outputs: ['Daily Vol', 'Annual Vol (×√256)', 'VolatilityResult']
        },
        {
            title: '3. Forecast Generation',
            description: 'ForecastManager applies EWMAC rules (default 6 pairs: 2/8, 4/16, 8/32, 16/64, 32/128, 64/256)',
            color: '#10b981',
            outputs: ['Raw EWMAC Forecasts', 'Multiple Timeframes']
        },
        {
            title: '4. Forecast Combination (FDM)',
            description: 'ForecastCombiner scales to -20/+20 range, applies equal/custom weights, calculates FDM',
            color: '#10b981',
            outputs: ['Combined Forecast', 'Scaled -20 to +20', 'FDM Applied']
        },
        {
            title: '5. Portfolio Weights (IDM)',
            description: 'PortfolioManager calculates instrument weights (equal/inverse vol/risk parity) and IDM from correlations',
            color: '#ec4899',
            outputs: ['Portfolio Weights', 'IDM (1.5-2.5)', 'Capital Allocation']
        },
        {
            title: '6. Position Sizing',
            description: 'PositionManager applies: Position = (Capital × VolTarget × IDM × Weight × Forecast) / (10 × Vol)',
            color: '#a855f7',
            outputs: ['Target Positions', 'Contract Sizes', 'Notional Values']
        },
        {
            title: '7. Risk Management',
            description: 'RiskManager checks leverage limits (max 2.0x), scales positions if exceeded, validates risk parameters',
            color: '#ef4444',
            outputs: ['Final Positions', 'Leverage Check', 'Risk Metrics']
        },
        {
            title: '8. Trade Generation',
            description: 'Trader applies position buffering (10% width), generates Trade objects with BUY/SELL actions',
            color: '#06b6d4',
            outputs: ['TradeSet', 'Trade Orders', 'Pipeline Summary']
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
                    <p style={{ color: '#cbd5e1', fontSize: '1.125rem', marginBottom: '0.5rem' }}>
                        Based on Robert Carver's "Systematic Trading"
                    </p>
                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                        Built with Polars • Pydantic • YFinance
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
                            Execution Pipeline
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
                                Trader.generate_trades() Pipeline
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
                                    onClick={() => setActiveFlow(Math.min(7, activeFlow + 1))}
                                    disabled={activeFlow === 7}
                                    style={{
                                        padding: '0.5rem 1rem',
                                        backgroundColor: '#3b82f6',
                                        color: 'white',
                                        borderRadius: '0.375rem',
                                        border: 'none',
                                        cursor: activeFlow === 7 ? 'not-allowed' : 'pointer',
                                        opacity: activeFlow === 7 ? 0.5 : 1,
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (activeFlow !== 7) e.currentTarget.style.backgroundColor = '#2563eb';
                                    }}
                                    onMouseLeave={(e) => {
                                        if (activeFlow !== 7) e.currentTarget.style.backgroundColor = '#3b82f6';
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
                                Module Dependencies
                            </h2>
                            <div style={{ marginBottom: '1.5rem' }}>
                                {[
                                    { from: 'Yahoo Finance', to: 'DataManager', active: activeFlow >= 0 },
                                    { from: 'DataManager', to: 'VolatilityManager', active: activeFlow >= 1 },
                                    { from: 'DataManager', to: 'ForecastManager', active: activeFlow >= 2 },
                                    { from: 'ForecastManager', to: 'ForecastCombiner', active: activeFlow >= 3 },
                                    { from: 'VolatilityManager', to: 'PortfolioManager', active: activeFlow >= 4 },
                                    { from: 'ForecastCombiner', to: 'PortfolioManager', active: activeFlow >= 4 },
                                    { from: 'PortfolioManager', to: 'PositionManager', active: activeFlow >= 5 },
                                    { from: 'PositionManager', to: 'RiskManager', active: activeFlow >= 6 },
                                    { from: 'RiskManager', to: 'Trader', active: activeFlow >= 7 },
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
                                    Current Step
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
                        { label: 'Core Modules', value: '7' },
                        { label: 'Key Classes', value: '28' },
                        { label: 'Pipeline Steps', value: '8' },
                        { label: 'EWMAC Pairs', value: '6' }
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

                {/* Footer Info */}
                <div style={{
                    marginTop: '2rem',
                    padding: '1.5rem',
                    backgroundColor: '#1e293b',
                    borderRadius: '0.5rem',
                    border: '1px solid #334155'
                }}>
                    <h3 style={{ color: 'white', fontSize: '1.125rem', marginBottom: '0.75rem' }}>
                        Key Carver Principles
                    </h3>
                    <ul style={{ color: '#cbd5e1', lineHeight: '1.8', margin: 0, paddingLeft: '1.5rem' }}>
                        <li><strong>Volatility Targeting:</strong> 20% annual volatility (VOLATILITY_TARGET = 0.20)</li>
                        <li><strong>EWMA Span:</strong> 36 days for volatility estimation (Carver recommends 32-36)</li>
                        <li><strong>Trading Days:</strong> 256 per year (BUSINESS_DAYS_PER_YEAR)</li>
                        <li><strong>Forecast Range:</strong> Scaled -20 to +20, target absolute forecast = 10</li>
                        <li><strong>FDM/IDM:</strong> Forecast & Instrument Diversification Multipliers (1.5-2.5 typical)</li>
                        <li><strong>Position Buffering:</strong> 10% buffer width to reduce turnover</li>
                        <li><strong>Max Leverage:</strong> 2.0x capital (MAX_LEVERAGE = 2.0)</li>
                    </ul>
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