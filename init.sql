-- PostgreSQL schema for minimal RAG (3FN)
CREATE TYPE doc_status AS ENUM ('PENDING','PROCESSING','READY','ERROR');
CREATE TYPE job_status AS ENUM ('PENDING','RUNNING','DONE','ERROR');

CREATE TABLE IF NOT EXISTS documents(
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  mime VARCHAR(100),
  upload_ts TIMESTAMP NOT NULL DEFAULT NOW(),
  path VARCHAR(500) NOT NULL,
  size BIGINT,
  status doc_status NOT NULL DEFAULT 'PENDING'
);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_ts ON documents(upload_ts);

CREATE TABLE IF NOT EXISTS doc_chunks(
  id SERIAL PRIMARY KEY,
  document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  token_count INT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc ON doc_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_idx ON doc_chunks(chunk_index);

CREATE TABLE IF NOT EXISTS embeddings(
  id SERIAL PRIMARY KEY,
  chunk_id INT NOT NULL REFERENCES doc_chunks(id) ON DELETE CASCADE,
  vector JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk ON embeddings(chunk_id);

CREATE TABLE IF NOT EXISTS queries(
  id SERIAL PRIMARY KEY,
  query_text TEXT NOT NULL,
  ts TIMESTAMP NOT NULL DEFAULT NOW(),
  result_refs JSONB
);
CREATE INDEX IF NOT EXISTS idx_queries_text ON queries USING GIN (to_tsvector('english', query_text));
CREATE INDEX IF NOT EXISTS idx_queries_ts ON queries(ts);

CREATE TABLE IF NOT EXISTS jobs(
  id SERIAL PRIMARY KEY,
  document_id INT REFERENCES documents(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  status job_status NOT NULL DEFAULT 'PENDING',
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_doc_status ON jobs(document_id, status);
