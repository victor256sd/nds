#################################################################################
# Copyright (c) 2026 victor256sd
# All rights reserved.
#
# 07.05.2026 - Added sidebar with RAG information and links for more info.
# 06.14.2026 - Initiate New Dawn Specialists AI Assistant for investigative information.
#
#################################################################################
import streamlit as st
import streamlit_authenticator as stauth
import openai
from openai import OpenAI
import os
import time
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from cryptography.fernet import Fernet
import re
import requests
from datetime import datetime
from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

# Disable the button called via on_click attribute.
def disable_button():
    st.session_state.disabled = True        

def search_everything(query: str, page_size: int = 100) -> List:
    # Execute a NewsAPI Everything search.
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(
        NEWS_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI Error: {data}")

    return data.get("articles", [])

def deduplicate_articles(articles: List[Dict]) -> List:
    # Deduplicate by URL.
    seen_urls = set()
    unique_articles = []

    for article in articles:
        url = article.get("url")

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_articles.append(article)

    return unique_articles

def parse_date(article: Dict) -> datetime:
    # Parse NewsAPI publishedAt field.
    published = article.get("publishedAt")

    if not published:
        return datetime.min.replace(tzinfo=None)

    try:
        return datetime.fromisoformat(
            published.replace("Z", "+00:00")
        )
    except Exception:
        return datetime.min.replace(tzinfo=None)

def execute_primary_search() -> List:
    # Run the broad query.
    print("Running primary search...")

    articles = search_everything(PRIMARY_QUERY)

    print(f"Primary search returned {len(articles)} articles")

    return articles

def execute_fallback_searches() -> List:
    # Run targeted searches if primary search is too sparse.
    print("Running fallback searches...")

    articles = []

    for query in FALLBACK_QUERIES:
        try:
            print(f"Searching: {query}")
            results = search_everything(query, page_size=50)
            articles.extend(results)

        except Exception as e:
            print(f"Error with query {query}: {e}")

    print(f"Fallback searches returned {len(articles)} raw articles")

    return articles

def build_news_feed(final_count: int, threshold: int) -> List:
    # Strategy:
    # 1. Run one comprehensive query.
    # 2. Deduplicate.
    # 3. If fewer than threshold articles,
    #    execute targeted fallback searches.
    # 4. Deduplicate again.
    # 5. Sort newest first.
    # 6. Return top N.
    articles = execute_primary_search()
    articles = deduplicate_articles(articles)

    print(
        f"Unique articles after primary search: {len(articles)}"
    )

    if len(articles) < threshold:

        print(
            f"Only {len(articles)} articles found. "
            f"Threshold is {threshold}. "
            f"Using fallback searches."
        )

        fallback_articles = execute_fallback_searches()
        articles.extend(fallback_articles)
        articles = deduplicate_articles(articles)

        print(
            f"Unique articles after fallback: {len(articles)}"
        )

    articles.sort(
        key=parse_date,
        reverse=True
    )
    return articles[:final_count]

def print_results(results: List[Dict]):
    st.sidebar.markdown("## School Litigation News")

    for index, article in enumerate(results, start=1):
        description = article.get("description", "")
        st.sidebar.markdown(
            f"""
            **{index}. {article.get('title')}**<br>
            **Source:** {article.get('source', {}).get('name', 'Unknown')}  
            **Published:** {format_published_date(article.get('publishedAt'))}<br> 
            **URL:** {article.get('url')}  
            **Summary:** {description}
            """, unsafe_allow_html=True)

# Make user-friendly date/time from News API date/time.
def format_published_date(date_str):

    if not date_str:
        return "Unknown"

    try:
        # Convert UTC string from NewsAPI
        utc_dt = datetime.fromisoformat(
            date_str.replace("Z", "+00:00")
        )

        # Convert to local timezone
        local_dt = utc_dt.astimezone(
            ZoneInfo("America/Los_Angeles")
        )

        return local_dt.strftime(
            "%B %d, %Y, %I:%M %p %Z"
        )

    except Exception:
        return date_str

    # for index, article in enumerate(results, start=1):

    #     st.sidebar.markdown(f"\n**{index}**. {article.get('title')}")
    #     st.sidebar.markdown(
    #         f"**Source**: "
    #         f"{article.get('source', {}).get('name', 'Unknown')}"
    #     )
    #     st.sidebar.markdown(f"**Published**: {article.get('publishedAt')}")
    #     st.sidebar.markdown(f"**URL**: {article.get('url')}")

    #     description = article.get("description")
    #     if description:
    #         st.sidebar.markdown(f"**Summary**: {description}\n")

# Definitive CSS selectors for Streamlit 1.45.1+
# st.markdown("""
# <style>
#     div[data-testid="stToolbar"] {
#         display: none !important;
#     }
#     div[data-testid="stDecoration"] {
#         display: none !important;
#     }
#     div[data-testid="stStatusWidget"] {
#         visibility: hidden !important;
#     }
# </style>
# """, unsafe_allow_html=True)

# Injecting CSS to completely wipe out the embedded footer frame
hide_embedded_frame = """
    <style>
    /* Hides the 'Built with Streamlit' footer and fullscreen toolbar */
    footer {visibility: hidden;}
    [data-testid="stEmbedFooter"] {display: none !important;}
    </style>
"""
#     <style>
#     /* Hides the 'Built with Streamlit' footer and fullscreen toolbar */
#     footer {visibility: hidden;}
#     [data-testid="stEmbedFooter"] {display: none !important;}
#     header {visibility: hidden;}
#     </style>
# """
st.markdown(hide_embedded_frame, unsafe_allow_html=True)
# st.markdown(
# """
# <style>
# [data-testid="stSidebar"] [aria-expanded="true"] > div:first-child {
# width: 400px; /* Set your desired width */
# }
# [data-testid="stSidebar"] [aria-expanded="false"] > div:first-child {
# width: 400px; /* Set your desired width */
# margin-left: -400px; /* Adjust margin for collapsed state */
# }
# </style>
# """,
# unsafe_allow_html=True,
# )

# Load config file with user credentials.
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initiate authentication.
authenticator = stauth.Authenticate(
    config['credentials'],
)

# Call user login form.
result_auth = authenticator.login("main")
    
# If login successful, continue to aitam page.
if st.session_state.get('authentication_status'):
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state.get('name')}* !')

    # # Initialize chat history.
    # if "ai_response" not in st.session_state:
    #     st.session_state.ai_response = []
    
    # Model list, Vector store ID, assistant IDs (one for initial upload eval, 
    # the second for follow-up user questions).
    MODEL_LIST = ["gpt-4o-mini"] #, "gpt-4.1-nano", "gpt-4.1", "o4-mini"] "gpt-5-nano"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    VECTOR_STORE_ID = st.secrets["VECTOR_STORE_ID"]
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
    INSTRUCTION_ENCRYPTED = b'gAAAAABqLvNXffJPc0tzu6K-6ZKd1iWJRF0qiFgNIbswiGXAwpGE4IiI7D6uI2w6u9ZukKsQt1XefO9WRx34YjiRMi6IKZx7qYfg_YLtC08wGOF1r38aIeBjbB47cmrzMN2mwbNxanrvB_EWBf1wZMWXnYQN9-WNXHh6593If4G2F2cyHTJJRg21Sr52xa6uFfbZKE8on2uld0smSJu99ZqwJRgQ5X4DHhsH37DPb5jLHubUWrLxuFXeTV2oCp1cC6Qo38G62rgugqADzGLFXke5w3oq5NBw9K82ywoDNXpoWyZECZlp8TDwVATqY-9RsX60chRbNANr6ZYi8A1Fi_0oLFMFOlk3qQM8bxkXRdmJ8mOnWG1gT-tXMaF5exxD8ocOESg0QP2kffGe1N-V6cTcGX2rO3u2SVQDx_fDLg5bRU2RWyBjU3cKrHdlw9OMqQVbTNSucSWr1UALk3XHfAsVIuux7MrZ5MnldUq9XfqptMqajaW13up__npy8IjQTRv37gdWccMtYuluZ97bHwbwscSOWu6gKLSrRyPN8loEq2TWa82ylqpDPQumehISDTs6qJ1IoGhYeL3bqe4_HxwIftgM-Fn3B8Ouvj2_Yc5VGbJ6wqDAKeDoQ1Y0BmwfVP70IY9XYR463Vn-k7HStu02vuUaX0tb07sjesuKzOCoIaMh_RO-R4z7mTkwUiegBp7vyZtzD6PcwAClopeQjNaVBHJHBeq2S-CeJqF4Qhp_DzESNKLEpuB5ZYawMdNQdn71WUfwtlTI5KDyZJtF5t9lQHqOJDWmqanwYj8sXA006AzKGKU0yIOjHALDmuNj17frIer4ODG082HMWhfb3hRpQsxd27rLqRZlu2a4qWVt8VWL17SIdN5xAMsa-YasibhnjOGdCDzzXvlBXSOFfOUtFIZKX5_bdMnzaIJSdazhpelHDdRe3v-6NwxWpt1SnRxionuxxOPBYtA6aS1m6FOw9dwS12utg0h-8-T6-rRuTZIOT0LKyDyBPweO7YR6OSX-Ga3zktA4sbcHj8lvVhdm2BqpCTm6MvZQls_B3xAqPdl92WzBW4yREKk2nGJ1iC5XJUHyEus7UMoyKRuCv_Pj8WOXpYNnbdzqlhcukBB12ZIAll2lDzLsr4BgU-bcKUgoyJYROTtSCV8_qQfj-3ii86MB_wPfLeegsbmjTHtUl7ey3jexcLAVzTRp3n2PGidtQW0u29jcKfR2rDMHMvMBawWuNiH7TG5-O2IpQ7D_8QD0dyUw8Vzi2FegBUCgzb90RgCCuA8nLwskvgEuCzS106RUHgRpD9yAtbWZnjWpI1tfOdyWWZZYY9jTz5WxVa7vjlT6hJIK_zuLmZTS_Yl78Zr-HYhTw6SEaKbRqgfnb61sC3D6VVBYZD0wRzeh4cVdbcloa_ds3kVj01lfPpG3wsyTvwCF9xlTOBu4Ihy8RvRRvUaOSv9_HUz4y2ZG0c4BOZjHy98lskI50ETAbJJENLqtxq4F_r6xeT0Z3G990gCwtbzNNSDlit_sNZfAeKBdFTkdGxkxf1UWbTZEX_gRbD8GzxkyNO-GDnj_Z0jSJxRw5dzwtfzVtHufPgegSiiZ0i6eZMMw5_bgXrJq_KetOSHY68e-ENjIYkRiltSglYrFLVyzJk-o9i-juBYDzql-3uu_1xW3aRKyDhOLYZQ3DAEWPtxyyh0-6edGVhh4IuKcKi4LY5waU6xVEL2O-GM4rk5RnYoklsG77qA9aCodYgU6-hnuF8URaFhWaAvxTzgKcCV1z0YFd178TV3mkhX7Tygca0MQAuS5PV1y4iO3GOujBFakfG_IY2_dpVNIbCaecFCyQCZqRu82LHcHJfinGGga4SzvQn6EIWJu63vlhHrCmGHNYe0BTSHVRrS7xSEX0xFtaGMS-IPy02D8y4E3erUsr9_Wb6wH86l7Epti82wN_UBgt2SlFUGXS2N78BZtaKnz017hbc4MeBtNWrdDs53x6iiuUBuY47ZC59-dCDZ9GgquQD-pMgZR3gR4dc9xhJfa7qABNevD2jzrPyCXHp9OY7lwVIDyTQORRUYSpSo6OwopT24_uL47jyNmwfOAOHXbs9wSZmfJuKc5YgCbTjrwlN7QuQ4i5VNWucY5po2ic0FUVDyq9QirtFpkoL_g-ykHzbXLZWW_uZKwRH-1tjaalSk1X73xdcd282kDLL5dQ8y-I_rNLo4Rh291gHdgG5bWNLx_lUJB62heP-7mkFncbyYRa7PPuHNEtdCCoTTJ3ujCujZBPdG8wlARYZ-N9CCx2pfZKdgHb6gIJh3wbYRPi0fJNVFFhPCOXWPBnU6kJqbAQ4huc2uCtk0C-sUC-BKh8UuqJawfq7xyKA90T5mfI9maPkM0B5W4vS3c7LLbsmcTmx4YQX-olSrZV6ooKSWOx4HZ2UtgRUdGXYQKs0AWCkC2JZJe13liF-x39ziGFnLlMxT2_O6RLEEEJoFis49RQ7UYV7LRKqo59hR59AbROJM-JbI7MzKWO2SxMC2QBUQsC3ZCaX6ItDs4RmrxhwWvt7jq2YNR2oxOT1hPnX97Bf5yG1B66wL5gYppX0dauLWo6ErW_N3D6IpejjvjqMlyHVtSRTKZB28Xq9SxZpqP5Fco0Tmugy8sdGnbARlNysra0lTdlNABOzGu8IcQuV82bH_n3EBXJIGpGyiKrk-hbnfFYTFzelHC6r0yro537FxLZ7jpku48P9SStMoEJHey_hCDRjrsfPsndhU78d01VkAxJDr4cdwpgCJZku_x0kjFSuzRU6134XCWgaAuAw_g6DNkt7netbmRrp7hrrWxgR61Ad72Xetbt-S5KUZOnPz7WkGIg1PbfXVvRHiWxVECmjbpzV-snpjL16BoXUQv2MMFrw7b9q-qZk_5IMbw-YO4KQqrPjJMbGa0mxMibuk_fFsHHkxl8AentTgYOMVc5hSJnhWV-6G--ODo3C60jHh_dGa2LyNapJeH2CPhyk_HBKHcKpplFN5Ofunxe5q0UsQrAIYQJFoYybJjuMIy52sJr-3cX2Tutp-dYkprRRjDab0jOCvwnPeQ25sTqEtRsw-TGFM3o0Ka7WIp1DHrYeWibSBVt6SeImKw9c1Qg4qWRq4zY-2dFOEzv-MLmikzfVP9UTi0k2OozbtiXztwabsl3HJGbnSUZSsca_NCAmala5ezL8Has9eWzhBWRSlJ55y9Jz7qrDXGn7-U9B01K2IgXllbxm3Zomit6mRvXQcStr-JQDSrPvJEa5zvauD3l0R42R_ROuALmXxQMi6NlD9lOby63IYmu-lkmlNzkhHDkKNqBEnvn2_lvHkTimi2JmN_CHO4SC65tGOx_xW3u0gT2XDCLX04OFhMQhVIbB-ty6bAxriDYtAU6RMD0m-sERfA6POA0atoj84TOJ8fsSkuSv6g9ABnug__-GR1iFWNC9bQI8OtbU2SHIRnwSiGveyank2DWGo0Wwr9qaXXSsJPM5XING-ieUXRWG4UjQXbTT87f_oTfSIpT9Is-hg-y2S__SMBkKgXeGt0x61NU1iRongrLKdICG6xPgRe5dPnQiZZLUPkkU_59ynT7qxCaFhvbiXtM9M11JlyJqn04G4l6ssySkVzJIA3E3j536qbgadCRF2sndp_6OsYvTlmTdISEkSGX1X_SYw83Nypf-S0CTyOWi1ZLVlsghEu8Ac-0dre95GpgkQnKnB94NfKL_soc2IzxQUBBMi0umYbi8idawhoCmir9IXLweWWkmAZT28KN7KQ6FD292UUJBa87I7M56_go3MAqtsQg5LXIqNu53S7LsclQ5jLScamwxEhoatLMVW3cEGeuK6sVl5E7VbmLlfbIMzYa-j0LGdG2zsFJT9CdgV8RviowHSdAgTs9TTABlQrNFSvQm-CvvnDf2joR3c4xs1Dk1GwvfdjZt368y4GReg3NNsC6zUHiZR6BZz30dDSBEswIoLp8PaoKsrGEeBMjxMTJOlzfajFPlL5F8ACcWejFjOcuBFoh_iZhT1Jkjc9w-Q6rZqZg4ejSBSZ9fPYCpMSsFXfZan6dsMcNKkVS3F6x-TZZEHcinA4VXZsbzovIm4q-CY2lSCXhf6JOH_HgOKSy-88di0CQCfKFGzeCrl9pBRxXguDH8YFfsg1gWhBS95YOwmxvhOpFAuiPt93MYEmPcbP7KOeEswo4G1dG-phl2VOIF6j6--2mOMrlispENo3UosAWx43EZ588-TJTJ4wjBGNogVb2g-TLsQMUxJr3u53g8OjCjOuWY0G9Mpa_B0v8ZXgmvli4Ai2ogegvwq8Hz7tLoo_gKdX3zZF0P8VUkRS8ieG3JmmeCpvvtAwyU44U-MNsJC3doup9QlTxtOLkjkKfLI70wW0f4_K39N03NCK08mTNUaq-ZVcB7gNZ6e5LebykD23GUEGQnHEQWvkI8wWZ1NAeoE6EAu-C3SAD3yukLhy42ngwxrn_GNvGCrgX5ZdHQtjmycOtpK-AaWiwvs7c2fBnQC8it3sxDAV1IFAnPoASeh-3bvJOsDwQEPz78xD4lo_ckpmWsaf7xorof0YJk8RJkEtu3xSktxsWWIMZHCI5m-0iHwV7vMsXuPb8l4HhNq7gtGCjj1hGEc5hA7Bq3o3U4f7NKSNmv3EF4d-QP-t6G7A4qFU069IW16IL0KwhJGALJNkTtUUycy4znQGLl04wcsDpT-vEUDHbQ8C15okOjk9fgrzGr86xp7uyLEeKC9ifMQOjuEjKPxU_Jw3IfE-rXmLxXLyLR55t5V4eIvJq3Xs92fd4ONA80_7m_5zagGaWaPjdbyIS-i2uJGAOy50vYFB1k7WYCIp_Si4ZEzTrwBUkSUj_bVvArNVH2Xx7e4FUAqsvHAfpE7YKLtCi02HYDn7poFFjfuLUYGO46vBWYstyj6bZwPAfnF47CjN6NsYWWtgWYVy66MUfpXC6uwhHXV9UfFvVOXd3gb32R_1_way7cRkCqnuOAbYTbnrCA9Ni8G4mZsLYS2vggw1Yvo5o8jYJV_f4sIZ94RzbsHAuf16Cn3tuEWjXcCv1i4rIxY9AoMTQanhX29JCF8TrOGmgXhMlX-3yLpR22FeH8p6zY3X0k_wDAcYP6oB_LwrYBPepZEciyet0Snz10tZz-y5r6dzZRqwl3JeZgDh7iJIyoCt1REs9nWTwK3ITj0slEIaV9w58eSxCCalDYAU6Ko4xcnO1DZuYNnWbo95EZelcyPbIrKJCKXZ3QecUpvi30cffsBOSoiibC630rVRcQhlQSW2FJIgF-naMr8pVt8XrME4gZOTQnfUiDjolgIYLJ0oR9cqyshN_6T3xBWu0NyUnl49YyJODDGkhFInbQomCYu72HKgeAVNmbElJE0UgQWBdosy8xYeUCO-nlLhm4AWJQttqN2TrTIRSDehu-fUxB8WvmG_woAS65Z8i4jEbwoXqiEWc62ep6vpeYxOK21V6B10RJbZsIZsUXT0qZgVaH4b0EN2olQiFWUS4JKNqVThnalOHq4yJE3re2-3xBQI9ExDDgzprBK6dq3ql_fpQwLRLwBJFuUhoCjVlhXZL5gwcE5I7dyS27urDnVvlVLVvRQWdCkq3-NxtEfT7OzII6zb0A9DxgKDQE_KUcq1CaL6-ibJhncNOIM_LxRALJVp9xJI_e2eIt0-PWrJWCQXlBe9JZbEtwCylQRQn5fNp1lepbdwi6-oos-0rs82EXBEV-gv4DLLz-e77Gh-Y2UYieY5RytIYMWYxHSD_o9bRsFX0lAq0gIgd_BZPekS0hceyn_w9pBp1NpU6oTrMYfFSb88jUMK3mNByUIE8BmFN-RoA-KSppmDBzmTrmfiVb_TVTHqi0STG-yKiUoFgyiGq57HuueFB5s5RCRv6bGQ00kUNAHI-VJjXOsGCvMYR7mfobm2yfPWYw_VCcUwwQiXXc2APMTf9pMtNzzBDHpfkAPv2AhPsFG1xETC3Uiy-bFwhVCCHKSWfa51V2HR7HNt_h8y0DN2fuTeWmJR3sTOkTxe5s4Q-FPiigzGt-_q4Sfu1rii7Tp1IctHYuS-N59YZ_Ti9JiH2KWNKyPlc_zDIWH3bNGkDn8AzGWLjl_eb4pkCtgcmualu5Dv632vvLIPElkSMsJvmc3eMY5dBuJ8d4skjOIQGMvBygR_KmxhuVz3f1amJEyp8tnFcNLX1S_-AU4brmhEjMb0IX95qQGBsJkorh_rlsgOKDErRjbIqWxqZPBeOh4mYlSm-IcXpKP71niaqWdhplcLfI8-w1S6MYzOFlbwFxm-yBvtJnVVyjcm7bMPJtxsp1z8CsMLmfpxndTleioyl2S4ctre2O_NwVtTqFnaDwMurnBrzAncno3e7AobRTFMe28Z6M9Ivn8imAHH1e-2pFWE6Z-INHyIk_7mKbI_MyHPysJGPouJ2Av3WQG7ASEXRbk1aEqd7mwFQUy5rBhX1hP5P46w-4hedA8liUWaUTxWgN-_ivYEL1MffV0RXRYnfLLkMsvtuDdyOtocdQ2QO6rkCN4F-Lh_-pAEMplOttAMb-nHxbOwccWx0POIZ7nHIHk61u69x9DbXOxpFShrG1gmH4Ny45_MsPAcG0HipN1Pf4XtBidW8NEBzak14JgI4jHg98yBry1dM5WgxkWd4tXn3IiZWdWoJEhC2iocB3NVQ15rGicPSS5Sz5OpquEkznnxze6hQkmFa5CoiaPNFXfki2zY8FLt9evjiWcRR13oLyjb5K452kIhjn-O1GN4cEttrxQbrknhmsvCOPuzxKLcnY3MGg370pCx94uUTG3zY7cf8i1LFkXFAV32E-2YAs1Eabh0p_zuUw46WQGSldR7NWMTwR2EX9Sl6yYSexn1T0MH9fUE_HyDSSbM6obUd1Pofun-7dd8lpX4UQkj5pCTVMPwpuy6t1xF8XV-VMY-NEKimfrNhsaidHUG_CjUV6Z8UWDsNBB6fVnF4cApnHbETuz0sRJ6dt7w_u-BqD77DyZxcxf2-HGFBFhnTFC2tZY34a6MJPhYbSr1Sec='
    
    key = st.secrets['INSTRUCTION_KEY'].encode()
    f = Fernet(key)
    INSTRUCTION = f.decrypt(INSTRUCTION_ENCRYPTED).decode()
    
    # Set page layout and title.
    st.set_page_config(page_title="New Dawn Chatbot", page_icon=":sunrise:", layout="wide", initial_sidebar_state="collapsed")
    st.header(":sunrise: New Dawn AI")

    #--------------------------------------------------
    # Setup sidebar.
    #--------------------------------------------------
    NEWS_API_URL = "https://newsapi.org/v2/everything"

    # Minimum number of articles we want before using fallback searches
    MIN_ARTICLE_THRESHOLD = 10
    
    # Final number of results to return
    FINAL_RESULT_COUNT = 10
    
    # Primary broad query
    PRIMARY_QUERY = """
    (
    "teacher misconduct" OR
    "educator misconduct" OR
    "teacher arrested" OR
    "teacher charged" OR
    "principal arrested" OR
    "principal charged" OR
    "school employee arrested" OR
    "school employee charged" OR
    "school lawsuit" OR
    "school district lawsuit" OR
    "school court case" OR
    "school district investigation" OR
    "school board lawsuit" OR
    "Title IX lawsuit"
    )
    """
    
    # Fallback queries if the broad search doesn't return enough relevant results
    FALLBACK_QUERIES = [
        '"teacher misconduct"',
        '"educator misconduct"',
        '"teacher arrested"',
        '"teacher charged"',
        '"principal arrested"',
        '"principal charged"',
        '"school employee arrested"',
        '"school employee charged"',
        '"school lawsuit"',
        '"school district lawsuit"',
        '"school court case"',
        '"school district investigation"',
        '"school board lawsuit"',
        '"student civil rights lawsuit"',
        '"Title IX lawsuit"',
    ]

    try:
        results = build_news_feed(final_count=10, threshold=10)
        print_results(results)
    except Exception as e:
        st.sidebar.markdown("*Unable to fetch news.*")

    #--------------------------------------------------

    left_column, middle_column, right_column = st.columns([1.4, 0.2, 1.4])

    # --- LEFT COLUMN: Tool description and disclaimer ---
    with left_column: 
        st.markdown("An AI-powered chatbot that helps users quickly find and understand insights from Chicago Public Schools Office of Inspector General reports and related resources on child exploitation.")
        st.markdown("*Disclaimer: The information provided by this chatbot is generated from selected CPS OIG reports and related resources and is intended solely for informational purposes. It does not constitute legal advice, investigative conclusions, or official CPS or OIG positions. Information may be incomplete, redacted, or subject to change. Users are responsible for verifying information through official sources and should consult qualified professionals or authorities for guidance. If you believe a child is at risk or a crime has occurred, contact law enforcement or appropriate reporting channels immediately.*")

    # --- RIGHT COLUMN: Resources ---
    with right_column:
        st.markdown("Additional Resources:")
        st.markdown(":black_medium_small_square: [Chicago Public Schools OIG Annual Reports](https://cpsoig.org/reports.html)")
        st.markdown(":black_medium_small_square: [HSI Child Investigations Handbook](https://www.ice.gov/node/65395)")
        st.markdown(":black_medium_small_square: [ICAC Exploitation and Violence Prevention](https://www.ice.gov/node/65395)")
        st.markdown(":black_medium_small_square: [US DOJ Child Forensic Interviewing](https://ojjdp.ojp.gov/sites/g/files/xyckuh176/files/pubs/248749.pdf)")
        st.markdown(":black_medium_small_square: [US DOJ Guides to Investigating Child Abuse](https://www.ojp.gov/library/publications/portable-guides-investigating-child-abuse)")
        st.info(":information_source: Access school litigation news in the sidebar.")
    
    # st.image("image.png", width=700)
    # st.markdown("###### Advancing dialogue on ethics for educators.")
    # st.markdown("###### Your starting point for educator ethics")
    
    # Field for OpenAI API key.
    openai_api_key = os.environ.get("OPENAI_API_KEY", None)

    # Retrieve user-selected openai model.
    # model: str = st.selectbox("Model", options=MODEL_LIST)
    model = "gpt-4o-mini"
    
    # If there's no openai api key, stop.
    if not openai_api_key:
        st.error("Please enter your OpenAI API key!")
        st.stop()
    
    # Create new form to search aitam library vector store.    
    with st.form(key="qa_form", clear_on_submit=False): #, height=300):
        query = st.text_area("**What would you like to discuss?**") #, height="stretch")
        submit = st.form_submit_button("Send")
        
    # If submit button is clicked, query the aitam library.            
    if submit:
        # If form is submitted without a query, stop.
        if not query:
            st.error("Enter a question to search Chicago OIG information!")
            st.stop()            
        # Setup output columns to display results.
        # answer_col, sources_col = st.columns(2)
        # Create new client for this submission.
        client2 = OpenAI(api_key=openai_api_key)
        # Query the aitam library vector store and include internet
        # serach results.
        with st.spinner('Thinking...'):
            response2 = client2.responses.create(
                instructions = INSTRUCTION,
                input = query,
                model = model,
                temperature = 0.6,
                # text={
                #     "verbosity": "low"
                # },
                tools = [{
                            "type": "file_search",
                            "vector_store_ids": [VECTOR_STORE_ID],
                }],
                include=["output[*].file_search_call.search_results"]
            )
        # Write response to the answer column.    
        # with answer_col:
        try:
            cleaned_response = re.sub(r'【.*?†.*?】', '', response2.output_text) #output[1].content[0].text)
        except:
            cleaned_response = re.sub(r'【.*?†.*?】', '', response2.output[1].content[0].text)
        # st.write("*The guidance and responses provided by this application are AI-generated and informed by the Model Code of Ethics for Educators and related professional standards. They are intended for informational and educational purposes only and do not constitute legal advice, official policy interpretation, or a substitute for professional judgment. Users should consult their school district policies, state regulations, or legal counsel for authoritative guidance on ethical or compliance matters. This tool is designed to assist, not replace, professional decision-making or formal review processes.*")
        st.markdown("#### Response")
        st.markdown(cleaned_response)

        st.markdown("#### Sources")
        # Extract annotations from the response, and print source files.
        try:
            annotations = response2.output[1].content[0].annotations
            retrieved_files = set([response2.filename for response2 in annotations])
            file_list_str = ", ".join(retrieved_files)
            st.markdown(f"**File(s):** {file_list_str}")
            # st.markdown("For additional information and resources, please visit [www.schools.utah.gov/board/](http://www.schools.utah.gov/board/).")
        except (AttributeError, IndexError):
            st.markdown("**File(s): n/a**")
            # st.markdown("For additional information and resources, please visit [www.schools.utah.gov/board/](http://www.schools.utah.gov/board/).")

        # st.session_state.ai_response = cleaned_response
        # Write files used to generate the answer.
        # with sources_col:
        #     st.markdown("#### Sources")
        #     # Extract annotations from the response, and print source files.
        #     annotations = response2.output[1].content[0].annotations
        #     retrieved_files = set([response2.filename for response2 in annotations])
        #     file_list_str = ", ".join(retrieved_files)
        #     st.markdown(f"**File(s):** {file_list_str}")

            # st.markdown("#### Token Usage")
            # input_tokens = response2.usage.input_tokens
            # output_tokens = response2.usage.output_tokens
            # total_tokens = input_tokens + output_tokens
            # input_tokens_str = f"{input_tokens:,}"
            # output_tokens_str = f"{output_tokens:,}"
            # total_tokens_str = f"{total_tokens:,}"

            # st.markdown(
            #     f"""
            #     <p style="margin-bottom:0;">Input Tokens: {input_tokens_str}</p>
            #     <p style="margin-bottom:0;">Output Tokens: {output_tokens_str}</p>
            #     """,
            #     unsafe_allow_html=True
            # )
            # st.markdown(f"Total Tokens: {total_tokens_str}")

            # if model == "gpt-4.1-nano":
            #     input_token_cost = .1/1000000
            #     output_token_cost = .4/1000000
            # elif model == "gpt-4o-mini":
            #     input_token_cost = .15/1000000
            #     output_token_cost = .6/1000000
            # elif model == "gpt-4.1":
            #     input_token_cost = 2.00/1000000
            #     output_token_cost = 8.00/1000000
            # elif model == "o4-mini":
            #     input_token_cost = 1.10/1000000
            #     output_token_cost = 4.40/1000000

            # cost = input_tokens*input_token_cost + output_tokens*output_token_cost
            # formatted_cost = "${:,.4f}".format(cost)
            
            # st.markdown(f"**Total Cost:** {formatted_cost}")

    # elif not submit:
    #         st.markdown("#### Response")
    #         st.markdown(st.session_state.ai_response)

elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')

elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')
