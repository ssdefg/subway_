import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. 전역 UI/UX 설정 (사진의 깔끔한 스타일 반영)
st.set_page_config(page_title="주거-교통 비용의 역설", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e9ecef; }
    .sql-container { background-color: #262730; color: #ffffff; padding: 15px; border-radius: 8px; font-family: monospace; }
    .paradox-warning { background-color: #fffde7; border-left: 5px solid #fbc02d; padding: 15px; border-radius: 5px; color: #856404; font-weight: 500; }
    .insight-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 5px solid #2196f3; color: #0d47a1; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터셋 및 분석 상수
MIN_WAGE_2026 = 10320
HOUSING_SAVING = 568876
TRANSIT_COST = 56000

# 소득 구간별 마이크로데이터 (사진 2의 데이터 기반)
income_df = pd.DataFrame({
    '소득 구간': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    '왕복 통근 시간(분)': [94.5, 88.2, 85.0, 82.1, 80.5, 78.1, 78.0, 79.2, 80.1, 80.7],
    '피로도 점수': [2.27, 2.15, 2.05, 1.95, 1.85, 1.80, 1.75, 1.70, 1.68, 1.65],
    '삶의 만족도': [1.80, 1.90, 2.10, 2.20, 2.30, 2.45, 2.55, 2.70, 2.85, 2.93]
})

# ---------------------------------------------------------
# SECTION 01: KPI 시뮬레이션 (사진 1 반영)
# ---------------------------------------------------------
st.markdown("### :orange[서울 강남구 → 수원 영통구 이주 시 시뮬레이션]")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

# 선택된 소득 1구간(최악의 케이스) 기준 시간 비용 계산
time_opp_cost = (94.5 * 20 * MIN_WAGE_2026) / 60
net_benefit = HOUSING_SAVING - TRANSIT_COST - time_opp_cost

with kpi_col1:
    st.metric("월 주거비 절감액 (A)", f"+{HOUSING_SAVING:,}원")
with kpi_col2:
    st.metric("추가 교통비 (B)", f"-{TRANSIT_COST:,}원")
with kpi_col3:
    st.metric("시간 기회비용 (C)", f"-{int(time_opp_cost):,}원")
with kpi_col4:
    st.metric("최종 실질 이득 (A-B-C)", f"{int(net_benefit):,}원", f"↑ {int(net_benefit/HOUSING_SAVING*100)}% 잔존")

# ---------------------------------------------------------
# SECTION 02: 소득 계층별 이동의 차별화 (사진 2 반영)
# ---------------------------------------------------------
st.divider()
st.markdown("### ⚖️ 소득 계층별 이동의 차별화")

# 사진 2의 그라데이션 및 스타일 구현
fig_income = px.bar(
    income_df, x='소득 구간', y='왕복 통근 시간(분)',
    color='왕복 통근 시간(분)',
    color_continuous_scale=['#ffede0', '#e31a1c', '#800026'], # 사진과 유사한 레드 계열 그라데이션
    text_auto='.1f'
)
fig_income.update_layout(
    yaxis=dict(range=[0, 105], title="왕복 통근 시간(분)"),
    xaxis=dict(tickmode='linear', title="소득 구간"),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    height=500
)
st.plotly_chart(fig_income, use_container_width=True)

# [고도화 요구사항: SQL Code View]
with st.expander("🔍 SQL Code View: 소득 계층별 통근시간 분석 쿼리"):
    st.code("""
-- [쿼리] 경기도 거주 서울 통근 근로자 한정 소득별 통근시간 추출
SELECT 가구총소득구간코드 as 소득_구간, 
       ROUND(AVG(주행동시간량_출근 + 주행동시간량_퇴근), 1) as 왕복통근시간
FROM time_budget_survey
WHERE 행정구역 = '경기도' AND 목적지_시도 = '서울'
GROUP BY 가구총소득구간코드
ORDER BY 소득_구간 ASC;
    """, language='sql')

# ---------------------------------------------------------
# SECTION 03: 통근 시간과 웰빙 & 피로도 역설 (사진 3 반영)
# ---------------------------------------------------------
st.divider()
st.markdown("### 🧠 통근 시간과 웰빙의 역비례 관계 및 피로도 역설")

# 사진 3의 노란색 경고창(Warning Box) 구현
st.markdown("""
    <div class='paradox-warning'>
        ⚠️ <b>피로도 역설 탐지:</b> 소득 1구간의 피로도 지표(2.27)가 소득 10구간보다 높은 것은 낮은 피로를 의미하지 않습니다. 
        이는 생계형 절박함과 긴 통근 시간 중 발생하는 '보상적 수면'이 데이터에 반영된 결과입니다.
    </div>
    """, unsafe_allow_html=True)

st.write("") # 간격 조절

# 사진 3의 선형 차트 구현
fig_wellbeing = go.Figure()
fig_wellbeing.add_trace(go.Scatter(
    x=income_df['왕복 통근 시간(분)'], y=income_df['삶의 만족도'],
    name='삶의 만족도', line=dict(color='#3498db', width=3), marker=dict(size=8)
))
fig_wellbeing.add_trace(go.Scatter(
    x=income_df['왕복 통근 시간(분)'], y=income_df['피로도 점수'],
    name='피로도 점수', line=dict(color='#f1c40f', width=3, dash='dot'), marker=dict(size=8)
))

fig_wellbeing.update_layout(
    xaxis_title="왕복 통근 시간 (분)",
    yaxis_title="점수 (1점에 가까울수록 악화)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    height=500
)
st.plotly_chart(fig_wellbeing, use_container_width=True)

# 사진 3의 하단 인사이트 박스 구현
st.markdown("""
    <div class='insight-box'>
        💡 <b>데이터 인사이트:</b> 주거비 절감액의 최대 64%가 통근 시간의 기회비용으로 소멸됩니다. 
        이는 단순한 거주지 이동이 아니라 '시간 주권'의 저당을 의미합니다.
    </div>
    """, unsafe_allow_html=True)

with st.expander("🔍 SQL Code View: 통근 시간-웰빙 상관관계 분석 쿼리"):
    st.code("""
-- [쿼리] 통근 시간량에 따른 주관적 피로도 및 삶의 만족도 추출
SELECT ROUND(주행동시간량_출근 + 주행동시간량_퇴근, 0) as 통근시간,
       AVG(피곤함정도코드) as 평균_피로도,
       AVG(삶만족도코드) as 평균_만족도
FROM time_budget_survey
GROUP BY 통근시간
HAVING COUNT(*) > 30
ORDER BY 통근시간 ASC;
    """, language='sql')

# ---------------------------------------------------------
# SECTION 04: 비용-편익 폭포수 차트 (추가된 분석 고도화)
# ---------------------------------------------------------
st.divider()
st.markdown("### 📊 회계적 착시를 깨는 실질 이득 구조 (Waterfall)")

fig_wf = go.Figure(go.Waterfall(
    orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["주거비 절감(+)", "교통비 증분(-)", "시간 가치 손실(-)", "실질 이득"],
    y = [HOUSING_SAVING, -TRANSIT_COST, -time_opp_cost, net_benefit],
    textposition = "outside",
    text = [f"+{HOUSING_SAVING:,}", f"-{TRANSIT_COST:,}", f"-{int(time_opp_cost):,}", f"={int(net_benefit):,}"],
    connector = {"line":{"color":"#64748B"}},
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db"}}
))
fig_wf.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=500)
st.plotly_chart(fig_wf, use_container_width=True)
