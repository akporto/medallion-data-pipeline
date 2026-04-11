# Pipeline Medallion Serverless na AWS (V1 MVP)

🌎 *For the English version of this document, [click here](./README.md).*

Este repositório contém um pipeline de Engenharia de Dados totalmente serverless e orientado a eventos construído na AWS. Ele implementa a Arquitetura Medallion (Bronze, Silver, Gold) lidando com ingestão de dados, validação, idempotência e processamento ETL, culminando em métricas de negócio acionáveis via banco de dados analítico.

> **🚀 Nota de Evolução:** Esta é a documentação da Arquitetura V1.0.0 (SQS + Lambda + Glue). A evolução para a V2, incorporando *Kinesis Data Firehose*, *AWS Step Functions* e integração com *Snowflake* (Snowpipe), está atualmente em desenvolvimento ativo.

## 🏗️ Design da Arquitetura (V1)

A infraestrutura segue os princípios de melhores práticas do *AWS Well-Architected Framework*, enfatizando uma abordagem 100% Serverless e o princípio KISS (*Keep It Simple, Stupid*).

1. **Ingestão (Bronze):** Um script gerador em Python envia eventos JSON brutos, simulando um e-commerce, para uma fila **AWS SQS**.
2. **Validação e Roteamento (Silver):** Uma função **AWS Lambda** consome a fila, valida a estrutura dos dados usando a biblioteca **Pydantic**, garante a idempotência através do **Amazon DynamoDB** (bloqueando o reprocessamento de eventos duplicados) e roteia os eventos válidos para o bucket S3 da camada Silver, particionados por tipo de evento.
3. **ETL e Agregação (Gold):** Um job **AWS Glue** (PySpark) lê os dados da camada Silver, padroniza os tipos, agrega as métricas financeiras e salva o resultado no formato otimizado `Parquet` no bucket Gold, utilizando particionamento por data de ingestão (*Event Time*).
4. **Analytics:** O **Amazon Athena** é utilizado para consultar as tabelas externas da camada Gold através do *AWS Glue Data Catalog*, disponibilizando os dados para consumo de BI.

## 📸 Provas de Execução e Validação do Pipeline

Abaixo está a documentação visual comprovando a execução de ponta a ponta e a resiliência do pipeline na nuvem.

<details>
<summary><b>1. Geração de Eventos e Ingestão (SQS)</b></summary>
<br>
Execução do script Python local enviando payloads simulados (Compras, Visualizações de Página, Carrinho, Reembolsos) para a fila SQS na AWS.
<br><br>
<img src="docs/event_generate.png" width="800">
</details>

<details>
<summary><b>2. Controle de Idempotência (DynamoDB)</b></summary>
<br>
A função Lambda registra cada `event_id` processado com uma regra de expiração (TTL). O status `SUCCEEDED` comprova que eventos duplicados são ativamente bloqueados.
<br><br>
<img src="docs/dynamo.png" width="800">
</details>

<details>
<summary><b>3. Camada Silver (Roteamento de Dados no S3)</b></summary>
<br>
Eventos validados pelo Pydantic são roteados com sucesso para suas respectivas pastas de domínio (ex: `add_to_cart`, `purchase`) no bucket Silver.
<br><br>
<img src="docs/s3_silver.png" width="800">
</details>

<details>
<summary><b>4. Processamento ETL (AWS Glue / PySpark)</b></summary>
<br>
O job Serverless do Apache Spark transformando os JSONs aninhados em métricas agregadas de negócio, executado com sucesso e sem falhas de memória.
<br><br>
<img src="docs/job_silver_to_gold.png" width="800">
</details>

<details>
<summary><b>5. Camada Gold (Parquet Otimizado)</b></summary>
<br>
Os dados chegam fisicamente ao bucket Gold, compactados com o algoritmo Snappy (Parquet) e perfeitamente particionados pelo Horário Original do Evento (`ingestion_date`).
<br><br>
<img src="docs/parquet_ingestion.png" width="800">
</details>

<details>
<summary><b>6. Business Analytics (Amazon Athena)</b></summary>
<br>
A validação final. Consultar a camada Gold via Athena produz métricas de negócios precisas (Receita Diária, Sessões Ativas, Total de Usuários) com latência de milissegundos e sem a necessidade de um servidor de banco de dados dedicado.
<br><br>
<img src="docs/result_athena.png" width="800">
</details>

---
### Stack Tecnológica
* **Cloud:** AWS (SQS, Lambda, DynamoDB, S3, Glue, Athena)
* **Infraestrutura como Código:** Terraform
* **Linguagens:** Python (Boto3, Pydantic, PySpark), SQL

---
## 👩‍💻 Autora
**Ana Kellen Nogueira Porto** *Desenvolvedora Backend*
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ana-kellen-nogueira-porto/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/akporto)
