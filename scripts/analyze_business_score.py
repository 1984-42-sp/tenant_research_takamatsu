import pandas as pd

df = pd.read_csv(
    "output/all_properties/cafe_property_evaluation.csv"
)

df["必要回転数"] = (
    df["推奨必要日客数"] /
    df["推定席数"]
)

print("\n=== パターン別中央値 ===")
print(
    df.groupby("事業成立パターン")[
        [
            "推奨必要日客数",
            "推定席数",
            "必要回転数",
            "必要月商"
        ]
    ].median().round(2)
)

print("\n=== ランク別中央値 ===")
print(
    df.groupby("評価ランク")[
        [
            "推奨必要日客数",
            "推定席数",
            "必要回転数",
            "必要月商"
        ]
    ].median().round(2)
)
print("\n=== パターン×ランク ===")

print(
    pd.crosstab(
        df["事業成立パターン"],
        df["評価ランク"]
    )
)

print(
    df[df["事業成立パターン"]=="郊外・駐車場依存型"][
        ["物件名","事業成立性スコア","評価ランク","推奨必要日客数","必要月商"]
    ].sort_values("事業成立性スコア", ascending=False)
)

print(
    df.groupby("事業成立パターン")[
        "事業成立性スコア"
    ].median().sort_values(ascending=False)
)