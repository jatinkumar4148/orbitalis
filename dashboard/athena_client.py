"""
Reusable helper to run Athena queries from Python and get results as
a pandas DataFrame. Streamlit pages will call query() with SQL and get
back rows — this hides all the boto3 polling/waiting logic.
"""

import time
import boto3
import pandas as pd

ATHENA_DATABASE = "orbitalis_glue_db"
ATHENA_OUTPUT_LOCATION = "s3://orbitalis-data-jatin2026/athena_query_results/"
AWS_REGION = "ap-south-1"


def run_query(sql: str, max_wait_seconds: int = 30) -> pd.DataFrame:
    """
    Runs a SQL query on Athena and returns results as a DataFrame.
    Polls Athena until the query finishes (Athena queries are async).
    """
    client = boto3.client("athena", region_name=AWS_REGION)

    response = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_LOCATION},
    )
    query_execution_id = response["QueryExecutionId"]

    # Poll until query completes (Athena is async — no query is instant)
    waited = 0
    while waited < max_wait_seconds:
        status = client.get_query_execution(QueryExecutionId=query_execution_id)
        state = status["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            break
        elif state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "Unknown error")
            raise RuntimeError(f"Athena query {state}: {reason}")

        time.sleep(1)
        waited += 1
    else:
        raise TimeoutError(f"Athena query did not finish within {max_wait_seconds}s")

    # Fetch results and convert to DataFrame
    result = client.get_query_results(QueryExecutionId=query_execution_id)
    columns = [col["Label"] for col in result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]

    rows = []
    for row in result["ResultSet"]["Rows"][1:]:  # skip header row
        rows.append([field.get("VarCharValue", None) for field in row["Data"]])

    return pd.DataFrame(rows, columns=columns)