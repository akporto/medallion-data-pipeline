"""
Glue PySpark job: Bronze -> Silver transition.
Responsibility: read raw JSON from Bronze S3, apply structural transformations,
enforce schema, and write Parquet to Silver S3.

Job parameters (passed via --job-bookmark-option and Glue job args):
  --bronze_path   s3://bucket/raw/
  --silver_path   s3://bucket/validated/
  --database_name glue_catalog_database
"""
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "bronze_path", "silver_path", "database_name"],
)

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

raw_df = spark.read.option("recursiveFileLookup", "true").json(args["bronze_path"])

silver_df = (
    raw_df.withColumn("ingestion_date", F.to_date(F.col("timestamp")))
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    .where(F.col("event_id").isNotNull())
)

(
    silver_df.write.mode("overwrite")
    .partitionBy("ingestion_date", "event_type")
    .parquet(args["silver_path"])
)

job.commit()
