/**
 * Medical System JavaScript Functions
 * Provides interactivity and enhancements for the medical system interface
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeMedicalSystem();
});

/**
 * Main initialization function
 */
function initializeMedicalSystem() {
    initializeTooltips();
    initializeSearchEnhancements();
    initializeTableEnhancements();
    initializeFormValidation();
    initializeLoadingStates();
    initializeMedicalAlerts();
    
    console.log('Medical System initialized successfully');
}

/**
 * Initialize Bootstrap tooltips for all elements
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 500, hide: 100 }
        });
    });
}

/**
 * Enhance search functionality
 */
function initializeSearchEnhancements() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    
    searchInputs.forEach(function(input) {
        // Add search icon animation
        input.addEventListener('focus', function() {
            const icon = this.closest('.input-group')?.querySelector('.fa-search');
            if (icon) {
                icon.classList.add('text-primary');
            }
        });
        
        input.addEventListener('blur', function() {
            const icon = this.closest('.input-group')?.querySelector('.fa-search');
            if (icon) {
                icon.classList.remove('text-primary');
            }
        });
        
        // Auto-search with debounce
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const form = this.closest('form');
            if (form && this.value.length >= 3) {
                searchTimeout = setTimeout(() => {
                    form.submit();
                }, 1000);
            }
        });
    });
}

/**
 * Enhance table functionality
 */
function initializeTableEnhancements() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(function(table) {
        // Add row click highlighting
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.addEventListener('click', function() {
                // Remove previous selections
                rows.forEach(r => r.classList.remove('table-active'));
                // Add selection to current row
                this.classList.add('table-active');
            });
        });
        
        // Add sorting capability for sortable columns
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, this);
            });
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, header) {
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove all sort classes
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        const comparison = aValue.localeCompare(bValue, undefined, { numeric: true });
        return isAscending ? -comparison : comparison;
    });
    
    // Add sort class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Reorder rows in DOM
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Form validation enhancements
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus first invalid field
                const firstInvalidField = form.querySelector(':invalid');
                if (firstInvalidField) {
                    firstInvalidField.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Loading states for async operations
 */
function initializeLoadingStates() {
    const buttons = document.querySelectorAll('button[type="submit"], .btn-loading');
    
    buttons.forEach(function(button) {
        button.addEventListener('click', function() {
            if (this.type === 'submit' || this.classList.contains('btn-loading')) {
                showButtonLoading(this);
            }
        });
    });
}

/**
 * Show loading state on button
 */
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading-spinner me-2"></span>Cargando...';
    button.disabled = true;
    
    // Restore button after timeout (fallback)
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 5000);
}

/**
 * Medical alerts and notifications
 */
function initializeMedicalAlerts() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(() => {
            const alertInstance = new bootstrap.Alert(alert);
            alertInstance.close();
        }, 5000);
    });
    
    // Check for critical medical values
    checkCriticalValues();
}

/**
 * Check for critical medical values and highlight them
 */
function checkCriticalValues() {
    const valueElements = document.querySelectorAll('[data-medical-value]');
    
    valueElements.forEach(function(element) {
        const value = parseFloat(element.dataset.medicalValue);
        const type = element.dataset.medicalType;
        
        if (isNaN(value)) return;
        
        // Define critical ranges for different medical parameters
        const criticalRanges = {
            'blood_pressure_systolic': { min: 90, max: 140 },
            'blood_pressure_diastolic': { min: 60, max: 90 },
            'heart_rate': { min: 60, max: 100 },
            'temperature': { min: 36.1, max: 37.2 },
            'glucose': { min: 70, max: 140 }
        };
        
        const range = criticalRanges[type];
        if (range) {
            if (value < range.min || value > range.max) {
                element.classList.add('value-abnormal');
                element.title = 'Valor fuera del rango normal';
            } else {
                element.classList.add('value-normal');
            }
        }
    });
}

/**
 * Format medical dates consistently
 */
function formatMedicalDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Filter table content dynamically
 */
function filterTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const searchLower = searchTerm.toLowerCase();
    
    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchLower) ? '' : 'none';
    });
}

/**
 * Medical data export functionality
 */
function exportMedicalData(format = 'csv') {
    const tables = document.querySelectorAll('.table');
    if (tables.length === 0) return;
    
    // For now, just print the page
    if (format === 'pdf') {
        window.print();
        return;
    }
    
    // CSV export would go here
    console.log('Export functionality would be implemented here');
}

/**
 * Patient quick search
 */
function quickSearchPatients(searchTerm) {
    if (searchTerm.length < 2) return;
    
    // This would make an AJAX call to search patients
    // For now, just redirect to patients page with search
    window.location.href = `/patients?search=${encodeURIComponent(searchTerm)}`;
}

/**
 * Medical code validation (SNOMED CT, ICD-10, etc.)
 */
function validateMedicalCode(code, type) {
    const patterns = {
        'snomed': /^\d+$/,
        'icd10': /^[A-Z]\d{2}(\.\d+)?$/,
        'atc': /^[A-Z]\d{2}[A-Z]{2}\d{2}$/
    };
    
    const pattern = patterns[type];
    return pattern ? pattern.test(code) : false;
}

/**
 * Medical calculator utilities
 */
const MedicalCalculators = {
    /**
     * Calculate BMI
     */
    calculateBMI: function(weight, height) {
        const heightM = height / 100;
        return (weight / (heightM * heightM)).toFixed(1);
    },
    
    /**
     * Calculate age from birth date
     */
    calculateAge: function(birthDate) {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        
        return age;
    },
    
    /**
     * Format dosage
     */
    formatDosage: function(amount, unit, frequency) {
        return `${amount} ${unit} ${frequency}`;
    }
};

/**
 * Accessibility enhancements
 */
function enhanceAccessibility() {
    // Add skip navigation
    const skipNav = document.createElement('a');
    skipNav.href = '#main-content';
    skipNav.className = 'sr-only sr-only-focusable';
    skipNav.textContent = 'Saltar al contenido principal';
    document.body.insertBefore(skipNav, document.body.firstChild);
    
    // Enhance keyboard navigation
    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
    interactiveElements.forEach(function(element) {
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && element.tagName === 'A') {
                element.click();
            }
        });
    });
}

// Initialize accessibility enhancements
enhanceAccessibility();

// Global utility functions
window.MedicalSystem = {
    formatDate: formatMedicalDate,
    filterTable: filterTable,
    exportData: exportMedicalData,
    searchPatients: quickSearchPatients,
    validateCode: validateMedicalCode,
    calculators: MedicalCalculators
};
