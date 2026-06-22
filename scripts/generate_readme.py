from pathlib import Path
from datetime import datetime

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_PATH = BASE_DIR / "scripts" / "README.md"

ALL_PROPERTIES_CSV = BASE_DIR / "output" / "all_properties" / "all_properties.csv"
EVALUATION_CSV = BASE_DIR / "output" / "all_properties" / "cafe_property_evaluation.csv"
DASHBOARD_CSV = BASE_DIR / "output" / "all_properties" / "cafe_business_dashboard.csv"
SIM_INDEX_CSV = BASE_DIR / "output" / "all_properties" / "property_business_simulations_index.csv"


def count_rows(path):
    if not path.exists():
        return "未生成"
    try:
        return f"{len(pd.read_csv(path))}件"
    except Exception:
        return "読込失敗"


def exists_label(path):
    return "あり" if path.exists() else "未生成"


def add_code_block(lines, lang, items):
    lines.append(f"```{lang}")
    for item in items:
        lines.append(item)
    lines.append("```")


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    all_count = count_rows(ALL_PROPERTIES_CSV)
    eval_count = count_rows(EVALUATION_CSV)
    dashboard_count = count_rows(DASHBOARD_CSV)
    sim_count = count_rows(SIM_INDEX_CSV)

    lines = []

    lines.append("# scripts README")
    lines.append("")
    lines.append(f"更新日時：{now}")
    lines.append("")
    lines.append("## 概要")
    lines.append("")
    lines.append("このディレクトリには、高松市の店舗・事業用賃貸物件データをもとに、カフェ開業候補地データベースを構築・評価・可視化するためのスクリプトを配置しています。")
    lines.append("")
    lines.append("本プロジェクトの目的は、単なる物件一覧の作成ではなく、**どの物件で、どのカフェ業態なら事業成立しやすいか**を分析できるデータベースを構築することです。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 現在のデータ状況")
    lines.append("")
    lines.append(f"- 統合物件データ：{all_count}")
    lines.append(f"- カフェ事業性評価：{eval_count}")
    lines.append(f"- ダッシュボード用CSV：{dashboard_count}")
    lines.append(f"- 営業シミュレーション連携CSV：{sim_count}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 推奨実行順序")
    lines.append("")
    lines.append("### 1. カフェ事業性評価")
    lines.append("")
    add_code_block(lines, "powershell", [
        "python scripts\\evaluate_cafe_properties_v2.py"
    ])
    lines.append("")
    lines.append("### 2. 評価結果分析")
    lines.append("")
    add_code_block(lines, "powershell", [
        "python scripts\\analyze_business_score.py"
    ])
    lines.append("")
    lines.append("### 3. 物件別営業シミュレーション生成")
    lines.append("")
    add_code_block(lines, "powershell", [
        "python scripts\\generate_property_business_simulations.py"
    ])
    lines.append("")
    lines.append("### 4. 事業性ダッシュボード生成")
    lines.append("")
    add_code_block(lines, "powershell", [
        "python scripts\\generate_cafe_business_dashboard.py"
    ])
    lines.append("")
    lines.append("### 5. scripts README更新")
    lines.append("")
    add_code_block(lines, "powershell", [
        "python scripts\\generate_readme.py"
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 主要成果物")
    lines.append("")
    lines.append("### 統合物件データ")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/all_properties.csv",
        "output/all_properties/all_properties_geocoded.csv",
        "output/all_properties/all_properties_geocode_failed.csv",
    ])
    lines.append("")
    lines.append("### カフェ事業性評価")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_property_evaluation.csv",
        "output/all_properties/cafe_property_evaluation.html",
        "output/all_properties/cafe_business_dashboard.csv",
        "output/all_properties/cafe_business_dashboard.html",
    ])
    lines.append("")
    lines.append("### 物件別営業シミュレーション")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/index.html",
        "output/all_properties/property_business_simulations/",
        "output/all_properties/property_business_simulations_index.csv",
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 主要スクリプト")
    lines.append("")
    lines.append("### evaluate_cafe_properties_v2.py")
    lines.append("")
    lines.append("統合済み物件データを読み込み、カフェ開業向けの事業成立性評価を行います。")
    lines.append("")
    lines.append("入力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/all_properties.csv"
    ])
    lines.append("")
    lines.append("出力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_property_evaluation.csv",
        "output/all_properties/cafe_business_dashboard.csv",
        "output/all_properties/cafe_property_evaluation.html",
    ])
    lines.append("")
    lines.append("主な処理：")
    lines.append("")
    lines.extend([
        "- 家賃・面積・坪数の数値補正",
        "- 坪単価算定",
        "- 立地区分判定",
        "- 店舗規模分類",
        "- 物件タイプ推定",
        "- 階数判定",
        "- 駐車場判定",
        "- 事業成立パターン判定",
        "- 推奨カフェモデル推定",
        "- 推定席数算定",
        "- 必要月商・必要日商算定",
        "- 理論必要日客数・推奨必要日客数算定",
        "- 初期投資下限・上限・中央値算定",
        "- 事業成立性スコア・評価ランク算定",
    ])
    lines.append("")
    lines.append("### analyze_business_score.py")
    lines.append("")
    lines.append("評価結果の妥当性を確認するための分析スクリプトです。")
    lines.append("")
    lines.append("入力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_property_evaluation.csv"
    ])
    lines.append("")
    lines.append("主な確認内容：")
    lines.append("")
    lines.extend([
        "- パターン別中央値",
        "- ランク別中央値",
        "- パターン×ランク分布",
        "- 必要回転数",
        "- 事業成立性スコア分布",
    ])
    lines.append("")
    lines.append("### generate_property_business_simulations.py")
    lines.append("")
    lines.append("各物件について、フルーツ×コーヒー×パフェ業態を前提にした営業シミュレーションHTMLを生成します。")
    lines.append("")
    lines.append("入力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_business_dashboard.csv"
    ])
    lines.append("")
    lines.append("出力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/index.html",
        "output/all_properties/property_business_simulations/",
        "output/all_properties/property_business_simulations_index.csv",
    ])
    lines.append("")
    lines.append("主な処理：")
    lines.append("")
    lines.extend([
        "- 商品構成戦略の自動判定",
        "- パフェ・フルーツドリンク・コーヒー比率の算定",
        "- 平日・休日必要客数の算定",
        "- 推奨人員体制の算定",
        "- 通年損益シミュレーション",
        "- 夏季かき氷ブースト算定",
        "- 個別物件HTML生成",
        "- 一覧HTML生成",
        "- 検索・ソート付き一覧生成",
        "- ダッシュボード連携用CSV生成",
    ])
    lines.append("")
    lines.append("### generate_cafe_business_dashboard.py")
    lines.append("")
    lines.append("カフェ事業性評価結果をもとに、インタラクティブな散布図ダッシュボードを生成します。")
    lines.append("")
    lines.append("入力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_business_dashboard.csv",
        "output/all_properties/property_business_simulations_index.csv",
    ])
    lines.append("")
    lines.append("出力：")
    lines.append("")
    add_code_block(lines, "text", [
        "output/all_properties/cafe_business_dashboard.html"
    ])
    lines.append("")
    lines.append("主な処理：")
    lines.append("")
    lines.extend([
        "- 必要月商 × 必要日客数の散布図生成",
        "- 評価ランク・飲食可否フィルタ",
        "- 物件詳細パネル表示",
        "- 物件一覧テーブル生成",
        "- 物件詳細URLリンク",
        "- 個別営業シミュレーションHTMLへのリンク",
    ])
    lines.append("")
    lines.append("### generate_readme.py")
    lines.append("")
    lines.append("このREADMEを自動生成します。")
    lines.append("")
    lines.append("出力：")
    lines.append("")
    add_code_block(lines, "text", [
        "scripts/README.md"
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 評価思想")
    lines.append("")
    lines.append("本プロジェクトでは、単純に「良い立地」を高評価にするのではなく、以下の流れで評価します。")
    lines.append("")
    add_code_block(lines, "text", [
        "物件条件",
        "↓",
        "適した事業モデル",
        "↓",
        "事業成立性",
    ])
    lines.append("")
    lines.append("現在は特に、**少ない客数で成立できるか**を重視しています。")
    lines.append("")
    lines.append("主な評価要素：")
    lines.append("")
    lines.extend([
        "- 推奨必要日客数",
        "- 必要月商",
        "- 初期投資中央値",
        "- 飲食可否",
        "- 階数",
        "- 駐車場",
        "- 事業成立パターン",
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 事業成立パターン")
    lines.append("")
    lines.append("現在の分類：")
    lines.append("")
    lines.extend([
        "- 中心街・高単価型",
        "- 中心街・高回転型",
        "- 準中心街・生活圏型",
        "- 郊外・駐車場依存型",
        "- 低固定費・小商圏型",
        "- 大型投資・高売上必須型",
        "- 家賃未定・問い合わせ必要型",
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 営業シミュレーションの前提")
    lines.append("")
    lines.append("現在の営業シミュレーションは、以下の業態を前提にしています。")
    lines.append("")
    add_code_block(lines, "text", [
        "フルーツ",
        "+",
        "コーヒー",
        "+",
        "パフェ",
        "+",
        "フルーツドリンク",
        "+",
        "夏季かき氷",
    ])
    lines.append("")
    lines.append("焼き菓子主体・ランチ主体ではありません。")
    lines.append("")
    lines.append("### 商品構成")
    lines.append("")
    lines.append("物件ごとの席数・立地・必要客数・事業成立パターンから、以下の比率を自動設定します。")
    lines.append("")
    lines.extend([
        "- パフェ",
        "- フルーツドリンク",
        "- コーヒー",
        "- その他",
    ])
    lines.append("")
    lines.append("### かき氷の扱い")
    lines.append("")
    lines.append("かき氷は通年損益には含めず、夏季の上振れ商品として別枠で扱います。")
    lines.append("")
    lines.append("### 人員計画")
    lines.append("")
    lines.append("ワンオペは採用しません。")
    lines.append("")
    lines.append("基本方針：")
    lines.append("")
    lines.extend([
        "- 最低2名出勤",
        "- カウンターキッチン内完結",
        "- 注文・会計・提供はカウンター中心",
        "- 客席へのフルサービスは前提にしない",
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 今後の検討項目")
    lines.append("")
    lines.extend([
        "- 事業計画書HTMLの作成",
        "- サブ資料作成",
        "- 営業シミュレーションの数値根拠整理",
        "- 商品構成比率の精度改善",
        "- 人件費・シフト詳細化",
        "- 季節変動モデルの改善",
        "- ダッシュボードと営業シミュレーションの導線整理",
        "- ディレクトリ構造整理",
    ])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 注意事項")
    lines.append("")
    lines.extend([
        "- 推測で物件を評価しない",
        "- 実物件データを優先する",
        "- 評価ロジックは固定せず、分析結果を見ながら改善する",
        "- 高評価物件だけを抽出するのではなく、取得できた全物件に目を通せる構成を維持する",
        "- 営業シミュレーションは事業計画検討の補助資料であり、最終判断には現地確認・内装条件・厨房条件・法規確認が必要",
    ])
    lines.append("")

    readme = "\n".join(lines)
    OUT_PATH.write_text(readme, encoding="utf-8")

    print(f"[SAVE] {OUT_PATH}")


if __name__ == "__main__":
    main()