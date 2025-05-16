// Error tracking
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Error: ' + msg + '\nURL: ' + url + '\nLine: ' + lineNo + '\nColumn: ' + columnNo + '\nError object: ' + JSON.stringify(error));
    return false;
};

// Loading state management
const loadingStates = {
    show: function(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    },
    hide: function(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }
};

// API request wrapper with loading states and error handling
async function apiRequest(url, options = {}) {
    const loadingElement = document.querySelector(options.loadingSelector);
    try {
        loadingStates.show(loadingElement);
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        showError(error.message);
        throw error;
    } finally {
        loadingStates.hide(loadingElement);
    }
}

// Error display
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }
}

// Event table management
const eventTable = {
    currentPage: 1,
    currentSortBy: 'timestamp',
    currentSortOrder: 'desc',
    
    init: function() {
        // Get initial state from URL if available
        this.parseUrlParams();
        this.bindEvents();
        this.loadEvents();
    },
    
    parseUrlParams: function() {
        const params = new URLSearchParams(window.location.search);
        this.currentPage = parseInt(params.get('page') || '1');
        this.currentSortBy = params.get('sort_by') || 'timestamp';
        this.currentSortOrder = params.get('sort_order') || 'desc';
    },
    
    updateUrl: function() {
        // Update browser URL with current filter and sort state
        const filterForm = document.getElementById('filter-form');
        if (!filterForm) return;
        
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        params.set('page', this.currentPage);
        params.set('sort_by', this.currentSortBy);
        params.set('sort_order', this.currentSortOrder);
        
        const newUrl = window.location.pathname + '?' + params.toString();
        window.history.pushState({}, '', newUrl);
    },
    
    bindEvents: function() {
        // Filter form submission
        const filterForm = document.getElementById('filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.currentPage = 1; // Reset to page 1 when filtering
                this.loadEvents();
            });
        }
        
        // Pagination
        const pagination = document.querySelector('.pagination');
        if (pagination) {
            pagination.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') {
                    e.preventDefault();
                    this.currentPage = parseInt(e.target.dataset.page);
                    this.loadEvents();
                }
            });
        }
        
        // Sorting
        const sortHeaders = document.querySelectorAll('th[data-sort]');
        sortHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                const currentOrder = header.dataset.order || '';
                const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
                
                // Update all headers
                sortHeaders.forEach(h => h.dataset.order = '');
                header.dataset.order = newOrder;
                
                this.currentSortBy = sortBy;
                this.currentSortOrder = newOrder;
                this.loadEvents();
            });
        });
    },
    
    loadEvents: async function() {
        try {
            const filterForm = document.getElementById('filter-form');
            if (!filterForm) {
                throw new Error('Filter form not found');
            }
            
            const formData = new FormData(filterForm);
            const params = new URLSearchParams();
            
            // Add form data to params
            for (const [key, value] of formData.entries()) {
                if (value) { // Only add non-empty values
                    params.append(key, value);
                }
            }
            
            // Add pagination and sorting
            params.append('page', this.currentPage);
            params.append('sort_by', this.currentSortBy);
            params.append('sort_order', this.currentSortOrder);
            
            console.log('Fetching events with params:', params.toString());
            
            const response = await apiRequest(`/api/events?${params.toString()}`, {
                loadingSelector: '#events-table'
            });
            
            if (!response || !response.success) {
                throw new Error((response && response.error) || 'Failed to load events');
            }
            
            // Update current state with response data
            const data = response.data;
            
            if (!data || !data.events) {
                throw new Error('Invalid data format returned from API');
            }
            
            this.renderEvents(data.events);
            this.renderPagination(data.page, data.total_pages);
            
            // Update URL to reflect current state
            this.updateUrl();
            
        } catch (error) {
            console.error('Failed to load events:', error);
            showError('Error loading events: ' + error.message);
        }
    },
    
    renderEvents: function(events) {
        const tbody = document.querySelector('#events-table tbody');
        if (!tbody) return;
        
        if (!events || events.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <div class="alert alert-secondary mb-0">
                            No events found matching your criteria
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = events.map(event => `
            <tr>
                <td>${new Date(event.timestamp).toLocaleString()}</td>
                <td>${event.payload_name || event.scid}</td>
                <td>${event.metric_type}</td>
                <td>${Number(event.value).toFixed(2)}</td>
                <td>${Number(event.threshold).toFixed(2)}</td>
                <td>
                    <span class="badge bg-${event.status === 'BREACH' ? 'danger' : 'success'}">
                        ${event.status}
                    </span>
                </td>
            </tr>
        `).join('');
    },
    
    renderPagination: function(currentPage, totalPages) {
        const pagination = document.querySelector('.pagination');
        if (!pagination) return;
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        const pages = [];
        
        // Previous page button
        if (currentPage > 1) {
            pages.push(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${currentPage - 1}">&laquo; Previous</a>
                </li>
            `);
        }
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            // Show a subset of pages if there are too many
            if (totalPages > 7) {
                if (
                    i === 1 || // Always show first page
                    i === totalPages || // Always show last page
                    (i >= currentPage - 1 && i <= currentPage + 1) // Show pages around current
                ) {
                    pages.push(`
                        <li class="page-item ${i === currentPage ? 'active' : ''}">
                            <a class="page-link" href="#" data-page="${i}">${i}</a>
                        </li>
                    `);
                } else if (
                    (i === 2 && currentPage > 3) ||
                    (i === totalPages - 1 && currentPage < totalPages - 2)
                ) {
                    // Add ellipsis for skipped pages
                    pages.push(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
                }
            } else {
                // Show all pages if there aren't too many
                pages.push(`
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `);
            }
        }
        
        // Next page button
        if (currentPage < totalPages) {
            pages.push(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${currentPage + 1}">Next &raquo;</a>
                </li>
            `);
        }
        
        pagination.innerHTML = pages.join('');
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the events page
    if (document.getElementById('events-table')) {
        eventTable.init();
    }
    
    // Initialize other page-specific functionality
    if (document.getElementById('run-monitor')) {
        // Handle manual monitor trigger
        document.getElementById('run-monitor').addEventListener('click', async function() {
            try {
                loadingStates.show(this);
                const response = await fetch('/api/monitor', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (response.ok) {
                    alert('Monitoring completed successfully!');
                    // Reload the page to show new data
                    window.location.reload();
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            } catch (error) {
                console.error('Error running monitor:', error);
                showError('Error: ' + error.message);
            } finally {
                loadingStates.hide(this);
            }
        });
    }
}); 