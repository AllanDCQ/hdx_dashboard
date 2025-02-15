# 📊 HealthScope Dashboard

Welcome to the **HealthScope Dashboard** GitHub repository. This project is designed to provide an **interactive and educational visualization of health data**. It enables researchers, analysts, and decision-makers to easily access public health information through interactive charts and detailed analysis.

## 🌍  Live Application

Access the interactive dashboard via the link: [HealthScope Dashboard](https://hdx-dashboard.onrender.com) <sub>(⚠️ The first connection may take more than a minute to load)</sub>.


## 🖼️ Dashboard Previews

<img width="944" alt="hdx-dashboard_image" src="https://github.com/user-attachments/assets/4dad0ddd-136b-44ae-a653-72e2d2b378b0" />

## 🧩 Project Overview

The **HealthScope Dashboard** extracts and visualizes **public health data** from the [Humanitarian Data Exchange (HDX)](https://data.humdata.org/). It allows users to **track health trends**, identify **high-risk areas**, and analyze the impact of interventions in real time.

### 🔑 Key Features:

- **Automated data extraction** from HDX using web scraping techniques.
- **Health trend analysis** by indicator and country.
- **Cloud deployment** with PostgreSQL for data storage.
- **Interactive dashboard** built with Dash and Plotly.

## 🔄 Webscraping and Data Management

The data displayed in this dashboard is sourced from **HDX**, a platform developed by the **United Nations Office for the Coordination of Humanitarian Affairs (OCHA)**. HDX aggregates datasets from organizations such as **UNICEF, WHO, and UNHCR** to provide insights into humanitarian crises, public health, and emergency response.

To ensure the **dynamic and continuous update of data**, the scraping system includes:
- A **modular web scraping architecture** (`FetchPage` and `FetchPageSingle` classes) to retrieve country-specific and global health indicators.
- **Optimized data storage** in PostgreSQL, reducing redundant requests and improving performance.
- **Automated data refresh** whenever an update is detected on HDX.

## 📊 Metrics Definitions

Health indicators are classified into **four main categories**, following WHO standards:

- **Health Status**: Mortality indicators and life expectancy.
- **Risk Factors**: Environmental and nutritional factors.
- **Service Coverage**: Vaccination and healthcare access.
- **Health System**: Hospital resources and birth registration.

## 🛠️ Installation & Setup

### 💻  Local Setup
1. Clone the repository:
```bash
git clone https://github.com/username/healthscope-dashboard.git
cd healthscope-dashboard
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python app.py
```

### 🌐 Dash Application
The dashboard is deployed on **Render**, utilizing PostgreSQL for secure data storage.
<p align="center">
    <img width="362" alt="webscraping" src="https://github.com/user-attachments/assets/fe6677bf-56d4-4b6d-87fd-e9002738e788" />
</p>
