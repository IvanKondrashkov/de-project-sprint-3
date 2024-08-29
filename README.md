# Проект 3-го спринта

![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-salad)
![SQL](https://img.shields.io/badge/-SQL-pink)

### Описание
Репозиторий предназначен для сдачи проекта 3-го спринта

### Структура репозитория
- `/migrations`
- `/src/dags`

### Схема данных, слой stg

<p float="center">
  <img src="src/image/de-project-sprint-3-stg.png" width="95%" />
</p>

### Схема данных, слой cdm

<p float="center">
  <img src="src/image/de-project-sprint-3-cdm.png" width="95%" />
</p>

### Панель управления дагами в Airflow

<p float="center">
  <img src="src/image/de-project-sprint-3-airflow-ui.png" width="95%" />
</p>

### Граф запуска тасок в Airflow

<p float="center">
  <img src="src/image/de-project-sprint-airflow-task-graph.png" width="95%" />
</p>

### Графики в Metabase
<p float="left">
  <img src="src/image/f_sales_q.png" width="47%" />
  <img src="src/image/f_sales_p.png" width="47%" />
</p>

### Как запустить контейнер
Запустите локально команду:

```
docker run -d -p 3000:3000 -p 15432:5432 --name=de-project-sprint-3-server cr.yandex/crp1r8pht0n0gl25aug1/project-sprint-3:latest
```

После того как запустится контейнер, у вас будут доступны:
1. Visual Studio Code
2. Airflow
3. Database