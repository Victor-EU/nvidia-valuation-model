# NVIDIA DCF Valuation Model

A full-stack web application for Discounted Cash Flow (DCF) valuation of NVIDIA and other public companies. Built with Svelte 5 and FastAPI.

## Features

- **Real-time Data Fetching**: Automatically fetch latest financial data from SEC EDGAR (10-K/10-Q filings) and Yahoo Finance (stock prices)
- **Multi-Segment DCF Analysis**: Separate projections for different business segments (AI, Automotive, Rest of Business)
- **Comprehensive Cost of Capital**: Multiple WACC calculation methods including CAPM with operating country ERP
- **10-Year Financial Projections**: Revenue growth, margin convergence, reinvestment calculations
- **Interactive UI**: Real-time recalculation as inputs change

## Tech Stack

### Frontend
- **Svelte 5** with Runes for reactive state management
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Vite** for build tooling

### Backend
- **FastAPI** (Python) for REST API
- **SQLite** for local data persistence
- **SEC EDGAR XBRL API** for official financial statements
- **Yahoo Finance** for real-time stock prices

## Project Structure

```
├── frontend/                 # Svelte 5 application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/   # UI components
│   │   │   ├── stores/       # Svelte stores (state management)
│   │   │   ├── services/     # API client
│   │   │   └── utils/        # Formatting utilities
│   │   └── routes/           # SvelteKit pages
│   └── package.json
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   │   ├── sec_data_fetcher.py   # SEC EDGAR integration
│   │   │   └── data_fetcher.py       # Yahoo Finance integration
│   │   └── main.py           # FastAPI entry point
│   └── requirements.txt
│
├── data/                     # Source data (Excel model)
└── docker-compose.yml        # PostgreSQL setup (optional)
```

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- npm or pnpm

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## API Endpoints

### Data Fetching
- `GET /api/data/fetch/{ticker}` - Fetch financial data from SEC + Yahoo
  - Query params: `source=auto|sec|yahoo`
- `GET /api/data/validate/{ticker}` - Validate ticker exists in SEC database

### Valuation Models
- `GET /api/models` - List saved models
- `POST /api/models` - Create new model
- `GET /api/models/{id}` - Get model by ID
- `PUT /api/models/{id}` - Update model
- `POST /api/models/{id}/calculate` - Run DCF calculations

## Data Sources

1. **SEC EDGAR XBRL API** (Primary)
   - Official 10-K and 10-Q filings
   - TTM (Trailing Twelve Months) calculations
   - Balance sheet snapshots
   - No authentication required

2. **Yahoo Finance** (Secondary)
   - Real-time stock prices
   - Market data

## Key Calculations

- **WACC**: Weighted Average Cost of Capital using CAPM
- **DCF**: Discounted Cash Flow with terminal value (Gordon Growth)
- **TTM**: Trailing Twelve Months for income statement items
- **Operating Margin Convergence**: Gradual convergence to target margins over projection period

## License

MIT

## Acknowledgments

Based on DCF methodology from Aswath Damodaran's valuation framework.
