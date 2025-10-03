✈️ Analyzing-Flight-Delays-and-Cancellations-using-Python-Power-BI

This project explores 111K+ rows of flight and weather data from the Pacific Northwest to uncover patterns, causes, and insights behind flight delays and cancellations.

It combines Python-based analysis for data wrangling and visualization with an interactive Power BI dashboard for business-ready insights.

📊 Project Overview

-->Objective: Identify key factors contributing to flight delays and cancellations.

-->Dataset: ~111,378 rows of flight and weather data (2022).

-->Tools Used:
           Python: Pandas, Matplotlib, Seaborn (data cleaning, wrangling, exploratory analysis).
           Power BI: Interactive dashboard with KPIs, maps, and drilldowns.
           
-->Key Skills: Data Wrangling, Visualization, Geospatial Mapping, Dashboarding, Storytelling with Data.


🛠️ Steps & Methodology

1. Data Preparation (Python)

-->Cleaned and transformed raw flight and weather CSVs.
   
-->Handled missing values, merged datasets, and created new features (delay categories, weather impact).

-->Validated dataset (~111K rows) for accuracy and consistency.

2. Exploratory Data Analysis (Python)
   
-->Time-Series Analysis: Trends in delays and cancellations by day/month.

-->Correlation Heatmaps: Factors influencing delays (weather, airports, airlines).

-->Geospatial Plots: Origin-destination routes with delay intensity.

3. Dashboard Development (Power BI)
   
-->Time-Series Chart (Line): Average delays/cancellations by month/day.

-->Bar/Column Charts: Delays by airline and airport.

-->Stacked Bars: Completed flights vs cancellations per airline.

-->Maps: Routes with delay intensity.

-->KPI Cards: Total flights, % delayed, % cancelled.

🚀 Key Insights

-->Certain airlines and routes consistently face higher delays.

-->Weather conditions are a major factor behind cancellation spikes.

-->Peak disruption periods occur around specific months, affecting passenger planning.

-->The interactive dashboard allows quick comparisons across airlines, airports, and timeframes.

📂 Repository Structure
├── flights2022.csv

├── flights_weather2022.csv

├── notebooks/
│   ├── data_cleaning.ipynb
│   ├── exploratory_analysis.ipynb
│   └── visualizations.ipynb

├── flights2020.pbix

├── README.md

🖼️ Sample Visualizations

-->Top 15 Airline Average Departure Delay
<img width="842" height="470" alt="monthly_avg_dep_delay" src="https://github.com/user-attachments/assets/8f34c035-be61-41f9-8a23-1849ca5d81e9" />

  -->Correlation Heatmap
<img width="790" height="590" alt="dep_delay_vs_TEMP" src="https://github.com/user-attachments/assets/548ad0c1-0cd8-45e2-a3e4-d5252d3b8fbb" />

-->Daily Cancellation With 30 day Rolling-Mean
<img width="1005" height="470" alt="daily_cancellations_rolling" src="https://github.com/user-attachments/assets/53c62f97-f911-441c-8172-aa38f1a31a7b" />

-->Departure delay Vs Temp
<img width="938" height="790" alt="correlation_heatmap" src="https://github.com/user-attachments/assets/ef7e3207-ff54-47c2-83b5-1fbd12be7f35" />

-->Monthly Average Deeparture Delay
<img width="989" height="590" alt="airline_avg_dep_delay_top15" src="https://github.com/user-attachments/assets/58cd06ff-24b9-4fd3-98dd-9f1c40293a3c" />

-->Power BI Dashboard Preview
<img width="1313" height="749" alt="Screenshot (10)" src="https://github.com/user-attachments/assets/cbf1cb07-1015-477b-bb27-896e6ec7eec9" />

📌 Future Improvements

   -->Automate data refresh in Power BI with updated datasets.
   
   -->Add machine learning models to predict delays based on weather and historical data.
   
   -->Deploy dashboard online for public access.





