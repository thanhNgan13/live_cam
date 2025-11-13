/**
 * WebSocket YOLO Streaming Module
 * Sử dụng Socket.IO để stream video với latency thấp
 */

class YOLOWebSocketStreamer {
    constructor(streamUrl) {
        this.streamUrl = streamUrl;
        this.socket = null;
        this.canvas = null;
        this.ctx = null;
        this.isStreaming = false;
        this.lastObjectURL = null;  // Track last URL to revoke
        this.isRendering = false;    // Prevent frame backlog
    }

    /**
     * Khởi tạo WebSocket connection
     */
    connect() {
        if (this.socket) {
            console.log('[WebSocket] Already connected');
            return;
        }

        // Kết nối đến Socket.IO server
        this.socket = io();

        // Event: Kết nối thành công
        this.socket.on('connect', () => {
            console.log('[WebSocket] Connected to server');
        });

        // Event: Mất kết nối
        this.socket.on('disconnect', () => {
            console.log('[WebSocket] Disconnected from server');
            this.isStreaming = false;
        });

        // Event: Nhận frame từ server (binary data)
        this.socket.on('yolo_frame', (frameBytes) => {
            this.renderFrame(frameBytes);
        });

        // Event: Stream started
        this.socket.on('stream_started', (data) => {
            console.log('[WebSocket] Stream started:', data.stream_url);
            this.isStreaming = true;
        });

        // Event: Stream stopped
        this.socket.on('stream_stopped', (data) => {
            console.log('[WebSocket] Stream stopped:', data.stream_url);
            this.isStreaming = false;
        });

        // Event: Error
        this.socket.on('error', (data) => {
            console.error('[WebSocket] Error:', data.message);
            alert(`WebSocket Error: ${data.message}`);
        });
    }

    /**
     * Khởi tạo canvas để hiển thị video
     */
    initCanvas(canvasElement) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
    }

    /**
     * Render frame lên canvas
     */
    renderFrame(frameBytes) {
        if (!this.canvas || !this.ctx) {
            console.error('[WebSocket] Canvas not initialized');
            return;
        }

        // Skip frame nếu đang render (tránh backlog)
        if (this.isRendering) {
            return;
        }

        this.isRendering = true;

        // Revoke URL cũ ngay lập tức
        if (this.lastObjectURL) {
            URL.revokeObjectURL(this.lastObjectURL);
            this.lastObjectURL = null;
        }

        // Tạo Blob từ binary data
        const blob = new Blob([frameBytes], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        this.lastObjectURL = url;

        const img = new Image();
        img.onload = () => {
            // Auto-resize canvas chỉ khi cần
            if (this.canvas.width !== img.width || this.canvas.height !== img.height) {
                this.canvas.width = img.width;
                this.canvas.height = img.height;
            }

            // Draw image to canvas
            this.ctx.drawImage(img, 0, 0);
            
            this.isRendering = false;
        };

        img.onerror = (error) => {
            console.error('[WebSocket] Error loading frame:', error);
            this.isRendering = false;
        };

        // Set image source
        img.src = url;
    }

    /**
     * Bắt đầu stream
     */
    startStream() {
        if (!this.socket) {
            console.error('[WebSocket] Not connected. Call connect() first.');
            return;
        }

        if (this.isStreaming) {
            console.log('[WebSocket] Already streaming');
            return;
        }

        console.log('[WebSocket] Starting stream:', this.streamUrl);
        this.socket.emit('start_yolo_stream', {
            stream_url: this.streamUrl
        });
    }

    /**
     * Dừng stream
     */
    stopStream() {
        if (!this.socket) {
            console.error('[WebSocket] Not connected');
            return;
        }

        console.log('[WebSocket] Stopping stream:', this.streamUrl);
        this.socket.emit('stop_yolo_stream', {
            stream_url: this.streamUrl
        });

        this.isStreaming = false;
    }

    /**
     * Ngắt kết nối WebSocket
     */
    disconnect() {
        // Clean up object URL
        if (this.lastObjectURL) {
            URL.revokeObjectURL(this.lastObjectURL);
            this.lastObjectURL = null;
        }

        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isStreaming = false;
    }

    /**
     * Kiểm tra trạng thái streaming
     */
    isActive() {
        return this.isStreaming;
    }
}

// Export để sử dụng ở các file khác
window.YOLOWebSocketStreamer = YOLOWebSocketStreamer;
