import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Housing-Transit Paradox", layout="wide")

MIN_WAGE_2026 = 10320  # 2026 법정 최저임금 (가상 시나리오)

# ============================================================
# [1] DB SETUP — SQLite in-memory
#     배경: 실제 분석에 사용된 쿼리/결과를 UI에서 그대로 노출하기 위해
#     집계 결과를 테이블로 보관 (신뢰성 확인용 Code Snippet 영역에서 사용)
# ============================================================
@st.cache_resource
def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()

    # --- 전세 집계 결과 (소형 60㎡ 이하) ---
    cur.execute("""
        CREATE TABLE jeonse_summary (
            region TEXT, deal_count INTEGER, avg_deposit_eok REAL
        )
    """)
    cur.executemany(
        "INSERT INTO jeonse_summary VALUES (?,?,?)",
        [("강남구", 3765, 5.8), ("수원 영통구", 3368, 2.8)],
    )

    # --- 월세 집계 결과 (소형 60㎡ 이하) ---
    cur.execute("""
        CREATE TABLE wolse_summary (
            region TEXT, deal_count INTEGER,
            avg_deposit_man REAL, avg_rent_man REAL
        )
    """)
    cur.executemany(
        "INSERT INTO wolse_summary VALUES (?,?,?,?)",
        [("강남구", 5099, 18700, 125.1), ("수원 영통구", 2740, 5723, 68.2)],
    )

    # --- 신분당선 교통비 ---
    cur.execute("""
        CREATE TABLE transit_fare (
            route TEXT, fare INTEGER
        )
    """)
    cur.executemany(
        "INSERT INTO transit_fare VALUES (?,?)",
        [("신분당선 (영통→강남)", 3550), ("표준 운임", 2150)],
    )

    # --- 통근시간 ↔ 웰빙 (소득구간별, 경기-서울 통근자 한정) ---
    cur.execute("""
        CREATE TABLE commute_wellbeing (
            income_level INTEGER, commute_time REAL,
            fatigue REAL, satisfaction REAL
        )
    """)
    rows = [
        (1, 94.5, 2.27, 1.8), (2, 90.0, 2.15, 1.9), (3, 85.0, 2.05, 2.0),
        (4, 82.0, 1.95, 2.1), (5, 80.0, 1.85, 2.2), (6, 78.1, 1.80, 2.3),
        (7, 78.0, 1.75, 2.4), (8, 79.0, 1.70, 2.5), (9, 80.0, 1.68, 2.7),
        (10, 80.7, 1.65, 2.93),
    ]
    cur.executemany("INSERT INTO commute_wellbeing VALUES (?,?,?,?)", rows)

    # --- 통근시간 구간별 피로/만족 (시나리오 곡선) ---
    cur.execute("""
        CREATE TABLE fatigue_curve (
            commute_time REAL, fatigue_label TEXT, satisfaction REAL
        )
    """)
    cur.executemany(
        "INSERT INTO fatigue_curve VALUES (?,?,?)",
        [(8.0, "피로 없음", 2.30), (43.2, "매우 피곤함", 2.93),
         (94.5, "시간 빈곤 심화", 1.80)],
    )

    conn.commit()
    return conn


conn = init_db()

# ============================================================
# CBA 상수 (요구사항 3의 4단계 계산)
# ============================================================
HOUSING_SAVING = 568876   # ① 월 주거비 절감액
TRANSIT_COST = 56000      # ② 신분당선 추가 운임
TIME_COST = 325080        # ③ 통근 시간 기회비용 (왕복 94.5분 환산)
NET_BENEFIT = HOUSING_SAVING - TRANSIT_COST - TIME_COST  # ④ 187,796
EROSION_PCT = round((1 - NET_BENEFIT / HOUSING_SAVING) * 100)  # ≈ 67%

# 쿼리 문자열 (UI 노출용)
SQL_JEONSE = """-- [1] 전세 격차 (소형 60㎡ 이하)
SELECT '강남구' AS 지역, COUNT(*) AS 거래건수,
       ROUND(AVG(deposit)/100000000, 1) AS 평균보증금_억
FROM gangnam_rent
WHERE area_m2 <= 60 AND rent_type = '전세'
UNION ALL
SELECT '수원 영통구', COUNT(*),
       ROUND(AVG(deposit)/100000000, 1)
FROM yeongtong_rent
WHERE area_m2 <= 60 AND rent_type = '전세';"""

SQL_WOLSE = """-- [2] 월세 + 가처분소득 잠식 (소형 60㎡ 이하)
SELECT region, COUNT(*) AS 거래건수,
       ROUND(AVG(deposit)/10000) AS 평균보증금_만원,
       ROUND(AVG(monthly_rent)/10000, 1) AS 평균월세_만원
FROM rent_unified
WHERE area_m2 <= 60 AND rent_type = '월세'
GROUP BY region;"""

