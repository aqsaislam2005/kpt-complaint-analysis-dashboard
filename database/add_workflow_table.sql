-- ============================================================
-- Complaint Workflow Table
-- ============================================================

USE kpt_complaints;

DROP TABLE IF EXISTS complaint_workflow;
CREATE TABLE complaint_workflow (
    workflow_id         INT PRIMARY KEY AUTO_INCREMENT,
    complaint_id          INT NOT NULL,
    stage_order            TINYINT,
    department               VARCHAR(100),
    action                    VARCHAR(50),
    routed_correctly          BOOLEAN NULL,
    comment                    TEXT,
    stage_timestamp             DATETIME,
    resolution_status            VARCHAR(20),

    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    INDEX idx_complaint_id (complaint_id),
    INDEX idx_department (department),
    INDEX idx_routed_correctly (routed_correctly)
);

DROP VIEW IF EXISTS complaint_workflow_summary;
CREATE VIEW complaint_workflow_summary AS
SELECT
    complaint_id,
    MAX(CASE WHEN stage_order = 2 THEN routed_correctly END) AS routed_correctly_first_try,
    MAX(CASE WHEN stage_order = 2 AND routed_correctly = FALSE THEN department END) AS misrouted_to_department,
    MAX(department) AS final_department,
    MAX(resolution_status) AS final_resolution_status,
    COUNT(*) AS total_stages,
    MIN(stage_timestamp) AS process_started_at,
    MAX(stage_timestamp) AS process_ended_at,
    TIMESTAMPDIFF(HOUR, MIN(stage_timestamp), MAX(stage_timestamp)) AS total_process_hours
FROM complaint_workflow
GROUP BY complaint_id;