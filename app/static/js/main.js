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
    init: function() {
        this.bindEvents();
        this.loadEvents();
    },
    
    bindEvents: function() {
        // Filter form submission
        const filterForm = document.getElementById('filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.loadEvents(1);
            });
        }
        
        // Pagination
        const pagination = document.querySelector('.pagination');
        if (pagination) {
            pagination.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') {
                    e.preventDefault();
                    const page = e.target.dataset.page;
                    this.loadEvents(page);
                }
            });
        }
        
        // Sorting
        const sortHeaders = document.querySelectorAll('th[data-sort]');
        sortHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                const currentOrder = header.dataset.order || 'asc';
                const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
                
                // Update all headers
                sortHeaders.forEach(h => h.dataset.order = '');
                header.dataset.order = newOrder;
                
                this.loadEvents(1, sortBy, newOrder);
            });
        });
    },
    
    loadEvents: async function(page = 1, sortBy = 'timestamp', sortOrder = 'desc') {
        try {
            const filterForm = document.getElementById('filter-form');
            const formData = new FormData(filterForm);
            const params = new URLSearchParams(formData);
            
            params.append('page', page);
            params.append('sort_by', sortBy);
            params.append('sort_order', sortOrder);
            
            const data = await apiRequest(`/api/events?${params.toString()}`, {
                loadingSelector: '#events-table'
            });
            
            this.renderEvents(data);
            this.renderPagination(data);
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    },
    
    renderEvents: function(data) {
        const tbody = document.querySelector('#events-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = data.events.map(event => `
            <tr>
                <td>${new Date(event.timestamp).toLocaleString()}</td>
                <td>${event.scid}</td>
                <td>${event.metric_type}</td>
                <td>${event.value}</td>
                <td>${event.threshold}</td>
                <td>
                    <span class="badge bg-${event.status === 'BREACH' ? 'danger' : 'success'}">
                        ${event.status}
                    </span>
                </td>
            </tr>
        `).join('');
    },
    
    renderPagination: function(data) {
        const pagination = document.querySelector('.pagination');
        if (!pagination) return;
        
        const pages = [];
        for (let i = 1; i <= data.total_pages; i++) {
            pages.push(`
                <li class="page-item ${i === data.page ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        pagination.innerHTML = pages.join('');
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    eventTable.init();
}); 