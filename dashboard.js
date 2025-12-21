/**
 * Hydroinformatics Dashboard
 * Interactive data visualization for water resources research
 * Author: Duc Tran
 */

// Dashboard Configuration
const CONFIG = {
    apiEndpoints: {
        github: 'https://api.github.com',
        scholar: 'https://scholar.google.com',
        usgs: 'https://waterservices.usgs.gov/nwis'
    },
    refreshInterval: 300000, // 5 minutes
    chartColors: {
        primary: '#0366d6',
        secondary: '#c5a059',
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545',
        info: '#17a2b8'
    },
    themes: {
        dark: {
            background: '#1a1b27',
            cardBg: '#24283b',
            text: '#c9d1d9',
            border: '#30363d'
        },
        light: {
            background: '#ffffff',
            cardBg: '#f6f8fa',
            text: '#24292f',
            border: '#d0d7de'
        }
    }
};

// Utility Functions
const Utils = {
    /**
     * Format number with commas
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function calls
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in ms
     * @returns {Function} Throttled function
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Deep clone an object
     * @param {Object} obj - Object to clone
     * @returns {Object} Cloned object
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * Generate unique ID
     * @returns {string} Unique ID
     */
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Parse date string to Date object
     * @param {string} dateStr - Date string
     * @returns {Date} Date object
     */
    parseDate(dateStr) {
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? null : date;
    },

    /**
     * Format date for display
     * @param {Date} date - Date object
     * @param {string} format - Format string
     * @returns {string} Formatted date
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        const pad = (n) => n.toString().padStart(2, '0');
        const year = date.getFullYear();
        const month = pad(date.getMonth() + 1);
        const day = pad(date.getDate());
        const hour = pad(date.getHours());
        const minute = pad(date.getMinutes());
        const second = pad(date.getSeconds());

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hour)
            .replace('mm', minute)
            .replace('ss', second);
    }
};

// Data Processing Module
const DataProcessor = {
    /**
     * Calculate statistics for a dataset
     * @param {Array<number>} data - Array of numbers
     * @returns {Object} Statistics object
     */
    calculateStats(data) {
        if (!data || data.length === 0) return null;

        const sorted = [...data].sort((a, b) => a - b);
        const sum = data.reduce((a, b) => a + b, 0);
        const mean = sum / data.length;
        const median = sorted.length % 2 === 0
            ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
            : sorted[Math.floor(sorted.length / 2)];

        const squaredDiffs = data.map(value => Math.pow(value - mean, 2));
        const variance = squaredDiffs.reduce((a, b) => a + b, 0) / data.length;
        const stdDev = Math.sqrt(variance);

        return {
            count: data.length,
            sum,
            mean,
            median,
            min: sorted[0],
            max: sorted[sorted.length - 1],
            range: sorted[sorted.length - 1] - sorted[0],
            variance,
            stdDev,
            q1: sorted[Math.floor(sorted.length * 0.25)],
            q3: sorted[Math.floor(sorted.length * 0.75)]
        };
    },

    /**
     * Normalize data to 0-1 range
     * @param {Array<number>} data - Array of numbers
     * @returns {Array<number>} Normalized data
     */
    normalize(data) {
        const min = Math.min(...data);
        const max = Math.max(...data);
        const range = max - min;
        return data.map(value => range === 0 ? 0 : (value - min) / range);
    },

    /**
     * Calculate moving average
     * @param {Array<number>} data - Array of numbers
     * @param {number} window - Window size
     * @returns {Array<number>} Moving averages
     */
    movingAverage(data, window) {
        const result = [];
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - window + 1);
            const subset = data.slice(start, i + 1);
            result.push(subset.reduce((a, b) => a + b, 0) / subset.length);
        }
        return result;
    },

    /**
     * Detect outliers using IQR method
     * @param {Array<number>} data - Array of numbers
     * @returns {Object} Outliers info
     */
    detectOutliers(data) {
        const sorted = [...data].sort((a, b) => a - b);
        const q1 = sorted[Math.floor(sorted.length * 0.25)];
        const q3 = sorted[Math.floor(sorted.length * 0.75)];
        const iqr = q3 - q1;
        const lowerBound = q1 - 1.5 * iqr;
        const upperBound = q3 + 1.5 * iqr;

        const outliers = data.filter(v => v < lowerBound || v > upperBound);
        const inliers = data.filter(v => v >= lowerBound && v <= upperBound);

        return { outliers, inliers, lowerBound, upperBound, iqr };
    },

    /**
     * Linear regression
     * @param {Array<number>} x - X values
     * @param {Array<number>} y - Y values
     * @returns {Object} Regression coefficients
     */
    linearRegression(x, y) {
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((total, xi, i) => total + xi * y[i], 0);
        const sumXX = x.reduce((total, xi) => total + xi * xi, 0);

        const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;

        // Calculate R-squared
        const yMean = sumY / n;
        const ssTotal = y.reduce((total, yi) => total + Math.pow(yi - yMean, 2), 0);
        const ssResidual = y.reduce((total, yi, i) => {
            const predicted = slope * x[i] + intercept;
            return total + Math.pow(yi - predicted, 2);
        }, 0);
        const rSquared = 1 - ssResidual / ssTotal;

        return { slope, intercept, rSquared };
    }
};

