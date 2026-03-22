output "api_url" {
  value = aws_apigatewayv2_stage.prod.invoke_url
}

output "user_pool_id" {
  value = aws_cognito_user_pool.this.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.this.id
}

output "lambda_name" {
  value = aws_lambda_function.api.function_name
}