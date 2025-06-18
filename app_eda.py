import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Population Trends 데이터셋 출처 및 소개
        st.markdown("""
        ---
        **Population Trends 데이터셋**  
        - 설명: 연도별·지역별 인구 및 출생·사망 정보를 담고 있는 데이터셋  
        - 주요 변수:  
          - `연도`: 연도  
          - `지역`: 지자체 이름  
          - `인구`: 해당 연도의 인구 수  
          - `출생아수(명)`: 해당 연도의 출생 수  
          - `사망자수(명)`: 해당 연도의 사망 수  
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("분석할 population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        # ----- 기본 전처리 -----
        # '세종' 지역의 모든 '-' 결측치를 0으로 치환
        sejong_mask = df['지역'] == '세종'
        df.loc[sejong_mask] = df.loc[sejong_mask].replace('-', 0)
        # 숫자형 변환
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # ----- 전처리 후 요약 분석 -----
        st.header("데이터프레임 구조 (df.info())")
        buf = io.StringIO()
        df.info(buf=buf)
        st.text(buf.getvalue())

        st.header("기초 통계량 (df.describe())")
        st.dataframe(df.describe())


        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:
            st.header("1. 기초 통계")
            st.subheader("데이터 정보")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("기초 통계량")
            st.dataframe(df.describe())

            st.subheader("결측치 및 중복 확인")
            missing = df.isnull().sum()
            st.bar_chart(missing)

            duplicates = df.duplicated().sum()
            st.write(f"- 중복 행 개수: {duplicates}개")

        # 2. 연도별 추이
        with tabs[1]:
            st.header("2. Yearly Population Trend")
            national_df = df[df['지역'] == '전국'][['연도', '인구', '출생아수(명)', '사망자수(명)']]
            national_df = national_df.sort_values('연도')

            years = national_df['연도'].values
            population = national_df['인구'].values

            # Plot historical trend
            fig, ax = plt.subplots()
            ax.plot(years, population, marker='o', linestyle='-')
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            # Predict 2035 population using recent 3-year net change
            recent = national_df.tail(3)
            net_changes = recent['출생아수(명)'] - recent['사망자수(명)']
            avg_net = net_changes.mean()
            last_year = int(years[-1])
            last_pop = int(population[-1])
            delta_years = 2035 - last_year
            predicted_pop_2035 = last_pop + avg_net * delta_years

            # Plot prediction
            ax.scatter(2035, predicted_pop_2035, color='red')
            ax.text(2035, predicted_pop_2035, f"2035: {int(predicted_pop_2035):,}",
                    va='bottom', ha='right')

            st.pyplot(fig)


        # 3. 지역별 분석
        with tabs[2]:
            st.header("3. Region-wise Population Change")

            # Exclude '전국' and map Korean region names to English
            region_map = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
                '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
                '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
            }
            recent_year = df['연도'].max()
            past_year = recent_year - 5

            region_df = df[df['지역'] != '전국']
            pop_first = region_df[region_df['연도'] == past_year][['지역','인구']].set_index('지역')
            pop_last  = region_df[region_df['연도'] == recent_year][['지역','인구']].set_index('지역')

            # Calculate absolute change
            change = (pop_last['인구'] - pop_first['인구']).dropna()
            change_df = change.reset_index().rename(columns={0:'change'}) if isinstance(change, pd.Series) else change.reset_index(name='change')
            change_df['change_thousand'] = change_df['change'] / 1000
            change_df['region_en'] = change_df['지역'].map(region_map)
            change_df = change_df.sort_values('change_thousand', ascending=False)

            # Plot absolute change
            fig, ax = plt.subplots()
            sns.barplot(x='change_thousand', y='region_en', data=change_df, ax=ax)
            for i, v in enumerate(change_df['change_thousand']):
                ax.text(v, i, f"{v:.1f}", va='center')
            ax.set_title("5-Year Population Change by Region")
            ax.set_xlabel("Change (Thousands)")
            ax.set_ylabel("")
            st.pyplot(fig)
            st.write("This chart shows the absolute population change over the last five years for each region (in thousands). Regions are sorted from highest to lowest change.")

            # Calculate percentage change
            pct_change = ((pop_last['인구'] - pop_first['인구']) / pop_first['인구'] * 100).dropna()
            pct_df = pct_change.reset_index().rename(columns={0:'pct_change'}) if isinstance(pct_change, pd.Series) else pct_change.reset_index(name='pct_change')
            pct_df['region_en'] = pct_df['지역'].map(region_map)
            pct_df = pct_df.sort_values('pct_change', ascending=False)

            # Plot percentage change
            fig2, ax2 = plt.subplots()
            sns.barplot(x='pct_change', y='region_en', data=pct_df, ax=ax2)
            for i, v in enumerate(pct_df['pct_change']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("5-Year Population Change Rate by Region")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("")
            st.pyplot(fig2)
            st.write("This chart displays the percentage population change relative to the population five years ago for each region. Regions are sorted from highest to lowest rate.")


        # 4. 변화량 분석
        with tabs[3]:
            st.header("4. Top 100 Population Changes")
            # Exclude nationwide data
        df_change = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
        # Compute year-over-year difference
        df_change['change'] = df_change.groupby('지역')['인구'].diff()
        df_change = df_change.dropna()

        # Select top 100 cases by absolute change
        top100 = df_change.sort_values('change', ascending=False).head(100)[['연도', '지역', 'change']]
        # Format numbers with thousand separators
        top100['change'] = top100['change'].astype(int).map(lambda x: f"{x:,}")

        # Style with color gradient: increases in blue, decreases in red
        styled = top100.style.background_gradient(cmap='RdBu', subset=['change'])

        # Display table
        st.dataframe(styled)
        st.write("Top 100 year-over-year population changes across regions (excluding nationwide). Blue indicates positive growth, red indicates decline.")

        # 5. 시각화
        with tabs[4]:
            # 5. Stacked Area Chart for Population by Region
            st.header("5. Population by Region Over Years")

            # Exclude nationwide and pivot
            subset = df[df['지역'] != '전국'][['연도', '지역', '인구']]
            pivot = subset.pivot(index='연도', columns='지역', values='인구')

            # Map Korean region names to English
            region_map = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
                '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
                '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
            }
            pivot.rename(columns=region_map, inplace=True)

            # Prepare colors
            colors = sns.color_palette('tab20', n_colors=pivot.shape[1])

            # Plot stacked area
            fig, ax = plt.subplots(figsize=(10, 6))
            pivot.plot.area(ax=ax, color=colors)
            ax.set_title("Population Trends by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig)

            # Optional: Heatmap visualization
            st.header("Population Heatmap by Region and Year")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.heatmap(pivot.T, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Population'})
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Region")
            st.pyplot(fig2)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()