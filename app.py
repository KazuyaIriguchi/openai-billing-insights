import streamlit as st
import pandas as pd
import json
import requests
import os
from datetime import datetime


def get_usage(year_month, organization):
    # 年と月の取得
    year, month = map(int, year_month.split('-'))

    # 開始日と終了日の作成
    start_date = f"{year}-{month:02d}-01"

    # 翌月の1日を計算
    year, month = (year, month + 1) if month < 12 else (year + 1, 1)
    end_date = f"{year}-{month:02d}-01"

    # API の URL の作成
    url = f"https://api.openai.com/dashboard/billing/usage?end_date={end_date}&start_date={start_date}"

    headers = {
        "openai-organization": organization,
        "authorization": "Bearer " + os.getenv("OPENAI_API_KEY"),
    }

    # API リクエストの送信と結果の表示
    response = requests.get(url, headers=headers)

    output_name = f"{start_date}_to_{end_date}_{organization}_usage.json"
    with open(output_name, "w") as f:
        json.dump(response.json(), f, indent=4)
    return response.json()

year_month = st.text_input("YYYY-MM")
organization = st.text_input("your organization")

if st.button("Get Usage"):
    # JSONデータをロードする（実際にはAPIからデータを取得するコードに置き換えてください）
    usage = get_usage(year_month, organization)

    # 各モデルの合計コストを計算
    total_costs = {}
    time_series_costs = []
    for daily_cost in usage["daily_costs"]:
        # タイムスタンプをdatetimeに変換
        timestamp = datetime.fromtimestamp(daily_cost["timestamp"])
        for line_item in daily_cost["line_items"]:
            name = line_item["name"]
            cost = line_item["cost"] / 100
            if name in total_costs:
                total_costs[name] += cost
            else:
                total_costs[name] = cost
            time_series_costs.append({"date": timestamp, "model": name, "cost": cost})

    # DataFrameに変換
    df = pd.DataFrame(list(total_costs.items()), columns=['Model', 'Cost'])
    df_ts = pd.DataFrame(time_series_costs)

    # 全モデルの合計コストを計算
    total_cost = df['Cost'].sum()

    # メインエリアに全モデルのデータとグラフ、全モデルの合計コストを表示
    st.write(df)
    st.bar_chart(df.set_index('Model')['Cost'])
    st.write('Total cost: ', total_cost)

    st.write(df_ts)
