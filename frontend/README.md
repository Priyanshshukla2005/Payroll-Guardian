# AI Payroll Guardian — Frontend Application

Modern enterprise payroll audit and anomaly investigation dashboard built with **React 18**, **TypeScript**, **Vite**, and **Tailwind CSS**.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js**: v18.0 or higher (v22 recommended)
- **FastAPI Backend**: Running on `http://localhost:8000`

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Start Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

### 4. Configuration
Create a `.env` file in `frontend/` if you need to override the backend API base URL:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🧪 Testing & Building

### Run Unit Tests
```bash
npm test
```

### Build Production Bundle
```bash
npm run build
```

---

## 📂 Architecture & Routing
- `/dashboard`: Executive risk overview & anomaly distribution charts
- `/payroll/upload`: Drag & drop CSV/JSON upload with validation
- `/analysis/:analysisId`: Searchable and filterable anomaly table
- `/anomalies/:analysisId/:employeeId`: Deep evidence, RAG citations & AI explanation
- `/compliance`: Statutory acts and policy knowledge search
- `/assistant`: Grounded conversational audit assistant
