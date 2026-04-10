output "function_arn" {
  description = "ARN of the deployed Lambda validator function."
  value       = aws_lambda_function.validator.arn
}

output "function_name" {
  description = "Name of the deployed Lambda validator function."
  value       = aws_lambda_function.validator.function_name
}
