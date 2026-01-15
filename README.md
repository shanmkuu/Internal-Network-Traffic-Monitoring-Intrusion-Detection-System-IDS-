# Internal Network Traffic Monitoring & Custom Intrusion Detection System (IDS)

A comprehensive cybersecurity dashboard for real-time network monitoring, traffic analysis, and intrusion detection. Built with React (Vite) and Python (FastAPI + Scapy).

## 🚀 Key Features

*   **Real-Time Traffic Monitoring**: Visualizes TCP, UDP, ICMP, HTTP, HTTPS, and DNS traffic flows live.
*   **Intrusion Detection**: Detects suspect patterns (e.g., Port Scanning, brute force) and logs alerts.
*   **Connected Devices**: Actively scans and lists devices on the local subnet (ARP scanning).
*   **Packet Capture Stream**: Live feed of network packets with protocol breakdown.
*   **System Logs**: Searchable, filterable logs of system events.
*   **Dark Glassmorphic UI**: Premium, cyber-themed interface for optimal visualization.

## 🛠️ System Architecture

*   **Frontend**: React 18, Vite, TailwindCSS, Recharts, Lucide Icons.
*   **Backend**: Python 3.10+, FastAPI (API Layer), Scapy (Network Sniffing).
*   **Database**: Supabase (PostgreSQL) for persisting alerts and stats.

---

## 📋 Prerequisites

1.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
2.  **Node.js & npm**: [Download Here](https://nodejs.org/)
3.  **Npcap (Windows Only)**: Required for Scapy to sniff packets.
    *   [Download Npcap](https://npcap.com/#download)
    *   **IMPORTANT**: During installation, check **"Install Npcap in WinPcap API-compatible Mode"**.
4.  **Supabase Account**: A free project for the database.

---

## ⚙️ Installation & Setup

### 1. Database Setup (Supabase)

1.  Create a new Supabase project.
2.  Go to **Project Settings -> API** and copy:
    *   `Project URL`
    *   `anon public` key
    *   `service_role` key (keep this secret!)
3.  Go to the **SQL Editor** in Supabase and run the initialization scripts found in `backend/`:
    *   First, the basic schema (not included inrepo, assuming pre-configured).
    *   Run `backend/update_schema.sql` (Adds HTTP/DNS columns).
    *   Run `backend/create_devices_table.sql` (Adds Connected Devices table).

### 2. Backend Setup

1.  Navigate to the `backend` directory:
    ```powershell
    cd backend
    ```
2.  Create a virtual environment:
    ```powershell
    python -m venv venv
    ```
3.  Activate the environment:
    ```powershell
    .\venv\Scripts\Activate
    ```
4.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```
5.  Configure Environment Variables:
    *   Create a `.env` file in the `backend/` folder (or root, check code).
    *   Add your Supabase credentials:
        ```env
        SUPABASE_URL=your_project_url
        SUPABASE_KEY=your_anon_key
        SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
        ```

### 3. Frontend Setup

1.  Navigate to the root directory (where `package.json` is):
    ```powershell
    cd ..
    ```
2.  Install dependencies:
    ```powershell
    npm install
    ```
3.  Configure Environment Variables:
    *   Create a `.env` file in the root.
    *   Add:
        ```env
        VITE_SUPABASE_URL=your_project_url
        VITE_SUPABASE_ANON_KEY=your_anon_key
        ```

---

## 🚦 How to Run the System

You need to run **three** separate terminals to have the full system operational.

### Terminal 1: Backend API
This serves the data to the frontend.
```powershell
cd backend
.\venv\Scripts\Activate
python main.py
```
*   Server runs at: `http://localhost:8000`
*   Docs available at: `http://localhost:8000/docs`

### Terminal 2: Network Monitor (The "Eye")
This captures live traffic. Run this as **Administrator** for full packet access.
```powershell
cd backend
.\venv\Scripts\Activate
python monitor.py
```
*   You should see "Starting IDS Monitor..."
*   It will auto-detect your Wi-Fi interface.

### Terminal 3: Frontend UI
This runs the dashboard.
```powershell
npm run dev
```
*   Open your browser to: `http://localhost:5173`

---

## 🔍 Modules Explained

*   **Security Command Center (Dashboard)**: High-level overview. Recent alerts, traffic volume, and system status.
*   **Live Traffic Monitor**: Real-time graphs. Click "Resume" to start the stream. Use the protocol buttons (TCP/UDP/DNS) to filter the chart lines.
*   **Network Analytics Hub**:
    *   **Top Threat Sources**: IPs generating the most alerts.
    *   **Connected Devices**: Active scan of devices on your Wi-Fi (updates every 30s).
*   **Security Alerts**: Detailed table of all detected threats. Support CSV export.
*   **System Logs**: Internal logs of when the monitor starts, stops, or encounters errors.

## 🐛 Troubleshooting

*   **No Traffic Data?**
    *   Ensure `monitor.py` is running as Administrator.
    *   Check if you installed **Npcap** in "WinPcap API-compatible Mode".
*   **"Missing Columns" Error?**
    *   Run the `backend/update_schema.sql` script in Supabase.
*   **Connected Devices not showing?**
    *   Wait 30 seconds for the first scan to complete.
    *   Ensure the backend machine has network access.

---

Built with ❤️ for Cyber Defense.
