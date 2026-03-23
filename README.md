# VPC-API-Radu
AWS based API to create VPC


The solution is a serverless API on AWS using Terraform that allows users to create VPCs with multiple subnets. The API is protected with Cognito authentication, and all created resources are stored in DynamoDB so they can be retrieved later. The solution uses API Gateway, Lambda, DynamoDB, and Cognito  deployed using Terraform.

The API Gateway exposes REST endpoints and routes requests to a Lambda function. The Lambda function contains the logic for creating VPCs and subnets using the AWS EC2 API. The results are stored in DynamoDB, and Cognito is used to authenticate users via JWT tokens.

-AUTHETICATION-
I used Amazon Cognito to implement authentication. Users sign up and log in through Cognito, which returns a JWT token. This token is then sent in the Authorization header when calling the API.

API Gateway validates the JWT token using a Cognito-based authorizer. Authorization is open to all authenticated users, meaning any valid user can access the API.

Create user

aws cognito-idp sign-up \
  --client-id YOUR_USER_POOL_CLIENT_ID \
  --username your_email@example.com \
  --password 'Password123!' \
  --user-attributes Name=email,Value=your_email@example.com

  The below command will generate a token which can be used to authenticate in order to interact with the API 

  aws cognito-idp initiate-auth \
  --client-id YOUR_USER_POOL_CLIENT_ID \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=your_email@example.com,PASSWORD='Password123!'

  -API Functionality-

  POST /vpcs
  This endpoint creates a new VPC and multiple subnets based on the request payload.

  GET /vpcs
  Returns all created VPCs from DynamoDB.

  GET /vpcs/{id}
  Returns all created VPCs from DynamoDB.

  -Lambda function-
  The Lambda function is written in Python using Boto3.
  Boto3 is the official AWS SDK for Python used to create,configure and manage AWS services .
  
  What it does:
  
  1.parses the request
  2.validates input
  3.calls EC2 APIs:
    create_vpc
    create_subnet
  4.stores data in DynamoDB
  5.returns structured JSON responses


Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e20f0bfc-9fd0-4ac0-b778-cb5cb1e9d82e" />

  