// Chart Builder Module
const ChartBuilder = {
    /**
     * Create a line chart configuration
     * @param {Object} options - Chart options
     * @returns {Object} Chart configuration
     */
    createLineChart(options) {
        const { labels, datasets, title, xLabel, yLabel } = options;

        return {
            type: 'line',
            data: {
                labels,
                datasets: datasets.map((ds, index) => ({
                    label: ds.label,
                    data: ds.data,
                    borderColor: ds.color || Object.values(CONFIG.chartColors)[index],
                    backgroundColor: (ds.color || Object.values(CONFIG.chartColors)[index]) + '20',
                    fill: ds.fill || false,
                    tension: ds.tension || 0.4,
                    pointRadius: ds.pointRadius || 3
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: !!title, text: title },
                    legend: { position: 'top' }
                },
                scales: {
                    x: { title: { display: !!xLabel, text: xLabel } },
                    y: { title: { display: !!yLabel, text: yLabel } }
                }
            }
        };
    },

    /**
     * Create a bar chart configuration
     * @param {Object} options - Chart options
     * @returns {Object} Chart configuration
     */
    createBarChart(options) {
        const { labels, datasets, title, horizontal } = options;

        return {
            type: 'bar',
            data: {
                labels,
                datasets: datasets.map((ds, index) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: ds.colors || Object.values(CONFIG.chartColors)[index],
                    borderRadius: 4
                }))
            },
            options: {
                indexAxis: horizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: !!title, text: title },
                    legend: { display: datasets.length > 1 }
                }
            }
        };
    },

    /**
     * Create a pie/doughnut chart configuration
     * @param {Object} options - Chart options
     * @returns {Object} Chart configuration
     */
    createPieChart(options) {
        const { labels, data, title, doughnut } = options;

        return {
            type: doughnut ? 'doughnut' : 'pie',
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: Object.values(CONFIG.chartColors)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: !!title, text: title },
                    legend: { position: 'right' }
                }
            }
        };
    },

    /**
     * Create a scatter plot configuration
     * @param {Object} options - Chart options
     * @returns {Object} Chart configuration
     */
    createScatterPlot(options) {
        const { datasets, title, xLabel, yLabel } = options;

        return {
            type: 'scatter',
            data: {
                datasets: datasets.map((ds, index) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: ds.color || Object.values(CONFIG.chartColors)[index],
                    pointRadius: ds.pointRadius || 5
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: !!title, text: title }
                },
                scales: {
                    x: { title: { display: !!xLabel, text: xLabel } },
                    y: { title: { display: !!yLabel, text: yLabel } }
                }
            }
        };
    }
};

// API Client Module
const APIClient = {
    /**
     * Fetch data from URL with error handling
     * @param {string} url - URL to fetch
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    async fetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Accept': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API fetch error: ${error.message}`);
            throw error;
        }
    },

    /**
     * Fetch GitHub user data
     * @param {string} username - GitHub username
     * @returns {Promise<Object>} User data
     */
    async getGitHubUser(username) {
        return this.fetch(`${CONFIG.apiEndpoints.github}/users/${username}`);
    },

    /**
     * Fetch GitHub repositories
     * @param {string} username - GitHub username
     * @returns {Promise<Array>} Repositories
     */
    async getGitHubRepos(username) {
        return this.fetch(
            `${CONFIG.apiEndpoints.github}/users/${username}/repos?sort=updated&per_page=100`
        );
    },

    /**
     * Fetch USGS streamflow data
     * @param {string} siteCode - USGS site code
     * @param {string} startDate - Start date
     * @param {string} endDate - End date
     * @returns {Promise<Object>} Streamflow data
     */
    async getUSGSStreamflow(siteCode, startDate, endDate) {
        const url = `${CONFIG.apiEndpoints.usgs}/iv/?format=json&sites=${siteCode}&startDT=${startDate}&endDT=${endDate}&parameterCd=00060`;
        return this.fetch(url);
    }
};

