output "lambda_validator_role_arn" {
  description = "ARN of the IAM execution role assigned to the Lambda validator function."
  value       = aws_iam_role.lambda_validator.arn
}

output "glue_role_arn" {
  description = "ARN of the IAM service role assigned to all Glue ETL jobs."
  value       = aws_iam_role.glue.arn
}
