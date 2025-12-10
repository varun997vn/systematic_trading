'use client';

import { useState } from 'react';
import api, { TradingSignal } from '@/lib/api';

export default function SignalMonitor() {
  const [ticker, setTicker] = useState('');
  const [signal, setSignal] = useState<TradingSignal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSignalColor = (signalValue: number) => {
    if (signalValue >= 15) return 'text-green-600';
    if (signalValue >= 10) return 'text-green-500';
    if (signalValue > 0) return 'text-blue-500';
    if (signalValue > -10) return 'text-orange-500';
    if (signalValue > -15) return 'text-red-500';
    return 'text-red-600';
  };

  const getSignalBgColor = (signalValue: number) => {
    if (signalValue >= 15) return 'bg-green-100';
    if (signalValue >= 10) return 'bg-green-50';
    if (signalValue > 0) return 'bg-blue-50';
    if (signalValue > -10) return 'bg-orange-50';
    if (signalValue > -15) return 'bg-red-50';
    return 'bg-red-100';
  };

  const handleCheckSignal = async () => {
    if (!ticker.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.signals.getLatest(ticker.toUpperCase());
      setSignal(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signal');
      setSignal(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCheckSignal();
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Signal Monitor</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex gap-3 mb-6">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter ticker (e.g., AAPL)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleCheckSignal}
            disabled={loading || !ticker.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Check Signal'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {signal && (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-sm font-medium text-gray-500 mb-2">Ticker</div>
                <div className="text-2xl font-bold text-gray-900">{signal.ticker}</div>
              </div>
              
              <div className="text-center">
                <div className="text-sm font-medium text-gray-500 mb-2">Current Price</div>
                <div className="text-2xl font-bold text-gray-900">
                  ${signal.close.toFixed(2)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-sm font-medium text-gray-500 mb-2">Signal Strength</div>
                <div className={`text-2xl font-bold ${getSignalColor(signal.signal)}`}>
                  {signal.signal > 0 ? '+' : ''}{signal.signal}
                </div>
                <div className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${getSignalBgColor(signal.signal)} ${getSignalColor(signal.signal)}`}>
                  {signal.label}
                </div>
              </div>
            </div>

            {signal.individual_signals && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">Individual Signals</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(signal.individual_signals).map(([name, value]) => (
                    <div key={name} className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">
                        {name.replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div className={`text-lg font-semibold ${getSignalColor(value as number)}`}>
                        {value > 0 ? '+' : ''}{value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                Last updated: {new Date(signal.date).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        {!signal && !error && !loading && (
          <div className="text-center py-8 text-gray-500">
            Enter a ticker symbol to check the latest trading signal
          </div>
        )}
      </div>
    </div>
  );
}
