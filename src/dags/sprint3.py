import time
import requests
import json
import pandas as pd
import logging

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.http_hook import HttpHook

HTTP_CONN_ID = HttpHook.get_connection('http_conn_id')
API_KEY = HTTP_CONN_ID.extra_dejson.get('api_key')
BASE_URL = HTTP_CONN_ID.host

POSTGRES_CONN_ID = 'postgresql_de'

NICKNAME = "ikondrashkov"
COHORT = "27"

task_logger = logging.getLogger("airflow.task")

headers = {
    'X-Nickname': NICKNAME,
    'X-Cohort': COHORT,
    'X-Project': 'True',
    'X-API-KEY': API_KEY,
    'Content-Type': 'application/x-www-form-urlencoded'
}


def generate_report(ti):
    task_logger.info('Making request generate_report')

    response = requests.post(f'{BASE_URL}/generate_report', headers=headers)
    response.raise_for_status()
    task_id = json.loads(response.content)['task_id']

    ti.xcom_push(key='task_id', value=task_id)
    task_logger.info(f'Response is {response.content}')


def get_report(ti):
    task_logger.info('Making request get_report')

    task_id = ti.xcom_pull(key='task_id')
    report_id = None

    for i in range(20):
        response = requests.get(f'{BASE_URL}/get_report?task_id={task_id}', headers=headers)
        response.raise_for_status()
        print(f'Response is {response.content}')
        status = json.loads(response.content)['status']
        if status == 'SUCCESS':
            report_id = json.loads(response.content)['data']['report_id']
            break
        else:
            time.sleep(10)

    if not report_id:
        raise TimeoutError('Report not found!')

    ti.xcom_push(key='report_id', value=report_id)
    task_logger.info(f'Report_id={report_id}')


def get_increment(date, ti):
    task_logger.info('Making request get_increment')

    report_id = ti.xcom_pull(key='report_id')
    response = requests.get(
        f'{BASE_URL}/get_increment?report_id={report_id}&date={str(date)}T00:00:00',
        headers=headers)
    response.raise_for_status()
    task_logger.info(f'Response is {response.content}')

    increment_id = json.loads(response.content)['data']['increment_id']
    if not increment_id:
        raise ValueError(f'Increment is empty. Most probably due to error in API call.')
    
    ti.xcom_push(key='increment_id', value=increment_id)
    task_logger.info(f'increment_id={increment_id}')


def upload_data_to_staging(filename, date, pg_table, pg_schema, ti):
    increment_id = ti.xcom_pull(key='increment_id')
    s3_filename = f'https://storage.yandexcloud.net/s3-sprint3/cohort_{COHORT}/{NICKNAME}/project/{increment_id}/{filename}'
    task_logger.info(s3_filename)
    local_filename = date.replace('-', '') + '_' + filename
    task_logger.info(local_filename)
    response = requests.get(s3_filename)
    response.raise_for_status()
    open(f"{local_filename}", "wb").write(response.content)
    task_logger.info(response.content)

    df = pd.read_csv(local_filename, index_col=0)
    df=df.drop_duplicates(subset=['uniq_id'])

    if 'status' not in df.columns:
        df['status'] = 'shipped'

    postgres_hook = PostgresHook(POSTGRES_CONN_ID)
    engine = postgres_hook.get_sqlalchemy_engine()
    row_count = df.to_sql(pg_table, engine, schema=pg_schema, if_exists='append', index=False)
    task_logger.info(f'{row_count} rows was inserted')


args = {
    "owner": "ikondrashkov",
    'email': ['ikondrashkov@yandex.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2
}

business_dt = '{{ ds }}'
load_d_tasks = list()

with DAG(
        'sales_mart',
        default_args=args,
        description='Provide default dag for sprint3',
        catchup=True,
        start_date=datetime.today() - timedelta(days=7),
        end_date=datetime.today() - timedelta(days=1),
) as dag:

    start = EmptyOperator(task_id='start')

    generate_report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report)

    get_report = PythonOperator(
        task_id='get_report',
        python_callable=get_report)

    get_increment = PythonOperator(
        task_id='get_increment',
        python_callable=get_increment,
        op_kwargs={'date': business_dt})

    delete_user_order_log = PostgresOperator(
        task_id='delete_user_order_log',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/staging.user_order_log-delete.sql",
        parameters={"date": {business_dt}}
    )

    update_user_order_log = PostgresOperator(
        task_id='update_user_order_log',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/staging.user_order_log-update.sql")

    update_f_sales = PostgresOperator(
        task_id='update_f_sales',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/mart.f_sales-update.sql")

    upload_user_order_inc = PythonOperator(
        task_id='upload_user_order_inc',
        python_callable=upload_data_to_staging,
        op_kwargs={'date': business_dt,
                   'filename': 'user_order_log_inc.csv',
                   'pg_table': 'user_order_log',
                   'pg_schema': 'staging'})


    for i in ['d_item', 'd_customer', 'd_city']:
        load_d_tasks.append(PostgresOperator(
            task_id=f'load_{i}',
            postgres_conn_id=POSTGRES_CONN_ID,
            sql=f'sql/mart.{i}-insert.sql',
            dag=dag
            )
        )

    load_f_sales = PostgresOperator(
        task_id='load_f_sales',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/mart.f_sales-insert.sql",
        parameters={"date": {business_dt}}
    )

    delete_f_customer_retention = PostgresOperator(
        task_id='delete_f_customer_retention',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/mart.f_customer_retention-create-delete.sql",
        parameters={"date": {business_dt}}
    )

    load_f_customer_retention = PostgresOperator(
        task_id='load_f_customer_retention',
        postgres_conn_id=POSTGRES_CONN_ID,
        sql="sql/mart.f_customer_retention-insert.sql",
        parameters={"date": {business_dt}}
    )

    end = EmptyOperator(task_id='end')

    (
        start >>
        generate_report >>
        get_report >>
        get_increment >>
        delete_user_order_log >>
        [update_user_order_log, update_f_sales] >>
        upload_user_order_inc >>
        load_d_tasks >>
        load_f_sales >>
        delete_f_customer_retention >>
        load_f_customer_retention >>
        end
    )