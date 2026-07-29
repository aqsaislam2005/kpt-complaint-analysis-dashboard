-- ============================================================
-- KPT Complaint Management System — Database Schema
-- Run with: mysql -u root -p kpt_complaints < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS kpt_complaints;
USE kpt_complaints;

-- Raw complaint data (as imported / entered)
DROP TABLE IF EXISTS complaints;
CREATE TABLE complaints (
    complaint_id      INT PRIMARY KEY AUTO_INCREMENT,
    original_id       VARCHAR(50),
    complaint_text    TEXT,
    category          VARCHAR(100),
    department        VARCHAR(100),
    status             ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    customer_id        VARCHAR(50),
    date_received      DATETIME,
    date_resolved      DATETIME NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_date_received (date_received),
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_department (department)
);

-- Analysis results (sentiment + predicted category + resolution prediction)
-- kept in a separate table so raw data is never overwritten
DROP TABLE IF EXISTS complaint_analysis;
CREATE TABLE complaint_analysis (
    analysis_id            INT PRIMARY KEY AUTO_INCREMENT,
    complaint_id            INT NOT NULL,

    -- Sentiment results
    sentiment_label          ENUM('Positive', 'Negative', 'Neutral') ,
    sentiment_score           FLOAT,               -- -1 (very negative) to +1 (very positive)
    sentiment_model_used      VARCHAR(50),          -- 'vader' or 'transformer'

    -- Category prediction (used when original category was missing/unlabeled)
    predicted_category         VARCHAR(100),
    category_confidence        FLOAT,

    -- Time features (precomputed for fast dashboard queries)
    complaint_hour              TINYINT,
    complaint_day_of_week        VARCHAR(15),
    complaint_month               VARCHAR(15),
    complaint_year                 SMALLINT,

    -- Resolution behavior
    resolution_time_hours          FLOAT,
    predicted_resolution_hours      FLOAT,

    analyzed_at                       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    INDEX idx_sentiment (sentiment_label),
    INDEX idx_month (complaint_month)
);

-- Convenience view joining everything together — this is what the
-- dashboard mostly queries from.
DROP VIEW IF EXISTS complaints_full_view;
CREATE VIEW complaints_full_view AS
SELECT
    c.complaint_id,
    c.original_id,
    c.complaint_text,
    COALESCE(c.category, a.predicted_category) AS final_category,
    c.department,
    c.status,
    c.customer_id,
    c.date_received,
    c.date_resolved,
    a.sentiment_label,
    a.sentiment_score,
    a.complaint_hour,
    a.complaint_day_of_week,
    a.complaint_month,
    a.complaint_year,
    a.resolution_time_hours,
    a.predicted_resolution_hours
FROM complaints c
LEFT JOIN complaint_analysis a ON c.complaint_id = a.complaint_id;
