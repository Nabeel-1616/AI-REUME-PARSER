import json
import boto3
import os
import logging
from decimal import Decimal
from botocore.exceptions import ClientError


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# AWS region
region = boto3.Session().region_name or "ap-south-1"

# DynamoDB resource
dynamodb = boto3.resource(
    "dynamodb",
    region_name=region
)


# Environment variables
CANDIDATES_TABLE = os.environ.get("CANDIDATES_TABLE")
ANALYSES_TABLE = os.environ.get("ANALYSES_TABLE")


def lambda_handler(event, context):
    """
    Retrieve all candidates with analysis status
    """

    try:

        logger.info(
            "Received event: %s",
            json.dumps(event)
        )


        # Handle CORS preflight
        if event.get("httpMethod") == "OPTIONS":
            return create_cors_response(
                200,
                {}
            )


        # Validate environment variables
        if not CANDIDATES_TABLE or not ANALYSES_TABLE:
            raise Exception(
                "Missing DynamoDB environment variables"
            )


        candidates = get_all_candidates_with_status()


        return create_cors_response(
            200,
            {
                "candidates": candidates
            }
        )


    except Exception as e:

        logger.exception(
            "Candidates Lambda failed"
        )

        return create_cors_response(
            500,
            {
                "error": str(e)
            }
        )



def get_all_candidates_with_status():

    try:

        candidates_table = dynamodb.Table(
            CANDIDATES_TABLE
        )

        analyses_table = dynamodb.Table(
            ANALYSES_TABLE
        )


        # Scan candidates table
        response = candidates_table.scan()

        candidates = response.get(
            "Items",
            []
        )


        # Handle pagination
        while "LastEvaluatedKey" in response:

            response = candidates_table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )

            candidates.extend(
                response.get(
                    "Items",
                    []
                )
            )


        formatted_candidates = []


        for candidate in candidates:

            candidate_id = candidate.get(
                "candidateId"
            )


            analysis_data = None


            # Check analysis table
            try:

                analysis_response = analyses_table.query(
                    IndexName="candidateId-index",
                    KeyConditionExpression=
                    "candidateId = :candidate_id",

                    ExpressionAttributeValues={
                        ":candidate_id": candidate_id
                    }
                )


                items = analysis_response.get(
                    "Items",
                    []
                )


                if items:
                    analysis_data = items[0]


            except Exception as query_error:

                logger.warning(
                    "Analysis lookup failed for %s : %s",
                    candidate_id,
                    str(query_error)
                )


            formatted_candidate = {

                "candidateId":
                    candidate_id,

                "name":
                    candidate.get(
                        "name",
                        "Unknown"
                    ),

                "email":
                    candidate.get(
                        "email",
                        "Unknown"
                    ),

                "fileName":
                    candidate.get(
                        "fileName",
                        "Unknown"
                    ),

                "fileType":
                    candidate.get(
                        "fileType",
                        "Unknown"
                    ),

                "uploadedAt":
                    candidate.get(
                        "uploadedAt"
                    ),

                "status":
                    candidate.get(
                        "status",
                        "uploaded"
                    ),

                "textExtractionStatus":
                    candidate.get(
                        "textExtractionStatus",
                        "pending"
                    ),

                "textractJobId":
                    candidate.get(
                        "textractJobId"
                    ),

                "s3Key":
                    candidate.get(
                        "s3Key"
                    ),


                "hasAnalysis":
                    analysis_data is not None,


                "analysisStatus":
                    analysis_data.get(
                        "status",
                        "processing"
                    )
                    if analysis_data
                    else "pending",


                "overallScore":
                    analysis_data.get(
                        "overallScore",
                        0
                    )
                    if analysis_data
                    else 0,


                "skillsCount":
                    len(
                        analysis_data.get(
                            "skills",
                            []
                        )
                    )
                    if analysis_data
                    else 0,


                "updatedAt":
                    candidate.get(
                        "updatedAt",
                        candidate.get(
                            "uploadedAt"
                        )
                    )
            }


            formatted_candidates.append(
                formatted_candidate
            )


        # Sort newest first
        formatted_candidates.sort(
            key=lambda x:
                x.get(
                    "uploadedAt",
                    ""
                ),
            reverse=True
        )


        logger.info(
            "Retrieved %s candidates",
            len(formatted_candidates)
        )


        return formatted_candidates



    except ClientError as e:

        logger.exception(
            "DynamoDB error"
        )

        raise e



    except Exception as e:

        logger.exception(
            "Error getting candidates"
        )

        raise e




def convert_decimals(obj):

    if isinstance(obj, Decimal):

        return float(obj)


    elif isinstance(obj, dict):

        return {
            key: convert_decimals(value)
            for key, value in obj.items()
        }


    elif isinstance(obj, list):

        return [
            convert_decimals(item)
            for item in obj
        ]


    return obj




def create_cors_response(
        status_code,
        body
):

    return {

        "statusCode":
            status_code,


        "headers": {

            "Access-Control-Allow-Origin":
                "*",

            "Access-Control-Allow-Headers":
                "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",

            "Access-Control-Allow-Methods":
                "GET,POST,PUT,DELETE,OPTIONS",

            "Content-Type":
                "application/json"
        },


        "body":
            json.dumps(
                convert_decimals(body)
            )
    }
