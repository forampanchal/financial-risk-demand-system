import json
from src.pipeline.daily_pipeline import main


def handler(event, context):
    try:
        main()
        return {
            "statusCode": 200,
            "body": json.dumps("Pipeline ran successfully.")
        }

    except Exception as e:
        print(f"Pipeline failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Pipeline failed: {str(e)}")
        }
