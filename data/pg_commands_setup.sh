CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION pg_trgm;
ALTER TABLE translations ALTER COLUMN word TYPE CITEXT;
CREATE UNIQUE INDEX translations_word_unique ON translations (word);
CREATE INDEX translations_word_idx ON translations (word);