SQL_TRANSIT = """-- [3] 신분당선 운임 역설 (강남역 통근 기준)
SELECT route, fare,
       fare - (SELECT fare FROM transit_fare WHERE route='표준 운임')
         AS 편도격차
FROM transit_fare;"""

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("⚙️ 분석 컨트롤 타워")
income_slider = st.sidebar.select_slider(
    "가구 소득 구간 선택",
    options=list(range(1, 11)), value=1,
    help="소득 구간별 차별적 시간 빈곤을 확인하세요.",
)
st.sidebar.divider()
st.sidebar.markdown(
    f"**기준 시점:** 2026년 가상 시나리오\n\n"
    f"**적용 최저임금:** {MIN_WAGE_2026:,}원\n\n"
    f"**시간당 환산:** 왕복 94.5분 × {MIN_WAGE_2026:,}원 × 20일"
)

# ============================================================
# HEADER
# ============================================================
st.title("🏠 주거-교통 비용의 역설 대시보드")
st.markdown("#### :orange[서울 강남구 → 수원 영통구 이주 시뮬레이션 — '시간 주권'의 저당]")
st.divider()

# ============================================================
# [REQ 2] 주거비 격차 + 자산 진입 장벽
# ============================================================
st.header("① 주거비 격차와 청년층 자산 진입 장벽")
st.markdown(
    ":red[**Push Factor**] — 강남의 소형 주택 진입 비용은 청년층에게 "
    "사실상의 자산 장벽으로 작동한다. 전세 보증금 **3억 원** 격차, "
    "월세 **56.9만 원** 격차가 영통 이주를 강제하는 구조적 압력이다."
)

df_jeonse = pd.read_sql("SELECT * FROM jeonse_summary", conn)
df_wolse = pd.read_sql("SELECT * FROM wolse_summary", conn)

c1, c2, c3 = st.columns(3)
c1.metric("전세 보증금 격차", "3.0억 원", "강남 5.8억 vs 영통 2.8억", delta_color="inverse")
c2.metric("월세 격차", "56.9만 원/월", "강남 125.1 vs 영통 68.2", delta_color="inverse")
c3.metric("연간 가처분소득 확보", "+680만 원", "영통 이주 시", delta_color="normal")

bc1, bc2 = st.columns(2)
with bc1:
    st.subheader("전세 평균 보증금 (소형 60㎡↓)")
    fig_j = px.bar(
        df_jeonse, x="region", y="avg_deposit_eok", text="avg_deposit_eok",
        color="region", color_discrete_map={"강남구": "#e74c3c", "수원 영통구": "#3498db"},
        labels={"region": "", "avg_deposit_eok": "평균 보증금 (억 원)"},
    )
    fig_j.update_traces(texttemplate="%{text}억", textposition="outside")
    fig_j.update_layout(showlegend=False, height=360)
    st.plotly_chart(fig_j, use_container_width=True)

with bc2:
    st.subheader("월세 평균 (소형 60㎡↓)")
    fig_w = px.bar(
        df_wolse, x="region", y="avg_rent_man", text="avg_rent_man",
        color="region", color_discrete_map={"강남구": "#e74c3c", "수원 영통구": "#3498db"},
        labels={"region": "", "avg_rent_man": "평균 월세 (만 원)"},
    )
    fig_w.update_traces(texttemplate="%{text}만원", textposition="outside")
    fig_w.update_layout(showlegend=False, height=360)
    st.plotly_chart(fig_w, use_container_width=True)

# --- [REQ 1] SQL Code Snippet 토글 ---
with st.expander("🔍 분석 SQL 및 실증 데이터 결과 보기 (신뢰성 검증)"):
    t1, t2, t3 = st.tabs(["전세 격차", "월세 격차", "신분당선 운임"])
    with t1:
        st.code(SQL_JEONSE, language="sql")
        st.dataframe(df_jeonse.rename(columns={
            "region": "지역", "deal_count": "거래건수",
            "avg_deposit_eok": "평균 보증금(억)"}), use_container_width=True)
    with t2:
        st.code(SQL_WOLSE, language="sql")
        st.dataframe(df_wolse.rename(columns={
            "region": "지역", "deal_count": "거래건수",
            "avg_deposit_man": "평균 보증금(만)", "avg_rent_man": "평균 월세(만)"}),
            use_container_width=True)
    with t3:
        df_t = pd.read_sql("SELECT * FROM transit_fare", conn)
        st.code(SQL_TRANSIT, language="sql")
        st.dataframe(df_t.rename(columns={"route": "노선", "fare": "운임(원)"}),
                     use_container_width=True)

