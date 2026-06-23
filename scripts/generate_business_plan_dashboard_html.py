from pathlib import Path
import html
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE_DIR / "output" / "all_properties" / "business_plan_dashboard.csv"
OUTPUT_HTML = BASE_DIR / "output" / "all_properties" / "business_plan_dashboard.html"
SIM_INDEX_CSV = BASE_DIR / "output" / "archive_csv" / "property_business_simulations_index.csv"

STAR_ORDER = ["★★★★★", "★★★★☆", "★★★☆☆", "★★☆☆☆", "★☆☆☆☆"]


def esc(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def money(value):
    if pd.isna(value):
        return ""
    return str(value)


def make_summary_cards(df):
    cards = []
    total = len(df)

    for star in STAR_ORDER:
        count = int((df["seongsu_fit_stars"] == star).sum())
        rate = count / total * 100 if total else 0
        cards.append(f"""
        <div class="summary-card">
            <div class="summary-star">{star}</div>
            <div class="summary-count">{count}件</div>
            <div class="summary-rate">{rate:.1f}%</div>
        </div>
        """)

    return "\n".join(cards)


def make_insight(df):
    high = df[df["seongsu_fit_stars"].isin(["★★★★★", "★★★★☆"])]
    if high.empty:
        return "<p>高スコア物件がまだ抽出されていません。</p>"

    avg_tsubo = high["坪数_補正"].mean()
    avg_rent = high["家賃_円"].mean()
    top_locations = high["立地区分"].value_counts().head(3)

    location_text = "、".join([f"{idx} {cnt}件" for idx, cnt in top_locations.items()])

    return f"""
    <ul>
        <li>★★★★☆以上の候補は <strong>{len(high)}件</strong>。</li>
        <li>高スコア候補の平均坪数は <strong>{avg_tsubo:.1f}坪</strong>。</li>
        <li>高スコア候補の平均家賃は <strong>{avg_rent:,.0f}円</strong>。</li>
        <li>主な立地区分は <strong>{esc(location_text)}</strong>。</li>
        <li>現時点では、中心街・一定規模・夜営業適性のある物件が上位に出やすい。</li>
    </ul>
    """

def load_simulation_link_map():
    if not SIM_INDEX_CSV.exists():
        print(f"[WARN] simulation index not found: {SIM_INDEX_CSV}")
        return {}

    sim_df = pd.read_csv(SIM_INDEX_CSV)

    name_col = "物件名"

    file_col = None
    for col in sim_df.columns:
        if col in ["営業シミュレーションURL", "ファイル名", "html_file", "simulation_file", "filename", "file_name"]:
            file_col = col
            break

    if file_col is None:
        for col in sim_df.columns:
            if "html" in col.lower() or "file" in col.lower() or "ファイル" in col:
                file_col = col
                break

    if name_col not in sim_df.columns or file_col is None:
        print("[WARN] simulation index columns not matched")
        print(sim_df.columns.tolist())
        return {}

    result = {}

    for _, row in sim_df.iterrows():
        name = str(row.get(name_col, "")).strip()
        filename = str(row.get(file_col, "")).strip()

        if not name or not filename:
            continue

        if not filename.startswith("property_business_simulations/"):
            filename = f"property_business_simulations/{filename}"

        result[name] = filename

    return result

def make_property_table(df, simulation_link_map):
    rows = []

    for _, row in df.iterrows():
        detail_url = esc(row.get("詳細URL", ""))
        link = f'<a href="{detail_url}" target="_blank">詳細</a>' if detail_url else ""
        from urllib.parse import quote
        property_name = str(row.get("物件名", "")).strip()

        map_link = (
            f'<a href="all_properties_map.html?property={quote(property_name)}">'
            'マップで見る'
            '</a>'
        )
        simulation_path = simulation_link_map.get(property_name, "")

        simulation_link = (
            f'<a href="{esc(simulation_path)}">営業SIM</a>'
            if simulation_path
            else ""
        )

        rows.append(f"""
        <tr>
            <td>{esc(row.get("seongsu_rank"))}</td>
            <td class="star">{esc(row.get("seongsu_fit_stars"))}</td>
            <td>{esc(row.get("seongsu_fit_score"))}</td>
            <td>{esc(row.get("物件名"))}</td>
            <td>{esc(row.get("所在地"))}</td>
            <td>{esc(row.get("坪数_補正"))}</td>
            <td>{esc(row.get("家賃"))}</td>
            <td>{esc(row.get("駐車場判定"))}</td>
            <td>{esc(row.get("seongsu_fit_type"))}</td>
            <td>{link}</td>
            <td>{simulation_link}</td>
            <td>{map_link}</td>
        </tr>

        <tr class="comment-row">
            <td></td>
            <td colspan="10">{esc(row.get("seongsu_fit_comment"))}</td>
        </tr>
        """)

    return "\n".join(rows)


def make_star_sections(df, simulation_link_map):
    sections = []

    for star in STAR_ORDER:
        part = df[df["seongsu_fit_stars"] == star].copy()
        if part.empty:
            continue

        sections.append(f"""
        <details class="star-section" {"open" if star in ["★★★★★", "★★★★☆"] else ""}>
            <summary>
                <span class="summary-title">{star}</span>
                <span class="summary-sub">{len(part)}件</span>
            </summary>

            <table>
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>星</th>
                        <th>スコア</th>
                        <th>物件名</th>
                        <th>所在地</th>
                        <th>坪数</th>
                        <th>家賃</th>
                        <th>駐車場</th>
                        <th>タイプ</th>
                        <th>詳細</th>
                        <th>営業SIM</th>
                    </tr>
                </thead>
                <tbody>
                    {make_property_table(part, simulation_link_map)}
                </tbody>
            </table>
        </details>
        """)

    return "\n".join(sections)


def main():
    df = pd.read_csv(INPUT_CSV)
    simulation_link_map = load_simulation_link_map()

    df = df.sort_values("seongsu_fit_score", ascending=False).reset_index(drop=True)

    html_text = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>実装可能ランキング</title>
<style>
body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f5f2ed;
    color: #24211d;
}}

