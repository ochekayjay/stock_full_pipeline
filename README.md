# 📊 STOCK INVESTMENT TRACKING PIPELINE

This project presents an end-to-end, autonomous, and scalable data pipeline for an tracking the appreciation path of stocks and how best to get maximum reward from stock investments. It extracts data from yahoo finance sources using an automated triggering from amazon event-bridge on an ECR-based lambda function, Loads the data into the warehouse either via incremental calls or backfills, then the data is being conveyed into a transformation section inclusive of:
- Transformation and deposition (performed by **DBT** hosted on **ECR**, configured on **ECS** and ran on **Fargate**).
- Data Registration (performed by a **Lambda function** extracting stock runs that breaks into newer heights or descend into newer lows for proper reconciliation and auditing), data gets deposited into google-sheets.
- Alerting Channel (Stock runs which are critical to investment plans are notified through neccessary channels like telegram in this case).
- Dashboard layer on **Tableau** (the performance and investment opportunities of the stock is displayed)

The pipeline is designed to provide actionable insights and operational efficiency, helping the investors make faster, smarter, data-driven decisions.

----
📌 Project Overview
----
Data Ingestion: Fivetran automates the ingestion of 8 core datasets from transactional systems into BigQuery.
Transformation: dbt performs modular data modeling using snapshots, star schema design, and incremental materializations.
Data Marts: Business-ready marts enable in-depth analysis across multiple functions.
Visualization: Tableau dashboard present interactive insights to business users.