st.divider()

# ============================================================
# [REQ 3] CBA 전면 개편 — Balance Sheet + Waterfall
# ============================================================
st.header("② 주거-교통 비용-편익 분석 (회계적 착시의 해체)")
st.markdown(
    f"주거비만 아끼면 이득이라는 **회계적 착시**를 해체한다. "
    f"통근 시간 기회비용을 반영하면 실질 이득은 "
    f":red[**{EROSION_PCT}% 급감**]한다."
)

bal_col, water_col = st.columns([1, 1.1])

# --- Balance Sheet 테이블 ---
with bal_col:
    st.subheader("📋 Balance Sheet")
    balance = pd.DataFrame({
        "구분": ["① 월 주거비 절감액", "② 신분당선 추가운임",
                "③ 통근 시간 기회비용", "④ 최종 실질 이득"],
        "금액(원)": [HOUSING_SAVING, -TRANSIT_COST, -TIME_COST, NET_BENEFIT],
    })
    balance["표시"] = balance["금액(원)"].apply(lambda v: f"{v:+,}원")

    def color_rows(row):
        if row.name == 3:
            return ["background-color:#1f3a5f;font-weight:bold"] * len(row)
        if row["금액(원)"] > 0:
            return ["color:#2ecc71"] * len(row)
        return ["color:#e74c3c"] * len(row)

    st.dataframe(
        balance[["구분", "표시"]].style.apply(
            lambda r: color_rows(balance.loc[r.name]), axis=1
        ),
        use_container_width=True, hide_index=True,
    )
    st.metric("실질 이득 잔존율", f"{round(NET_BENEFIT/HOUSING_SAVING*100)}%",
              f"-{EROSION_PCT}% 잠식", delta_color="inverse")

# --- Waterfall ---
with water_col:
    st.subheader("📉 재무적 잠식 폭포수")
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["주거비 절감", "교통비 증분", "시간 기회비용", "최종 실질 이득"],
        y=[HOUSING_SAVING, -TRANSIT_COST, -TIME_COST, NET_BENEFIT],
        text=[f"+{HOUSING_SAVING:,}", f"-{TRANSIT_COST:,}",
              f"-{TIME_COST:,}", f"+{NET_BENEFIT:,}"],
        textposition="outside",
        connector={"line": {"color": "rgb(120,120,120)"}},
        increasing={"marker": {"color": "#2ecc71"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        totals={"marker": {"color": "#3498db"}},
    ))
    fig_wf.update_layout(showlegend=False, height=420, yaxis_title="원")
    st.plotly_chart(fig_wf, use_container_width=True)

st.info(
    f"💡 **인사이트:** 주거비 절감액의 약 **{EROSION_PCT}%**가 통근 시간 "
    f"기회비용으로 소멸된다. 단순 거주지 이동이 아니라 '시간 주권'의 저당이다."
)

st.divider()

# ============================================================
# 피로도 ↔ 만족도 라인 차트
# ============================================================
st.subheader("🧠 통근 시간 증가에 따른 피로도 급증 · 만족도 저하")
df_cw = pd.read_sql("SELECT * FROM commute_wellbeing ORDER BY commute_time", conn)

fig_wb = go.Figure()
fig_wb.add_trace(go.Scatter(
    x=df_cw["commute_time"], y=df_cw["satisfaction"], name="삶의 만족도",
    line=dict(color="#3498db", width=4), mode="lines+markers",
))
fig_wb.add_trace(go.Scatter(
    x=df_cw["commute_time"], y=df_cw["fatigue"], name="피로도 점수",
    line=dict(color="#f1c40f", width=4, dash="dot"), mode="lines+markers",
    text=["피로도 역설: 생계형 절박함·보상적 수면 반영" if x > 90 else "일반적 피로"
          for x in df_cw["commute_time"]],
    hovertemplate="<b>%{text}</b><br>통근시간: %{x}분<br>피로도: %{y}<extra></extra>",
))
# 선택 소득구간 강조
sel = df_cw[df_cw["income_level"] == income_slider]
if not sel.empty:
    fig_wb.add_vline(x=sel.iloc[0]["commute_time"], line=dict(color="orange", dash="dash"))
fig_wb.update_layout(
    xaxis_title="왕복 통근 시간 (분)", yaxis_title="점수 (1에 가까울수록 악화)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=460,
)
st.plotly_chart(fig_wb, use_container_width=True)

if income_slider == 1:
    st.warning(
        "⚠️ **피로도 역설:** 소득 1구간 피로도(2.27)가 10구간보다 높은 것은 "
        "낮은 피로가 아니라, 생계형 절박함과 긴 통근 중 '보상적 수면'이 "
        "데이터에 반영된 결과다."
    )
