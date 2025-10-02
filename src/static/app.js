// DTCC Trade Analysis Dashboard JavaScript

class DTCCDashboard {
    constructor() {
        this.selectedCurrencies = [];
        this.availableCurrencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD'];
        this.majorCurrencies = ['USD', 'EUR', 'GBP', 'JPY'];
        this.asianCurrencies = ['INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD'];
        this.currentView = 'grouped';
        this.refreshInterval = null;
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.setupMultiSelect();
        await this.loadInitialData();
        this.startAutoRefresh();
        this.showToast('Dashboard initialized successfully', 'success');
    }
    
    setupEventListeners() {
        // Filter controls (only if they exist)
        const applyFiltersBtn = document.getElementById('applyFilters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }
        
        const clearCurrenciesBtn = document.getElementById('clearCurrencies');
        if (clearCurrenciesBtn) {
            clearCurrenciesBtn.addEventListener('click', () => this.clearAllCurrencies());
        }
        
        const resetFiltersBtn = document.getElementById('resetFilters');
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        }
        
        const manualRunBtn = document.getElementById('manualRun');
        if (manualRunBtn) {
            manualRunBtn.addEventListener('click', () => this.triggerManualRun());
        }
        
        // Manual refresh button
        const manualRefreshBtn = document.getElementById('manualRefresh');
        if (manualRefreshBtn) {
            manualRefreshBtn.addEventListener('click', () => this.triggerManualRefresh());
        }
        
        // Currency quick select buttons (only if they exist)
        const selectMajorBtn = document.getElementById('selectMajor');
        if (selectMajorBtn) {
            selectMajorBtn.addEventListener('click', () => this.selectCurrencyGroup('major'));
        }
        
        const selectAsianBtn = document.getElementById('selectAsian');
        if (selectAsianBtn) {
            selectAsianBtn.addEventListener('click', () => this.selectCurrencyGroup('asian'));
        }
        
        const selectAllBtn = document.getElementById('selectAll');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectCurrencyGroup('all'));
        }
        
        const clearAllBtn = document.getElementById('clearAll');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.selectCurrencyGroup('clear'));
        }
        
        // Date quick select buttons (only if they exist)
        const todayBtn = document.getElementById('today');
        if (todayBtn) {
            todayBtn.addEventListener('click', () => this.setDateRange('today'));
        }
        
        const last7daysBtn = document.getElementById('last7days');
        if (last7daysBtn) {
            last7daysBtn.addEventListener('click', () => this.setDateRange('7days'));
        }
        
        const last30daysBtn = document.getElementById('last30days');
        if (last30daysBtn) {
            last30daysBtn.addEventListener('click', () => this.setDateRange('30days'));
        }
        
        // View toggle
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchView(e.target.dataset.view));
        });
        
        // Refresh logs
        const refreshLogsBtn = document.getElementById('refreshLogs');
        if (refreshLogsBtn) {
            refreshLogsBtn.addEventListener('click', () => this.loadProcessingStatus());
        }
        
        // Toggle Trades Report
        const toggleTradesReportBtn = document.getElementById('toggleTradesReport');
        if (toggleTradesReportBtn) {
            toggleTradesReportBtn.addEventListener('click', () => this.toggleTradesReport());
        }
        
        // Toggle Processing Status
        const toggleProcessingStatusBtn = document.getElementById('toggleProcessingStatus');
        if (toggleProcessingStatusBtn) {
            toggleProcessingStatusBtn.addEventListener('click', () => this.toggleProcessingStatus());
        }
        
        // MCP Queries
        this.setupMCPEventListeners();
        
        // Date inputs (only if they exist)
        const startDateInput = document.getElementById('startDate');
        if (startDateInput) {
            startDateInput.addEventListener('change', () => this.validateDateRange());
        }
        
        const endDateInput = document.getElementById('endDate');
        if (endDateInput) {
            endDateInput.addEventListener('change', () => this.validateDateRange());
        }
    }
    
    setupMultiSelect() {
        const multiSelect = document.getElementById('currencySelect');
        const display = document.getElementById('currencyDisplay');
        const dropdown = document.getElementById('currencyDropdown');
        const searchInput = document.getElementById('currencySearch');
        const optionsContainer = document.getElementById('currencyOptions');
        
        if (!multiSelect || !display || !dropdown || !searchInput || !optionsContainer) {
            return; // Elements don't exist, skip setup
        }
        
        display.addEventListener('click', () => {
            multiSelect.classList.toggle('open');
            if (multiSelect.classList.contains('open')) {
                searchInput.focus();
            }
        });
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {
            this.filterCurrencies(e.target.value);
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!multiSelect.contains(e.target)) {
                multiSelect.classList.remove('open');
            }
        });
    }
    
    async loadInitialData() {
        try {
            this.updateStatus('loading', 'Loading initial data...');
            
            // Populate currency options (only if elements exist)
            this.populateCurrencyOptions();
            
            // Set default date range (last 7 days) - only if elements exist
            this.setDateRange('7days');
            
            // Set default currencies (major currencies) - only if elements exist
            this.selectedCurrencies = [...this.majorCurrencies];
            this.updateCurrencyDisplay();
            this.updateCurrencyCheckboxes();
            
            // Load initial data
            await Promise.all([
                this.loadCommentary(),
                this.loadSummary(),
                this.loadProcessingStatus()
            ]);
            
            this.updateStatus('online', 'Connected');
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.updateStatus('error', 'Connection failed');
            this.showToast('Failed to load initial data', 'error');
        }
    }
    
    populateCurrencyOptions() {
        const optionsContainer = document.getElementById('currencyOptions');
        if (!optionsContainer) return; // Element doesn't exist, skip
        
        optionsContainer.innerHTML = '';
        
        this.availableCurrencies.forEach(currency => {
            const option = document.createElement('div');
            option.className = 'multi-select-option';
            option.innerHTML = `
                <input type="checkbox" id="currency-${currency}" value="${currency}">
                <label for="currency-${currency}">${currency}</label>
            `;
            
            const checkbox = option.querySelector('input');
            checkbox.addEventListener('change', () => this.toggleCurrency(currency));
            
            optionsContainer.appendChild(option);
        });
    }
    
    selectCurrencyGroup(group) {
        switch (group) {
            case 'major':
                this.selectedCurrencies = [...this.majorCurrencies];
                break;
            case 'asian':
                this.selectedCurrencies = [...this.asianCurrencies];
                break;
            case 'all':
                this.selectedCurrencies = [...this.availableCurrencies];
                break;
            case 'clear':
                this.selectedCurrencies = [];
                break;
        }
        
        this.updateCurrencyDisplay();
        this.updateCurrencyCheckboxes();
        this.showToast(`${group === 'clear' ? 'Cleared' : 'Selected'} ${group} currencies`, 'info');
    }
    
    setDateRange(range) {
        const endDate = new Date();
        let startDate = new Date();
        
        switch (range) {
            case 'today':
                startDate = new Date();
                break;
            case '7days':
                startDate.setDate(startDate.getDate() - 7);
                break;
            case '30days':
                startDate.setDate(startDate.getDate() - 30);
                break;
        }
        
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput) {
            startDateInput.value = startDate.toISOString().split('T')[0];
        }
        if (endDateInput) {
            endDateInput.value = endDate.toISOString().split('T')[0];
        }
        
        this.showToast(`Date range set to ${range}`, 'info');
    }
    
    toggleCurrency(currency) {
        const index = this.selectedCurrencies.indexOf(currency);
        if (index > -1) {
            this.selectedCurrencies.splice(index, 1);
        } else {
            this.selectedCurrencies.push(currency);
        }
        
        this.updateCurrencyDisplay();
        this.updateCurrencyCheckboxes();
    }
    
    updateCurrencyDisplay() {
        const display = document.getElementById('currencyDisplay');
        if (!display) return; // Element doesn't exist, skip
        
        if (this.selectedCurrencies.length === 0) {
            display.textContent = 'Select currencies...';
        } else if (this.selectedCurrencies.length === 1) {
            display.textContent = this.selectedCurrencies[0];
        } else {
            display.textContent = `${this.selectedCurrencies.length} currencies selected`;
        }
    }
    
    updateCurrencyCheckboxes() {
        this.availableCurrencies.forEach(currency => {
            const checkbox = document.getElementById(`currency-${currency}`);
            const option = checkbox?.closest('.multi-select-option');
            
            if (checkbox) {
                checkbox.checked = this.selectedCurrencies.includes(currency);
                option?.classList.toggle('selected', checkbox.checked);
            }
        });
    }
    
    filterCurrencies(searchTerm) {
        const options = document.querySelectorAll('#currencyOptions .multi-select-option');
        const term = searchTerm.toLowerCase();
        
        options.forEach(option => {
            const currency = option.querySelector('label').textContent.toLowerCase();
            const matches = currency.includes(term);
            option.style.display = matches ? 'block' : 'none';
        });
    }
    
    clearAllCurrencies() {
        // Clear selected currencies
        this.selectedCurrencies = [];
        
        // Update display
        this.updateCurrencyDisplay();
        
        // Update checkboxes
        this.updateCurrencyCheckboxes();
        
        // Clear search input
        const searchInput = document.getElementById('currencySearch');
        if (searchInput) {
            searchInput.value = '';
            this.filterCurrencies(''); // Show all options
        }
        
        // Show success message
        this.showToast('All currencies cleared', 'info');
    }
    
    validateDateRange() {
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (!startDateInput || !endDateInput) return; // Elements don't exist, skip
        
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            this.showToast('Start date cannot be after end date', 'warning');
            return false;
        }
        
        return true;
    }
    
    async triggerManualRefresh() {
        const button = document.getElementById('manualRefresh');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        button.disabled = true;
        
        try {
            this.updateStatus('processing', 'Force refreshing data...');
            
            // Use the dedicated manual-refresh endpoint
            const response = await fetch('/api/manual-refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Data refreshed successfully', 'success');
                
                // Wait a moment for processing to complete
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Reload all data
                await Promise.all([
                    this.loadCommentary(),
                    this.loadSummary(),
                    this.loadProcessingStatus()
                ]);
                
                this.updateStatus('online', 'Connected');
                this.showToast('Page data reloaded', 'success');
                
            } else {
                this.showToast('Manual refresh failed: ' + data.error, 'error');
                this.updateStatus('error', 'Refresh failed');
            }
            
        } catch (error) {
            console.error('Error during manual refresh:', error);
            this.showToast('Failed to refresh data', 'error');
            this.updateStatus('error', 'Refresh failed');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    async applyFilters() {
        if (!this.validateDateRange()) return;
        
        if (this.selectedCurrencies.length === 0) {
            this.showToast('Please select at least one currency', 'warning');
            return;
        }
        
        this.updateStatus('processing', 'Applying filters...');
        
        try {
            await Promise.all([
                this.loadCommentary(),
                this.loadSummary()
            ]);
            
            this.updateStatus('online', 'Connected');
            this.showToast('Filters applied successfully', 'success');
            
        } catch (error) {
            console.error('Error applying filters:', error);
            this.updateStatus('error', 'Filter error');
            this.showToast('Failed to apply filters', 'error');
        }
    }
    
    resetFilters() {
        // Reset to default values
        this.setDateRange('7days');
        this.selectedCurrencies = [...this.majorCurrencies];
        this.updateCurrencyDisplay();
        this.updateCurrencyCheckboxes();
        
        this.applyFilters();
        this.showToast('Filters reset to defaults', 'info');
    }
    
    async triggerManualRun() {
        const button = document.getElementById('manualRun');
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/manual-run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type: 'both' })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Manual run completed successfully', 'success');
                // Refresh data after manual run
                setTimeout(() => {
                    this.loadCommentary();
                    this.loadSummary();
                    this.loadProcessingStatus();
                }, 2000);
            } else {
                this.showToast('Manual run failed: ' + data.error, 'error');
            }
            
        } catch (error) {
            console.error('Error triggering manual run:', error);
            this.showToast('Failed to trigger manual run', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    switchView(view) {
        this.currentView = view;
        
        // Update toggle buttons
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        // Re-render commentary with new view
        this.renderCommentary();
    }
    
    async loadCommentary() {
        try {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate
            });
            
            this.selectedCurrencies.forEach(currency => {
                params.append('currencies', currency);
            });
            
            const response = await fetch(`/api/commentary?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.commentaryData = data.data;
                this.renderCommentary();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Error loading commentary:', error);
            this.showCommentaryError('Failed to load commentary data');
        }
    }
    
    renderCommentary() {
        const container = document.getElementById('commentaryContainer');
        
        if (!this.commentaryData || Object.keys(this.commentaryData).length === 0) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-info-circle"></i>
                    <p>No commentary data available for the selected filters</p>
                </div>
            `;
            return;
        }
        
        if (this.currentView === 'grouped') {
            this.renderGroupedCommentary(container);
        } else {
            this.renderCurrencyCommentary(container);
        }
    }
    
    renderGroupedCommentary(container) {
        const dates = Object.keys(this.commentaryData).sort().reverse();
        
        let html = '';
        dates.forEach(date => {
            const dateData = this.commentaryData[date];
            const formattedDate = new Date(date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            html += `
                <div class="commentary-date-group">
                    <div class="date-header">
                        <i class="fas fa-calendar-day"></i>
                        ${formattedDate}
                    </div>
            `;
            
            Object.keys(dateData).forEach(currency => {
                const commentary = dateData[currency];
                html += this.renderCurrencyCommentaryBlock(currency, commentary);
            });
            
            html += '</div>';
        });
        
        container.innerHTML = html;
    }
    
    renderCurrencyCommentary(container) {
        const currencies = {};
        
        // Group by currency
        Object.keys(this.commentaryData).forEach(date => {
            Object.keys(this.commentaryData[date]).forEach(currency => {
                if (!currencies[currency]) {
                    currencies[currency] = [];
                }
                currencies[currency].push({
                    date,
                    ...this.commentaryData[date][currency]
                });
            });
        });
        
        let html = '';
        Object.keys(currencies).sort().forEach(currency => {
            const commentaries = currencies[currency].sort((a, b) => new Date(b.date) - new Date(a.date));
            
            html += `
                <div class="commentary-date-group">
                    <div class="date-header">
                        <span class="currency-badge">${currency}</span>
                        ${commentaries.length} commentary entries
                    </div>
            `;
            
            commentaries.forEach(commentary => {
                const formattedDate = new Date(commentary.date).toLocaleDateString();
                html += `
                    <div class="currency-commentary">
                        <div class="currency-header">
                            <span style="font-weight: 600;">${formattedDate}</span>
                        </div>
                        <div class="commentary-text">${commentary.commentary_text}</div>
                    </div>
                `;
            });
            
            html += '</div>';
        });
        
        container.innerHTML = html;
    }
    
    renderCurrencyCommentaryBlock(currency, commentary) {
        return `
            <div class="currency-commentary">
                <div class="currency-header">
                    <span class="currency-badge">${currency}</span>
                </div>
                <div class="commentary-text">${commentary.commentary_text}</div>
            </div>
        `;
    }
    
    showCommentaryError(message) {
        const container = document.getElementById('commentaryContainer');
        container.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    async loadSummary() {
        try {
            // Update last update time
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }
    
    updateLastUpdateTime() {
        const lastUpdateElement = document.getElementById('lastUpdateDisplay');
        if (lastUpdateElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            lastUpdateElement.querySelector('span').textContent = `Last Update: ${timeString}`;
        }
    }
    
    async loadProcessingStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.renderProcessingLogs(data.status.recent_logs || []);
                
                // Update status indicator
                if (data.status.running) {
                    this.updateStatus('online', 'Processing active');
                } else {
                    this.updateStatus('error', 'Processing stopped');
                }
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Error loading processing status:', error);
            this.updateStatus('error', 'Status unavailable');
        }
    }
    
    renderProcessingLogs(logs) {
        const container = document.getElementById('logsContainer');
        const expandable = document.getElementById('logsExpandable');
        
        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-info-circle"></i>
                    <p>No processing logs available</p>
                </div>
            `;
            expandable.innerHTML = '';
            return;
        }
        
        // Show first log in main container
        const firstLog = logs[0];
        const firstTime = new Date(firstLog.run_timestamp).toLocaleString();
        const firstStatusClass = firstLog.status;
        
        container.innerHTML = `
            <div class="log-item">
                <div class="log-entry">
                    <div class="log-status ${firstStatusClass}"></div>
                    <div class="log-content">
                        <div class="log-type">${firstLog.process_type.toUpperCase()}</div>
                        <div class="log-time">${firstTime}</div>
                        <div class="log-details">
                            ${firstLog.status === 'success' ? 
                                `Processed ${firstLog.records_processed} records in ${firstLog.execution_time_seconds?.toFixed(2)}s` :
                                firstLog.error_message || 'Processing...'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Show remaining logs in expandable container
        if (logs.length > 1) {
            let expandableHtml = '';
            logs.slice(1).forEach(log => {
                const time = new Date(log.run_timestamp).toLocaleString();
                const statusClass = log.status;
                
                expandableHtml += `
                    <div class="log-item">
                        <div class="log-entry">
                            <div class="log-status ${statusClass}"></div>
                            <div class="log-content">
                                <div class="log-type">${log.process_type.toUpperCase()}</div>
                                <div class="log-time">${time}</div>
                                <div class="log-details">
                                    ${log.status === 'success' ? 
                                        `Processed ${log.records_processed} records in ${log.execution_time_seconds?.toFixed(2)}s` :
                                        log.error_message || 'Processing...'
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            expandable.innerHTML = expandableHtml;
        } else {
            expandable.innerHTML = '';
        }
    }
    
    updateStatus(status, text) {
        const dot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        dot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }
    
    formatDV01(value) {
        if (!value || value === 0) return '0';
        
        const absValue = Math.abs(value);
        if (absValue >= 1000000) {
            return `${(value / 1000000).toFixed(1)}M`;
        } else if (absValue >= 1000) {
            return `${(value / 1000).toFixed(0)}k`;
        } else {
            return value.toFixed(0);
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        }[type] || 'fas fa-info-circle';
        
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    
    startAutoRefresh() {
        // Refresh data every 2 minutes
        this.refreshInterval = setInterval(() => {
            this.loadCommentary();
            this.loadSummary();
            this.loadProcessingStatus();
        }, 120000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Trades Report Toggle
    toggleTradesReport() {
        const container = document.getElementById('commentaryContainer');
        const controls = document.getElementById('tradesReportControls');
        const filters = document.getElementById('compactFilters');
        const toggleBtn = document.getElementById('toggleTradesReport');
        const icon = toggleBtn.querySelector('i');
        
        if (container.style.display === 'none') {
            // Expand
            container.style.display = 'block';
            controls.style.display = 'flex';
            filters.style.display = 'block';
            toggleBtn.classList.add('expanded');
            icon.className = 'fas fa-chevron-up';
            
            // Load commentary data if not already loaded
            this.loadCommentary();
        } else {
            // Collapse
            container.style.display = 'none';
            controls.style.display = 'none';
            filters.style.display = 'none';
            toggleBtn.classList.remove('expanded');
            icon.className = 'fas fa-chevron-down';
        }
    }

    // Processing Status Toggle
    toggleProcessingStatus() {
        const container = document.getElementById('logsContainer');
        const expandable = document.getElementById('logsExpandable');
        const toggleBtn = document.getElementById('toggleProcessingStatus');
        const icon = toggleBtn.querySelector('i');
        
        if (container.classList.contains('expanded')) {
            // Collapse - show only first item
            container.classList.remove('expanded');
            expandable.style.display = 'none';
            toggleBtn.classList.remove('expanded');
            icon.className = 'fas fa-chevron-down';
        } else {
            // Expand - show all items
            container.classList.add('expanded');
            expandable.style.display = 'block';
            toggleBtn.classList.add('expanded');
            icon.className = 'fas fa-chevron-up';
        }
    }

    // MCP Queries functionality
    setupMCPEventListeners() {
        // Query execution
        document.getElementById('executeQuery').addEventListener('click', () => this.executeMCPQuery());
        document.getElementById('mcpQueryInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeMCPQuery();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.dataset.query;
                document.getElementById('mcpQueryInput').value = query;
                this.executeMCPQuery();
            });
        });

        // History toggle
        document.getElementById('toggleHistory').addEventListener('click', () => this.toggleQueryHistory());

        // Clear history
        document.getElementById('clearQueryHistory').addEventListener('click', () => this.clearQueryHistory());

        // Export results
        document.getElementById('exportResults').addEventListener('click', () => this.exportMCPResults());
    }

    async executeMCPQuery() {
        const queryInput = document.getElementById('mcpQueryInput');
        const query = queryInput.value.trim();
        
        if (!query) {
            this.showToast('Please enter a query', 'error');
            return;
        }

        // Show loading state
        this.showMCPLoading();

        try {
            const response = await fetch('/api/mcp-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.displayMCPResults(data.results, data.query);
                this.addToQueryHistory(query);
                this.showToast('Query executed successfully', 'success');
            } else {
                throw new Error(data.error || 'Query failed');
            }
        } catch (error) {
            console.error('MCP Query Error:', error);
            this.showMCPError(error.message);
            this.showToast('Query failed: ' + error.message, 'error');
        }
    }

    showMCPLoading() {
        const resultsContainer = document.getElementById('mcpResults');
        resultsContainer.innerHTML = `
            <div class="mcp-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Processing query...</span>
            </div>
        `;
    }

    showMCPError(message) {
        const resultsContainer = document.getElementById('mcpResults');
        resultsContainer.innerHTML = `
            <div class="mcp-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Error: ${message}</span>
            </div>
        `;
        document.getElementById('resultsCount').textContent = '0 results';
    }

    displayMCPResults(results, query) {
        const resultsContainer = document.getElementById('mcpResults');
        const resultsCount = document.getElementById('resultsCount');
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No results found for your query</p>
                </div>
            `;
            resultsCount.textContent = '0 results';
            return;
        }

        // Check if results are analysis/summary/commentary or table data
        const firstResult = results[0];
        if (firstResult.type === 'analysis' || firstResult.type === 'summary' || firstResult.type === 'commentary') {
            this.displayAnalysisResults(results, resultsContainer, resultsCount);
        } else {
            // Create results table for regular data
            const table = this.createResultsTable(results);
            resultsContainer.innerHTML = '';
            resultsContainer.appendChild(table);
            resultsCount.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
        }
    }

    displayAnalysisResults(results, resultsContainer, resultsCount) {
        const result = results[0];
        const type = result.type;
        const content = result.content;
        const tradeCount = result.trade_count || 0;
        const generatedAt = result.generated_at || new Date().toISOString();
        
        const icon = type === 'summary' ? 'fas fa-chart-pie' : 'fas fa-comment-dots';
        const title = type === 'summary' ? 'Analysis Summary' : 'Market Commentary';
        
        resultsContainer.innerHTML = `
            <div class="analysis-result">
                <div class="analysis-header">
                    <div class="analysis-title">
                        <i class="${icon}"></i>
                        <h3>${title}</h3>
                    </div>
                    <div class="analysis-meta">
                        <span class="trade-count">${tradeCount} trades analyzed</span>
                        <span class="generated-at">${new Date(generatedAt).toLocaleTimeString()}</span>
                    </div>
                </div>
                <div class="analysis-content">
                    <div class="analysis-text">${this.formatAnalysisContent(content)}</div>
                </div>
            </div>
        `;
        
        resultsCount.textContent = `${tradeCount} trades analyzed`;
    }

    formatAnalysisContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gim, '<h4>$1</h4>')
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/^# (.*$)/gim, '<h2>$1</h2>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.*)$/gim, '<p>$1</p>')
            .replace(/<p><\/p>/g, '')
            .replace(/<p>(<[h|l])/g, '$1')
            .replace(/(<\/[h|l]>)<\/p>/g, '$1');
    }

    createResultsTable(results) {
        const table = document.createElement('table');
        table.className = 'results-table';
        
        // Get all unique keys from results
        const allKeys = [...new Set(results.flatMap(result => Object.keys(result)))];
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        allKeys.forEach(key => {
            const th = document.createElement('th');
            th.textContent = this.formatColumnName(key);
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        results.forEach(result => {
            const row = document.createElement('tr');
            allKeys.forEach(key => {
                const td = document.createElement('td');
                td.textContent = this.formatCellValue(result[key] || '');
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        return table;
    }

    formatColumnName(key) {
        // Convert snake_case to Title Case
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatCellValue(value) {
        if (value === null || value === undefined) return '';
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        return String(value);
    }

    addToQueryHistory(query) {
        const historyList = document.getElementById('historyList');
        const timestamp = new Date().toLocaleTimeString();
        
        // Remove "No queries yet" message if it exists
        const noHistory = historyList.querySelector('.no-history');
        if (noHistory) {
            noHistory.remove();
        }
        
        // Create history item
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <span class="history-query">${query}</span>
            <span class="history-timestamp">${timestamp}</span>
        `;
        
        // Add click handler to reuse query
        historyItem.addEventListener('click', () => {
            document.getElementById('mcpQueryInput').value = query;
        });
        
        // Add to top of history
        historyList.insertBefore(historyItem, historyList.firstChild);
        
        // Limit history to 10 items
        const items = historyList.querySelectorAll('.history-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
    }

    toggleQueryHistory() {
        const historyContent = document.getElementById('queryHistory');
        const toggleBtn = document.getElementById('toggleHistory');
        const icon = toggleBtn.querySelector('i');
        
        if (historyContent.style.display === 'none') {
            historyContent.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            historyContent.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    }

    clearQueryHistory() {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '<p class="no-history">No queries yet</p>';
        this.showToast('Query history cleared', 'success');
    }

    exportMCPResults() {
        const resultsContainer = document.getElementById('mcpResults');
        const table = resultsContainer.querySelector('.results-table');
        
        if (!table) {
            this.showToast('No results to export', 'error');
            return;
        }
        
        // Convert table to CSV
        const csv = this.tableToCSV(table);
        this.downloadCSV(csv, 'mcp-query-results.csv');
        this.showToast('Results exported successfully', 'success');
    }

    tableToCSV(table) {
        const rows = Array.from(table.querySelectorAll('tr'));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            return cells.map(cell => `"${cell.textContent.replace(/"/g, '""')}"`).join(',');
        }).join('\n');
    }

    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DTCCDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        window.dashboard?.stopAutoRefresh();
    } else {
        window.dashboard?.startAutoRefresh();
    }
});

