'use client';

import { useState } from 'react';
import api from '@/lib/api';

export default function TickerSearch() {
  const [ticker, setTicker] = useState('');
  const [tickers, setTickers] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSingleDownload = async () => {
    if (!ticker.trim()) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await api.data.downloadTicker(ticker.toUpperCase());
      setMessage({ type: 'success', text: result.message });
      setTicker('');
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to download ticker data' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMultipleDownload = async () => {
    const tickerList = tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
    
    if (tickerList.length === 0) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await api.data.downloadMultiple(tickerList);
      setMessage({ type: 'success', text: result.message });
      setTickers('');
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to download ticker data' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Management</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        {message && (
          <div className={`mb-4 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            <p className={`text-sm ${
              message.type === 'success' ? 'text-green-800' : 'text-red-800'
            }`}>
              {message.text}
            </p>
          </div>
        )}

        <div className="space-y-4">
          {/* Single Ticker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Download Single Ticker
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="e.g., AAPL"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={handleSingleDownload}
                disabled={loading || !ticker.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                Download
              </button>
            </div>
          </div>

          {/* Multiple Tickers */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Download Multiple Tickers (comma-separated)
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={tickers}
                onChange={(e) => setTickers(e.target.value)}
                placeholder="e.g., AAPL, MSFT, GOOGL"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={handleMultipleDownload}
                disabled={loading || !tickers.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                Download All
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Downloads will process in the background. Data will be available for analysis once complete.
          </p>
        </div>
      </div>
    </div>
  );
}
