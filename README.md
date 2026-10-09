# YouTube Automated Video Ingestion & Publishing Pipeline

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Interactive Demo](https://img.shields.io/badge/demo-GitHub%20Pages-red.svg)](https://udbhav-shrinet.github.io/youtube-auto-uploader/)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Containerized automated production daemon and publishing pipeline for scheduled video ingestion, chunked resumable uploading, and metadata management via YouTube Data API v3.

---

## 🚀 Live Interactive Showcase

Simulate the video publishing queue and schedule console:  
👉 **[Launch AutoUploader Studio](https://udbhav-shrinet.github.io/youtube-auto-uploader/)**

---

## ✨ Key Capabilities

- **Resumable Chunked Uploads**: 5MB buffer streaming for fault-tolerant video uploads over unstable network connections.
- **Automated OAuth2 Flow**: Persistent token storage with automated background token refresh.
- **Cron Scheduling Engine**: Automated background worker that monitors watch directories and publishes on scheduled intervals.
- **Dockerized Runtime**: Containerized environment for microservice deployments and headless cloud servers.

---

## 🛠️ System Architecture

```text
┌─────────────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│  Rendered Media Files   │ ───>  │  Scheduled Cron Engine │ ───>  │ Chunked Resumable    │
│  (.mp4, .mov, metadata) │       │  Queue & Payload Mgr   │       │  YouTube API Client  │
└─────────────────────────┘       └────────────────────────┘       └──────────┬───────────┘
                                                                              │
                                                   ┌──────────────────────────┴──────────────────────────┐
                                                   ▼                                                     ▼
                                       ┌─────────────────────────┐                           ┌───────────────────────┐
                                       │   Live YouTube Video    │                           │  GitHub Pages Studio  │
                                       │   Public / Scheduled    │                           │  Publishing Dashboard │
                                       └─────────────────────────┘                           └───────────────────────┘
```

---

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/udbhav-shrinet/youtube-auto-uploader.git
   cd youtube-auto-uploader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute Video Upload**:
   ```bash
   python main.py --file "video.mp4" --title "System Architecture Overview" --privacy "public"
   ```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
