
# 🛡️ Lazarus — Zombie API Discovery & Defence Platform

**Lazarus** is an advanced API security platform designed to **discover, monitor, and secure your API ecosystem**. It specializes in identifying undocumented (*Shadow*), deprecated but active (*Zombie*), and unused (*Stale*) APIs while providing automated remediation, compliance reporting, and AI-powered insights.

---

## 🚀 Overview

Modern API ecosystems often grow uncontrollably, leaving behind:

* Undocumented endpoints (Shadow APIs)
* Deprecated but still active endpoints (Zombie APIs)
* Unused endpoints (Stale APIs)

**Lazarus solves this problem** by combining:

* Real-time traffic analysis
* Security posture evaluation
* Automated remediation workflows
* AI-powered explanations

---

## 🏗️ Architecture

Lazarus is built using a **modern full-stack architecture**:

### 🔹 Backend

* **FastAPI (Python)**

  * API catalog management
  * Security analysis engine
  * Decommissioning workflows
  * AI integration

### 🔹 Frontend

* **React + Vite + TailwindCSS**

  * Interactive dashboards
  * API insights visualization
  * AI chat interface

### 🔹 Database

* **MongoDB**

  * Stores logs, honeypots, redirects
  * Maintains audit trails

### 🔹 AI Engine

* **OpenRouter (Qwen LLM)**

  * Context-aware explanations
  * Natural language querying of system data

---

## ✨ Key Features

### 1️⃣ API Catalog Explorer & Traffic Analysis

* Compares **OpenAPI definitions vs live traffic**
* Automatically classifies APIs into:

  * ✅ Active
  * 🧟 Zombie
  * 👤 Shadow
  * ⏳ Stale

---

### 2️⃣ Security Posture Assessment

Each API is evaluated across:

* 🔐 Authentication (OAuth2, JWT, etc.)
* 🔒 Encryption (TLS checks)
* 🚦 Rate Limiting
* 📤 Data Exposure (PII leaks, secrets)
* 🧪 Input Validation

---

### 3️⃣ Safe API Decommissioning

* 🚫 HTTP **410 Gone** intercept responses
* 🔁 Smart **traffic redirection (301/302)**
* 📧 Automated stakeholder notifications
* 📜 Full compliance audit trail

---

### 4️⃣ External URL Scanner

Scan any external endpoint for:

* Missing security headers
* Weak CORS configurations
* Exposed server details
* Common sensitive paths (`/admin`, `/.env`, `/swagger`)

---

### 5️⃣ Honeypot Deployment

* Deploy traps on suspicious endpoints
* Monitor malicious traffic attempts
* Strengthen threat intelligence

---

### 6️⃣ AI-Powered Assistant

Ask questions in plain English:

* “Which APIs lack rate limiting?”
* “Explain this risk to a non-technical manager.”
* “Summarize shadow API exposure.”

💡 AI responses are based on **live internal system data**

---

### 7️⃣ Compliance & Audit Reporting

* 📄 Downloadable compliance reports
* 🧾 Full decommission lifecycle tracking:

  1. Traffic rerouting
  2. Gateway blocking
  3. DNS removal
  4. Token revocation
  5. Documentation cleanup
  6. Stakeholder notification

---

## 📁 Project Structure

```bash
c:\UBI\
├── .env
├── server.py
├── mock_data.py
├── database.py
├── ai_engine.py
├── openrouter_engine.py
├── email_notifier.py
└── frontend/
    ├── index.html
    ├── tailwind.config.js
    └── src/
        ├── components/
        │   ├── DashboardHome.jsx
        │   ├── ApiDetail.jsx
        │   ├── ExternalScanner.jsx
        │   ├── Reports.jsx
        │   ├── AiChat.jsx
        │   ├── Sidebar.jsx
```

---

## ⚙️ Setup & Installation

### 🔧 Prerequisites

* Python **3.10+**
* Node.js **16+**
* MongoDB instance

---

### 1️⃣ Environment Configuration

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=qwen/qwen3-235b-a22b:free

# MongoDB URI
MONGO_URI=your_mongodb_connection

# Email (optional)
SMTP_HOST=your_smtp_host
SMTP_PORT=your_port
SMTP_USER=your_email
SMTP_PASS=your_password
```

---

### 2️⃣ Backend Setup

```bash
# Activate virtual environment
source .venv/bin/activate
# OR (Windows)
.\.venv\Scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Run server
uvicorn server:app --reload
```

---

### 3️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## 🛡️ Usage Workflow

### 1. Dashboard Monitoring

* Review critical APIs (Shadow / Zombie)

### 2. Deep Analysis

* Inspect API details
* Use AI explanations for clarity

### 3. Take Action

* Decommission unsafe APIs
* Redirect traffic safely

### 4. External Validation

* Scan production/staging URLs

### 5. Compliance Reporting

* Export reports for audits

---

## 📌 Best Practices

* Regularly monitor Shadow APIs
* Immediately decommission unused endpoints
* Use honeypots for suspicious traffic
* Validate external exposure frequently
* Maintain compliance logs for audits

---

## 🎯 Use Cases

* Enterprise API governance
* Security compliance (PCI-DSS, SOC2)
* DevSecOps pipelines
* API lifecycle management

---

## 💡 Tagline

> **Lazarus — Protecting your API estate from the shadows.**

---
