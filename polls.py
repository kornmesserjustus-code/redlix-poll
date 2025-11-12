from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
from threading import Thread
import time
import os
from datetime import datetime, timedelta

# Get the directory where polls.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Shared poll state
poll_state = {
    'active': False,
    'question': '',
    'options': [],
    'votes': {},
    'start_time': None
}

vote_cooldowns = {}  # Store IP addresses and their cooldown end times

# Display Server (Port 5000)
display_app = Flask(__name__)
CORS(display_app)

DISPLAY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Poll Display for OBS v.1.0 / PART OF STREAMING TOOLS REDLIX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 30px;
            background: #00FF00;
            color: white;
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            min-height: 100vh;
        }
        .poll-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(110deg, rgba(0,0,0,0.95), rgba(0,0,0,0.85));
            padding: 40px;
            border-radius: 20px;
            max-width: 800px;
            width: 90vw;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        .poll-container::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: translateX(-100%);
            animation: shimmer 10s infinite;
            border-radius: 20px;
        }
        @keyframes shimmer {
            100% { transform: translateX(100%); }
        }
        h1 {
            color: #fff;
            margin-bottom: 15px;
            text-align: center;
            font-size: 2em;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .question {
            font-size: 1.5em;
            color: rgba(255,255,255,0.9);
            margin-bottom: 30px;
            text-align: center;
            font-weight: 600;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.15);
        }
        .option {
            margin: 15px 0;
            padding: 20px;
            background: rgba(128, 26, 48, 0.3);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .option-content {
            position: relative;
            z-index: 2;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .option-text {
            color: white;
            font-size: 1.2em;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
        }
        .option-votes {
            color: white;
            font-size: 1.3em;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        .option-bar {
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            background: rgb(128, 26, 48);
            transition: width 0.5s ease;
            z-index: 1;
            border-radius: 12px;
        }
        .waiting {
            text-align: center;
            color: rgba(255,255,255,0.7);
            font-size: 1.3em;
            padding: 60px 20px;
        }
        .waiting h1 {
            margin-bottom: 15px;
        }
        .total-votes {
            text-align: center;
            margin-top: 30px;
            font-size: 1.1em;
            color: rgba(255,255,255,0.8);
            font-weight: 600;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
    </style>
</head>
<body>
    <div class="poll-container" id="pollContainer">
        <div class="waiting">
            <h1>📊 Waiting for Poll...</h1>
            <p>No active poll at the moment</p>
        </div>
    </div>
    <script>
        function updateDisplay() {
            fetch('http://localhost:5000/api/poll')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('pollContainer');
                    if (!data.active) {
                        container.innerHTML = `
                            <div class="waiting">
                                <h1>📊 Waiting for Poll...</h1>
                                <p>No active poll at the moment</p>
                            </div>
                        `;
                        return;
                    }
                    
                    const totalVotes = Object.values(data.votes).reduce((a, b) => a + b, 0);
                    let html = `
                        <h1>Live Poll Results</h1>
                        <div class="question">${data.question}</div>
                    `;
                    
                    data.options.forEach(option => {
                        const votes = data.votes[option] || 0;
                        const percentage = totalVotes > 0 ? (votes / totalVotes * 100).toFixed(1) : 0;
                        html += `
                            <div class="option">
                                <div class="option-bar" style="width: ${percentage}%"></div>
                                <div class="option-content">
                                    <span class="option-text">${option}</span>
                                    <span class="option-votes">${votes} (${percentage}%)</span>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += `<div class="total-votes">Total Votes: ${totalVotes}</div>`;
                    container.innerHTML = html;
                });
        }
        
        setInterval(updateDisplay, 1000);
        updateDisplay();
    </script>
</body>
</html>
"""

@display_app.route('/')
def display():
    return render_template_string(DISPLAY_HTML)

@display_app.route('/api/poll')
def get_poll():
    return jsonify(poll_state)

# Add route to serve media files
@display_app.route('/media/<path:filename>')
def serve_media(filename):
    media_dir = os.path.join(BASE_DIR, 'media')
    return send_from_directory(media_dir, filename)

# Dashboard Server (Port 5001)
dashboard_app = Flask(__name__)
CORS(dashboard_app)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>REDLIX | Poll Dashboard Alpha v.1.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-red: rgb(128, 26, 48);
            --dark-gray: rgb(38, 38, 38);
            --burgundy: rgb(49, 18, 26);
            --white: #ffffff;
            --light-gray: #f5f5f5;
            --border: #d0d0d0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: var(--white);
            color: var(--dark-gray);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            padding: 0;
            line-height: 1.5;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: var(--primary-red);
            padding: 1rem 2rem;
            border: 3px solid var(--dark-gray);
            border-left: none;
            border-right: none;
            border-top: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header-logo {
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .header-logo img {
            height: 100%;
            width: auto;
            object-fit: contain;
        }

        .version-badge {
            background: var(--white);
            color: var(--primary-red);
            padding: 0.4rem 0.8rem;
            border: 2px solid var(--dark-gray);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .dashboard {
            padding: 1.5rem;
        }

        .panel {
            background: var(--light-gray);
            border: 3px solid var(--dark-gray);
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--dark-gray);
            margin-bottom: 1rem;
        }

        h1 {
            font-size: 1rem;
            font-weight: 700;
            color: var(--dark-gray);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        h1::before {
            content: '';
            display: block;
            width: 6px;
            height: 6px;
            background: var(--primary-red);
            border: 2px solid var(--dark-gray);
        }

        .status {
            text-align: center;
            padding: 1rem;
            font-weight: 700;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            border: 3px solid var(--dark-gray);
            margin-bottom: 1rem;
        }

        .status.active {
            background: var(--primary-red);
            color: var(--white);
        }

        .status.inactive {
            background: var(--burgundy);
            color: var(--white);
        }

        .form-group {
            margin: 1rem 0;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--dark-gray);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input[type="text"] {
            width: 100%;
            padding: 0.75rem;
            background: var(--white);
            border: 3px solid var(--dark-gray);
            color: var(--dark-gray);
            font-size: 0.85rem;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: var(--primary-red);
        }

        .options-list {
            margin: 0.75rem 0;
        }

        .option-item {
            display: flex;
            gap: 0.5rem;
            margin: 0.5rem 0;
        }

        .option-item input {
            flex: 1;
        }

        button {
            background: var(--white);
            border: 3px solid var(--dark-gray);
            color: var(--dark-gray);
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.15s;
            min-width: 100px;
            font-family: 'Inter', sans-serif;
        }

        button:hover {
            background: var(--primary-red);
            color: var(--white);
        }

        button:active {
            transform: scale(0.95);
        }

        .btn-primary {
            background: var(--primary-red);
            color: var(--white);
        }

        .btn-primary:hover {
            background: var(--burgundy);
        }

        .btn-secondary {
            background: var(--burgundy);
            color: var(--white);
        }

        .btn-secondary:hover {
            background: var(--primary-red);
        }

        .button-group {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .results {
            margin-top: 1rem;
        }

        .results h3 {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.75rem;
            color: var(--dark-gray);
        }

        .result-item {
            padding: 0.75rem;
            margin: 0.5rem 0;
            background: var(--white);
            border: 2px solid var(--dark-gray);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .result-item span {
            font-weight: 500;
        }

        .result-item strong {
            font-weight: 700;
            color: var(--primary-red);
        }

        .footer {
            background: var(--dark-gray);
            padding: 1rem 2rem;
            border: 3px solid var(--dark-gray);
            border-left: none;
            border-right: none;
            border-bottom: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 2rem;
        }

        .footer-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .footer-logo {
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .footer-logo img {
            height: 100%;
            width: auto;
            object-fit: contain;
        }

        .footer-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .footer-title {
            font-size: 0.875rem;
            font-weight: 700;
            color: var(--white);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .footer-subtitle {
            font-size: 0.7rem;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
        }

        .footer-right {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .footer-version {
            background: var(--white);
            color: var(--primary-red);
            padding: 0.4rem 0.6rem;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 1px;
            border: 2px solid var(--dark-gray);
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <div class="header-logo">
                    <img src="media/headerlogo.png" alt="REDLIX Poll System Logo">
                </div>
            </div>
            <div class="version-badge">Poll System v.1.0</div>
        </div>

        <div class="dashboard">
            <div class="panel">
                <div class="panel-header">
                    <h1>📊 Poll Dashboard</h1>
                </div>
                <div id="status" class="status inactive">Poll Inactive</div>
                
                <div class="form-group">
                    <label>Poll Question:</label>
                    <input type="text" id="question" placeholder="Enter your poll question">
                </div>
                
                <div class="form-group">
                    <label>Options:</label>
                    <div class="options-list" id="optionsList">
                        <div class="option-item">
                            <input type="text" placeholder="Option 1">
                        </div>
                        <div class="option-item">
                            <input type="text" placeholder="Option 2">
                        </div>
                    </div>
                    <button class="btn-secondary" onclick="addOption()">+ Add Option</button>
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" onclick="startPoll()">▶️ Start Poll</button>
                    <button onclick="stopPoll()">⏹️ Stop Poll</button>
                    <button onclick="resetPoll()">🔄 Reset Votes</button>
                </div>
                
                <div class="results" id="results"></div>
            </div>
        </div>

        <div class="footer">
            <div class="footer-left">
                <div class="footer-logo">
                    <img src="media/redlixlogo.svg" alt="REDLIX Logo">
                </div>
                <div class="footer-info">
                    <div class="footer-title">REDLIX POLL SYSTEM</div>
                    <div class="footer-subtitle">Professional live polling for streaming</div>
                </div>
            </div>
            <div class="footer-right">
                <div class="footer-version">Alpha v.1.0</div>
            </div>
        </div>
    </div>
    
    <script>
        function addOption() {
            const list = document.getElementById('optionsList');
            const num = list.children.length + 1;
            const div = document.createElement('div');
            div.className = 'option-item';
            div.innerHTML = `<input type="text" placeholder="Option ${num}">`;
            list.appendChild(div);
        }
        
        function startPoll() {
            const question = document.getElementById('question').value;
            const optionInputs = document.querySelectorAll('#optionsList input');
            const options = Array.from(optionInputs)
                .map(i => i.value.trim())
                .filter(v => v);
            
            if (!question || options.length < 2) {
                alert('Please enter a question and at least 2 options');
                return;
            }
            
            fetch('http://localhost:5001/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question, options})
            }).then(() => updateStatus());
        }
        
        function stopPoll() {
            fetch('http://localhost:5001/api/stop', {method: 'POST'})
                .then(() => updateStatus());
        }
        
        function resetPoll() {
            fetch('http://localhost:5001/api/reset', {method: 'POST'})
                .then(() => updateStatus());
        }
        
        function updateStatus() {
            fetch('http://localhost:5000/api/poll')
                .then(r => r.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    if (data.active) {
                        statusDiv.className = 'status active';
                        statusDiv.textContent = '✅ Poll Active';
                        
                        const totalVotes = Object.values(data.votes).reduce((a, b) => a + b, 0);
                        let html = '<h3>Current Results:</h3>';
                        data.options.forEach(opt => {
                            const votes = data.votes[opt] || 0;
                            html += `
                                <div class="result-item">
                                    <span>${opt}</span>
                                    <strong>${votes} votes</strong>
                                </div>
                            `;
                        });
                        html += `<p style="text-align: center; margin-top: 15px; font-weight: 700;"><strong>Total: ${totalVotes} votes</strong></p>`;
                        document.getElementById('results').innerHTML = html;
                    } else {
                        statusDiv.className = 'status inactive';
                        statusDiv.textContent = '⛔ Poll Inactive';
                        document.getElementById('results').innerHTML = '';
                    }
                });
        }
        
        setInterval(updateStatus, 2000);
        updateStatus();
    </script>
</body>
</html>
"""

@dashboard_app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@dashboard_app.route('/api/start', methods=['POST'])
def start_poll():
    data = request.json
    poll_state['active'] = True
    poll_state['question'] = data['question']
    poll_state['options'] = data['options']
    poll_state['votes'] = {opt: 0 for opt in data['options']}
    poll_state['start_time'] = time.time()
    return jsonify({'success': True})

@dashboard_app.route('/api/stop', methods=['POST'])
def stop_poll():
    poll_state['active'] = False
    return jsonify({'success': True})

@dashboard_app.route('/api/reset', methods=['POST'])
def reset_poll():
    if poll_state['options']:
        poll_state['votes'] = {opt: 0 for opt in poll_state['options']}
    return jsonify({'success': True})

# Add route to serve media files
@dashboard_app.route('/media/<path:filename>')
def serve_media_dashboard(filename):
    media_dir = os.path.join(BASE_DIR, 'media')
    return send_from_directory(media_dir, filename)

# Voting Server (Port 5002)
voting_app = Flask(__name__)
CORS(voting_app)

VOTING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Vote Now | REDLIX Poll System</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-red: rgb(128, 26, 48);
            --dark-gray: rgb(38, 38, 38);
            --burgundy: rgb(49, 18, 26);
            --white: #ffffff;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--primary-red) 0%, var(--burgundy) 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: var(--white);
            border: 3px solid var(--dark-gray);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            color: var(--dark-gray);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.5rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .question {
            font-size: 1.3em;
            color: var(--dark-gray);
            margin-bottom: 30px;
            text-align: center;
            font-weight: 600;
            padding: 20px;
            background: #f5f5f5;
            border: 2px solid var(--dark-gray);
        }

        .vote-option {
            margin: 15px 0;
            padding: 20px;
            background: var(--primary-red);
            border: 3px solid var(--dark-gray);
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            color: white;
            font-size: 1.1em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .vote-option:hover {
            background: var(--burgundy);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }

        .vote-option:active {
            transform: translateY(-1px);
        }

        .message {
            text-align: center;
            padding: 20px;
            margin-top: 20px;
            font-weight: 700;
            border: 3px solid var(--dark-gray);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .success {
            background: var(--primary-red);
            color: white;
        }

        .error {
            background: var(--burgundy);
            color: white;
        }

        .waiting {
            text-align: center;
            color: var(--dark-gray);
            padding: 40px;
        }

        .waiting h2 {
            margin-bottom: 15px;
            font-size: 1.3rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }

        .waiting p {
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Add these new styles after the existing ones */
        .frozen {
            pointer-events: none;
            position: relative;
        }

        .frozen::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, 
                rgba(173, 216, 230, 0.9) 0%,
                rgba(135, 206, 250, 0.9) 25%,
                rgba(176, 224, 230, 0.9) 50%,
                rgba(173, 216, 230, 0.9) 75%,
                rgba(135, 206, 250, 0.9) 100%);
            animation: iceShimmer 2s ease-in-out infinite;
            pointer-events: none;
            z-index: 1000;
        }

        @keyframes iceShimmer {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 0.95; }
        }

        .cooldown-overlay {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(173, 216, 230, 0.95);
            border: 5px solid var(--dark-gray);
            padding: 40px 60px;
            z-index: 1001;
            text-align: center;
            box-shadow: 0 0 50px rgba(135, 206, 250, 0.8);
            animation: icePulse 1s ease-in-out infinite;
        }

        @keyframes icePulse {
            0%, 100% { box-shadow: 0 0 50px rgba(135, 206, 250, 0.8); }
            50% { box-shadow: 0 0 80px rgba(135, 206, 250, 1); }
        }

        .cooldown-overlay h2 {
            color: var(--dark-gray);
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.5);
        }

        .cooldown-timer {
            font-size: 4em;
            font-weight: 700;
            color: var(--primary-red);
            margin: 20px 0;
            font-family: 'JetBrains Mono', monospace;
            text-shadow: 3px 3px 6px rgba(255, 255, 255, 0.7);
        }

        .cooldown-message {
            font-size: 1.1em;
            color: var(--dark-gray);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .ice-crystals {
            position: absolute;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 999;
        }

        .crystal {
            position: absolute;
            color: rgba(173, 216, 230, 0.6);
            font-size: 30px;
            animation: fall linear infinite;
        }

        @keyframes fall {
            from {
                transform: translateY(-100px) rotate(0deg);
                opacity: 1;
            }
            to {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0.3;
            }
        }
    </style>
</head>
<body>
    <div class="ice-crystals" id="crystals"></div>
    <div class="container" id="voteContainer">
        <div class="waiting">
            <h2>⏳ Waiting for Poll...</h2>
            <p>No active poll available</p>
        </div>
    </div>
    
    <script>
        let cooldownInterval = null;
        let remainingTime = 0;

        function createIceCrystals() {
            const container = document.getElementById('crystals');
            const crystalChars = ['❄', '❅', '❆', '✻', '✼', '❉'];
            
            for (let i = 0; i < 20; i++) {
                const crystal = document.createElement('div');
                crystal.className = 'crystal';
                crystal.textContent = crystalChars[Math.floor(Math.random() * crystalChars.length)];
                crystal.style.left = Math.random() * 100 + '%';
                crystal.style.animationDuration = (Math.random() * 3 + 2) + 's';
                crystal.style.animationDelay = Math.random() * 5 + 's';
                container.appendChild(crystal);
            }
        }

        function showCooldown(seconds) {
            remainingTime = seconds;
            const container = document.getElementById('voteContainer');
            container.classList.add('frozen');
            
            const overlay = document.createElement('div');
            overlay.className = 'cooldown-overlay';
            overlay.id = 'cooldownOverlay';
            overlay.innerHTML = `
                <h2>🧊 VOTE LOCKED</h2>
                <div class="cooldown-timer" id="cooldownTimer">${seconds}</div>
                <div class="cooldown-message">Wait before voting again</div>
            `;
            document.body.appendChild(overlay);

            createIceCrystals();

            cooldownInterval = setInterval(() => {
                remainingTime--;
                const timer = document.getElementById('cooldownTimer');
                if (timer) {
                    timer.textContent = remainingTime;
                }

                if (remainingTime <= 0) {
                    clearInterval(cooldownInterval);
                    container.classList.remove('frozen');
                    const overlayElement = document.getElementById('cooldownOverlay');
                    if (overlayElement) {
                        overlayElement.remove();
                    }
                    document.getElementById('crystals').innerHTML = '';
                    updateVoting();
                }
            }, 1000);
        }

        function checkCooldown() {
            fetch('http://localhost:5002/api/cooldown')
                .then(r => r.json())
                .then(data => {
                    if (data.on_cooldown && data.remaining > 0) {
                        showCooldown(data.remaining);
                    }
                });
        }

        function vote(option) {
            fetch('http://localhost:5002/api/vote', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({option})
            })
            .then(r => r.json())
            .then(data => {
                const container = document.getElementById('voteContainer');
                if (data.success) {
                    container.innerHTML = `
                        <h1>✅ Vote Submitted!</h1>
                        <div class="message success">
                            Thank you for voting!<br>
                            Your vote for "${option}" has been recorded.
                        </div>
                    `;
                    setTimeout(() => {
                        showCooldown(data.cooldown);
                    }, 2000);
                } else {
                    if (data.cooldown) {
                        showCooldown(data.cooldown);
                    } else {
                        alert(data.message || 'Error submitting vote');
                    }
                }
            });
        }
        
        function updateVoting() {
            fetch('http://localhost:5000/api/poll')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('voteContainer');
                    if (!data.active) {
                        container.innerHTML = `
                            <div class="waiting">
                                <h2>⏳ Waiting for Poll...</h2>
                                <p>No active poll available</p>
                            </div>
                        `;
                        return;
                    }
                    
                    let html = `
                        <h1>🗳️ Cast Your Vote</h1>
                        <div class="question">${data.question}</div>
                    `;
                    
                    data.options.forEach(option => {
                        html += `
                            <div class="vote-option" onclick="vote('${option}')">
                                ${option}
                            </div>
                        `;
                    });
                    
                    container.innerHTML = html;
                });
        }
        
        // Check cooldown on page load
        checkCooldown();
        
        setInterval(updateVoting, 3000);
        updateVoting();
    </script>
</body>
</html>
"""

@voting_app.route('/')
def voting():
    return render_template_string(VOTING_HTML)

@voting_app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.json
    option = data.get('option')
    
    # Get voter's IP address
    voter_ip = request.remote_addr
    
    if not poll_state['active']:
        return jsonify({'success': False, 'message': 'No active poll'})
    
    if option not in poll_state['options']:
        return jsonify({'success': False, 'message': 'Invalid option'})
    
    # Check cooldown
    current_time = datetime.now()
    if voter_ip in vote_cooldowns:
        cooldown_end = vote_cooldowns[voter_ip]
        if current_time < cooldown_end:
            remaining = int((cooldown_end - current_time).total_seconds())
            return jsonify({
                'success': False, 
                'message': f'Please wait {remaining} seconds before voting again',
                'cooldown': remaining
            })
    
    # Register the vote
    poll_state['votes'][option] += 1
    
    # Set or reset the voter's cooldown
    vote_cooldowns[voter_ip] = current_time + timedelta(seconds=30)
    
    return jsonify({'success': True, 'cooldown': 30})

@voting_app.route('/api/cooldown', methods=['GET'])
def check_cooldown():
    voter_ip = request.remote_addr
    current_time = datetime.now()
    
    if voter_ip in vote_cooldowns:
        cooldown_end = vote_cooldowns[voter_ip]
        if current_time < cooldown_end:
            remaining = int((cooldown_end - current_time).total_seconds())
            return jsonify({'on_cooldown': True, 'remaining': remaining})
    
    return jsonify({'on_cooldown': False, 'remaining': 0})

if __name__ == '__main__':
    # Print server overview
    print("\n" + "="*60)
    print("🚀 REDLIX POLL SYSTEM - SERVER OVERVIEW")
    print("="*60)
    print("\n📊 DISPLAY SERVER (OBS Browser Source)")
    print(f"   └─ http://localhost:5000")
    print(f"   └─ Use this URL in OBS Browser Source\n")
    
    print("⚙️  DASHBOARD SERVER (Control Panel)")
    print(f"   └─ http://localhost:5001")
    print(f"   └─ Open in browser to manage polls\n")
    
    print("🗳️  VOTING SERVER (Public Voting)")
    print(f"   └─ http://localhost:5002")
    print(f"   └─ Share this URL with your audience\n")
    
    print("="*60)
    print("✅ All servers are running!")
    print("⏹️  Press CTRL+C to stop all servers")
    print("="*60 + "\n")
    
    # Run the apps on separate threads
    def run_display():
        display_app.run(port=5000, debug=False, use_reloader=False)
    
    def run_dashboard():
        dashboard_app.run(port=5001, debug=False, use_reloader=False)
    
    def run_voting():
        voting_app.run(port=5002, debug=False, use_reloader=False)
    
    Thread(target=run_display).start()
    Thread(target=run_dashboard).start()
    Thread(target=run_voting).start()