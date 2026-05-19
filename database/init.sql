CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    batch_id VARCHAR(36) NOT NULL,
    city VARCHAR(120) NOT NULL,
    niche VARCHAR(120) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    email VARCHAR(255),
    phone VARCHAR(80),
    address TEXT,
    source_url VARCHAR(500),
    quality_score FLOAT NOT NULL DEFAULT 0,
    issues_json TEXT NOT NULL DEFAULT '[]',
    generated_email_subject VARCHAR(255),
    generated_email_body TEXT,
    email_status VARCHAR(40) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_leads_user_id ON leads(user_id);
CREATE INDEX IF NOT EXISTS ix_leads_batch_id ON leads(batch_id);
CREATE INDEX IF NOT EXISTS ix_leads_city ON leads(city);
CREATE INDEX IF NOT EXISTS ix_leads_niche ON leads(niche);

CREATE TABLE IF NOT EXISTS outreach_logs (
    id VARCHAR(36) PRIMARY KEY,
    lead_id VARCHAR(36) NOT NULL REFERENCES leads(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    status VARCHAR(40) NOT NULL,
    message TEXT NOT NULL,
    provider_message_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_outreach_logs_lead_id ON outreach_logs(lead_id);
CREATE INDEX IF NOT EXISTS ix_outreach_logs_user_id ON outreach_logs(user_id);

CREATE TABLE IF NOT EXISTS opt_outs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_opt_outs_email ON opt_outs(email);

