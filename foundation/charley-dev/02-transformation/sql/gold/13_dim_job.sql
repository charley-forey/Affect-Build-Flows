-- gold: dim_Job - the job pipeline, from "somebody asked for it" to "it went to bid".
--
-- THIS FILE IS THE LINK BETWEEN THE POWER AUTOMATE FLOWS AND THIS PLATFORM, and until it
-- existed there was none. power-automate/README.md listed "dim_Job source" as one of the
-- four jobs the Job Register does - "Fabric ingests the list as-is, the columns are already
-- the dimension" - while no bronze table, no silver parser and no gold DDL existed anywhere
-- in the repo. The flows created folders and issued job numbers, and not one row of that
-- reached Fabric.
--
-- THE CHAIN, end to end:
--     Job Register (SharePoint, /sites/BUILD)  written by power-automate/flows/*.json
--       ->  cd_bronze_man_job_register    CD_Manual_Ingest.Dataflow, the one query that
--                                         reads SITE_BUILD rather than SITE
--       ->  cd_silver_man_job_register    sql/silver/30_manual_silver.sql
--       ->  sv_man_job_register           sql/silver/01_source_views_cd.sql
--       ->  THIS FILE
--
-- NO ProjectKey, AND THAT IS NOT AN OVERSIGHT. A job is registered when somebody asks for
-- an estimate. Most of the columns here are filled in before anyone knows whether the work
-- will be won, and a job that is lost at bid never becomes a Procore project at all. Giving
-- this table a ProjectKey would mean either inventing one or dropping every unwon job, and
-- the second is how "how many jobs did we estimate this year" quietly becomes "how many did
-- we win". When the Procore link is wanted later it belongs on dim_Project as an attribute
-- pointing here, not the other way round.
--
-- Declared then filled, the same shape as 40_man_tables.sql: the CREATE is the contract and
-- runs whether or not a flow has ever executed, so a measure over an empty table returns
-- BLANK - a visible gap - rather than breaking a model with a missing table.

CREATE OR REPLACE TABLE dim_Job (
    RegisterId          INT,        -- SharePoint item id. The row's identity, not the job's.
    JobNumber           STRING,     -- 'YY-###'. The job's identity, and NOT unique by
                                    -- construction - see the DQ note below.
    JobYear             INT,
    JobSeq              INT,
    ProjectName         STRING,     -- As typed. The sanitised form only ever exists as a
                                    -- folder name; this is what the person actually wrote.
    Stage               STRING,     -- REQUESTED | ESTIMATING | BIDDING | FAILED
    EstimatingFolderUrl STRING,
    ProjectFolderUrl    STRING,     -- Empty until converted. The flows also use this as
                                    -- their loop guard.
    RequestedBy         STRING,
    RequestedAt         TIMESTAMP,
    CompletedAt         TIMESTAMP,
    CopyJobStatus       STRING,     -- Last CreateCopyJobs outcome, skips included.
    ErrorDetail         STRING,     -- Empty on a healthy run.
    LastModified        TIMESTAMP,
    LastModifiedBy      STRING
);

-- WHY JobNumber IS NOT DECLARED UNIQUE HERE, and is checked instead.
--
-- Two rows sharing a JobNumber is the failure this whole chain is worth building for. The
-- flows issue numbers by reading max(JobSeq), adding one, and writing it back, which is
-- safe only because both triggers are set to `concurrency: runs: 1`. That is a SETTING, not
-- code: anyone editing the flow in the Power Automate designer can turn it off without
-- touching a line, and then two jobs get called 26-025. Nothing errors, no copy job fails,
-- and nobody notices until someone opens the wrong folder weeks later with real documents
-- in both trees.
--
-- test_flows.py catches that setting disappearing in a diff. Nothing caught it in
-- production. dq/expectations.py now does, as a blocking expectation - so the collision
-- fails the nightly gate on the day it happens. That only works because silver deduplicates
-- on the SharePoint item id rather than on JobNumber; deduplicating on the number would
-- discard one of the two real jobs and hide the very thing being checked.

INSERT INTO dim_Job (RegisterId, JobNumber, JobYear, JobSeq, ProjectName, Stage,
                     EstimatingFolderUrl, ProjectFolderUrl, RequestedBy, RequestedAt,
                     CompletedAt, CopyJobStatus, ErrorDetail, LastModified, LastModifiedBy)
SELECT register_id, job_number, job_year, job_seq, project_name, stage,
       estimating_folder_url, project_folder_url, requested_by, requested_at,
       completed_at, copy_job_status, error_detail, last_modified, last_modified_by
FROM sv_man_job_register;
