"""
Financial Data Fetcher Service

Fetches company financial data from Yahoo Finance using yfinance.
Returns TTM (Trailing Twelve Months) data for income statement items
and latest snapshot for balance sheet items.

Strategy:
1. Use yfinance for quarterly financials
2. Calculate TTM by summing last 4 quarters (income statement)
3. Use latest quarter for balance sheet items
4. Fall back to chart API for reliable price data
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Simple cache to avoid rate limiting
_cache: dict = {}
_cache_ttl = 300  # 5 minutes

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


@dataclass
class CompanyFinancials:
    """Structured company financial data."""
    ticker: str
    company_name: str

    # Income Statement (TTM - Trailing Twelve Months)
    revenues: float
    operating_income: float
    interest_expense: float

    # Balance Sheet (Latest Quarter Snapshot)
    book_equity: float
    book_debt: float
    cash: float

    # Market Data
    stock_price: float
    shares_outstanding: float
    market_cap: float

    # Calculated/Derived
    effective_tax_rate: float

    # Metadata
    data_as_of: str
    fiscal_year_end: Optional[str]
    most_recent_quarter: Optional[str]
    currency: str
    data_source: str = "Yahoo Finance"

    # Data quality flags
    has_full_financials: bool = False
    data_notes: list[str] = field(default_factory=list)


def fetch_from_yahoo_chart_api(ticker: str) -> dict:
    """
    Fetch basic price data from Yahoo Finance chart API.
    This endpoint is the most reliable and doesn't require authentication.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "interval": "1d",
        "range": "5d"
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    result = data.get("chart", {}).get("result", [])
    if not result:
        raise ValueError(f"No data found for ticker: {ticker}")

    return result[0].get("meta", {})


def calculate_ttm_from_quarterly(quarterly_df, field_names: list[str]) -> Optional[float]:
    """
    Calculate TTM (Trailing Twelve Months) from quarterly data.
    Sums the most recent 4 quarters.

    Args:
        quarterly_df: pandas DataFrame with quarterly data (columns are dates, rows are metrics)
        field_names: List of possible field names to look for (varies by data source)

    Returns:
        TTM value as float, or None if not available
    """
    if quarterly_df is None or quarterly_df.empty:
        return None

    try:
        # Find the first matching field name
        for field_name in field_names:
            if field_name in quarterly_df.index:
                # Get the row for this metric
                row = quarterly_df.loc[field_name]
                # Drop NaN values and get the most recent 4 quarters
                values = row.dropna()

                if len(values) >= 4:
                    # Sum the 4 most recent quarters
                    ttm = float(values.iloc[:4].sum())
                    logger.debug(f"TTM for {field_name}: {ttm} (from 4 quarters)")
                    return ttm
                elif len(values) > 0:
                    # If we have fewer than 4 quarters, extrapolate
                    avg_quarter = float(values.mean())
                    ttm = avg_quarter * 4
                    logger.debug(f"TTM for {field_name}: {ttm} (extrapolated from {len(values)} quarters)")
                    return ttm

        return None
    except Exception as e:
        logger.warning(f"TTM calculation failed: {e}")
        return None


def get_latest_balance_sheet_value(quarterly_df, field_names: list[str]) -> Optional[float]:
    """
    Get the most recent value from quarterly balance sheet.

    Args:
        quarterly_df: pandas DataFrame with quarterly balance sheet
        field_names: List of possible field names to look for

    Returns:
        Latest value as float, or None if not available
    """
    if quarterly_df is None or quarterly_df.empty:
        return None

    try:
        for field_name in field_names:
            if field_name in quarterly_df.index:
                row = quarterly_df.loc[field_name]
                values = row.dropna()
                if len(values) > 0:
                    # Return the most recent value (first column after dropping NaN)
                    return float(values.iloc[0])
        return None
    except Exception as e:
        logger.warning(f"Balance sheet extraction failed: {e}")
        return None


