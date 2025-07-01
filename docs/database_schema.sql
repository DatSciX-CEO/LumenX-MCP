CREATE TABLE IF NOT EXISTS legal_spend_invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(50),
    matter_id VARCHAR(50),
    matter_name VARCHAR(255),
    department VARCHAR(100) NOT NULL DEFAULT 'Legal',
    practice_area VARCHAR(100),
    invoice_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    expense_category VARCHAR(100),
    description TEXT,
    billing_period_start DATE,
    billing_period_end DATE,
    status VARCHAR(50) DEFAULT 'approved',
    budget_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_invoice_date ON legal_spend_invoices(invoice_date);
CREATE INDEX idx_vendor_name ON legal_spend_invoices(vendor_name);
CREATE INDEX idx_department ON legal_spend_invoices(department);
CREATE INDEX idx_status ON legal_spend_invoices(status);

-- For SQL Server, adjust syntax:
/*
CREATE TABLE legal_spend_invoices (
    invoice_id NVARCHAR(50) PRIMARY KEY,
    vendor_name NVARCHAR(255) NOT NULL,
    vendor_type NVARCHAR(50),
    matter_id NVARCHAR(50),
    matter_name NVARCHAR(255),
    department NVARCHAR(100) NOT NULL DEFAULT 'Legal',
    practice_area NVARCHAR(100),
    invoice_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency NVARCHAR(3) DEFAULT 'USD',
    expense_category NVARCHAR(100),
    description NVARCHAR(MAX),
    billing_period_start DATE,
    billing_period_end DATE,
    status NVARCHAR(50) DEFAULT 'approved',
    budget_code NVARCHAR(50),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
*/