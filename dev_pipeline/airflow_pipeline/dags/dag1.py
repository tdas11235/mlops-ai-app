from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator
import requests
import time
from airflow.exceptions import AirflowFailException
import pandas as pd
import includes.train as tr
from includes.initdb import CREATE_FEEDBACK_TABLE
import os
from datetime import datetime

CSV_PATH = '/opt/airflow/shared_data/feedback.csv'
POSTGRES_CONN_ID = 'mlops_pg_conn'
EXPORT_DIR = '/tmp/airflow_exports'

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1)
}


def wait_for_mlflow_server(timeout=300, interval=10):
    mlflow_url = "http://mlflow-tracking:5000"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(mlflow_url, timeout=3)
            if response.status_code == 200:
                print("MLflow tracking server is up.")
                return
            else:
                print(
                    f"MLflow responded with status code {response.status_code}, retrying...")
        except requests.exceptions.RequestException:
            print("MLflow server not reachable yet, retrying...")
        time.sleep(interval)

    raise AirflowFailException(
        f"Timed out after {timeout} seconds waiting for MLflow")


def read_insert():
    df = pd.read_csv(CSV_PATH, header=None, names=[
                     "article_id", "label", "text", "timestamp"])
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO article_feedback (article_title, sentiment, feedback_time, processed)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (article_title, feedback_time) DO NOTHING;
        """
    for _, row in df.iterrows():
            cursor.execute(insert_sql, (
                row['text'],
                row.get('label'),
                row['timestamp'],
                row.get('processed', False),
            ))

    conn.commit()
    cursor.close()
    conn.close()


def check_unprocessed_count(ti):
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    count = pg_hook.get_first(
        "SELECT COUNT(*) FROM article_feedback WHERE processed = FALSE;")[0]
    return 'prepare_training_data' if count >= 2 else 'skip_training'


def prepare_training_data(ti):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = os.path.join(EXPORT_DIR, f"training_data_{timestamp}.csv")

    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    df = pg_hook.get_pandas_df("""
        SELECT id, sentiment, article_title, feedback_time
        FROM article_feedback
        WHERE processed = FALSE;
    """)
    df['feedback_time'] = df['feedback_time'].dt.tz_localize(
        'UTC').dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    df.to_csv(
        export_path,
        index=False,
        header=False,
    )
    ti.xcom_push(key='training_csv', value=export_path)


def update_processed_and_train(ti):
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    pg_hook.run(
        "UPDATE article_feedback SET processed = TRUE WHERE processed = FALSE;")
    csv_path = ti.xcom_pull(
        task_ids='prepare_training_data', key='training_csv')
    tr.train(csv_path)


with DAG(
    dag_id='article_feedback_pipeline',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description='Pipeline for inserting feedback and training model',
) as dag:
    
    wait_for_mlflow_task = PythonOperator(
        task_id='wait_for_mlflow_server',
        python_callable=wait_for_mlflow_server,
    )

    create_feedback_table = SQLExecuteQueryOperator(
        task_id="create_feedback_table",
        conn_id="mlops_pg_conn",
        sql=CREATE_FEEDBACK_TABLE,
    )
     
    read_insert_task = PythonOperator(
        task_id='read_and_insert_csv',
        python_callable=read_insert,
    )

    check_count_task = BranchPythonOperator(
        task_id='check_unprocessed_count',
        python_callable=check_unprocessed_count,
    )

    prepare_training_data_task = PythonOperator(
        task_id='prepare_training_data',
        python_callable=prepare_training_data,
    )

    train_and_update_task = PythonOperator(
        task_id='train_and_update',
        python_callable=update_processed_and_train,
    )

    skip_training = DummyOperator(task_id='skip_training')
    end = DummyOperator(
        task_id='end', trigger_rule='none_failed_min_one_success')
    
    create_feedback_table >> read_insert_task >> check_count_task
    check_count_task >> [prepare_training_data_task, skip_training]
    prepare_training_data_task >> wait_for_mlflow_task >> train_and_update_task >> end
    skip_training >> end

    


