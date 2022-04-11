import logging

from airflow import DAG
from airflow.decorators import task, dag
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from airflow.providers.databricks.operators.databricks import (
    DatabricksSubmitRunOperator,
    DatabricksRunNowOperator,
)
# from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
# from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.email_operator import EmailOperator


from datetime import datetime, timedelta

DATABRICKS_CLUSTER_ID = "0222-192411-cnzydi8s"
DATABRICKS_CONNECTION_ID = "databricks_default"
notebook_task = {
    "notebook_path": "/Shared/dag-workshop",
}


# specifying which companies I'd like data from (by using their stock tickers)
# portfolio2 = ['MSFT', 'AAPL', 'IBM', 'WMT', 'SHOP', 'LWLG', 'ALB', 'LYV', 'GOOGL', 'TTGT', 'TSLA', 'GME', 'AMZN', 'TGT', 'COST', 'COKE','TPL', 'BX', 'MORN', 'CBRE', 
#             'NVDA', 'AMD', 'NEE']
# portfolio = ['SHOP', 'MSFT'] # reduced portfolio to make script quicker (pre prod, less api calls)

portfolio = {
            "stocks": "MSFT AAPL IBM WMT SHOP GOOGL TSLA GME AMZN COST COKE CBRE NVDA AMD PG"
            }



with DAG(
    "databricks_dag",
    start_date=datetime(2021, 1, 1),
    schedule_interval='2 1 * * *',
    catchup=False,
    default_args={
        "email_on_failure": False,
        "email_on_retry": False,
    },
) as dag:

    # opr_submit_run = DatabricksSubmitRunOperator(
    #     task_id="start_cluster",
    #     databricks_conn_id=DATABRICKS_CONNECTION_ID,
    #     existing_cluster_id=DATABRICKS_CLUSTER_ID,
    #     notebook_task = notebook_task

    # )

    opr_run_now = DatabricksRunNowOperator(
        task_id="run_job",
        databricks_conn_id=DATABRICKS_CONNECTION_ID,
        job_id=137122987688189,
        do_xcom_push=True,
        notebook_params = portfolio
# 137122987688189
# test 1087568806385694
        
    )

    # get value from databricks from xcom
    @task
    def retrieve_xcom(databricks_run_id: str):
        databricks_hook = DatabricksHook()
        model_uri = databricks_hook.get_run_output(databricks_run_id)['notebook_output']['result']
        return model_uri

    # send email
    mail = EmailOperator(
        task_id='mail',
        to='amir.zahreddine@astronomer.io',
        subject='Daily Movers',
        html_content="{{ task_instance.xcom_pull(task_ids='retrieve_xcom') }}",
        )

#    opr_submit_run >> 
opr_run_now >> retrieve_xcom(opr_run_now.output['run_id']) >> mail
