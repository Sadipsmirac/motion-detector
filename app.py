# cloud_ai_app.py - Uses external AI services (no OpenCV needed)
from flask import Flask, render_template_string, jsonify, request
import base64
import json
import requests
import os

app = Flask(__name__)

# Use free AI APIs instead of local processing
# Options: 
# 1. Roboflow (free tier: 1000 requests/month)
# 2. Clarifai (free tier available)
# 3. Google Vision API (free tier)

HTML_WITH_CLOUD_AI = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Object Detection - Cloud Based</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 20px;
        }
        h1 {
            text-align: center;
            color: #667eea;
        }
        .info-box {
            background: #e0f2fe;
            border-left: 4px solid #0284c7;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .video-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        video, canvas {
            width: 100%;
            border-radius: 10px;
            background: #000;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            font-size: 16px;
        }
        button:hover {
            background: #5a67d8;
        }
        .results {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .object-tag {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Cloud-Based AI Object Detection</h1>
        
        <div class="info-box">
            <strong>💡 How it works:</strong><br>
            This version uses cloud AI services for object detection, which means:
            <ul>
                <li>✅ No heavy processing on Render's free tier</li>
                <li>✅ Works within 512MB RAM limit</li>
                <li>✅ Fast and reliable</li>
                <li>✅ Multiple AI providers available</li>
            </ul>
        </div>
        
        <div class="video-container">
            <div>
                <h3>Camera Feed</h3>
                <video id="video" autoplay muted></video>
            </div>
            <div>
                <h3>Captured Frame</h3>
                <canvas id="canvas"></canvas>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button onclick="startCamera()">📷 Start Camera</button>
            <button onclick="captureAndDetect()">🎯 Detect Objects</button>
            <button onclick="stopCamera()">⏹️ Stop</button>
        </div>
        
        <div id="results" class="results" style="display:none;">
            <h3>Detected Objects:</h3>
            <div id="objectList"></div>
        </div>
    </div>
    
    <script>
        let stream = null;
        
        async function startCamera() {
            try {
                const video = document.getElementById('video');
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
            } catch (err) {
                alert('Camera error: ' + err);
            }
        }
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                document.getElementById('video').srcObject = null;
            }
        }
        
        async function captureAndDetect() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            
            // Convert to blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob);
                
                try {
                    // Send to server for cloud AI processing
                    const response = await fetch('/api/detect_cloud', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    displayResults(result);
                } catch (err) {
                    console.error('Detection error:', err);
                }
            }, 'image/jpeg');
        }
        
        function displayResults(result) {
            const resultsDiv = document.getElementById('results');
            const objectList = document.getElementById('objectList');
            
            if (result.objects && result.objects.length > 0) {
                resultsDiv.style.display = 'block';
                objectList.innerHTML = result.objects.map(obj => 
                    `<span class="object-tag">${obj.label} (${(obj.confidence * 100).toFixed(1)}%)</span>`
                ).join('');
            } else {
                objectList.innerHTML = '<p>No objects detected</p>';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_WITH_CLOUD_AI)

@app.route('/api/detect_cloud', methods=['POST'])
def detect_cloud():
    """Use cloud AI service for detection"""
    try:
        # Option 1: Use Roboflow (free tier)
        # Sign up at https://roboflow.com and get API key
        ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY', 'YOUR_API_KEY')
        
        if ROBOFLOW_API_KEY != 'YOUR_API_KEY':
            # Use Roboflow API
            image_file = request.files.get('image')
            response = requests.post(
                f"https://detect.roboflow.com/coco/9",
                params={"api_key": ROBOFLOW_API_KEY},
                files={"file": image_file.read()}
            )
            
            result = response.json()
            objects = [
                {
                    'label': pred['class'],
                    'confidence': pred['confidence']
                }
                for pred in result.get('predictions', [])
            ]
            
            return jsonify({'success': True, 'objects': objects})
        
        # Option 2: Use TensorFlow.js in browser (no API needed)
        # This is just a mock response for demo
        return jsonify({
            'success': True,
            'objects': [
                {'label': 'person', 'confidence': 0.95},
                {'label': 'laptop', 'confidence': 0.87}
            ],
            'message': 'Using mock detection. Set up cloud AI API for real detection.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'mode': 'cloud_ai'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)