import json
import requests
import os
from datetime import datetime, timedelta
from collections import defaultdict
import time
from tqdm import tqdm

# reference: https://openai.com/pricing
model_pricing = {}
with open("./pricing.json", "r") as f:
    model_pricing = json.load(f)

# API rate limit measures against
API_WAIT_TIME = 12  # sec

def call_usage_api(date: str) -> requests.Response:
    # エンドポイントとヘッダーの設定
    url = "https://api.openai.com/v1/usage"
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
    params = {"date": date}

    try:
        # APIリクエストの実行
        response = requests.get(url, headers=headers, params=params)
        return response
    except Exception as e:
        print(e)
        return e

def get_model_costs(data: dict) -> dict:
    # 各モデルの統計を保存する辞書
    model_stats = defaultdict(lambda: {'n_context_tokens_total': 0, 'n_generated_tokens_total': 0})

    # データの各エントリをループして、各モデルの統計を計算
    for entry in data['data']:
        snapshot_id = entry['snapshot_id']
        model_stats[snapshot_id]['n_context_tokens_total'] += entry['n_context_tokens_total']
        model_stats[snapshot_id]['n_generated_tokens_total'] += entry['n_generated_tokens_total']

    # 各モデルのコストを計算
    model_costs = {}
    for model, stats in model_stats.items():
        cost_rate = model_pricing[model]
        context_token_cost = stats['n_context_tokens_total'] * (cost_rate['context'] / cost_rate["per_tokens"])
        generated_token_cost = stats['n_generated_tokens_total'] * (cost_rate['generated'] / cost_rate["per_tokens"])
        total_cost = context_token_cost + generated_token_cost
        model_costs[model] = {
            'context_token_cost': context_token_cost,
            'generated_token_cost': generated_token_cost,
            'total_cost': total_cost
        }
    model_costs["total_costs"] = sum(v["total_cost"] for k, v in model_costs.items())
    return model_costs

def get_whisper_costs(data: dict) -> dict:
    whisper_data = data.get("whisper_api_data", [])
    # 合計使用秒数とコストを計算
    whisper_cost_def = model_pricing["whisper-1"]
    total_seconds = sum(entry["num_seconds"] for entry in whisper_data)
    total_whisper_cost = (total_seconds / (whisper_cost_def["per_minutes"] * 60)) * whisper_cost_def["context"]
    return {
        "total_seconds": total_seconds,
        "total_costs": total_whisper_cost
    }

def get_daily_usage(date: str) -> dict:
    # コスト取得
    data = call_usage_api(date).json()

    # GPTモデル、Whisperのコスト計算
    # todo: fine tuning, dalleモデルへの対応
    model_costs = get_model_costs(data)
    whisper_costs = get_whisper_costs(data)
    return {
        "total_costs": model_costs["total_costs"] + whisper_costs["total_costs"],
        "model_costs": model_costs,
        "whisper_costs": whisper_costs
    }

def get_monthly_usage(year_month: str, wait_time: float=API_WAIT_TIME, dryrun: bool=False, callback=None):
    # 年と月の取得
    year, month = map(int, year_month.split('-'))

    # 開始日と終了日の作成
    start_date = datetime(year, month, 1)

    # 翌月の1日を計算
    year, month = (year, month + 1) if month < 12 else (year + 1, 1)
    end_date = datetime(year, month, 1) - timedelta(days=1)

    # 各モデルの月次統計
    monthly_usage = {}

    # 指定された月の各日に対してAPIリクエストを送信
    total_days = (end_date - start_date).days + 1
    pbar = tqdm(total=total_days, desc="Processing")
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        data = {}
        if not dryrun:
            data = get_daily_usage(date_str)
        monthly_usage[date_str] = data

        pbar.set_description(f"Processing: {date_str}")
        pbar.update(1)

        if callback:
            progress_percentage = current_date.day / total_days
            callback(progress_percentage)

        time.sleep(wait_time)
        current_date += timedelta(days=1)
    return monthly_usage

def export_monthly_usage_data(year: str, month: str, usage_data: dict):
    output_name = f"{year}_{month}_openai_api_usage.json"
    with open(output_name, "w") as f:
        json.dump(usage_data, f, indent=4)
    print(f"{output_name=}")


if __name__ == "__main__":
    year_month = "2023-07"
    monthly_usage = get_monthly_usage(year_month)
    export_monthly_usage_data("2023", "07", monthly_usage)
