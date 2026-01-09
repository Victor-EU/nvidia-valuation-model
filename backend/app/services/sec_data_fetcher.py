"""
SEC EDGAR Data Fetcher Service

Fetches company financial data from SEC EDGAR's XBRL API.
Returns TTM (Trailing Twelve Months) data for income statement items
and latest quarter snapshot for balance sheet items.

SEC EDGAR API:
- Free, public, no authentication required
- Rate limit: 10 requests/second (be a good citizen)
- Must include User-Agent header identifying your application

Data Sources:
- Company CIK lookup: https://www.sec.gov/files/company_tickers.json
- XBRL facts: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Cache for CIK lookups and company data
_cik_cache: dict[str, str] = {}
_company_tickers: Optional[dict] = None
_company_tickers_loaded_at: Optional[datetime] = None
_data_cache: dict[str, tuple[datetime, "SECCompanyFinancials"]] = {}
_data_cache_ttl = 3600  # 1 hour - SEC data doesn't change frequently

# SEC requires User-Agent identifying the requester
SEC_USER_AGENT = "NVIDIAValuationModel/1.0 (contact@example.com)"
SEC_BASE_URL = "https://data.sec.gov"
SEC_WWW_URL = "https://www.sec.gov"


@dataclass
class SECCompanyFinancials:
    """Structured company financial data from SEC filings."""
    ticker: str
    cik: str
    company_name: str

    # Income Statement (TTM - Trailing Twelve Months)
    revenues: float
    operating_income: float
    interest_expense: float

    # Balance Sheet (Latest Quarter Snapshot)
    book_equity: float
    book_debt: float
    cash: float

    # Market Data (not from SEC - need other source)
    shares_outstanding: float

    # Calculated
    effective_tax_rate: float

    # Metadata
    data_as_of: str
    most_recent_quarter: Optional[str]
    fiscal_year_end: Optional[str]
    currency: str = "USD"
    data_source: str = "SEC EDGAR"

    # Data quality
    has_full_financials: bool = False
    data_notes: list[str] = field(default_factory=list)


# XBRL concept mapping - different companies use different tags
# We try each in order until we find data
XBRL_CONCEPTS = {
    # Income Statement items (will sum for TTM)
    "revenues": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "TotalRevenuesAndOtherIncome",
        "NetRevenues",
    ],
    "operating_income": [
        "OperatingIncome",
        "OperatingIncomeLoss",
        "IncomeLossFromOperations",
        "IncomeLossFromContinuingOperations",
    ],
    "interest_expense": [
        "InterestExpense",
        "InterestExpenseDebt",
        "InterestAndDebtExpense",
        "InterestPaid",
    ],
    "income_tax_expense": [
        "IncomeTaxExpenseBenefit",
        "IncomeTaxesPaidNet",
        "CurrentIncomeTaxExpenseBenefit",
    ],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
        "IncomeLossBeforeIncomeTaxes",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],

    # Balance Sheet items (will get latest value)
    "book_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "TotalEquity",
        "CommonStockholdersEquity",
    ],
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    "short_term_debt": [
        "ShortTermBorrowings",
        "DebtCurrent",
        "LongTermDebtCurrent",
        "ShortTermDebtWeightedAverageInterestRate",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "Cash",
        "CashAndCashEquivalents",
    ],
    # Marketable securities (short-term investments) - added to cash for valuation
    "marketable_securities": [
        "MarketableSecuritiesCurrent",
        "ShortTermInvestments",
        "AvailableForSaleSecuritiesCurrent",
        "MarketableSecurities",
        "InvestmentsInDebtAndMarketableEquitySecuritiesAndCertainTradingAssetsAtFairValue",
    ],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "CommonStockSharesIssued",
    ],
}


async def get_http_client() -> httpx.AsyncClient:
    """Create HTTP client with proper headers for SEC."""
    return httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept": "application/json",
        }
    )


async def load_company_tickers() -> dict:
    """
    Load the SEC company tickers mapping file.
    This maps ticker symbols to CIK numbers.
    Cached for 24 hours.
    """
    global _company_tickers, _company_tickers_loaded_at

    # Check if we have a recent cache
    if _company_tickers and _company_tickers_loaded_at:
        if datetime.now() - _company_tickers_loaded_at < timedelta(hours=24):
            return _company_tickers

    logger.info("Loading SEC company tickers mapping...")

    async with await get_http_client() as client:
        response = await client.get(f"{SEC_WWW_URL}/files/company_tickers.json")
        response.raise_for_status()
        data = response.json()

    # Convert to ticker -> CIK mapping
    # Original format: {"0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."}}
    _company_tickers = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", ""))
        if ticker and cik:
            _company_tickers[ticker] = {
                "cik": cik,
                "name": entry.get("title", ""),
            }

    _company_tickers_loaded_at = datetime.now()
    logger.info(f"Loaded {len(_company_tickers)} company tickers")

    return _company_tickers


async def get_cik(ticker: str) -> tuple[str, str]:
    """
    Look up CIK (Central Index Key) from ticker symbol.

    Returns:
        Tuple of (CIK, company_name)

    Raises:
        ValueError if ticker not found
    """
    ticker = ticker.upper().strip()

    # Check cache
    if ticker in _cik_cache:
        tickers = await load_company_tickers()
        info = tickers.get(ticker, {})
        return _cik_cache[ticker], info.get("name", ticker)

    # Load tickers and look up
    tickers = await load_company_tickers()

    if ticker not in tickers:
        raise ValueError(f"Ticker {ticker} not found in SEC database")

    info = tickers[ticker]
    cik = info["cik"]
    _cik_cache[ticker] = cik

    return cik, info.get("name", ticker)


async def fetch_company_facts(cik: str) -> dict:
    """
    Fetch all XBRL facts for a company from SEC EDGAR.

    Args:
        cik: Central Index Key (will be zero-padded to 10 digits)

    Returns:
        Dict containing all XBRL facts for the company
    """
    # CIK must be zero-padded to 10 digits
    cik_padded = cik.zfill(10)
    url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"

    logger.info(f"Fetching SEC XBRL facts from {url}")

    async with await get_http_client() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def get_quarterly_values(us_gaap: dict, concepts: list[str]) -> list[dict]:
    """
    Get all quarterly values for a set of concepts.

    Returns list of dicts with: val, end, form, fp (fiscal period), filed, fy (fiscal year)

    Important: Deduplicates by fiscal year + fiscal period to avoid counting
    the same quarter multiple times (can happen with amendments or different contexts).
    """
    all_values = []

    for concept in concepts:
        if concept not in us_gaap:
            continue

        concept_data = us_gaap[concept]
        units = concept_data.get("units", {})

        # Try USD first, then pure numbers
        for unit_type in ["USD", "pure", "shares"]:
            if unit_type in units:
                values = units[unit_type]

                # Filter to 10-Q filings (quarterly) with single quarter data
                # frame="CY2024Q3" indicates cumulative, we want quarterly
                quarterly = []
                for v in values:
                    form = v.get("form", "")
                    fp = v.get("fp", "")
                    frame = v.get("frame", "")

                    # Only 10-Q filings with Q1-Q4 fiscal periods
                    if form != "10-Q" or fp not in ["Q1", "Q2", "Q3", "Q4"]:
                        continue

                    # Skip if this is a cumulative frame (like CY2024Q3I for 9-month)
                    # We want the quarterly values, not YTD
                    # The frame field indicates the period type
                    if frame and "I" not in frame:
                        # Frames without 'I' suffix are typically instantaneous/point-in-time
                        # or already quarterly
                        pass

                    quarterly.append(v)

                if quarterly:
                    all_values.extend(quarterly)
                    break  # Found data for this concept, don't try other units

    # Deduplicate by (fiscal year, fiscal period) - keep the most recently filed
    # This handles cases where the same quarter appears multiple times
    by_period: dict[tuple, dict] = {}
    for v in all_values:
        fy = v.get("fy")
        fp = v.get("fp")
        filed = v.get("filed", "")

        if fy and fp:
            key = (fy, fp)
            # Keep the most recently filed version
            if key not in by_period or filed > by_period[key].get("filed", ""):
                by_period[key] = v

    unique_values = list(by_period.values())

    # Sort by end date descending (most recent first)
    unique_values.sort(key=lambda x: x.get("end", ""), reverse=True)

    return unique_values


def calculate_ttm(us_gaap: dict, metric: str) -> tuple[float, list[str]]:
    """
    Calculate TTM (Trailing Twelve Months) for an income statement metric.

    Strategy:
    1. Try to get annual (10-K) value first - most accurate
    2. If no recent 10-K, sum quarterly values
    3. Handle both standalone quarterly and YTD cumulative reporting

    SEC XBRL Reporting Patterns:
    - Some companies report standalone quarterly values in 10-Q
    - Some companies report YTD cumulative values in 10-Q
    - 10-K always has the full fiscal year value

    Returns:
        Tuple of (TTM value, list of notes about calculation)
    """
    concepts = XBRL_CONCEPTS.get(metric, [])
    notes = []

    # First, try to get the most recent annual (10-K) value
    annual_value, annual_date = get_annual_value(us_gaap, concepts)

    # Get quarterly data
    quarterly = get_quarterly_values(us_gaap, concepts)

    if annual_value > 0 and len(quarterly) < 4:
        # If we have a recent annual but not enough quarters, use the annual
        notes.append(f"{metric}: From 10-K as of {annual_date}")
        return annual_value, notes

    if len(quarterly) >= 4:
        # We have 4 quarters - check if they're standalone or cumulative
        # Sort by fiscal year descending, then by quarter descending
        quarterly.sort(key=lambda x: (x.get("fy", 0), x.get("fp", "Q0")), reverse=True)

        # Check if values look cumulative (Q3 > Q2 > Q1 for same FY)
        # by looking at the pattern of values
        q_values = quarterly[:4]

        # Group by fiscal year to detect cumulative reporting
        by_fy: dict[int, list[dict]] = {}
        for q in q_values:
            fy = q.get("fy", 0)
            if fy not in by_fy:
                by_fy[fy] = []
            by_fy[fy].append(q)

        # For each fiscal year, sort quarters and check if cumulative
        is_cumulative = False
        for fy, fy_quarters in by_fy.items():
            fy_quarters.sort(key=lambda x: x.get("fp", "Q0"))
            # Check if later quarters have higher values (cumulative pattern)
            for i in range(1, len(fy_quarters)):
                prev_val = fy_quarters[i-1].get("val", 0)
                curr_val = fy_quarters[i].get("val", 0)
                if curr_val > prev_val * 1.5:  # Q2 YTD should be ~2x Q1
                    is_cumulative = True
                    break

        if is_cumulative:
            # Convert YTD to standalone by subtraction
            # This is complex - for now, use annual value if available
            if annual_value > 0:
                notes.append(f"{metric}: From 10-K (YTD reporting detected in 10-Q)")
                return annual_value, notes
            else:
                # Try to calculate TTM from the most recent complete fiscal year
                # Q3 YTD = Q1 + Q2 + Q3, so we need to subtract
                notes.append(f"{metric}: Estimated from YTD values")
                # Just use the most recent value as rough estimate
                ttm = quarterly[0].get("val", 0)
                return ttm, notes
        else:
            # Standalone quarterly values - sum them
            ttm = sum(q.get("val", 0) for q in q_values)
            quarters_used = [f"{q.get('fp', '?')}-{q.get('fy', '?')}" for q in q_values]
            notes.append(f"{metric}: TTM from {', '.join(quarters_used)}")
            return ttm, notes

    elif len(quarterly) > 0:
        # Not enough quarters - use annual if available, else extrapolate
        if annual_value > 0:
            notes.append(f"{metric}: From 10-K as of {annual_date}")
            return annual_value, notes

        avg_quarter = sum(q.get("val", 0) for q in quarterly) / len(quarterly)
        ttm = avg_quarter * 4
        notes.append(f"{metric}: Estimated from {len(quarterly)} quarter(s)")
        return ttm, notes

    # No quarterly data - try annual
    if annual_value > 0:
        notes.append(f"{metric}: From 10-K as of {annual_date}")
        return annual_value, notes

    return 0.0, [f"{metric}: No data found"]


def get_annual_value(us_gaap: dict, concepts: list[str]) -> tuple[float, Optional[str]]:
    """
    Get the most recent annual (10-K) value for a metric.

    Searches ALL concepts and returns the most recent value across all of them.
    This ensures we get the latest data even if companies change XBRL tags over time.

    Returns:
        Tuple of (value, end date)
    """
    all_annual = []

    for concept in concepts:
        if concept not in us_gaap:
            continue

        concept_data = us_gaap[concept]
        units = concept_data.get("units", {})

        for unit_type in ["USD", "pure", "shares"]:
            if unit_type not in units:
                continue

            values = units[unit_type]

            # Filter to 10-K filings only
            annual = [v for v in values if v.get("form") == "10-K"]
            all_annual.extend(annual)

    if all_annual:
        # Sort by end date descending to get most recent
        all_annual.sort(key=lambda x: x.get("end", ""), reverse=True)
        latest = all_annual[0]
        return float(latest.get("val", 0)), latest.get("end")

    return 0.0, None


def get_latest_balance_sheet_value(us_gaap: dict, metric: str) -> tuple[float, Optional[str], list[str]]:
    """
    Get the most recent value for a balance sheet metric.

    Searches ALL concepts and returns the most recent value across all of them,
    sorted by end date (the period the value represents).

    Returns:
        Tuple of (value, quarter end date, notes)
    """
    concepts = XBRL_CONCEPTS.get(metric, [])
    notes = []
    all_values = []

    for concept in concepts:
        if concept not in us_gaap:
            continue

        concept_data = us_gaap[concept]
        units = concept_data.get("units", {})

        for unit_type in ["USD", "pure", "shares"]:
            if unit_type not in units:
                continue

            values = units[unit_type]
            all_values.extend(values)

    if all_values:
        # Sort by end date descending (most recent period first)
        all_values.sort(key=lambda x: x.get("end", ""), reverse=True)
        latest = all_values[0]
        val = latest.get("val", 0)
        end_date = latest.get("end")
        form = latest.get("form", "")
        notes.append(f"{metric}: From {form} as of {end_date}")
        return float(val), end_date, notes

    return 0.0, None, [f"{metric}: No data found"]


async def fetch_sec_company_data(ticker: str) -> SECCompanyFinancials:
    """
    Fetch comprehensive financial data for a company from SEC EDGAR.

    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')

    Returns:
        SECCompanyFinancials object with all available data

    Raises:
        ValueError: If ticker is invalid or data unavailable
    """
    ticker = ticker.upper().strip()
    logger.info(f"Fetching SEC data for {ticker}")

    # Check cache
    cache_key = ticker
    if cache_key in _data_cache:
        cached_at, cached_data = _data_cache[cache_key]
        if datetime.now() - cached_at < timedelta(seconds=_data_cache_ttl):
            logger.info(f"Returning cached SEC data for {ticker}")
            return cached_data

    data_notes: list[str] = []

    # Step 1: Get CIK from ticker
    try:
        cik, company_name = await get_cik(ticker)
        logger.info(f"Found CIK {cik} for {ticker} ({company_name})")
    except ValueError as e:
        raise ValueError(f"Could not find SEC CIK for ticker {ticker}: {e}")

    # Step 2: Fetch XBRL facts
    try:
        facts = await fetch_company_facts(cik)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(f"No SEC XBRL data available for {ticker} (CIK: {cik})")
        raise ValueError(f"SEC API error for {ticker}: {e}")

    # Step 3: Extract financial data
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    if not us_gaap:
        raise ValueError(f"No US-GAAP data found for {ticker}")

    # Income Statement - TTM calculations
    revenues, rev_notes = calculate_ttm(us_gaap, "revenues")
    data_notes.extend(rev_notes)

    operating_income, op_notes = calculate_ttm(us_gaap, "operating_income")
    data_notes.extend(op_notes)

    interest_expense, int_notes = calculate_ttm(us_gaap, "interest_expense")
    data_notes.extend(int_notes)

    # For tax rate calculation
    income_tax, _ = calculate_ttm(us_gaap, "income_tax_expense")
    pretax_income, _ = calculate_ttm(us_gaap, "pretax_income")

    # Balance Sheet - Latest values
    book_equity, equity_date, equity_notes = get_latest_balance_sheet_value(us_gaap, "book_equity")
    data_notes.extend(equity_notes)

    long_term_debt, _, _ = get_latest_balance_sheet_value(us_gaap, "long_term_debt")
    short_term_debt, _, _ = get_latest_balance_sheet_value(us_gaap, "short_term_debt")
    book_debt = long_term_debt + short_term_debt
    if book_debt > 0:
        data_notes.append(f"book_debt: LT debt ({long_term_debt:,.0f}) + ST debt ({short_term_debt:,.0f})")

    cash, cash_date, cash_notes = get_latest_balance_sheet_value(us_gaap, "cash")

    # Add marketable securities to cash for valuation purposes (total liquid assets)
    marketable_securities, ms_date, _ = get_latest_balance_sheet_value(us_gaap, "marketable_securities")
    if marketable_securities > 0:
        cash_notes = [f"cash: Cash ({cash:,.0f}) + Marketable Securities ({marketable_securities:,.0f}) from 10-Q as of {cash_date or ms_date}"]
        cash = cash + marketable_securities
    data_notes.extend(cash_notes)

    shares_outstanding, _, shares_notes = get_latest_balance_sheet_value(us_gaap, "shares_outstanding")
    data_notes.extend(shares_notes)

    # Calculate effective tax rate
    effective_tax_rate = 0.21  # Default US corporate rate
    if pretax_income > 0 and income_tax > 0:
        calculated_rate = abs(income_tax) / pretax_income
        if 0 < calculated_rate < 0.5:  # Sanity check
            effective_tax_rate = calculated_rate
            data_notes.append(f"effective_tax_rate: Calculated as {effective_tax_rate:.1%}")
    else:
        data_notes.append("effective_tax_rate: Using default 21%")

    # Determine most recent quarter
    most_recent_quarter = equity_date or cash_date

    # Check if we have full financials
    has_full_financials = revenues > 0 and book_equity != 0

    # Log summary
    logger.info(f"SEC data summary for {company_name} ({ticker}):")
    logger.info(f"  Revenue (TTM): ${revenues:,.0f}")
    logger.info(f"  Operating Income (TTM): ${operating_income:,.0f}")
    logger.info(f"  Book Equity: ${book_equity:,.0f}")
    logger.info(f"  Book Debt: ${book_debt:,.0f}")
    logger.info(f"  Cash: ${cash:,.0f}")
    logger.info(f"  Shares Outstanding: {shares_outstanding:,.0f}")
    logger.info(f"  Most Recent Quarter: {most_recent_quarter}")

    result = SECCompanyFinancials(
        ticker=ticker,
        cik=cik,
        company_name=company_name,
        revenues=revenues,
        operating_income=operating_income,
        interest_expense=interest_expense,
        book_equity=book_equity,
        book_debt=book_debt,
        cash=cash,
        shares_outstanding=shares_outstanding,
        effective_tax_rate=effective_tax_rate,
        data_as_of=datetime.now().isoformat(),
        most_recent_quarter=most_recent_quarter,
        fiscal_year_end=None,  # Could extract from submissions endpoint
        has_full_financials=has_full_financials,
        data_notes=data_notes,
    )

    # Cache the result
    _data_cache[cache_key] = (datetime.now(), result)

    return result


async def validate_sec_ticker(ticker: str) -> bool:
    """Check if a ticker exists in SEC database."""
    try:
        await get_cik(ticker.upper().strip())
        return True
    except ValueError:
        return False
