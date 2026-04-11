# AWS Serverless Medallion Pipeline (V1 MVP)

> 🇧🇷 *Para a versão em português deste documento, [clique aqui](./README.pt-br.md).*

This repository contains a fully serverless, event-driven Data Engineering pipeline built on AWS. It implements the Medallion Architecture (Bronze, Silver, Gold) handling data ingestion, validation, idempotency, and ETL processing, culminating in actionable business metrics via SQL.

> **🚀 Evolution Note:** This is the V1.0.0 Architecture (SQS + Lambda + Glue). The V2 evolution incorporating Kinesis Data Firehose, AWS Step Functions, and Snowflake Snowpipe is currently under active development.

## 🏗️ Architecture Design (V1)

The infrastructure follows standard AWS Well-Architected Framework principles, emphasizing a Serverless and KISS (Keep It Simple, Stupid) approach.

1. **Ingestion (Bronze):** A Python generator pushes raw JSON events into an **AWS SQS** queue.
2. **Validation & Routing (Silver):** An **AWS Lambda** function consumes the queue, validates the schema using **Pydantic**, ensures idempotency via **Amazon DynamoDB** (preventing duplicate processing), and routes valid events to the Silver S3 bucket partitioned by event type.
3. **ETL & Aggregation (Gold):** An **AWS Glue** (PySpark) job reads the Silver layer, standardizes data types, aggregates metrics, and saves the output in optimized `Parquet` format partitioned by ingestion date.
4. **Analytics:** **Amazon Athena** queries the external Gold tables via the AWS Glue Data Catalog.

## 📸 Execution Proofs & Pipeline Validation

Below is the visual documentation proving the end-to-end execution of the pipeline.

<details>
<summary><b>1. Event Generation & SQS Ingestion</b></summary>
<br>
Execution of the local Python generator sending mock e-commerce payloads (Purchase, Page View, Add to Cart, Refund) to the AWS environment.
<br><br>
<img src="docs/event_generate.png" width="800">
</details>

<details>
<summary><b>2. Idempotency Control (DynamoDB)</b></summary>
<br>
The Lambda function registers every processed `event_id` with a TTL (Time to Live). The `SUCCEEDED` status proves duplicates are actively blocked.
<br><br>
<img src="docs/dynamo.png" width="800">
</details>

<details>
<summary><b>3. Silver Layer (S3 Data Routing)</b></summary>
<br>
Valid events are successfully parsed and routed to their specific domain folders in the Silver bucket.
<br><br>
<img src="docs/s3_silver.png" width="800">
</details>

<details>
<summary><b>4. ETL Processing (AWS Glue / PySpark)</b></summary>
<br>
The serverless Spark job transforming nested JSONs into aggregated metrics successfully executed.
<br><br>
<img src="docs/job_silver_to_gold.png" width="800">
</details>

<details>
<summary><b>5. Gold Layer (Optimized Parquet)</b></summary>
<br>
Data successfully lands in the Gold bucket, compressed as Snappy Parquet and properly partitioned by Event Time (`ingestion_date`).
<br><br>
<img src="docs/parquet_ingestion.png" width="800">
</details>

<details>
<summary><b>6. Business Analytics (Amazon Athena)</b></summary>
<br>
The final validation. Querying the Gold layer via Athena yields accurate business metrics (Daily Revenue, Active Sessions, Total Users) without a dedicated database server.
<br><br>
<img src="docs/result_athena.png" width="800">
</details>

---
### Tech Stack
* **Cloud:** AWS (SQS, Lambda, DynamoDB, S3, Glue, Athena)
* **IaC:** Terraform
* **Languages:** Python (Boto3, Pydantic, PySpark), SQL

---
## 👩‍💻 Author
**Ana Kellen Nogueira Porto** *Backend Developer*
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ana-kellen-nogueira-porto/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/akporto)