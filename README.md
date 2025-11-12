# 🗳️ Redlix Polling System (RPS v1)

[![Version](https://img.shields.io/badge/version-1.0.0--alpha-orange.svg)](https://github.com/yourusername/redlix-poll)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)

> A real-time polling system with chromakey support for live streaming and broadcasts

![RPS Banner](https://via.placeholder.com/800x200/667eea/ffffff?text=Redlix+Polling+System)

## ✨ Features

- 🎥 **Chromakey Display** - Green screen background perfect for OBS/streaming software
- ⚡ **Real-time Updates** - Live vote counting with automatic refresh
- 🎛️ **Easy Control Panel** - Intuitive dashboard to manage polls
- 🗳️ **Simple Voting** - One-click voting interface for audiences
- 📊 **Live Results** - Visual progress bars and vote percentages
- 🔄 **Vote Management** - Reset, start, and stop polls on the fly

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python polls.py
   ```

## 📋 Usage

Once the application is running, you'll have access to three interfaces:

### 📺 Display Server (Port 5000)
- **URL:** `http://localhost:5000`
- Shows live poll results with green chromakey background
- Updates automatically every second
- Perfect for OBS/streaming software

### 🎛️ Dashboard (Port 5001)
- **URL:** `http://localhost:5001`
- Create poll questions and options
- Start/Stop polls
- Reset vote counts
- View real-time results

### 🗳️ Voting Page (Port 5002)
- **URL:** `http://localhost:5002`
- Public page where users vote
- Simple one-click voting
- Shows current poll question

## 🎬 Workflow

1. Open **Dashboard** (port 5001) to create and start a poll
2. Share **Voting page** (port 5002) with your audience
3. Use **Display** (port 5000) in your streaming software
4. Monitor results - Dashboard and Display update live!

## 🛠️ Tech Stack

- **Backend:** Flask 3.1.2
- **CORS:** Flask-CORS 6.0.1
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Threading:** Python Threading

## 📦 Project Structure

```
redlix-poll/
├── polls.py           # Main application file
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## ⚙️ Configuration

All servers run on localhost by default:
- Display: Port 5000
- Dashboard: Port 5001
- Voting: Port 5002

To change ports, modify the `run_display()`, `run_dashboard()`, and `run_voting()` functions in polls.py.

**Redlix**

---

<p align="center">Made with ❤️ for streamers and content creators</p>
<p align="center">© 2025 Redlix Polling System - Alpha Release</p>
