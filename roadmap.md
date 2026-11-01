# Development Roadmap — AWS Serverless Medallion Pipeline

This roadmap describes planned work for evolving the current V1 pipeline into a more resilient, observable, and analytics-ready data platform.

> **Planning note:** The estimates below represent future engineering effort, not completed work. They are estimates for implementation, infrastructure changes, validation, and project-level documentation. Actual effort may change after design decisions or technical discoveries.

## Current baseline

The current V1 uses an event-driven, serverless AWS architecture:

- **Ingestion:** Python event generator and Amazon SQS.
- **Validation and routing:** AWS Lambda, Pydantic, and DynamoDB-based idempotency.
- **Storage:** Amazon S3 with Bronze, Silver, and Gold layers.
- **Processing:** AWS Glue with PySpark, producing partitioned Parquet files.
- **Analytics:** AWS Glue Data Catalog and Amazon Athena.
- **Infrastructure and quality:** Terraform, automated CI, unit tests, and integration tests.

## Planned evolution (V2)

| # | Workstream | Estimated effort | Status |
|---|---|---:|---|
| 1 | Add an Amazon Kinesis Data Firehose ingestion path | 10h | Not started |
| 2 | Orchestrate ETL processing with AWS Step Functions | 10h | Not started |
| 3 | Integrate Snowflake Snowpipe with the S3 data lake | 12h | Not started |
| 4 | Implement controlled reprocessing and failure recovery | 10h | Not started |
| 5 | Strengthen data validation and data quality checks | 8h | Not started |
| 6 | Improve observability with Amazon CloudWatch | 8h | Not started |
| 7 | Improve idempotency and duplicate-event handling | 6h | Not started |
| 8 | Optimize Parquet layout and S3 partitioning | 6h | Not started |
| 9 | Expand automated tests and technical documentation | 10h | Not started |
| | **Total estimated effort** | **80h** | |

## Workstream details

### 1. Add an Amazon Kinesis Data Firehose ingestion path — 10h

**Planned work**
- Define how Firehose will coexist with the current SQS-based ingestion path, or whether it will replace a specific part of it.
- Provision the required Firehose resources and IAM permissions with Terraform.
- Configure delivery to the appropriate S3 landing location, including buffering, compression, and failure handling where applicable.
- Validate delivery behavior using synthetic event data.

**Expected outcome**
- A documented and reproducible Firehose ingestion path that lands data in S3.
- An explicit architecture decision describing the relationship between Firehose and the existing SQS flow.

### 2. Orchestrate ETL processing with AWS Step Functions — 10h

**Planned work**
- Design a state machine for the required Glue processing stages.
- Provision the state machine and execution permissions using Terraform.
- Configure task sequencing, retries, timeouts, and failure branches.
- Test successful executions and representative failure scenarios.

**Expected outcome**
- A repeatable orchestration workflow for the ETL stages, with visible execution status and defined failure behavior.

### 3. Integrate Snowflake Snowpipe with the S3 data lake — 12h

**Planned work**
- Define the target Snowflake database, schema, stage, file format, and ingestion table.
- Configure the required S3 access integration and least-privilege permissions.
- Create and validate the Snowpipe ingestion configuration and its notification mechanism.
- Test automatic ingestion with synthetic files and document operational prerequisites.

**Expected outcome**
- A documented and validated path for automatically loading eligible S3 data into Snowflake.

**Dependency**
- Access to an appropriately configured Snowflake account and the required AWS permissions. External provisioning or approval wait time is not included in this estimate.

### 4. Implement controlled reprocessing and failure recovery — 10h

**Planned work**
- Define reprocessing inputs, such as date ranges or selected partitions.
- Implement a controlled mechanism to rerun eligible processing stages.
- Define retry, failure, and recovery behavior for interrupted executions.
- Validate that reprocessing does not create unintended duplicate outputs.

**Expected outcome**
- A documented reprocessing procedure with predictable behavior and validation for repeated runs.

### 5. Strengthen data validation and data quality checks — 8h

**Planned work**
- Extend schema and field-level validation for incoming events.
- Add checks for required fields, data types, and invalid values.
- Define how invalid records are reported or isolated for later inspection.
- Add automated tests for valid, invalid, and boundary-case records.

**Expected outcome**
- Explicit data quality rules and test coverage for representative valid and invalid input records.

### 6. Improve observability with Amazon CloudWatch — 8h

**Planned work**
- Review and standardize logs for the Lambda and Glue processing paths.
- Add relevant metrics for processing volume, failures, and execution outcomes.
- Configure CloudWatch alarms for selected operational failure conditions.
- Document where to inspect logs, metrics, and alarms when troubleshooting.

**Expected outcome**
- A documented monitoring approach with useful logs, metrics, and alarms for key pipeline components.

### 7. Improve idempotency and duplicate-event handling — 6h

**Planned work**
- Review the current DynamoDB idempotency strategy and its behavior during retries.
- Define handling for duplicate, delayed, and repeatedly delivered events.
- Improve state transitions or expiration behavior where required.
- Add tests for duplicate delivery and retry scenarios.

**Expected outcome**
- Better-defined and tested duplicate-event behavior across normal processing and retries.

### 8. Optimize Parquet layout and S3 partitioning — 6h

**Planned work**
- Review current file sizes, compression, and partition strategy.
- Evaluate small-file and partition-skew risks using representative synthetic data.
- Apply justified changes to Parquet output and partitioning.
- Validate that Athena queries continue to return correct results after the changes.

**Expected outcome**
- Documented storage-layout decisions and validated Parquet output suitable for the intended query patterns.

### 9. Expand automated tests and technical documentation — 10h

**Planned work**
- Extend unit tests for new processing, validation, and recovery behavior.
- Add or update integration tests for supported AWS workflows, using mocks or isolated test resources as appropriate.
- Update CI workflows to validate the new components without exposing credentials.
- Update architecture diagrams, setup instructions, operational notes, and troubleshooting guidance.

**Expected outcome**
- A repeatable test and CI process for the V2 changes, accompanied by current technical documentation.

## Delivery principles

- Keep infrastructure changes reproducible and managed through Terraform where practical.
- Use synthetic data in examples and automated tests; do not commit real customer or personal data.
- Do not commit AWS credentials, Snowflake credentials, tokens, private keys, or other secrets.
- Prefer least-privilege IAM permissions and isolated development resources.
- Validate changes incrementally and keep the existing V1 behavior documented.
- Update this roadmap as scope, estimates, and implementation status change.

## Estimate assumptions

- The **80 hours** represent estimated engineering effort across the nine workstreams.
- Estimates include implementation, project-level infrastructure work, validation, and the documentation stated in each workstream.
- Time waiting for external account access, approvals, long-running cloud operations, or third-party support is excluded.
- Workstream order may change based on architecture decisions and external dependencies.
- All items are planned future work and should remain marked **Not started** until implementation begins.
