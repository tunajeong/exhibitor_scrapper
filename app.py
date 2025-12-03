import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="MICE Exhibition Scraper", page_icon="exhibition", layout="wide")

st.title("🏛️ 범용 전시회 참가업체 스크래퍼")
st.markdown("""
이 도구는 전시회 웹사이트에서 참가업체 목록과 품목을 수집합니다.
**사이트마다 구조가 다르므로**, 개발자 도구(F12)를 통해 데이터의 위치(CSS Selector)를 확인하여 입력해야 합니다.
""")

# --- 2. 사용자 입력 사이드바 ---
with st.sidebar:
    st.header("설정 (Settings)")
    target_url = st.text_input("대상 URL", value="https://www.kes.org/kor/search/company_list.asp?admission=2025")
    
    st.info("아래 선택자(Selector)는 크롬 개발자 도구에서 'Copy Selector' 기능을 활용하세요.")
    
    # KES 예시를 위한 기본값 설정 (실제 사이트 구조에 맞춰 조정 필요할 수 있음)
    container_selector = st.text_input("1. 업체 목록 컨테이너 (반복되는 요소)", value="table.tbl_list tbody tr")
    name_selector = st.text_input("2. 업체명 위치 (컨테이너 내부)", value="td.al_left a")
    item_selector = st.text_input("3. 전시 품목 위치 (컨테이너 내부)", value="td.al_left") 
    
    start_scraping = st.button("데이터 수집 시작", type="primary")

# --- 3. 스크래핑 로직 ---
def scrape_data(url, container_sel, name_sel, item_sel):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # 오류 발생 시 예외 처리
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 반복되는 컨테이너(행) 찾기
        containers = soup.select(container_sel)
        
        data_list = []
        
        progress_bar = st.progress(0)
        total = len(containers)
        
        for idx, item in enumerate(containers):
            # 진행률 업데이트
            progress_bar.progress((idx + 1) / total)
            
            try:
                # 업체명 추출
                name_el = item.select_one(name_sel)
                name = name_el.get_text(strip=True) if name_el else "N/A"
                
                # 품목 추출 (보통 업체명과 같은 셀에 있거나 다른 셀에 있음, 여기서는 단순 텍스트 추출 예시)
                # 실제 KES 사이트는 구조가 복잡할 수 있어, 텍스트 정제가 필요할 수 있음
                product_el = item.select_one(item_sel)
                product = product_el.get_text(strip=True) if product_el else "N/A"

                # 데이터 정제 (업체명과 품목이 겹치는 경우 등을 위한 간단한 처리)
                if name in product:
                    product = product.replace(name, "").strip()

                data_list.append({
                    "업체명": name,
                    "전시품목/내용": product,
                    "비고": "추출 성공"
                })
            except Exception as e:
                continue
                
        return pd.DataFrame(data_list)

    except Exception as e:
        st.error(f"스크래핑 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# --- 4. 메인 실행 화면 ---
if start_scraping:
    if not target_url or not container_selector:
        st.warning("URL과 컨테이너 선택자를 입력해주세요.")
    else:
        with st.spinner(f"'{target_url}'에서 데이터를 가져오는 중입니다..."):
            df = scrape_data(target_url, container_selector, name_selector, item_selector)
            
            if not df.empty:
                st.success(f"총 {len(df)}개의 데이터를 성공적으로 수집했습니다!")
                st.dataframe(df, use_container_width=True)
                
                # CSV 다운로드 버튼
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV로 다운로드",
                    data=csv,
                    file_name='exhibition_data.csv',
                    mime='text/csv',
                )
            else:
                st.warning("데이터를 찾지 못했습니다. 선택자(Selector)가 올바른지 확인해주세요.")

# --- 5. 사용 가이드 (팁) ---
st.markdown("---")
with st.expander("🔍 선택자(Selector) 찾는 법 (필독)"):
    st.write("""
    1. 크롬 브라우저에서 대상 전시회 사이트를 엽니다.
    2. 수집하고 싶은 데이터(예: 업체명) 위에서 **우클릭 -> 검사(Inspect)**를 누릅니다.
    3. 개발자 도구(Elements 패널)에서 해당 태그가 하이라이트됩니다.
    4. 해당 태그 위에서 **우클릭 -> Copy -> Copy selector**를 클릭합니다.
    5. 복사된 값을 위 입력창에 붙여넣습니다.
    """)