// Dashboard State Management
class DashboardState {
    constructor() {
        this.state = {
            theme: 'dark',
            data: {},
            filters: {},
            charts: [],
            loading: false,
            error: null
        };
        this.listeners = [];
    }

    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return Utils.deepClone(this.state);
    }

    /**
     * Update state
     * @param {Object} updates - State updates
     */
    setState(updates) {
        this.state = { ...this.state, ...updates };
        this.notifyListeners();
    }

    /**
     * Subscribe to state changes
     * @param {Function} listener - Listener function
     * @returns {Function} Unsubscribe function
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    /**
     * Notify all listeners
     */
    notifyListeners() {
        this.listeners.forEach(listener => listener(this.state));
    }
}

// Dashboard Component
class HydroDashboard {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.state = new DashboardState();
        this.charts = new Map();

        this.init();
    }

    /**
     * Initialize dashboard
     */
    async init() {
        this.state.setState({ loading: true });

        try {
            await this.loadData();
            this.render();
            this.setupEventListeners();
        } catch (error) {
            this.state.setState({ error: error.message });
            console.error('Dashboard init error:', error);
        } finally {
            this.state.setState({ loading: false });
        }
    }

    /**
     * Load initial data
     */
    async loadData() {
        const [githubData] = await Promise.all([
            APIClient.getGitHubRepos('ductran27')
        ]);

        this.state.setState({
            data: {
                github: githubData
            }
        });
    }

    /**
     * Render dashboard
     */
    render() {
        if (!this.container) return;

        const state = this.state.getState();

        if (state.loading) {
            this.container.innerHTML = '<div class="loading">Loading dashboard...</div>';
            return;
        }

        if (state.error) {
            this.container.innerHTML = `<div class="error">Error: ${state.error}</div>`;
            return;
        }

        this.container.innerHTML = `
            <div class="dashboard-header">
                <h1>Hydroinformatics Dashboard</h1>
                <div class="controls">
                    <button id="refreshBtn">Refresh</button>
                    <button id="themeBtn">Toggle Theme</button>
                </div>
            </div>
            <div class="dashboard-grid">
                <div class="card" id="statsCard">
                    <h3>Repository Statistics</h3>
                    <div id="statsContent"></div>
                </div>
                <div class="card" id="languagesCard">
                    <h3>Languages</h3>
                    <canvas id="languagesChart"></canvas>
                </div>
                <div class="card" id="activityCard">
                    <h3>Recent Activity</h3>
                    <canvas id="activityChart"></canvas>
                </div>
            </div>
        `;

        this.renderStats();
        this.renderCharts();
    }

    /**
     * Render statistics
     */
    renderStats() {
        const data = this.state.getState().data.github || [];
        const stats = {
            totalRepos: data.length,
            totalStars: data.reduce((sum, r) => sum + r.stargazers_count, 0),
            totalForks: data.reduce((sum, r) => sum + r.forks_count, 0),
            languages: [...new Set(data.map(r => r.language).filter(Boolean))]
        };

        const statsContent = document.getElementById('statsContent');
        if (statsContent) {
            statsContent.innerHTML = `
                <div class="stat"><span class="value">${stats.totalRepos}</span><span class="label">Repositories</span></div>
                <div class="stat"><span class="value">${stats.totalStars}</span><span class="label">Stars</span></div>
                <div class="stat"><span class="value">${stats.totalForks}</span><span class="label">Forks</span></div>
                <div class="stat"><span class="value">${stats.languages.length}</span><span class="label">Languages</span></div>
            `;
        }
    }

    /**
     * Render charts
     */
    renderCharts() {
        // Languages chart would be rendered here with Chart.js
        console.log('Charts rendered');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const refreshBtn = document.getElementById('refreshBtn');
        const themeBtn = document.getElementById('themeBtn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.init());
        }

        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const currentTheme = this.state.getState().theme;
                this.state.setState({
                    theme: currentTheme === 'dark' ? 'light' : 'dark'
                });
                this.render();
            });
        }
    }

    /**
     * Destroy dashboard
     */
    destroy() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CONFIG,
        Utils,
        DataProcessor,
        ChartBuilder,
        APIClient,
        DashboardState,
        HydroDashboard
    };
}

// Auto-initialize if dashboard container exists
document.addEventListener('DOMContentLoaded', () => {
    const dashboardContainer = document.getElementById('hydroDashboard');
    if (dashboardContainer) {
        window.hydroDashboard = new HydroDashboard('hydroDashboard');
    }
});
