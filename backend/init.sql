-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Reference Data Tables
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    moodys_rating VARCHAR(10),
    adj_default_spread DECIMAL(12,8),
    equity_risk_premium DECIMAL(12,8),
    country_risk_premium DECIMAL(12,8),
    corporate_tax_rate DECIMAL(8,6),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    region VARCHAR(20) DEFAULT 'US',
    num_firms INTEGER,
    revenue_growth_5yr DECIMAL(12,8),
    operating_margin DECIMAL(12,8),
    after_tax_roc DECIMAL(12,8),
    effective_tax_rate DECIMAL(12,8),
    unlevered_beta DECIMAL(12,8),
    levered_beta DECIMAL(12,8),
    cost_of_equity DECIMAL(12,8),
    std_dev_stock DECIMAL(12,8),
    pretax_cost_of_debt DECIMAL(12,8),
    debt_to_capital DECIMAL(12,8),
    cost_of_capital DECIMAL(12,8),
    sales_to_capital DECIMAL(12,8),
    ev_to_sales DECIMAL(12,8),
    ev_to_ebitda DECIMAL(12,8),
    ev_to_ebit DECIMAL(12,8),
    price_to_book DECIMAL(12,8),
    trailing_pe DECIMAL(12,8),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, region)
);

CREATE TABLE IF NOT EXISTS synthetic_ratings (
    id SERIAL PRIMARY KEY,
    firm_type VARCHAR(50) NOT NULL,
    icr_min DECIMAL(12,6),
    icr_max DECIMAL(12,6),
    rating VARCHAR(10) NOT NULL,
    spread DECIMAL(12,8) NOT NULL
);

CREATE TABLE IF NOT EXISTS rating_spreads (
    id SERIAL PRIMARY KEY,
    rating VARCHAR(10) NOT NULL UNIQUE,
    spread DECIMAL(12,8) NOT NULL
);

-- Valuation Model Tables
CREATE TABLE IF NOT EXISTS valuation_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    company_name VARCHAR(100),
    valuation_date DATE,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Company fundamentals (JSONB for flexibility)
    base_year_data JSONB DEFAULT '{}',

    -- Value drivers
    value_drivers JSONB DEFAULT '{}',

    -- Market inputs
    market_inputs JSONB DEFAULT '{}',

    -- R&D settings
    rd_settings JSONB DEFAULT '{}',

    -- Operating lease settings
    lease_settings JSONB DEFAULT '{}',

    -- Employee options
    option_settings JSONB DEFAULT '{}',

    -- Override assumptions
    overrides JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS business_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES valuation_models(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    segment_type VARCHAR(50),
    segment_order INTEGER DEFAULT 0,
    inputs JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cost_of_capital_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES valuation_models(id) ON DELETE CASCADE,
    approach VARCHAR(50) DEFAULT 'detailed',
    direct_coc DECIMAL(12,8),
    beta_approach VARCHAR(50) DEFAULT 'single_business_us',
    direct_beta DECIMAL(12,8),
    erp_approach VARCHAR(50) DEFAULT 'operating_countries',
    direct_erp DECIMAL(12,8),
    operating_countries JSONB DEFAULT '[]',
    debt_approach VARCHAR(50) DEFAULT 'actual_rating',
    actual_rating VARCHAR(10),
    firm_type INTEGER DEFAULT 1,
    debt_maturity DECIMAL(8,4) DEFAULT 3,
    preferred_shares INTEGER,
    preferred_price DECIMAL(12,4),
    preferred_dividend DECIMAL(12,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_countries_name ON countries(name);
CREATE INDEX IF NOT EXISTS idx_industries_name ON industries(name);
CREATE INDEX IF NOT EXISTS idx_industries_region ON industries(region);
CREATE INDEX IF NOT EXISTS idx_models_name ON valuation_models(name);
CREATE INDEX IF NOT EXISTS idx_segments_model ON business_segments(model_id);
CREATE INDEX IF NOT EXISTS idx_coc_model ON cost_of_capital_settings(model_id);
