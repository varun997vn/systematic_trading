'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Box, CircularProgress } from '@mui/material';
import { type PlotParams } from 'react-plotly.js';

const Plot = dynamic(() => import('react-plotly.js'), {
    ssr: false,
    loading: () => (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
            <CircularProgress />
        </Box>
    ),
});

// ============================================
// Line Chart Component
// ============================================

export interface LineChartData {
    x: string[] | number[];
    y: number[];
    name: string;
    color?: string;
}

export interface LineChartProps {
    data: LineChartData[];
    title?: string;
    height?: number;
    yAxisTitle?: string;
    xAxisTitle?: string;
}

export function LineChart({
                              data,
                              title = 'Line Chart',
                              height = 400,
                              yAxisTitle = '',
                              xAxisTitle = '',
                          }: LineChartProps) {
    const plotData: PlotParams['data'] = data.map((line) => ({
        type: 'scatter',
        mode: 'lines',
        x: line.x,
        y: line.y,
        name: line.name,
        line: {
            color: line.color || '#3b82f6',
            width: 2,
        },
        hovertemplate: '<b>%{fullData.name}</b><br>%{x}<br>%{y:.2f}<extra></extra>',
    }));

    const layout: PlotParams['layout'] = {
        title: {
            text: title,
            font: { size: 16, color: '#f1f5f9' },
        },
        autosize: true,
        height: height,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
        font: { color: '#94a3b8' },
        xaxis: {
            title: xAxisTitle,
            gridcolor: '#334155',
            showgrid: true,
        },
        yaxis: {
            title: yAxisTitle,
            gridcolor: '#334155',
            showgrid: true,
        },
        margin: { l: 60, r: 40, t: 60, b: 50 },
        legend: {
            x: 0.01,
            y: 0.99,
            bgcolor: 'rgba(30, 41, 59, 0.8)',
            bordercolor: '#334155',
            borderwidth: 1,
        },
        hovermode: 'x unified',
    };

    const config: PlotParams['config'] = {
        displayModeBar: true,
        displaylogo: false,
        responsive: true,
    };

    return (
        <Box sx={{ width: '100%' }}>
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%' }}
                useResizeHandler
            />
        </Box>
    );
}

// ============================================
// Performance Chart Component
// ============================================

export interface PerformanceData {
    dates: string[];
    portfolioValue: number[];
    benchmarkValue?: number[];
    drawdown?: number[];
}

export interface PerformanceChartProps {
    data: PerformanceData;
    title?: string;
    height?: number;
}

export function PerformanceChart({
                                     data,
                                     title = 'Portfolio Performance',
                                     height = 500,
                                 }: PerformanceChartProps) {
    const plotData: PlotParams['data'] = [
        {
            type: 'scatter',
            mode: 'lines',
            x: data.dates,
            y: data.portfolioValue,
            name: 'Portfolio',
            line: { color: '#3b82f6', width: 2 },
            yaxis: 'y',
        },
    ];

    if (data.benchmarkValue) {
        plotData.push({
            type: 'scatter',
            mode: 'lines',
            x: data.dates,
            y: data.benchmarkValue,
            name: 'Benchmark',
            line: { color: '#94a3b8', width: 2, dash: 'dash' },
            yaxis: 'y',
        });
    }

    if (data.drawdown) {
        plotData.push({
            type: 'scatter',
            mode: 'lines',
            x: data.dates,
            y: data.drawdown,
            name: 'Drawdown',
            fill: 'tozeroy',
            line: { color: '#ef4444', width: 1 },
            fillcolor: 'rgba(239, 68, 68, 0.2)',
            yaxis: 'y2',
        });
    }

    const layout: PlotParams['layout'] = {
        title: {
            text: title,
            font: { size: 18, color: '#f1f5f9' },
        },
        autosize: true,
        height: height,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
        font: { color: '#94a3b8' },
        xaxis: {
            gridcolor: '#334155',
            showgrid: true,
        },
        yaxis: {
            title: 'Portfolio Value ($)',
            domain: data.drawdown ? [0.3, 1] : [0, 1],
            gridcolor: '#334155',
            showgrid: true,
            tickformat: '$,.0f',
        },
        ...(data.drawdown && {
            yaxis2: {
                title: 'Drawdown (%)',
                domain: [0, 0.25],
                gridcolor: '#334155',
                showgrid: true,
                tickformat: '.1%',
            },
        }),
        margin: { l: 60, r: 40, t: 60, b: 50 },
        legend: {
            x: 0.01,
            y: 0.99,
            bgcolor: 'rgba(30, 41, 59, 0.8)',
            bordercolor: '#334155',
            borderwidth: 1,
        },
        hovermode: 'x unified',
    };

    const config: PlotParams['config'] = {
        displayModeBar: true,
        displaylogo: false,
        responsive: true,
    };

    return (
        <Box sx={{ width: '100%' }}>
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%' }}
                useResizeHandler
            />
        </Box>
    );
}

