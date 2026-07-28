import json
import boto3
import os
import logging
from decimal import Decimal


logger = logging.getLogger()
logger.setLevel(logging.INFO)


region = boto3.Session().region_name or "ap-south-1"

dynamodb = boto3.resource(
    "dynamodb",
    region_name=region
)


CANDIDATES_TABLE = os.environ.get("CANDIDATES_TABLE")
ANALYSES_TABLE = os.environ.get("ANALYSES_TABLE")



def lambda_handler(event, context):

    try:

        logger.info(
            "Analysis event: %s",
            json.dumps(event)
        )


        # CORS
        if event.get("httpMethod") == "OPTIONS":
            return create_cors_response(
                200,
                {}
            )


        params = event.get(
            "queryStringParameters"
        ) or {}


        candidate_id = params.get(
            "candidateId"
        )


        if candidate_id:

            result = get_candidate_analysis(
                candidate_id
            )


            if result:

                return create_cors_response(
                    200,
                    result
                )


            return create_cors_response(
                404,
                {
                    "error":
                    "Analysis not found"
                }
            )


        results = get_all_analyses()


        return create_cors_response(
            200,
            {
                "analyses": results
            }
        )


    except Exception as e:

        logger.exception(
            "Analysis Lambda Error"
        )

        return create_cors_response(
            500,
            {
                "error": str(e)
            }
        )



def get_candidate_analysis(candidate_id):

    try:


        # -------------------------------
        # Get Analysis
        # -------------------------------

        analyses_table = dynamodb.Table(
            ANALYSES_TABLE
        )


        response = analyses_table.query(
            IndexName="candidateId-index",

            KeyConditionExpression=
            "candidateId = :candidate_id",

            ExpressionAttributeValues={
                ":candidate_id":
                candidate_id
            }
        )


        items = response.get(
            "Items",
            []
        )


        if not items:

            logger.warning(
                f"No analysis found for {candidate_id}"
            )

            return None



        analysis = items[0]



        # -------------------------------
        # Get Candidate
        # -------------------------------

        candidates_table = dynamodb.Table(
            CANDIDATES_TABLE
        )


        candidate_data = {}



        # First try your existing schema

        try:

            candidate_response = candidates_table.get_item(
                Key={
                    "candidateId":
                    candidate_id
                }
            )


            candidate_data = candidate_response.get(
                "Item",
                {}
            )


        except Exception:

            pass



        # Compatibility for old candidate_id records

        if not candidate_data:


            scan = candidates_table.scan(
                FilterExpression=
                "candidate_id = :cid",

                ExpressionAttributeValues={
                    ":cid":
                    candidate_id
                }
            )


            old_items = scan.get(
                "Items",
                []
            )


            if old_items:

                candidate_data = old_items[0]




        return {


            "analysisId":
            analysis.get(
                "analysisId"
            ),


            "candidateId":
            candidate_id,


            "candidateName":
            candidate_data.get(
                "name",
                "Unknown"
            ),


            "candidateEmail":
            candidate_data.get(
                "email",
                "Unknown"
            ),


            "fileName":
            candidate_data.get(
                "fileName",
                candidate_data.get(
                    "resume_key",
                    "Unknown"
                )
            ),



            "status":
            analysis.get(
                "status",
                "completed"
            ),



            "textExtractionStatus":
            analysis.get(
                "textExtractionStatus",
                "completed"
            ),



            "extractedText":
            analysis.get(
                "extractedText",
                candidate_data.get(
                    "extracted_text",
                    ""
                )
            ),



            "skills":
            analysis.get(
                "skills",
                candidate_data.get(
                    "skills",
                    []
                )
            ),



            "jobTitles":
            analysis.get(
                "jobTitles",
                []
            ),



            "experience":
            analysis.get(
                "experience",
                candidate_data.get(
                    "experience",
                    []
                )
            ),



            "education":
            analysis.get(
                "education",
                []
            ),



            "overallScore":
            analysis.get(
                "overallScore",
                0
            ),



            "organizations":
            analysis.get(
                "organizations",
                []
            ),



            "keyPhrases":
            analysis.get(
                "keyPhrases",
                []
            ),



            "createdAt":
            analysis.get(
                "createdAt"
            ),



            "updatedAt":
            analysis.get(
                "updatedAt"
            )

        }



    except Exception as e:

        logger.exception(
            "get_candidate_analysis error"
        )

        return None





def get_all_analyses():

    try:


        table = dynamodb.Table(
            ANALYSES_TABLE
        )


        response = table.scan()


        return convert_decimals(
            response.get(
                "Items",
                []
            )
        )


    except Exception as e:


        logger.exception(
            "get_all_analyses error"
        )

        return []





def convert_decimals(obj):

    if isinstance(obj, Decimal):

        return float(obj)


    if isinstance(obj, dict):

        return {
            k:
            convert_decimals(v)
            for k,v in obj.items()
        }


    if isinstance(obj,list):

        return [
            convert_decimals(x)
            for x in obj
        ]


    return obj





def create_cors_response(
        status_code,
        body
):


    return {


        "statusCode":
        status_code,


        "headers":{


            "Access-Control-Allow-Origin":
            "*",


            "Access-Control-Allow-Headers":
            "*",


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
