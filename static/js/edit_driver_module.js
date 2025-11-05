/**
 * Edit Driver module
 */

import { showNotification, apiRequest } from './common.js';

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handleSubmit(event) {
    event.preventDefault();

    const driverId = document.getElementById('driver_id').value;
    const formData = {
        name: document.getElementById('name').value,
        license: document.getElementById('license').value,
        phone: document.getElementById('phone').value,
        stream_url: document.getElementById('stream_url').value,
        status: document.getElementById('status').value
    };

    try {
        await apiRequest(`/api/drivers/${driverId}`, {
            method: 'PUT',
            body: JSON.stringify(formData)
        });

        showNotification('✓ Đã cập nhật thông tin tài xế!', 'success');
        
        // Redirect after short delay
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    } catch (error) {
        showNotification('✗ Lỗi: ' + error.message, 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('driverForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
});

// Export for direct usage if needed
export { handleSubmit };
