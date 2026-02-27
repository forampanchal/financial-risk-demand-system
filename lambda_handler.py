import json
from src.pipeline.daily_pipeline import main


def handler(event, context):
    """
    This is the entry point AWS Lambda calls every day.
    EventBridge fires the cron → Lambda calls this handler → 
    handler calls your pipeline.
    """
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
            "body": json.dumps(f"Piple failed: {str(e)}")

        }

# ## What's Happening Here

# **`handler(event, context)`** — this is the function AWS Lambda looks for. When EventBridge fires the cron at 6am, Lambda calls exactly this function. The name `handler` is just a convention.

# **`event`** — contains info about what triggered Lambda. In our case EventBridge sends a simple scheduled event. We don't actually need it but Lambda always passes it.

# **`context`** — contains runtime info like how much memory is being used, time remaining etc. We don't need it either but Lambda always passes it.

# **`main()`** — this is just calling your existing `daily_pipeline.py` main function. The handler is intentionally thin — all the real logic stays in your pipeline.

# **`try/except`** — if anything crashes inside the pipeline, Lambda catches it and returns a 500 status instead of silently failing. You'll be able to see this in CloudWatch logs.

# ---

# ## Project Structure Now Looks Like
# ```
# financial-risk-monitor/
#     api/
#         app.py
#     src/
#         pipeline/
#             daily_pipeline.py
#         utils/
#             config.py
#         ...
#     lambda_handler.py     ← new file here
#     Dockerfile
#     requirements.txt