// ============================================
// Heatmap Chart Component (for correlation matrices)
// ============================================

export interface HeatmapChartProps {
    data: number[][];
    xLabels: string[];
    yLabels: string[];
    title?: string;
    height?: number;
    colorscale?: string;
}

export function HeatmapChart({
                                 data,
                                 xLabels,
                                 yLabels,
                                 title = 'Correlation Matrix',
                                 height = 500,
                                 colorscale = 'RdBu',
                             }: HeatmapChartProps) {
    const plotData: PlotParams['data'] = [
        {
            type: 'heatmap',
            z: data,
            x: xLabels,
            y: yLabels,
            colorscale: colorscale,
            hovertemplate: '<b>%{y} vs %{x}</b><br>Correlation: %{z:.2f}<extra></extra>',
            zmid: 0,
        },
    ];

    const layout: PlotParams['layout'] = {
        title: {
            text: title,
            font: { size: 18, color: '#f1f5f9' },
        },
        autosize: true,
        height: height,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94a3b8' },
        xaxis: {
            side: 'bottom',
        },
        yaxis: {
            autorange: 'reversed',
        },
        margin: { l: 100, r: 100, t: 60, b: 100 },
    };

    const config: PlotParams['config'] = {
        displayModeBar: true,
        displaylogo: false,
        responsive: true,
    };

    return (
        <Box sx={{ width: '100%' }}>
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%' }}
                useResizeHandler
            />
        </Box>
    );
}

// ============================================
// Distribution Chart (Histogram)
// ============================================

export interface DistributionChartProps {
    data: number[];
    title?: string;
    height?: number;
    xAxisTitle?: string;
    bins?: number;
}

export function DistributionChart({
                                      data,
                                      title = 'Distribution',
                                      height = 400,
                                      xAxisTitle = 'Value',
                                      bins = 50,
                                  }: DistributionChartProps) {
    const plotData: PlotParams['data'] = [
        {
            type: 'histogram',
            x: data,
            nbinsx: bins,
            marker: {
                color: '#3b82f6',
                line: { color: '#1e40af', width: 1 },
            },
            hovertemplate: '<b>Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>',
        },
    ];

    const layout: PlotParams['layout'] = {
        title: {
            text: title,
            font: { size: 16, color: '#f1f5f9' },
        },
        autosize: true,
        height: height,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
        font: { color: '#94a3b8' },
        xaxis: {
            title: xAxisTitle,
            gridcolor: '#334155',
            showgrid: true,
        },
        yaxis: {
            title: 'Frequency',
            gridcolor: '#334155',
            showgrid: true,
        },
        margin: { l: 60, r: 40, t: 60, b: 50 },
        bargap: 0.05,
    };

    const config: PlotParams['config'] = {
        displayModeBar: true,
        displaylogo: false,
        responsive: true,
    };

    return (
        <Box sx={{ width: '100%' }}>
            <Plot
                data={plotData}
                layout={layout}
                config={config}
                style={{ width: '100%' }}
                useResizeHandler
            />
        </Box>
    );
}

export default {
    LineChart,
    PerformanceChart,
    HeatmapChart,
    DistributionChart,
};