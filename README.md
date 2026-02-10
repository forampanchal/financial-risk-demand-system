# Financial Risk & Demand Intelligence System

An end-to-end machine learning platform that forecasts daily transaction demand, detects volatility-driven risk, and supports automated retraining and deployment using AWS, Docker, and CI/CD.

## Project Objective
The goal of this project is to simulate and build a production-grade ML system that:
- Generates daily demand forecasts
- Detects anomalous demand behavior
- Computes quantitative risk scores
- Automates model retraining and deployment

## System Overview
The system operates as a daily batch pipeline:
1. Ingest daily demand data
2. Generate rolling forecasts (7 / 30 / 90 days)
3. Detect anomalies and volatility shifts
4. Compute demand risk scores
5. Store results and trigger alerts when risk is elevated

## Tech Stack
- Python
- Time Series Forecasting (Prophet)
- Anomaly Detection (Isolation Forest)
- FastAPI
- Docker
- AWS (S3, EC2, ECR, CloudWatch)
- GitHub Actions (CI/CD)

## Project Status
🚧 In progress — data simulation and system architecture finalized.