def fetch_with_yfinance(ticker: str) -> Optional[dict]:
    """
    Fetch comprehensive financial data using yfinance library.

    Strategy: Avoid the rate-limited quoteSummary endpoint by:
    1. Getting financials first (uses a different endpoint)
    2. Getting fast_info for basic market data (less rate-limited)
    3. Only falling back to info if needed

    Returns dict with:
    - info: Company info and market data
    - quarterly_income: Quarterly income statement
    - quarterly_balance: Quarterly balance sheet
    """
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)

        # Try to get quarterly financial statements FIRST
        # These use different endpoints that are less rate-limited
        quarterly_income = None
        quarterly_balance = None

        logger.info(f"Attempting to fetch quarterly income statement for {ticker}...")
        try:
            quarterly_income = stock.quarterly_income_stmt
            if quarterly_income is not None and not quarterly_income.empty:
                logger.info(f"SUCCESS: Got quarterly income statement: {quarterly_income.shape}")
                logger.info(f"Income statement columns: {list(quarterly_income.columns)[:4]}")
                logger.info(f"Income statement rows: {list(quarterly_income.index)[:10]}")
            else:
                logger.info(f"Quarterly income statement returned empty or None")
                quarterly_income = None
        except Exception as e:
            logger.warning(f"FAILED to fetch quarterly income: {type(e).__name__}: {e}")

        logger.info(f"Attempting to fetch quarterly balance sheet for {ticker}...")
        try:
            quarterly_balance = stock.quarterly_balance_sheet
            if quarterly_balance is not None and not quarterly_balance.empty:
                logger.info(f"SUCCESS: Got quarterly balance sheet: {quarterly_balance.shape}")
                logger.info(f"Balance sheet columns: {list(quarterly_balance.columns)[:4]}")
                logger.info(f"Balance sheet rows: {list(quarterly_balance.index)[:10]}")
            else:
                logger.info(f"Quarterly balance sheet returned empty or None")
                quarterly_balance = None
        except Exception as e:
            logger.warning(f"FAILED to fetch quarterly balance sheet: {type(e).__name__}: {e}")

        # Try fast_info first - it's less rate-limited than info
        info = {}
        try:
            fast_info = stock.fast_info
            info = {
                'regularMarketPrice': getattr(fast_info, 'last_price', None),
                'previousClose': getattr(fast_info, 'previous_close', None),
                'marketCap': getattr(fast_info, 'market_cap', None),
                'sharesOutstanding': getattr(fast_info, 'shares', None),
                'currency': getattr(fast_info, 'currency', 'USD'),
            }
            logger.info(f"Got fast_info: price={info.get('regularMarketPrice')}, shares={info.get('sharesOutstanding')}")
        except Exception as e:
            logger.warning(f"Could not get fast_info: {e}")

        # Only try full info if we need more data and don't have financials
        # This is the rate-limited endpoint
        if not quarterly_income and not quarterly_balance:
            try:
                full_info = stock.info
                if full_info:
                    info.update(full_info)
                    logger.info(f"Got full info for {ticker}")
            except Exception as e:
                logger.warning(f"Could not get full info (likely rate limited): {e}")

        # We need at least some data
        if not info.get('regularMarketPrice') and quarterly_income is None and quarterly_balance is None:
            return None

        return {
            'info': info,
            'quarterly_income': quarterly_income,
            'quarterly_balance': quarterly_balance,
        }

    except ImportError:
        logger.error("yfinance library not installed")
        return None
    except Exception as e:
        logger.warning(f"yfinance fetch failed: {e}")
        return None


