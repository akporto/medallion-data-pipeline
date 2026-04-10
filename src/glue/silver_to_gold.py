"""
Glue PySpark job: Silver - Gold transition.
Responsibility: aggregate validated Silver data into feature-store-ready datasets
and write to Gold S3 (consumed by Snowpipe).

Job parameters:
  --silver_path   s3://bucket/validated/
  --gold_path     s3://bucket/gold/
"""
import sys
from decimal import Decimal

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "silver_path", "gold_path"],
)

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

silver_df = (
    spark.read
    .option("recursiveFileLookup", "true")
    .json(args["silver_path"])
    .withColumn("ingestion_date", F.to_date(F.col("timestamp")))
)

gold_df = (
    silver_df.groupBy("user_id", "ingestion_date")
    .agg(
        F.count("event_id").alias("total_events"),
        F.sum(
            F.when(F.col("event_type") == "purchase", F.col("amount")).otherwise(None)
        ).alias("total_purchase_amount"),
        F.countDistinct("session_id").alias("distinct_sessions"),
        F.max("timestamp").alias("last_event_at"),
    )
    .withColumn(
        "total_purchase_amount",
        F.coalesce(F.col("total_purchase_amount"), F.lit(Decimal("0.00"))),
    )
)

(
    gold_df.write.mode("overwrite")
    .partitionBy("ingestion_date")
    .parquet(args["gold_path"])
)

job.commit()
