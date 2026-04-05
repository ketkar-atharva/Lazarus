# Lazarus — Zombie API Discovery & Defence Platform

Welcome to the **Lazarus API Defence Platform** documentation. Lazarus is a comprehensive security tool designed specifically to protect, monitor, and manage the lifecycle of your API estate. It specializes in locating undocumented ("Shadow"), deprecated but active ("Zombie"), and inactive ("Stale") APIs, offering automated defence responses such as decommissioning, honeypot deployments, and compliance reporting.

---

## 🏗️ Architecture & Core Components

Lazarus operates with a FastAPI-driven Python backend and a React-based frontend (Vite + TailwindCSS).

- **Backend (`FastAPI`)**: Powers the data catalog, AI integration, scanning engines, and handles HTTP redirections/intercepts for decommissioned endpoints.
- **Frontend (`React + Vite`)**: A rich, responsive UI providing detailed dashboards, API security reports, interactive AI chats, and visual indicators of potential system vulnerabilities.
- **Database Backend (`MongoDB`)**: Persists honeypots, redirect rules, activity logs, and comprehensive decommission audit trails.
- **AI Engine (`OpenRouter/Qwen`)**: Integrates an LLM capable of explaining technical risks and querying the live security data dynamically in natural language.

---

## ✨ Key Features

### 1. API Catalog Explorer & Traffic Analysis
Lazarus hooks into live telemetry (or mock data representations) alongside your official OpenAPI definitions. 
It analyzes the discrepancies between the expected API catalog and real traffic flows, automatically classifying endpoints into four categories:
- ✅ **Active**: Documented and verified endpoints processing normal traffic.
- 🧟 **Zombie**: APIs marked as deprecated in documentation but still receiving active production traffic.
- 👤 **Shadow**: Undocumented endpoints receiving traffic (potential backdoors or forgotten development servers).
- ⏳ **Stale**: Documented APIs receiving zero traffic.

### 2. Comprehensive Security Posture Assessments
Every API within the catalog undergoes an automated security assessment (detailed deep-dive scoring). Lazarus evaluates:
- **Authentication**: Checks for modern protocols (OAuth 2.0, JWT) vs empty/hardcoded/legacy basic auth.
- **Encryption**: Flags outdated TLS variants or expired certificates.
- **Rate Limiting**: Verifies the presence of throttling limits to thwart brute-forcing.
- **Data Exposure**: Analyzes responses and warns about PII leakage or critical exposures (e.g., exposed DB connection strings).
- **Input Validation**: Ensures proper schema enforcement to prevent injection attempts.

### 3. Safe API Decommissioning & Redirection Workflow
One of Lazarus's highlight features is the ability to securely and permanently take an API offline, complete with an auditing trail designed for regulatory compliance (e.g., PCI-DSS v4.0).
- **Graceful Intercepts**: When an API is decommissioned, Lazarus can act as an intercept middleware, returning a polished HTML fallback message (HTTP 410 Gone) explaining why the API was taken down.
- **Traffic Redirection (Real Route Switching)**: Administrators can specify a safe endpoint. Traffic hitting the decommissioned route is intercepted with a user-friendly UI and swiftly redirected to the new authorized location.
- **Automated Stakeholder Notifications**: Emails are dispatched listing the decommission details to internal lists, CISO, and DevOps groups.

### 4. External URL Scanner
Lazarus includes an additive module for real-time external surface monitoring. Users can enter any URL to run an active probe. The scanner identifies:
- Reachability and latency.
- Missing security headers (HSTS, CSP, X-Frame-Options, etc.).
- Permissive CORS (Cross-Origin Resource Sharing) configurations (`*`).
- Exposed Server technology leaks via response headers.
- **Shadow Path Probing**: It actively tests common backdoor/sensitive paths (`/admin`, `/.env`, `/swagger`) and classifies the responses, assigning an overall risk impact score.

