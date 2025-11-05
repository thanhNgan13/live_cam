/**
 * Driver View module - Video streaming and screenshot management
 */

import { showNotification } from './common.js';

let photoGallery = [];
let driverId;
let snapshotUrl;

/**
 * Initialize driver view
 */
function initialize() {
    // Get driver ID and snapshot URL from script context
    driverId = window.DRIVER_ID;
    snapshotUrl = window.SNAPSHOT_URL;
    
    updateGalleryDisplay();
}

/**
 * Handle stream error
 */
export function handleStreamError() {
    const errorMsg = document.getElementById('errorMessage');
    errorMsg.style.display = 'block';
    showNotification('⚠️ Không thể kết nối camera', 'error');
}

/**
 * Refresh video stream
 */
export function refreshStream() {
    const videoStream = document.getElementById('videoStream');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const errorMsg = document.getElementById('errorMessage');
    const baseUrl = videoStream.getAttribute('data-base-url');
    const timestamp = new Date().getTime();
    
    // Show loading spinner
    loadingOverlay.classList.add('active');
    videoStream.classList.add('loading');
    errorMsg.style.display = 'none';
    
    // Update stream URL
    videoStream.src = `${baseUrl}?t=${timestamp}`;
    
    // Hide loading after stream loads or timeout
    const hideLoading = () => {
        loadingOverlay.classList.remove('active');
        videoStream.classList.remove('loading');
    };
    
    videoStream.onload = hideLoading;
    setTimeout(hideLoading, 2000); // Fallback timeout
    
    showNotification('🔄 Đã làm mới stream', 'info');
}

/**
 * Take screenshot
 */
export async function takeScreenshot() {
    try {
        // Show flash effect
        const flashOverlay = document.getElementById('flashOverlay');
        flashOverlay.classList.add('active');
        setTimeout(() => flashOverlay.classList.remove('active'), 200);

        // Fetch snapshot from server
        const response = await fetch(snapshotUrl);
        if (!response.ok) {
            throw new Error('Không thể chụp ảnh');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Add to gallery
        const photo = {
            id: Date.now(),
            url: url,
            timestamp: new Date().toLocaleString('vi-VN')
        };
        
        photoGallery.push(photo);
        updateGalleryDisplay();
        
        showNotification('✓ Đã chụp ảnh!', 'success');
    } catch (error) {
        console.error('Screenshot error:', error);
        showNotification('✗ Lỗi chụp ảnh: ' + error.message, 'error');
    }
}

/**
 * Update gallery display
 */
function updateGalleryDisplay() {
    const gallery = document.getElementById('gallery');
    const photoCount = document.getElementById('photoCount');
    const clearBtn = document.getElementById('clearBtn');
    
    photoCount.textContent = photoGallery.length;
    clearBtn.style.display = photoGallery.length > 0 ? 'block' : 'none';
    
    if (photoGallery.length === 0) {
        gallery.innerHTML = `
            <div class="gallery-empty" style="grid-column: 1 / -1;">
                <div class="icon">📷</div>
                <p>Chưa có ảnh nào.<br>Nhấn "Chụp ảnh" để bắt đầu.</p>
            </div>
        `;
        return;
    }
    
    gallery.innerHTML = photoGallery.map(photo => `
        <div class="gallery-item">
            <img src="${photo.url}" alt="Screenshot">
            <div class="gallery-timestamp">${photo.timestamp}</div>
            <div class="gallery-item-actions">
                <button class="btn-download" onclick="window.downloadPhoto(${photo.id})">
                    ⬇️ Tải
                </button>
                <button class="btn-delete" onclick="window.deletePhoto(${photo.id})">
                    🗑️ Xóa
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Download photo
 * @param {number} photoId - Photo ID
 */
export function downloadPhoto(photoId) {
    const photo = photoGallery.find(p => p.id === photoId);
    if (!photo) return;
    
    const link = document.createElement('a');
    link.href = photo.url;
    link.download = `driver_${driverId}_${photoId}.jpg`;
    link.click();
    
    showNotification('⬇️ Đang tải ảnh...', 'info');
}

/**
 * Delete single photo
 * @param {number} photoId - Photo ID
 */
export function deletePhoto(photoId) {
    if (!confirm('Xóa ảnh này?')) return;
    
    const photo = photoGallery.find(p => p.id === photoId);
    if (photo) {
        URL.revokeObjectURL(photo.url);
    }
    
    photoGallery = photoGallery.filter(p => p.id !== photoId);
    updateGalleryDisplay();
    
    showNotification('✓ Đã xóa ảnh', 'success');
}

/**
 * Clear all photos
 */
export function clearGallery() {
    if (!confirm(`Xóa tất cả ${photoGallery.length} ảnh?`)) return;
    
    // Revoke all object URLs
    photoGallery.forEach(photo => {
        URL.revokeObjectURL(photo.url);
    });
    
    photoGallery = [];
    updateGalleryDisplay();
    
    showNotification('✓ Đã xóa toàn bộ ảnh', 'success');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    photoGallery.forEach(photo => {
        URL.revokeObjectURL(photo.url);
    });
});

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initialize);

// Expose functions globally for onclick handlers
window.handleStreamError = handleStreamError;
window.refreshStream = refreshStream;
window.takeScreenshot = takeScreenshot;
window.downloadPhoto = downloadPhoto;
window.deletePhoto = deletePhoto;
window.clearGallery = clearGallery;
