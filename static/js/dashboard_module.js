/**
 * Dashboard module - Driver list management
 */

import { showNotification, apiRequest, confirmAction } from './common.js';

/**
 * Filter drivers by search query
 * @param {string} query - Search query
 */
export function filterDrivers(query) {
    const driverCards = document.querySelectorAll('.driver-card');
    const searchLower = query.toLowerCase();
    
    driverCards.forEach(card => {
        const name = card.querySelector('h3').textContent.toLowerCase();
        const license = card.querySelector('.driver-info').textContent.toLowerCase();
        
        if (name.includes(searchLower) || license.includes(searchLower)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Delete driver
 * @param {number} driverId - Driver ID to delete
 */
export async function deleteDriver(driverId) {
    if (!confirmAction('Bạn có chắc muốn xóa tài xế này?')) {
        return;
    }
    
    try {
        await apiRequest(`/api/drivers/${driverId}`, {
            method: 'DELETE'
        });
        
        showNotification('✓ Đã xóa tài xế!', 'success');
        
        // Reload page after short delay
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    } catch (error) {
        showNotification('✗ Lỗi: ' + error.message, 'error');
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Setup search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterDrivers(e.target.value);
        });
    }
    
    // Make functions globally available for onclick handlers
    window.filterDrivers = filterDrivers;
    window.deleteDriver = deleteDriver;
});