### 5. Automated Honeypots Deployment
Administrators can deploy deceptive Honeypots on suspected Shadow API routes. This allows security teams to log, trap, and monitor malicious actors attempting unauthorized probing before the route is permanently blocked at the gateway.

### 6. Natural Language AI Assistant
Lazarus integrates with OpenRouter's Qwen LLM. By injecting current, live API metrics (amount of zombie APIs, average risk score, specific critical vulnerabilities) tightly into the system context prompt, users can query the platform in plain English:
- *"Explain the risk of API-BNK-003 to a non-technical manager."*
- *"Which of our APIs are lacking rate-limiter protection?"*
- *"Summarize our current Shadow API exposure."*
The AI engine interprets this and offers concise, actionable remediation advice strictly based on live internal data.

### 7. Compliance & Audit Reporting
Need to prove due diligence to regulators? Lazarus handles this automatically:
- A downloadable **Compliance Report** is generated for decommissioned endpoints.
- Provides a detailed 6-step breakdown timeline (traffic routed, gateway blocked, DNS removed, tokens revoked, doc removed, stakeholders notified).
- Displays pre-decommission risk scores and post-decommission verified impacts to present immediately to auditors.

---

## 📁 Project Structure

```text
c:\UBI\
├── .env                    # Environment variables (DB config, OpenRouter API Keys)
├── server.py               # Main FastAPI Application Setup, Routes & Middleware
├── mock_data.py            # The data definition layer representing telemetry, catalogs, and logs
├── database.py             # MongoDB connection logic and queries
├── ai_engine.py            # Local, rule-based AI interpretation
├── openrouter_engine.py    # The OpenRouter LLM chatbot integration logic for contextual insights
├── email_notifier.py       # Notification handling for the decommission workflow
└── frontend/               # React application root
    ├── index.html
    ├── tailwind.config.js
    ├── src/
    │   ├── components/
    │   │   ├── DashboardHome.jsx     # Overview widgets, metrics
    │   │   ├── ApiDetail.jsx         # Drill-down into specific APIs, triggering decommissions/honeypots
    │   │   ├── ExternalScanner.jsx   # Extneral URL scanning UI
    │   │   ├── Reports.jsx           # Activity logs, Decommission actions
    │   │   ├── AiChat.jsx            # The interactive LLM chat window
    │   │   ├── Sidebar.jsx           # Application Navigation
    ...
```

---

## 🚀 Setup & Environment

Ensure you have Python 3.10+ and Node.js installed.

1. **Environment Config**: Provide your MongoDB URI, Email SMTP details (if testing emails), and OpenRouter API key inside the `.env` file.
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxx
   OPENROUTER_MODEL=qwen/qwen3-235b-a22b:free
   # MongoDB config goes here...
   ```
2. **Backend**:
   - Activate your virtual environment `source .venv/bin/activate` or `.\.venv\Scripts\activate`
   - Run the FastAPI server: `uvicorn server:app --reload`
3. **Frontend**:
   - Navigate to the frontend directory: `cd frontend`
   - Install dependencies: `npm install`
   - Run the Vite development server: `npm run dev`

---

## 🛡️ Best Practices & Usage Flow

1. **Dashboard Triage**: Start your day in the Lazarus Dashboard. Review the top "Critical" or "Shadow" endpoints.
2. **Detail Investigation**: Click into a Critical endpoint, e.g., the "Legacy Auth Token API". Review the AI-generated risk explanation if the technical details are unclear.
3. **Actioning**: If the endpoint is undocumented or legacy, use the Decommission tool to immediately issue a platform-wide 410 intercept or configure a 301 Redirect to loop legitimate traffic to the secure V2 variant.
4. **Validating External Posture**: Once internal estates are cleaned, use the External Scanner to run immediate perimeter checks validating your staging or production URLs against common misconfigurations.
5. **Reporting**: After a sprint, visit the Reports tab to review the historical logs mapping all Decommissions—handing these directly over to the compliance review teams.

---
*Lazarus API Defence Platform — Protecting your API estate from the shadows.*
