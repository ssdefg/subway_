import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. 전역 UI/UX 설정: 고대비 사이버 펑크 테마
st.set_page_config(page_title="Housing-Transit Paradox Analysis", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #0B0E14; color: #FFFFFF; }
# ---------------------------------------------------------
# [추가 코드] 사이버펑크 스타일 메인 타이틀 CSS (기존 <style> 태그 내부에 추가)
# ---------------------------------------------------------
"""
.main-title-container {
    padding: 20px 0 10px 0;
    border-bottom: 2px solid #30363D;
    margin-bottom: 35px;
}
.main-title {
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00F2FF 0%, #FF007F 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}
.main-subtitle {
    color: #8B949E;
    font-size: 1.1rem;
    margin-top: 8px;
    font-weight: 500;
}
"""

# ---------------------------------------------------------
# [추가 코드] 최상단 화면 출력부 (st.set_page_config 및 스타일 정의 바로 아래에 삽입)
# ---------------------------------------------------------
st.markdown("""
    <div class='main-title-container'>
        <div class='main-title'>Housing-Transit Paradox Analysis</div>
        <div class='main-subtitle'>서울의 주거비용과 경기도의 교통에 치이는 사람들</div>
    </div>
    """, unsafe_allow_html=True)    
    /* 고대비 KPI 카드 */
    .metric-container {
        background: #161B22; border-radius: 10px; padding: 25px;
        border: 1px solid #30363D; border-top: 4px solid #00F2FF;
        text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #00F2FF; }
    .metric-label { color: #8B949E; font-size: 1rem; margin-bottom: 10px; font-weight: 600; }
    
    /* 피로도 역설 경고창 */
    .paradox-warning {
        background-color: #2D1B2D; border: 1px solid #FF007F;
        padding: 20px; border-radius: 8px; color: #FFB3D9;
        margin: 20px 0; line-height: 1.6;
    }
    
    /* 데이터 인사이트 박스 */
    .insight-box {
        background-color: #0D1117; padding: 20px; border-radius: 10px;
        color: #00F2FF; border: 1px solid #30363D; font-weight: 500;
    }
    
    /* SQL Code Block 가독성 향상 */
    .stCodeBlock { border: 1px solid #30363D !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# 실증 분석 데이터 상수 정의
MIN_WAGE_2026 = 10320
HOUSING_SAVING = 568876
TRANSIT_EXTRA = 56000
TIME_COST = (94.5 / 60.0) * MIN_WAGE_2026 * 20
NET_BENEFIT = HOUSING_SAVING - TRANSIT_EXTRA - TIME_COST

# ---------------------------------------------------------
# 상단 KPI 시뮬레이션 (분석 결과 요약)
# ---------------------------------------------------------
st.markdown("### <span style='color:#F97316;'>서울 강남구 → 수원 영통구 이주 시 시뮬레이션 요약</span>", unsafe_allow_html=True)
kpi_cols = st.columns(4)
metrics = [
    ("월 주거비 절감액 (A)", f"+{HOUSING_SAVING:,}원", "#00F2FF"),
    ("추가 교통비 (B)", f"-{TRANSIT_EXTRA:,}원", "#FF007F"),
    ("시간 기회비용 (C)", f"-{int(TIME_COST):,}원", "#94A3B8"),
    ("최종 실질 이득 (A-B-C)", f"{int(NET_BENEFIT):,}원", "#00F2FF")
]
for i, (label, val, color) in enumerate(metrics):
    with kpi_cols[i]:
        st.markdown(f"<div class='metric-container' style='border-top-color:{color};'><div class='metric-label'>{label}</div><div class='metric-value' style='color:{color};'>{val}</div></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SECTION 01: 자산 진입 장벽 및 주거 고정비 분석
# ---------------------------------------------------------
st.divider()
st.subheader("01. 주거 고정비 분석_강남vs영통")
col_a1, col_a2 = st.columns([1.2, 1])

with col_a1:
    fig_rent = go.Figure(data=[
        go.Bar(name='강남구', x=['전세 평균', '월세 보증금'], y=[58037.5, 18746.0], marker_color='#00F2FF', textposition='auto'),
        go.Bar(name='수원 영통구', x=['전세 평균', '월세 보증금'], y=[27563.0, 5723.5], marker_color='#30363D', textposition='auto')
    ])
    fig_rent.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF", size=14), height=400, legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_rent, use_container_width=True)

with col_a2:
    st.markdown("""<div class='insight-box'><b>[초기 자산 장벽]</b> 전세 격차 <b>3.0억 원</b> 실증. 스스로의 근로 소득만으로 강남권에 주거 자리를 잡는 것이 원천적으로 불가능함.<br><br><b>[가처분 소득 잠식]</b> 영통 이주 시 월 고정 주거비 <b>56.9만 원</b> 절감. 이것이 청년들을 경기 외곽으로 밀어내는 '경제적 밀어내기 압력(Push Factor)'의 본질입니다.</div>""", unsafe_allow_html=True)

with st.expander("🔍 분석 SQL 원문 보기"):
    st.code("""SELECT '강남구' as 지역, COUNT(*) as 거래건수, 
       ROUND(AVG("보증금(만원)"), 1) as "평균 전세금 (만원)",
       ROUND(AVG("보증금(만원)") / 10000.0, 1) as "평균 전세금 (억원)"
FROM gangnam_rent
WHERE "전월세구분" = '전세' AND "전용면적(㎡)" <= 60

UNION ALL

SELECT '수원시 영통구' as 지역, COUNT(*) as 거래건수, 
       ROUND(AVG("보증금(만원)"), 1) as "평균 전세금 (만원)",
       ROUND(AVG("보증금(만원)") / 10000.0, 1) as "평균 전세금 (억원)"
FROM yeongtong_rent
WHERE "전월세구분" = '전세' AND "전용면적(㎡)" <= 60;

SELECT '강남구' as 지역, COUNT(*) as 거래건수, 
       ROUND(AVG("보증금(만원)"), 1) as "평균 월세보증금 (만원)",
       ROUND(AVG("월세금(만원)"), 1) as "평균 월세 (만원)"
FROM gangnam_rent
WHERE "전월세구분" = '월세' AND "전용면적(㎡)" <= 60

UNION ALL

SELECT '수원시 영통구' as 지역, COUNT(*) as 거래건수, 
       ROUND(AVG("보증금(만원)"), 1) as "평균 월세보증금 (만원)",
       ROUND(AVG("월세금(만원)"), 1) as "평균 월세 (만원)"
FROM yeongtong_rent
WHERE "전월세구분" = '월세' AND "전용면적(㎡)" <= 60;""", language="sql")

# ---------------------------------------------------------
# SECTION 02: 회계적 착시의 해체
# ---------------------------------------------------------
st.divider()
st.subheader("02. 주거와 교통의 트레이드오프")

fig_wf = go.Figure(go.Waterfall(
    orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["주거비 절감(+)", "교통비 증분(-)", "시간 가치 손실(-)", "실질 이득"],
    y = [HOUSING_SAVING, -TRANSIT_EXTRA, -TIME_COST, NET_BENEFIT],
    decreasing = {"marker":{"color":"#FF007F"}},
    increasing = {"marker":{"color":"#00F2FF"}},
    totals = {"marker":{"color":"#00F2FF"}}
))
fig_wf.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFFFFF", height=450)
st.plotly_chart(fig_wf, use_container_width=True)

with st.expander("🔍 분석 SQL 원문 보기"):
    st.code("""SELECT s."하차역 (광교역 승차 기준)" as 목적지_역, 
       s."신분당선 실제 요금 (원)" as 신분당선_요금, 
       st."수도권 표준요금 (원)" as 표준_요금,
       (s."신분당선 실제 요금 (원)" - st."수도권 표준요금 (원)") as "편도 운임 격차 (원)",
       s."월간 교통비 (원_20일 기준)" as 신분당선_월교통비,
       st."월간 교통비 (원_20일 기준)" as 표준_월교통비,
       (s."월간 교통비 (원_20일 기준)" - st."월간 교통비 (원_20일 기준)") as "월 누적 추가부담액 (원)"
FROM shinbundang_fare s
JOIN standard_fare st ON s."하차역 (광교역 승차 기준)" = st."하차역 (광교역 승차 기준)"
WHERE s."하차역 (광교역 승차 기준)" IN ('판교', '강남', '신사')
ORDER BY s."신분당선 실제 요금 (원)" ASC;

SELECT 
    ROUND(g_rent.avg_rent - y_rent.avg_rent, 0) as "① 월 주거비 절감액 (원)",
    (s."월간 교통비 (원_20일 기준)" - st."월간 교통비 (원_20일 기준)") as "② 신분당선 추가운임 (원)",
    ROUND((94.5 / 60.0) * 10320 * 20, 0) as "③ 통근 시간량 기회비용 (원)",
    ROUND((g_rent.avg_rent - y_rent.avg_rent) - (s."월간 교통비 (원_20일 기준)" - st."월간 교통비 (원_20일 기준)") - ((94.5 / 60.0) * 10320 * 20), 0) as "④ 최종 실질 이득 (원)"
FROM 
    (SELECT AVG("월세금(만원)") * 10000 as avg_rent FROM gangnam_rent WHERE "전월세구분" = '월세' AND "전용면적(㎡)" <= 60) g_rent,
    (SELECT AVG("월세금(만원)") * 10000 as avg_rent FROM yeongtong_rent WHERE "전월세구분" = '월세' AND "전용면적(㎡)" <= 60) y_rent,
    shinbundang_fare s
JOIN standard_fare st ON s."하차역 (광교역 승차 기준)" = st."하차역 (광교역 승차 기준)"
WHERE s."하차역 (광교역 승차 기준)" = '강남';""", language="sql")

# ---------------------------------------------------------
# SECTION 03: 이동의 계층화
# ---------------------------------------------------------
st.divider()
st.subheader("03. 이동의 계층화")
income_df = pd.DataFrame({'구간': [1,2,3,4,5,6,7,8,9,10], '시간': [94.5, 85.2, 82.1, 80.5, 79.5, 78.1, 78.0, 79.0, 80.0, 80.7]})

fig_strat = px.bar(income_df, x='구간', y='시간', color='시간', color_continuous_scale=['#FFEDD5', '#FB923C', '#B91C1C'])
fig_strat.update_layout(yaxis=dict(range=[70, 100], title="왕복 통근 시간(분)"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFFFFF")
st.plotly_chart(fig_strat, use_container_width=True)

with st.expander("🔍 분석 SQL 원문 보기"):
    st.code("""SELECT "가구총소득구간코드" as 소득_구간,
       COUNT(*) as 응답자수,
       ROUND(AVG("(주행동시간량_921) 출근" + "(주행동시간량_922) 퇴근"), 1) as "일평균 왕복통근시간 (분)",
       ROUND(AVG("피곤함정도코드"), 2) as "평균 피로도"
FROM time_budget
WHERE "행정구역시도코드" = 31 AND ("(주행동시간량_921) 출근" + "(주행동시간량_922) 퇴근") > 0
GROUP BY "가구총소득구간코드"
ORDER BY "가구총소득구간코드" ASC;""", language="sql")

# ---------------------------------------------------------
# SECTION 04: 통근 시간과 웰빙의 상관관계
# ---------------------------------------------------------
st.divider()
st.subheader("04. 통근 시간과 삶의 만족도 상관관계")

st.markdown("<div class='paradox-warning'>⚠️ <b>피로도 역설 탐지:</b> 소득 1구간의 피로도 지표(2.27)가 고소득층(1.65)보다 수치상 '덜 피곤함'을 보이는 현상은 생계형 절박함과 보상적 수면이 반영된 통계적 착시입니다. 본질은 길 위의 <b>94.5분</b>입니다.</div>", unsafe_allow_html=True)

wellbeing_df = pd.DataFrame({
    '시간': [8.0, 16.8, 34.1, 43.2, 78.1, 80.7, 94.5],
    '만족도': [2.30, 2.41, 2.54, 2.93, 2.60, 2.20, 1.85],
    '피로도': [4.0, 3.5, 2.8, 1.0, 1.75, 1.65, 2.27]
})

fig_wb = go.Figure()
fig_wb.add_trace(go.Scatter(x=wellbeing_df['시간'], y=wellbeing_df['만족도'], name='평균 삶의 만족도 (1=최악)', line=dict(color='#00F2FF', width=4), mode='lines+markers'))
fig_wb.add_trace(go.Scatter(x=wellbeing_df['시간'], y=wellbeing_df['피로도'], name='평균 피로도 점수 (1=최악)', line=dict(color='#FF007F', width=4, dash='dot'), mode='lines+markers'))
fig_wb.update_layout(xaxis_title="일 왕복 통근 시간 (분)", yaxis_title="점수", legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#FFFFFF", height=500)
st.plotly_chart(fig_wb, use_container_width=True)

with st.expander("🔍 분석 SQL 원문 보기"):
    st.code("""SELECT "피곤함정도코드" as 피로도_수준,
       COUNT(*) as 응답자수,
       ROUND(AVG("(주행동시간량_921) 출근" + "(주행동시간량_922) 퇴근"), 1) as "일평균 왕복통근시간 (분)", 
       ROUND(AVG("삶만족도코드"), 2) as "평균 삶의 만족도"
FROM time_budget
GROUP BY "피곤함정도코드"
ORDER BY "피곤함정도코드" ASC;""", language="sql")

st.markdown("<div class='insight-box' style='text-align:center;'>💡 <b>최종 분석 결론:</b> 주거비 절감액의 64%가 보이지 않는 시간 비용으로 소멸됩니다. 경기도 이주는 '시간 주권'의 저당입니다.</div>", unsafe_allow_html=True)