def fetch_company_data(ticker: str, max_retries: int = 1) -> CompanyFinancials:
    """
    Fetch comprehensive financial data for a company.

    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
        max_retries: Number of retry attempts on failure

    Returns:
        CompanyFinancials object with all available data

    Raises:
        ValueError: If ticker is invalid or no data available
    """
    ticker = ticker.upper().strip()
    logger.info(f"Fetching financial data for {ticker}")

    # Check cache first
    cache_key = f"{ticker}_{datetime.now().strftime('%Y%m%d%H%M')[:11]}"
    if cache_key in _cache:
        logger.info(f"Returning cached data for {ticker}")
        return _cache[cache_key]

    # Initialize with defaults
    company_name = ticker
    revenues = 0.0
    operating_income = 0.0
    interest_expense = 0.0
    book_equity = 0.0
    book_debt = 0.0
    cash = 0.0
    stock_price = 0.0
    shares_outstanding = 0.0
    market_cap = 0.0
    effective_tax_rate = 0.21  # Default US corporate rate
    currency = "USD"
    fiscal_year_end = None
    most_recent_quarter = None
    has_full_financials = False
    data_notes: list[str] = []

    last_error = None

    # Try yfinance with retries
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                logger.info(f"Retry attempt {attempt + 1}, waiting {wait_time}s...")
                time.sleep(wait_time)

            yf_data = fetch_with_yfinance(ticker)

            if yf_data:
                info = yf_data.get('info', {})
                quarterly_income = yf_data.get('quarterly_income')
                quarterly_balance = yf_data.get('quarterly_balance')

                # === Basic Info ===
                company_name = info.get('longName') or info.get('shortName') or ticker
                currency = info.get('currency', 'USD')
                fiscal_year_end = info.get('fiscalYearEnd')

                # === Market Data ===
                stock_price = float(info.get('regularMarketPrice') or info.get('currentPrice') or 0)
                shares_outstanding = float(info.get('sharesOutstanding') or 0)
                market_cap = float(info.get('marketCap') or 0)

                # === Income Statement - Calculate TTM ===
                # Revenue - try multiple field names
                ttm_revenue = calculate_ttm_from_quarterly(
                    quarterly_income,
                    ['Total Revenue', 'Operating Revenue', 'Revenue']
                )
                if ttm_revenue and ttm_revenue > 0:
                    revenues = ttm_revenue
                    data_notes.append("Revenue: TTM from 4 quarters")
                    has_full_financials = True
                elif info.get('totalRevenue'):
                    revenues = float(info.get('totalRevenue'))
                    data_notes.append("Revenue: Annual from info")

                # Operating Income
                ttm_op_income = calculate_ttm_from_quarterly(
                    quarterly_income,
                    ['Operating Income', 'EBIT', 'Operating Profit']
                )
                if ttm_op_income is not None:
                    operating_income = ttm_op_income
                    data_notes.append("Operating Income: TTM from 4 quarters")
                elif info.get('operatingMargins') and revenues > 0:
                    operating_income = revenues * float(info.get('operatingMargins', 0))
                    data_notes.append("Operating Income: Estimated from margin")

                # Interest Expense (often reported as negative)
                ttm_interest = calculate_ttm_from_quarterly(
                    quarterly_income,
                    ['Interest Expense', 'Interest Expense Non Operating', 'Net Interest Income']
                )
                if ttm_interest is not None:
                    interest_expense = abs(ttm_interest)  # Use absolute value
                    data_notes.append("Interest Expense: TTM from 4 quarters")

                # === Balance Sheet - Latest Quarter ===
                if quarterly_balance is not None and not quarterly_balance.empty:
                    # Get the date of the most recent quarter
                    try:
                        most_recent_quarter = str(quarterly_balance.columns[0].date())
                    except Exception:
                        most_recent_quarter = str(quarterly_balance.columns[0])

                    # Book Equity (Stockholders' Equity)
                    equity = get_latest_balance_sheet_value(
                        quarterly_balance,
                        ['Stockholders Equity', 'Total Stockholders Equity',
                         'Common Stock Equity', 'Total Equity Gross Minority Interest']
                    )
                    if equity is not None:
                        book_equity = equity
                        data_notes.append(f"Book Equity: Latest quarter ({most_recent_quarter})")

                    # Total Debt
                    debt = get_latest_balance_sheet_value(
                        quarterly_balance,
                        ['Total Debt', 'Total Liabilities Net Minority Interest',
                         'Long Term Debt', 'Long Term Debt And Capital Lease Obligation']
                    )
                    if debt is not None:
                        book_debt = debt
                    else:
                        # Try summing short-term and long-term debt
                        short_debt = get_latest_balance_sheet_value(
                            quarterly_balance,
                            ['Current Debt', 'Current Debt And Capital Lease Obligation',
                             'Short Term Debt']
                        ) or 0
                        long_debt = get_latest_balance_sheet_value(
                            quarterly_balance,
                            ['Long Term Debt', 'Long Term Debt And Capital Lease Obligation']
                        ) or 0
                        book_debt = short_debt + long_debt

                    if book_debt > 0:
                        data_notes.append(f"Book Debt: Latest quarter ({most_recent_quarter})")

                    # Cash and Cash Equivalents
                    cash_value = get_latest_balance_sheet_value(
                        quarterly_balance,
                        ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments',
                         'Cash', 'Cash And Short Term Investments']
                    )
                    if cash_value is not None:
                        cash = cash_value
                        data_notes.append(f"Cash: Latest quarter ({most_recent_quarter})")

                # === Effective Tax Rate ===
                if info.get('effectiveTaxRate'):
                    effective_tax_rate = float(info.get('effectiveTaxRate'))
                    data_notes.append("Tax Rate: From company info")
                else:
                    # Try to calculate from income statement
                    ttm_pretax = calculate_ttm_from_quarterly(
                        quarterly_income,
                        ['Pretax Income', 'Income Before Tax', 'EBT']
                    )
                    ttm_tax = calculate_ttm_from_quarterly(
                        quarterly_income,
                        ['Tax Provision', 'Income Tax Expense', 'Tax Expense']
                    )
                    if ttm_pretax and ttm_tax and ttm_pretax > 0:
                        calculated_rate = abs(ttm_tax) / ttm_pretax
                        if 0 < calculated_rate < 0.5:  # Sanity check
                            effective_tax_rate = calculated_rate
                            data_notes.append("Tax Rate: Calculated from TTM")

                logger.info(f"Successfully fetched data for {company_name} ({ticker})")
                break  # Success - exit retry loop

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.warning(f"All yfinance attempts failed, falling back to chart API")

    # Always try to get reliable price from chart API
    try:
        meta = fetch_from_yahoo_chart_api(ticker)
        chart_price = meta.get("regularMarketPrice", 0)
        if chart_price:
            if stock_price == 0:
                stock_price = chart_price
            # Use chart API company name if we don't have one
            if company_name == ticker:
                company_name = meta.get("longName") or meta.get("shortName") or ticker
            currency = meta.get("currency", currency)
            data_notes.append("Stock Price: Real-time from Yahoo Finance")
    except Exception as e:
        logger.warning(f"Chart API fallback failed: {e}")

    # Add note about rate limiting if we didn't get full financials
    if not has_full_financials:
        data_notes.append("Financial statements: Unavailable (Yahoo Finance rate limited)")
        data_notes.append("For full data: Use SEC EDGAR, Bloomberg, or enter manually")

    # Validate we got at least price data
    if stock_price == 0:
        raise ValueError(f"Failed to fetch any data for {ticker}: {str(last_error)}")

    # Log summary
    logger.info(f"Data summary for {company_name}:")
    logger.info(f"  Stock Price: ${stock_price:.2f}")
    logger.info(f"  Revenue (TTM): ${revenues:,.0f}")
    logger.info(f"  Operating Income (TTM): ${operating_income:,.0f}")
    logger.info(f"  Book Equity: ${book_equity:,.0f}")
    logger.info(f"  Book Debt: ${book_debt:,.0f}")
    logger.info(f"  Cash: ${cash:,.0f}")
    logger.info(f"  Shares Outstanding: {shares_outstanding:,.0f}")
    logger.info(f"  Full financials available: {has_full_financials}")

    result = CompanyFinancials(
        ticker=ticker.upper(),
        company_name=company_name,
        revenues=revenues,
        operating_income=operating_income,
        interest_expense=interest_expense,
        book_equity=book_equity,
        book_debt=book_debt,
        cash=cash,
        stock_price=stock_price,
        shares_outstanding=shares_outstanding,
        market_cap=market_cap,
        effective_tax_rate=effective_tax_rate,
        data_as_of=datetime.now().isoformat(),
        fiscal_year_end=fiscal_year_end,
        most_recent_quarter=most_recent_quarter,
        currency=currency,
        has_full_financials=has_full_financials,
        data_notes=data_notes,
    )

    # Cache the result
    _cache[cache_key] = result
    return result


def validate_ticker(ticker: str) -> bool:
    """Check if a ticker symbol is valid."""
    try:
        meta = fetch_from_yahoo_chart_api(ticker.upper().strip())
        return meta.get("regularMarketPrice") is not None
    except Exception:
        return False
