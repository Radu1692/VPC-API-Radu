import json
import os
import ipaddress
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client("ec2")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }


def validate_payload(body):
    required = ["name", "cidr_block", "subnets"]
    for field in required:
        if field not in body:
            raise ValueError(f"Missing field: {field}")

    vpc_network = ipaddress.ip_network(body["cidr_block"])

    subnet_networks = []
    for subnet in body["subnets"]:
        for field in ["name", "cidr_block", "availability_zone"]:
            if field not in subnet:
                raise ValueError(f"Missing subnet field: {field}")

        subnet_net = ipaddress.ip_network(subnet["cidr_block"])

        if not subnet_net.subnet_of(vpc_network):
            raise ValueError(f"Subnet {subnet['cidr_block']} is not inside VPC CIDR {body['cidr_block']}")

        for existing in subnet_networks:
            if subnet_net.overlaps(existing):
                raise ValueError(f"Subnet {subnet['cidr_block']} overlaps with {existing}")

        subnet_networks.append(subnet_net)


def get_claims(event):
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    jwt_data = authorizer.get("jwt", {})
    return jwt_data.get("claims", {})


def create_vpc_handler(event):
    try:
        body = json.loads(event.get("body") or "{}")
        validate_payload(body)

        name = body["name"]
        cidr_block = body["cidr_block"]
        subnets = body["subnets"]

        vpc_resp = ec2.create_vpc(CidrBlock=cidr_block)
        vpc_id = vpc_resp["Vpc"]["VpcId"]

        ec2.create_tags(
            Resources=[vpc_id],
            Tags=[
                {"Key": "Name", "Value": name},
                {"Key": "ManagedBy", "Value": "vpc-api"}
            ]
        )

        created_subnets = []
        for subnet in subnets:
            subnet_resp = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=subnet["cidr_block"],
                AvailabilityZone=subnet["availability_zone"]
            )
            subnet_id = subnet_resp["Subnet"]["SubnetId"]

            ec2.create_tags(
                Resources=[subnet_id],
                Tags=[
                    {"Key": "Name", "Value": subnet["name"]},
                    {"Key": "ManagedBy", "Value": "vpc-api"}
                ]
            )

            created_subnets.append({
                "subnet_id": subnet_id,
                "name": subnet["name"],
                "cidr_block": subnet["cidr_block"],
                "availability_zone": subnet["availability_zone"]
            })

        claims = get_claims(event)
        created_by = claims.get("email") or claims.get("sub") or "unknown"

        item = {
            "resource_id": vpc_id,
            "name": name,
            "cidr_block": cidr_block,
            "subnets": created_subnets,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by
        }

        table.put_item(Item=item)

        return response(201, item)

    except ValueError as e:
        return response(400, {"message": str(e)})
    except ClientError as e:
        return response(500, {"message": str(e)})


def get_vpc_handler(vpc_id):
    result = table.get_item(Key={"resource_id": vpc_id})
    item = result.get("Item")

    if not item:
        return response(404, {"message": "VPC not found"})

    return response(200, item)


def list_vpcs_handler():
    result = table.scan()
    return response(200, result.get("Items", []))


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path_params = event.get("pathParameters") or {}

    if method == "POST":
        return create_vpc_handler(event)

    if method == "GET" and "id" in path_params:
        return get_vpc_handler(path_params["id"])

    if method == "GET":
        return list_vpcs_handler()

    return response(405, {"message": "Method not allowed"})