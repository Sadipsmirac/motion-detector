# app.py - Simplified version that works on Render
from flask import Flask, render_template_string, jsonify, request
import json
import base64
import os

app = Flask(__name__)

# Simple HTML template with motion detection (no OpenCV needed for basic version)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Motion Detection App</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5em;
        }

        .status {
            text-align: center;
            padding: 15px;
            background: #10b981;
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: 600;
        }

        .video-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        @media (max-width: 768px) {
            .video-container {
                grid-template-columns: 1fr;
            }
        }

        .video-wrapper {
            position: relative;
            background: #000;
            border-radius: 15px;
            overflow: hidden;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .video-label {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            z-index: 10;
        }

        video, canvas {
            width: 100%;
            height: auto;
            display: block;
        }

        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 20px 0;
            flex-wrap: wrap;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .stop-btn {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }

        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .motion-bar {
            width: 100%;
            height: 40px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }

        .motion-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }

        .alert {
            display: none;
            background: #fee2e2;
            border: 2px solid #ef4444;
            color: #991b1b;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
            animation: pulse 1s ease-in-out infinite;
            margin-bottom: 20px;
        }

        .alert.active {
            display: block;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Motion Detection</h1>
        
        <div class="status">
            ✅ Server Running on Render | Camera: Browser-Based | Detection: Active
        </div>

        <div class="alert" id="motionAlert">
            ⚠️ MOTION DETECTED!
        </div>

        <div class="video-container">
            <div class="video-wrapper">
                <div class="video-label">Live Camera</div>
                <video id="video" autoplay muted></video>
            </div>
            <div class="video-wrapper">
                <div class="video-label">Motion View</div>
                <canvas id="canvas"></canvas>
            </div>
        </div>

        <div class="motion-bar">
            <div class="motion-fill" id="motionBar">
                <span id="motionPercent">0%</span>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Current Motion</div>
                <div class="stat-value" id="currentMotion">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Peak Motion</div>
                <div class="stat-value" id="peakMotion">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Detections</div>
                <div class="stat-value" id="detectionCount">0</div>
            </div>
        </div>

        <div class="controls">
            <button onclick="startDetection()">▶️ Start Detection</button>
            <button class="stop-btn" onclick="stopDetection()">⏹️ Stop</button>
            <button onclick="resetStats()">🔄 Reset Stats</button>
        </div>
    </div>

    <script>
        let stream = null;
        let animationId = null;
        let previousFrame = null;
        let peakMotion = 0;
        let detectionCount = 0;
        let isDetecting = false;

        async function startDetection() {
            try {
                const video = document.getElementById('video');
                const canvas = document.getElementById('canvas');
                const ctx = canvas.getContext('2d');
                
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    } 
                });
                
                video.srcObject = stream;
                
                video.addEventListener('loadedmetadata', () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    isDetecting = true;
                    detectMotion();
                });
            } catch (err) {
                alert('Camera access error: ' + err.message);
            }
        }

        function stopDetection() {
            isDetecting = false;
            
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
            
            document.getElementById('video').srcObject = null;
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }

        function detectMotion() {
            if (!isDetecting) return;

            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const currentFrame = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            if (previousFrame) {
                let motion = 0;
                const sensitivity = 30;
                
                for (let i = 0; i < currentFrame.data.length; i += 4) {
                    const rDiff = Math.abs(currentFrame.data[i] - previousFrame.data[i]);
                    const gDiff = Math.abs(currentFrame.data[i + 1] - previousFrame.data[i + 1]);
                    const bDiff = Math.abs(currentFrame.data[i + 2] - previousFrame.data[i + 2]);
                    
                    const diff = (rDiff + gDiff + bDiff) / 3;
                    
                    if (diff > sensitivity) {
                        motion++;
                        currentFrame.data[i] = 255;
                        currentFrame.data[i + 1] = 0;
                        currentFrame.data[i + 2] = 0;
                    }
                }
                
                const percentage = (motion / (currentFrame.data.length / 4)) * 100;
                updateStats(percentage);
                ctx.putImageData(currentFrame, 0, 0);
            }
            
            previousFrame = currentFrame;
            animationId = requestAnimationFrame(detectMotion);
        }

        function updateStats(percentage) {
            const rounded = Math.round(percentage * 10) / 10;
            
            document.getElementById('currentMotion').textContent = rounded + '%';
            document.getElementById('motionBar').style.width = Math.min(rounded * 3, 100) + '%';
            document.getElementById('motionPercent').textContent = rounded + '%';
            
            if (rounded > peakMotion) {
                peakMotion = rounded;
                document.getElementById('peakMotion').textContent = peakMotion + '%';
            }
            
            if (rounded > 5) { // 5% threshold
                if (!document.getElementById('motionAlert').classList.contains('active')) {
                    document.getElementById('motionAlert').classList.add('active');
                    detectionCount++;
                    document.getElementById('detectionCount').textContent = detectionCount;
                    
                    setTimeout(() => {
                        document.getElementById('motionAlert').classList.remove('active');
                    }, 2000);
                }
            }
        }

        function resetStats() {
            peakMotion = 0;
            detectionCount = 0;
            document.getElementById('peakMotion').textContent = '0%';
            document.getElementById('detectionCount').textContent = '0';
        }

        // Test endpoint
        fetch('/api/status')
            .then(r => r.json())
            .then(data => console.log('Server status:', data))
            .catch(err => console.log('Server check failed:', err));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    """Status endpoint to check if server is running"""
    return jsonify({
        'status': 'running',
        'server': 'Render',
        'message': 'Motion detection server is active'
    })

@app.route('/api/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy'}), 200

# This is important for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)