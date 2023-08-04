import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from get_api_usage import get_monthly_usage


def get_current_year_month() -> tuple:
    """今日の年と月を取得する

    Returns:
        tuple(str, str): 年, 月
    """
    return datetime.datetime.now().year, datetime.datetime.now().month

def update_progress(progress: float):
    """WebUIのプログレスバーを更新

    Args:
        progress (float): _description_
    """
    progress_bar.progress(progress)
    progress_text.text(f"Processing {int(progress * 100)}% completed.")

st.title("OpenAI API Monthly Usage")

# get the current year and month
current_year, current_month = get_current_year_month()
# Define available years and months
available_years = list(range(2020, 2024))
available_months = list(range(1, 13))

# Find the index of the current year and month
default_year_index = available_years.index(current_year)
default_month_index = available_months.index(current_month)

# Create select boxes for year and month with default values
selected_year = st.selectbox("Select Year:", available_years, index=default_year_index)
selected_month = st.selectbox("Select Month:", available_months, index=default_month_index)

progress_bar = st.progress(0)
progress_text = st.empty()

if st.button("Get Usage"):
    year_month = f"{selected_year}-{selected_month:02}"
    # 各モデルの合計コストを計算
    monthly_usage = get_monthly_usage(year_month, callback=update_progress)

    progress_bar.progress(100)
    progress_text.text("Completed!")

    # Transforming the data into a structured format for visualization
    rows = []
    for date, details in monthly_usage.items():
        total_costs = details['total_costs']
        model_costs = details['model_costs']['total_costs']
        whisper_costs = details['whisper_costs']['total_costs']

        # Detailed model costs
        gpt4_costs = details['model_costs'].get('gpt-4-0613', {}).get('total_cost', 0)
        gpt3_turbo_costs = details['model_costs'].get('gpt-3.5-turbo-0613', {}).get('total_cost', 0)

        rows.append((date, total_costs, model_costs, whisper_costs, gpt4_costs, gpt3_turbo_costs))

    # Creating a DataFrame
    usage_df = pd.DataFrame(rows, columns=['Date', 'Total Costs', 'Model Costs', 'Whisper Costs', 'GPT-4 Costs', 'GPT-3.5 Turbo Costs'])

    # Displaying the first few rows
    usage_df.head()

    # Display the DataFrame as a table
    st.write("API Usage Details for July 2023:")
    st.write(usage_df)

    # Plot Total Costs
    st.write("Total Costs Over Time:")
    fig1, ax1 = plt.subplots()
    usage_df.plot(x='Date', y='Total Costs', ax=ax1)
    st.pyplot(fig1)

    # Plot Model Costs
    st.write("GPT-4 and GPT-3.5 Turbo Costs Over Time:")
    fig2, ax2 = plt.subplots()
    usage_df.plot(x='Date', y=['GPT-4 Costs', 'GPT-3.5 Turbo Costs'], ax=ax2)
    st.pyplot(fig2)

    # Plot Whisper Costs
    st.write("Whisper Costs Over Time:")
    fig3, ax3 = plt.subplots()
    usage_df.plot(x='Date', y='Whisper Costs', ax=ax3)
    st.pyplot(fig3)

    st.write("Note: Customize the visualization further as needed.")
