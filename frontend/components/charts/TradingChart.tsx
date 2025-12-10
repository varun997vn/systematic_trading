'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Box, CircularProgress } from '@mui/material';
import { type PlotParams } from 'react-plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), {
    ssr: false,
    loading: () => (
        <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            height={600}
        >
            <CircularProgress />
        </Box>
    ),
});

export interface CandlestickData {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume?: number[];
}

export interface SignalPoint {
    date: string;
    price: number;
    strength?: number;
    label?: string;
}

export interface TradingChartProps {
    data: CandlestickData;
    buySignals?: SignalPoint[];
    sellSignals?: SignalPoint[];
    title?: string;
    height?: number;
    showVolume?: boolean;
    showRangeslider?: boolean;
}

export function TradingChart({
                                 data,
                                 buySignals = [],
                                 sellSignals = [],
                                 title = 'Price Chart',
                                 height = 700,
                                 showVolume = true,
                                 showRangeslider = false,
                             }: TradingChartProps) {
    const plotData: PlotParams['data'] = [
        // Candlestick chart
        {
            type: 'candlestick',
            x: data.dates,
            open: data.open,
            high: data.high,
            low: data.low,
            close: data.close,
            name: 'Price',
            increasing: {
                line: { color: '#10b981', width: 1 },
                fillcolor: '#10b981',
            },
            decreasing: {
                line: { color: '#ef4444', width: 1 },
                fillcolor: '#ef4444',
            },
            yaxis: 'y',
            xaxis: 'x',
        },
    ];

    // Add buy signals
    if (buySignals.length > 0) {
        plotData.push({
            type: 'scatter',
            mode: 'markers+text',
            x: buySignals.map((s) => s.date),
            y: buySignals.map((s) => s.price),
            name: 'Buy Signal',
            text: buySignals.map((s) => s.label || ''),
            textposition: 'bottom center',
            marker: {
                color: '#10b981',
                size: 14,
                symbol: 'triangle-up',
                line: { color: '#065f46', width: 2 },
            },
            hovertemplate: '<b>Buy Signal</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>',
            yaxis: 'y',
            xaxis: 'x',
        });
    }

    // Add sell signals
    if (sellSignals.length > 0) {
        plotData.push({
            type: 'scatter',
            mode: 'markers+text',
            x: sellSignals.map((s) => s.date),
            y: sellSignals.map((s) => s.price),
            name: 'Sell Signal',
            text: sellSignals.map((s) => s.label || ''),
            textposition: 'top center',
            marker: {
                color: '#ef4444',
                size: 14,
                symbol: 'triangle-down',
                line: { color: '#991b1b', width: 2 },
            },
            hovertemplate: '<b>Sell Signal</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>',
            yaxis: 'y',
            xaxis: 'x',
        });
    }

    // Add volume bars
    if (showVolume && data.volume) {
        const volumeColors = data.close.map((close, i) => {
            if (i === 0) return 'rgba(16, 185, 129, 0.4)';
            return close >= data.close[i - 1]
                ? 'rgba(16, 185, 129, 0.4)'
                : 'rgba(239, 68, 68, 0.4)';
        });

        plotData.push({
            type: 'bar',
            x: data.dates,
            y: data.volume,
            name: 'Volume',
            yaxis: 'y2',
            xaxis: 'x',
            marker: {
                color: volumeColors,
            },
            hovertemplate: '<b>Volume</b><br>%{y:,.0f}<extra></extra>',
        });
    }

    const layout: PlotParams['layout'] = {
        title: {
            text: title,
            font: { size: 18, color: '#f1f5f9', family: 'Inter, sans-serif' },
        },
        autosize: true,
        height: height,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
        font: { color: '#94a3b8', family: 'Inter, sans-serif' },
        xaxis: {
            domain: [0, 1],
            rangeslider: { visible: showRangeslider },
            gridcolor: '#334155',
            showgrid: true,
            type: 'date',
        },
        yaxis: {
            domain: showVolume ? [0.25, 1] : [0, 1],
            gridcolor: '#334155',
            showgrid: true,
            side: 'right',
            tickformat: '$.2f',
        },
        ...(showVolume &&
            data.volume && {
                yaxis2: {
                    domain: [0, 0.2],
                    gridcolor: '#334155',
                    showgrid: false,
                    side: 'right',
                },
            }),
        margin: { l: 50, r: 80, t: 60, b: 50 },
        legend: {
            x: 0.01,
            y: 0.99,
            orientation: 'h',
            bgcolor: 'rgba(30, 41, 59, 0.8)',
            bordercolor: '#334155',
            borderwidth: 1,
        },
        hovermode: 'x unified',
        dragmode: 'zoom',
    };

    const config: PlotParams['config'] = {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
        responsive: true,
    };

    return (
        <Box sx={{ width: '100%', height: '100%' }}>
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
            />
        </Box>
    );
}

export default TradingChart;