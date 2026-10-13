CREATE TABLE events (
    id BIGINT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    age_days INT NOT NULL
);
