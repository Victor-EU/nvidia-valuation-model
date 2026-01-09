"""
Data Fetching API Routes

Endpoints for fetching real-time financial data from external sources.

Data Sources:
1. SEC EDGAR (primary) - Official financial statements from 10-Q/10-K filings
2. Yahoo Finance (secondary) - Real-time stock price

Strategy:
- Financial statements (revenue, income, balance sheet) from SEC EDGAR
- Stock price from Yahoo Finance chart API
- Combine both for complete data
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.data_fetcher import fetch_company_data, fetch_from_yahoo_chart_api
from app.services.sec_data_fetcher import fetch_sec_company_data, validate_sec_ticker

logger = logging.getLogger(__name__)
router = APIRouter()


class CompanyDataResponse(BaseModel):
    """Response model for company financial data."""
    ticker: str
    company_name: str

    # Income Statement (TTM)
    revenues: float
    operating_income: float
    interest_expense: float

    # Balance Sheet
    book_equity: float
    book_debt: float
    cash: float

    # Market Data
    stock_price: float
    shares_outstanding: float
    market_cap: float

    # Calculated
    effective_tax_rate: float

    # Metadata
    data_as_of: str
    fiscal_year_end: Optional[str]
    most_recent_quarter: Optional[str]
    currency: str
    data_source: str

    # Data quality indicators
    has_full_financials: bool = False
    data_notes: list[str] = []


class TickerValidationResponse(BaseModel):
    """Response for ticker validation."""
    ticker: str
    valid: bool
    company_name: Optional[str] = None


@router.get("/fetch/{ticker}", response_model=CompanyDataResponse)
async def fetch_financial_data(
    ticker: str,
    source: str = Query(default="auto", description="Data source: 'auto', 'sec', or 'yahoo'")
):
    """
    Fetch latest financial data for a company.

    Data Sources:
    - 'auto' (default): SEC for financials + Yahoo for stock price
    - 'sec': SEC EDGAR only (official filings)
    - 'yahoo': Yahoo Finance only

    Returns TTM (Trailing Twelve Months) data for income statement items
    and latest quarter snapshot for balance sheet items.

    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL, MSFT)
        source: Data source preference

    Returns:
        CompanyDataResponse with all financial data
    """
    ticker = ticker.upper().strip()

    if not ticker or len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")

    logger.info(f"API request to fetch data for ticker: {ticker} (source: {source})")

    try:
        if source == "yahoo":
            # Use Yahoo Finance only
            return await fetch_yahoo_only(ticker)
        elif source == "sec":
            # Use SEC only (no stock price)
            return await fetch_sec_only(ticker)
        else:
            # Auto: SEC for financials + Yahoo for stock price
            return await fetch_combined(ticker)

    except ValueError as e:
        logger.warning(f"Data fetch failed for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


async def fetch_combined(ticker: str) -> CompanyDataResponse:
    """
    Fetch data from both SEC and Yahoo, combining the best of each.

    SEC: Financial statements (TTM revenue, operating income, balance sheet)
    Yahoo: Real-time stock price
    """
    data_notes = []
    stock_price = 0.0
    market_cap = 0.0

    # Step 1: Get real-time stock price from Yahoo Finance chart API
    try:
        chart_data = fetch_from_yahoo_chart_api(ticker)
        stock_price = chart_data.get("regularMarketPrice", 0.0)
        data_notes.append("Stock Price: Real-time from Yahoo Finance")
        logger.info(f"Got stock price for {ticker}: ${stock_price:.2f}")
    except Exception as e:
        logger.warning(f"Could not get stock price from Yahoo: {e}")
        data_notes.append("Stock Price: Not available (Yahoo API error)")

    # Step 2: Get financial statements from SEC EDGAR
    try:
        sec_data = await fetch_sec_company_data(ticker)

        # Calculate market cap if we have both price and shares
        shares = sec_data.shares_outstanding
        if stock_price > 0 and shares > 0:
            market_cap = stock_price * shares

        # Combine SEC financials with Yahoo price
        return CompanyDataResponse(
            ticker=sec_data.ticker,
            company_name=sec_data.company_name,
            revenues=sec_data.revenues,
            operating_income=sec_data.operating_income,
            interest_expense=sec_data.interest_expense,
            book_equity=sec_data.book_equity,
            book_debt=sec_data.book_debt,
            cash=sec_data.cash,
            stock_price=stock_price,
            shares_outstanding=shares,
            market_cap=market_cap,
            effective_tax_rate=sec_data.effective_tax_rate,
            data_as_of=sec_data.data_as_of,
            fiscal_year_end=sec_data.fiscal_year_end,
            most_recent_quarter=sec_data.most_recent_quarter,
            currency=sec_data.currency,
            data_source="SEC EDGAR + Yahoo Finance",
            has_full_financials=sec_data.has_full_financials,
            data_notes=data_notes + sec_data.data_notes,
        )

    except Exception as e:
        logger.warning(f"SEC data fetch failed for {ticker}: {e}")
        data_notes.append(f"SEC EDGAR: {str(e)}")

        # Fall back to Yahoo only
        return await fetch_yahoo_only(ticker, extra_notes=data_notes)


async def fetch_sec_only(ticker: str) -> CompanyDataResponse:
    """Fetch data from SEC EDGAR only."""
    sec_data = await fetch_sec_company_data(ticker)

    return CompanyDataResponse(
        ticker=sec_data.ticker,
        company_name=sec_data.company_name,
        revenues=sec_data.revenues,
        operating_income=sec_data.operating_income,
        interest_expense=sec_data.interest_expense,
        book_equity=sec_data.book_equity,
        book_debt=sec_data.book_debt,
        cash=sec_data.cash,
        stock_price=0.0,  # SEC doesn't have real-time price
        shares_outstanding=sec_data.shares_outstanding,
        market_cap=0.0,
        effective_tax_rate=sec_data.effective_tax_rate,
        data_as_of=sec_data.data_as_of,
        fiscal_year_end=sec_data.fiscal_year_end,
        most_recent_quarter=sec_data.most_recent_quarter,
        currency=sec_data.currency,
        data_source="SEC EDGAR",
        has_full_financials=sec_data.has_full_financials,
        data_notes=sec_data.data_notes + ["Stock price not available from SEC (use Yahoo for price)"],
    )


async def fetch_yahoo_only(ticker: str, extra_notes: list[str] = None) -> CompanyDataResponse:
    """Fetch data from Yahoo Finance only."""
    data = fetch_company_data(ticker)

    notes = extra_notes or []
    notes.extend(data.data_notes)

    return CompanyDataResponse(
        ticker=data.ticker,
        company_name=data.company_name,
        revenues=data.revenues,
        operating_income=data.operating_income,
        interest_expense=data.interest_expense,
        book_equity=data.book_equity,
        book_debt=data.book_debt,
        cash=data.cash,
        stock_price=data.stock_price,
        shares_outstanding=data.shares_outstanding,
        market_cap=data.market_cap,
        effective_tax_rate=data.effective_tax_rate,
        data_as_of=data.data_as_of,
        fiscal_year_end=data.fiscal_year_end,
        most_recent_quarter=data.most_recent_quarter,
        currency=data.currency,
        data_source=data.data_source,
        has_full_financials=data.has_full_financials,
        data_notes=notes,
    )


@router.get("/validate/{ticker}", response_model=TickerValidationResponse)
async def validate_ticker_endpoint(ticker: str):
    """
    Validate if a ticker symbol exists in SEC database.

    Args:
        ticker: Stock ticker symbol to validate

    Returns:
        TickerValidationResponse with validity status
    """
    ticker = ticker.upper().strip()

    if not ticker or len(ticker) > 10:
        return TickerValidationResponse(ticker=ticker, valid=False)

    try:
        is_valid = await validate_sec_ticker(ticker)

        if is_valid:
            # Get company name from SEC
            from app.services.sec_data_fetcher import get_cik
            _, company_name = await get_cik(ticker)
            return TickerValidationResponse(
                ticker=ticker,
                valid=True,
                company_name=company_name
            )

        return TickerValidationResponse(ticker=ticker, valid=False)

    except Exception as e:
        logger.warning(f"Ticker validation failed for {ticker}: {e}")
        return TickerValidationResponse(ticker=ticker, valid=False)
