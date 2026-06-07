import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3

# [설정] 페이지 구성
st.set_page_config(page_title="Housing-Transit Paradox", layout="wide")

# [상수] 2026년 법정 최저임금
MIN_WAGE_2026 = 10320 

# [1] 데이터 로딩 및 SQLite 연동
@st.cache_resource
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    # 소득 구간별 실증 데이터 (경기도 거주 서울 통근자 한정)
    cursor.execute('''
        CREATE TABLE commute_data (
            income_level INTEGER,
            region_type TEXT,
            commute_time REAL,
            fatigue REAL,
            satisfaction REAL
        )
    ''')
    
    # 실증 데이터 삽입 (Section 2 기반)
    data = [
        # 경기-서울 한정 데이터 (평균의 함정 해체)
        (1, 'Gyeonggi-Seoul', 94.5, 2.27, 1.8),
        (2, 'Gyeonggi-Seoul', 90.0, 2.15, 1.9),
        (3, 'Gyeonggi-Seoul', 85.0, 2.05, 2.0),
        (4, 'Gyeonggi-Seoul', 82.0, 1.95, 2.1),
        (5, 'Gyeonggi-Seoul', 80.0, 1.85, 2.2),
        (6, 'Gyeonggi-Seoul', 78.1, 1.80, 2.3),
        (7, 'Gyeonggi-Seoul', 78.0, 1.75, 2.4),
        (8, 'Gyeonggi-Seoul', 79.0, 1.70, 2.5),
        (9, 'Gyeonggi-Seoul', 80.0, 1.68, 2.7),
        (10, 'Gyeonggi-Seoul', 80.7, 1.65, 2.93),
        # 전국 평균 데이터 (평균의 함정 예시)
        *[ (i, 'National', 42.0, 1.5, 2.5) for i in range(1, 11) ]
    ]
    cursor.executemany('INSERT INTO commute_data VALUES (?,?,?,?,?)', data)
    return conn

conn = init_db()

# [2] 사이드바 및 필터 설계
st.sidebar.title("⚙️ 분석 컨트롤 타워")
region_filter = st.sidebar.selectbox("행정구역 필터", ["경기도 거주 서울 통근자", "전국 평균 (평균의 함정)"])
region_key = "Gyeonggi-Seoul" if region_filter == "경기도 거주 서울 통근자" else "National"

income_slider = st.sidebar.select_slider(
    "가구 소득 구간 선택", 
    options=list(range(1, 11)), 
    value=1,
    help="소득 구간별 차별적 시간 빈곤을 확인하세요."
)

st.sidebar.divider()
st.sidebar.markdown(f"**기준 시점:** 2026년 가상 시나리오\n\n**적용 최저임금:** {MIN_WAGE_2026:,}원")

# [3] 데이터 쿼리 및 연산
query = f"SELECT * FROM commute_data WHERE region_type = '{region_key}'"
df = pd.read_sql(query, conn)
selected_data = df[df['income_level'] == income_slider].iloc[0]

# KPI 연산 로직
housing_saving = 568876 # 데이터 2 기반
transit_cost = 56000    # 데이터 3 기반 (강남역 목적지)
time_value_loss = (selected_data['commute_time'] * 20 * MIN_WAGE_2026) / 60
net_benefit = housing_saving - transit_cost - time_value_loss

# [4] 대시보드 렌더링 - 상단 KPI
st.title("🏠 주거-교통 비용의 역설 대시보드")
st.markdown("#### :orange[서울 강남구 → 수원 영통구 이주 시 시뮬레이션]")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("월 주거비 절감액 (A)", f"+{housing_saving:,}원")
kpi2.metric("추가 교통비 (B)", f"-{transit_cost:,}원", delta_color="inverse")
kpi3.metric("시간 기회비용 (C)", f"-{int(time_value_loss):,}원", delta_color="inverse")

benefit_color = "normal" if net_benefit > 0 else "inverse"
kpi4.metric("최종 실질 이득 (A-B-C)", f"{int(net_benefit):,}원", 
           delta=f"{int(net_benefit/housing_saving*100)}% 잔존", delta_color=benefit_color)

st.divider()

# [5] 메인 차트 영역
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("📉 재무적 잠식 과정 (Waterfall)")
    fig_waterfall = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["주거비 절감", "교통비 증분", "시간 가치 손실", "최종 실질 이득"],
        y = [housing_saving, -transit_cost, -time_value_loss, net_benefit],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        increasing = {"marker":{"color": "#2ecc71"}},
        decreasing = {"marker":{"color": "#e74c3c"}},
        totals = {"marker":{"color": "#3498db"}}
    ))
    fig_waterfall.update_layout(showlegend=False, height=450)
    st.plotly_chart(fig_waterfall, use_container_width=True)

with col_right:
    st.subheader("⚖️ 소득 계층별 이동의 차별화")
    fig_bar = px.bar(
        df, x='income_level', y='commute_time',
        labels={'income_level': '소득 구간', 'commute_time': '왕복 통근 시간(분)'},
        color='commute_time', color_continuous_scale='Reds'
    )
    # 강조 표시
    fig_bar.add_shape(type="line", x0=income_slider-0.5, x1=income_slider-0.5, y0=0, y1=100, line=dict(color="Yellow", width=3))
    fig_bar.update_layout(height=450)
    st.plotly_chart(fig_bar, use_container_width=True)

# [6] 하단 웰빙 상관관계 분석
st.divider()
st.subheader("🧠 통근 시간과 웰빙의 역비례 관계 및 피로도 역설")

fig_wellbeing = go.Figure()

# 만족도 축
fig_wellbeing.add_trace(go.Scatter(
    x=df['commute_time'], y=df['satisfaction'], name="삶의 만족도",
    line=dict(color="#3498db", width=4), mode='lines+markers'
))

# 피로도 축
fig_wellbeing.add_trace(go.Scatter(
    x=df['commute_time'], y=df['fatigue'], name="피로도 점수",
    line=dict(color="#f1c40f", width=4, dash='dot'), mode='lines+markers',
    hovertemplate="<b>%{text}</b><br>통근시간: %{x}분<br>피로도: %{y}",
    text=["피로도 역설: 생계형 절박함과 보상적 수면 반영" if x > 90 else "일반적 피로" for x in df['commute_time']]
))

fig_wellbeing.update_layout(
    xaxis_title="왕복 통근 시간 (분)",
    yaxis_title="점수 (1점에 가까울수록 악화)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500
)

# 소득 1구간 피로도 역설 강조를 위한 주석
if income_slider == 1 and region_key == "Gyeonggi-Seoul":
    st.warning("⚠️ **피로도 역설 탐지:** 소득 1구간의 피로도 지표(2.27)가 소득 10구간보다 높은 것은 낮은 피로를 의미하지 않습니다. 이는 생계형 절박함과 긴 통근 시간 중 발생하는 '보상적 수면'이 데이터에 반영된 결과입니다.")

st.plotly_chart(fig_wellbeing, use_container_width=True)

# 하단 정보
st.info("💡 **데이터 인사이트:** 주거비 절감액의 최대 64%가 통근 시간의 기회비용으로 소멸됩니다. 이는 단순한 거주지 이동이 아니라 '시간 주권'의 저당을 의미합니다.")