header {{
    padding: 32px 40px;
    background: #1f1d1a;
    color: #fff;
}}

header h1 {{
    margin: 0 0 12px;
    font-size: 28px;
}}

header p {{
    margin: 0;
    color: #d8d1c7;
    line-height: 1.7;
}}

main {{
    padding: 28px 40px 60px;
}}

.section {{
    margin-bottom: 32px;
}}

.section h2 {{
    font-size: 22px;
    margin-bottom: 16px;
}}

.summary-grid {{
    display: grid;
    grid-template-columns: repeat(5, minmax(140px, 1fr));
    gap: 16px;
}}

.summary-card {{
    background: #fff;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}}

.summary-star {{
    font-size: 22px;
    margin-bottom: 12px;
}}

.summary-count {{
    font-size: 28px;
    font-weight: 700;
}}

.summary-rate {{
    margin-top: 4px;
    color: #777;
}}

.insight-box {{
    background: #fff;
    border-radius: 16px;
    padding: 22px 26px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}}

.insight-box li {{
    margin: 8px 0;
}}

.star-section {{
    background: #fff;
    border-radius: 16px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    overflow: hidden;
}}

.star-section summary {{
    cursor: pointer;
    padding: 20px 24px;
    font-size: 18px;
    font-weight: 700;
    background: #fff;
}}

.summary-title {{
    margin-right: 12px;
}}

.summary-sub {{
    color: #777;
    font-size: 15px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}

th {{
    background: #eee7dc;
    text-align: left;
    padding: 10px;
    white-space: nowrap;
}}

td {{
    border-top: 1px solid #eee;
    padding: 10px;
    vertical-align: top;
}}

.star {{
    white-space: nowrap;
    font-size: 16px;
}}

.comment-row td {{
    background: #faf8f4;
    color: #5b554c;
    line-height: 1.6;
}}

a {{
    color: #6b4f2a;
    font-weight: 700;
}}

@media (max-width: 900px) {{
    header, main {{
        padding-left: 18px;
        padding-right: 18px;
    }}

    .summary-grid {{
        grid-template-columns: 1fr 1fr;
    }}

    table {{
        font-size: 12px;
    }}
}}
</style>
</head>
<body>
<header>
    <h1>実装可能ランキング</h1>
    <p>
        高松市内の店舗・事業用賃貸物件216件を対象に、韓国ソンス風フルーツカフェをどの程度現実的に実装できるかをランキング化したPhase5用ダッシュボード。
        個別物件の詳細確認ではなく、ブランド実装可能性の俯瞰と出店戦略のブラッシュアップを目的とする。
    </p>
</header>

<main>
    <section class="section">
        <h2>星別ランキング集計</h2>
        <div class="summary-grid">
            {make_summary_cards(df)}
        </div>
    </section>

    <section class="section">
        <h2>高スコア物件に共通する条件</h2>
        <div class="insight-box">
            {make_insight(df)}
        </div>
    </section>

    <section class="section">
        <h2>星ランク別候補物件リスト</h2>
        {make_star_sections(df, simulation_link_map)}
    </section>
</main>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html_text, encoding="utf-8")

    print(f"[LOAD] {INPUT_CSV}")
    print(f"[SAVE] {OUTPUT_HTML}")
    print(f"[ROWS] {len(df)}")


if __name__ == "__main__":
    main()

