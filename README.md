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
- **Data Ingestion**: Lambda function automates the ingestion of raw financial data from into Redshift.
- **Transformation**: dbt performs modular data modeling using snapshots, star schema design, and incremental materializations.
- **Data Marts**: Business-ready marts enable in-depth analysis across multiple functions.
- **Visualization**: Tableau dashboard present interactive insights to business users.
- **Data Alerts**: Stock values that breaks in or out of bucket gets registered on google-sheet for future auditing and reconciliation and also gets sent to notification channels like telegram

----
🛠️ Tech Stack
----
- **Event-bridge + Lambda Function** – Automated data ingestion from stock data sources
- **Redshift** – Scalable cloud data warehouse
- **Dbt** – Transformation, testing, documentation, and version control
- **Tableau** – Business intelligence and dashboarding
- **Google App Script** - low-code development platform that helps poll data from external databases into goole workspaces and dispense data into external downstream environments.
<img width="1164" height="776" alt="Screenshot 2026-09-30 at 10 22 26" src="https://github.com/user-attachments/assets/7034152d-5ae4-47b0-94a0-e401af9fa3fb" />

----
🧱 dbt Models & Data Warehouse Design
----
**🟨 Dimension Tables (dim_*)**
- `highest_lowest_valuation_dim :` an adjustable bucket that compares the current stock value with the record highest and lowest. It places the current stock in a tier in view of its value relative to 5 created buckets formed within the record highest and lowest stock records.
- `average_valuation_dim :` compares current stock value with its position with regards to the average stock value and its standard deviation. It checks whether it is **Below** the subtraction of standard dev from average stock value, **above** their sum or **between** them.
- `moving_avg_comparison_dim :` uses running average mean between 3 months and 6 months to check **bullish** and **bearish** alignments.

**🟨 Factless Fact Tables**
- `highest_lowest_stock_metric :` It accounts for the streaks a stock spend within the buckets formed from `highest_lowest_valuation_dim`. Particularly, highlighting the start_date and end_date a stock spends within the buckets, also noting the highest and lowest stock traded value within that window.
- `moving_average_stock_metric :` It displays the streaks a stock spend between the buckets formed from `average_valuation_dim` whether it is **Below** ,**above** or **between** .
- `stock_average_metric :` Checks the streaks whether stock falls in **bullish** or **bearish** alignments.

**🟨 Source and Snapshot Tables**
- `stock_live_table :` Cleaned data from yahoo finance.
- `stock_snapshot_table :` Daily record on what buckets every stock holds before exporting that information to factless tables for streak padding and window showcasing
<img width="3128" height="3568" alt="image" src="https://github.com/user-attachments/assets/d99ccb05-2e3b-4c44-8888-a6fff06b98e5" />

