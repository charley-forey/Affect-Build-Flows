-- silver: Procore meetings and the project team - the Weekly Dashboard's two new sources.
--
-- Both added 2026-10-25 after the Oct 21 call, and both verified live first (a read-only
-- probe notebook: 200 on every active project). Field names are from the live payload.
--
-- MEETINGS. Scorecard.xlsx scores the OAC and trade partner meetings on "agenda sent at
-- least 24 hours in advance and minutes sent out within 24 hours after the meeting". The
-- list endpoint carries what is needed for most of that:
--
--   meeting_date            the date only - the start time is on the per-meeting detail
--   mode                    'agenda' until the meeting is switched to minutes
--   occurred                true once the meeting has been held
--   last_distributed_event  'agenda' or 'minutes' - the LAST thing sent out
--   distributed_at          when that last send happened, in the sender's local offset
--                           ('2026-06-11T09:02:39-04:00'), so its first ten characters are
--                           the local date the email went out
--
-- ONLY THE LAST SEND SURVIVES. Distributing the minutes overwrites the agenda's timestamp,
-- so for a minuted meeting this endpoint cannot say when its agenda went out. The
-- per-meeting change_history endpoint does ("Agenda Distributed", with a time); it costs one
-- request per meeting and is the next step, not this one. Gold marks that agenda check as
-- unverified rather than guessing - see 46_dashboard_facts.sql.
--
-- The response is one record per meeting SERIES; procore_scope.normalize_records flattens it
-- to one row per meeting before bronze, keeping the series in _source_group.group_title.
-- The series title is how gold tells an OAC meeting from a trade partner meeting
-- (seed_MeetingCategory).

CREATE OR REPLACE TABLE cd_silver_meetings AS
SELECT
    CAST(_project_id                                         AS STRING)  AS project_id,
    CAST(get_json_object(payload, '$.id')                    AS STRING)  AS meeting_id,
    TRIM(get_json_object(payload, '$._source_group.group_title'))        AS series_title,
    TRIM(get_json_object(payload, '$.title'))                            AS title,
    CAST(get_json_object(payload, '$.meeting_date')          AS DATE)    AS meeting_date,
    LOWER(TRIM(get_json_object(payload, '$.mode')))                      AS meeting_mode,
    CAST(get_json_object(payload, '$.occurred')              AS BOOLEAN) AS occurred,
    LOWER(TRIM(get_json_object(payload, '$.last_distributed_event')))    AS last_distributed_event,
    -- The local date, read off the offset string. Casting to TIMESTAMP first would convert
    -- to UTC and move an 8pm send onto the next day.
    CAST(SUBSTR(get_json_object(payload, '$.distributed_at'), 1, 10) AS DATE) AS distributed_date,
    get_json_object(payload, '$.distributed_at')                         AS distributed_at_local,
    -- created_at is UTC ('Z'); kept as a timestamp and compared in gold.
    CAST(get_json_object(payload, '$.created_at')            AS TIMESTAMP) AS created_at,
    CAST(get_json_object(payload, '$.position')              AS INT)     AS position,
    CAST(get_json_object(payload, '$.meeting_topics_count')  AS INT)     AS topic_count,
    _ingested_at, _batch_id
FROM cd_bronze_procore_meetings
WHERE get_json_object(payload, '$.id') IS NOT NULL;

DELETE FROM cd_dq_rejects WHERE target_table IN ('cd_silver_meetings', 'cd_silver_project_roles');
INSERT INTO cd_dq_rejects
SELECT 'cd_silver_meetings', 'missing id', payload, _batch_id
FROM cd_bronze_procore_meetings
WHERE get_json_object(payload, '$.id') IS NULL;

-- PROJECT ROLES. One row per person per role on the project's Procore directory. The
-- Portfolio page's TEAM column is "Initials of: PM, APM, Super, Asst Super from Procore";
-- gold picks those four (and the Project Executive, the one accountable name the call asked
-- for) by role name. Many projects have only some of the four filled in - checked live
-- 2026-10-25 - and the report shows exactly what Procore holds rather than filling gaps.
CREATE OR REPLACE TABLE cd_silver_project_roles AS
SELECT
    CAST(_project_id                                  AS STRING)  AS project_id,
    CAST(get_json_object(payload, '$.id')             AS STRING)  AS role_assignment_id,
    TRIM(get_json_object(payload, '$.role'))                      AS role_name,
    TRIM(get_json_object(payload, '$.name'))                      AS member_name,
    CAST(get_json_object(payload, '$.is_active')      AS BOOLEAN) AS is_active,
    CAST(get_json_object(payload, '$.user_id')        AS STRING)  AS user_id,
    _ingested_at, _batch_id
FROM cd_bronze_procore_project_roles
WHERE get_json_object(payload, '$.id') IS NOT NULL;

INSERT INTO cd_dq_rejects
SELECT 'cd_silver_project_roles', 'missing id', payload, _batch_id
FROM cd_bronze_procore_project_roles
WHERE get_json_object(payload, '$.id') IS NULL;
