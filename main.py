#################################################################################
# Copyright (c) 2026 victor256sd
# All rights reserved.
#
# 06.05.2026 - Added image map for logo.
#
# 05.06.2026 - Added logo.
#
# 04.28.2026 - Updated landing page language based on NASDTEC direction.
#
# 04.23.2026 - Updated instructions with information obtained from beta testing
# survey.
#
# 02.27.2026 - Instructions reverted to 11/30/2025 instruction set, vector store
# reduced to MCEE documents only.
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

# Disable the button called via on_click attribute.
def disable_button():
    st.session_state.disabled = True        

# Definitive CSS selectors for Streamlit 1.45.1+
st.markdown("""
<style>
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    div[data-testid="stStatusWidget"] {
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

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
    INSTRUCTION_ENCRYPTED = b'gAAAAABp6r99WmfinfR-gNl_e-VL-5nt1EM9D0jgrWSt56dDIrmyIu0EiifRTsaFn3xzRTT31eC0bE3w0wz8Ds9LK1a2uRJ_kzxEFhuHdV3YZqVxtfnBiyIJ4nqAiMotiGftd8D14Y2Y04b1JKenOJfjEZdUa9XHg-hS9u1ehJucui0f-eNlgftrGK1A3sbuLcX2P0Pektxv7XtZGZ3lCjSUo_Y5lPjb_GDX3d8-hAF_dd_m9sl5tC7FyISPm-12SMNj84729Zi4ks6XzqqZuFEhWHcdsCSjqXzERKyhwhaf-OpfDJg3_W84tkmSDfF-8Ifa8R5rFuI8cg6SiE8r_vAUzE2PZX6h4bTIrmcVHoFz4qHHDuxI4WkZ-gAujW1eXpOz2tEjJCLy_dvGymNFFxAUzXAfJADQrxjyd4lp6k5ACj3vYKrZPmYl_0Rd-qoLOvOZTBh3b47Qv5S4WAh26_NoESrY0MYGpaUo9MOeb4KIkNt5C1bQ1hjQIvhZAHV8RtrRQG_tnhYCJBG6j0ECaTE0amuG9GR0pXJnWYNY9UUTDMGUWmWBV8YBqRQLR07QGBOE1g17HMe5roRHgfgrW_y8hzt8FfjE9yN4jskXFMmkmbwwja_yWX3z-N3Hjs3n_cYmEBPi4CmdWxilngdCD0E2uAk3W_LEmF_M0TyP7Z_GOUylMepFZl0hc5J-m3EVWBbBOd-1ImulU9WN5CWR3rSafPJoEUUTMxsq025FmwNwFBZHdaI2LFPpOgYjIdmZPFmdsSoe8owPB2YYF9H9gyagRu6n7ZN1q-WTQhnG1EQkjdy1-aDxlOI8E3nHKvbxrBVz5Bzi9zagHNt14TWAlKIlvTBL15i3gIo4WDf26s7s0enVIQAwcPCB-QrFffzLS6iT3JdV3ggeeIDO_J-LKfV_QYnC28Ef9oQ1mU-oVOMNTLd4rr_PQCti07ZrR0fcVx_WwIMuFlQERX6po88S_dMH3CR9KNp2bBNKTG-IHBJkYTSO9mHYZ1pJQPrfYGav3AQs0OVfJvW-XR13KHRykCqXhuqgrWAYxe3G1FpXhBJrPDkAd8RChdd-4uy953jovAT8pmlRvEWPL_d3ViclmQlHXa9DyQxSJaW7E2_mc9jYmEaVdjddCq8zFb8ltoh8b_x9OvNZJaSIbkcpmDF6HxF4NSLpFEHnGiTu-THlcmyk0sepm9C71nhgaiLQ7-3waO5UZkpXAowOSLphc461QYtt52B1AzzS0PvZM-1K_zJ6zr4v-NJpQXtDkgBBvUFZQxq4Nu_2wWJRE8rBec_aLDz-keu7UcmOEoSAVWv2VzGNAXdfcUHBbbo4iRaYiq0riQ_Ues7KmzH14eAAFjZp5rJz_noku6cQ51zui4sXJ0nT1WAjg0LvOWbEaZarpjWAY5V0pTD7QhdVp2KtXQUnj4kSQevsn3aLF-TafnwAmsnbx4TQUuGaJTJWj9ubOOD0n_2VDppirpBCTQ4dsnwccT6fOKWbT8osP2IL5LbYHPYiVDOxBQR29S0LWM2KxvK5hVONyYPPUH-vIa0zX3AcCBRbCe0gDtoed18guUVJk1PrXoio9x8gKV9Gix2VoBsIW0v5xnpiDTrUqHauVfF42Z5lyo-q4bFRtDyn2_lrZO6dHFnW3MjHQUXaJ6T7dD_iLqYXX6evObWHlJoezB42X09sgkuzhtrNiiYZ-Z8ZL5Opn-2Jsi3RfIfadNShWvnMGtuxPKFkRkcIwZODOCb3v09pwZ13XXqHb8__3uqhF3bPTADFDeMA0eRAPkxcdU2upj8musGL8p0dL2mltJLzS4khYpXahniJB1rVc3jEP5ZhsseLhuPZNTAbkRiejTZBtyV7NhXAggUBNiuThDlxd_fx-ZoaG51w0B2drAMpRL1Q5zBtVa2rc2lJsxLLbTUuvjqCyCAzoR55V1r21DOJwNqKjjOt6qxS3tGSrCAh9Ga9eQE5X4KDvf8hbh5hewAz5HDASJzc9JeM_e33wnZ4NP9_iyqwHENOjVCAPiUksqeBTAudXPDUAuq_6LvNkouBq7T-1bwNZVlOCPW54qiS8u9Ag23xtFg4w3N4lKzpei8LEqqtod37nBGgA4NuJwHseFZdG2A2GmZVh2e9TTZpXNTmFB8MnGn3ymqIoDw2q_3divhm9-Hfc7-g_n9rDYkAledJqmgGfc5gnAT20ibTJlxp8qR8xRoDKR-6fiXhUagyB3l5g-QYm0YlhDGPYtfNwJxUxsK_4ivrsrlPvPKinq3obDLG6lgBU25eL8Y6VQCcOstr8fqx8CKPkTIV-9UboOBlcB9rw6k00DvT0kk_mYTBB4rq-XyMC9kkSG9i5S25YlSz6xj3zCfZucZdw-6kM3lEy3zp54IGmSAp3Zxl3jgbsGqXdDqlQeVKu5tDeT0Xz8_B6bpBdqCEsxOoLAPT8YSB-SoZbwSgY5divhj_a5HFrcPeOVRzPKVUOj6oSVtmgB8B7L2YYBCAOYheNBbWX6ba_6oSM-0hPFzubp3xoqx9ggyiYUd7E-QGNsrAm8S2WHZhBCp3ey2qS05LmeS2HcL25wrXj7isVGWPVQ4U-6Nnv2sbu209TbHf0jKZ1o2hFTf-BmKMXRfDWb6QU15Xq-03wi3mwsmczLvNorh4Jhgato7r-oBscgNA6nOjoNILjJ2b4OXPtm-1UYWncMWgNmFJ_jNrrrNa0MWTio8qB3lgxwnmu068B5m30T6SU4GotuFnLCQevjEN5gU1n2HpWpE70vSoiNyFZ1_g2TIMCozJtaqvyMMFEJ3wwWnU4-Q-6rSfagfQwowznigp0g6ftJ2LSXQcM0zcnsO27ExmlfpKOwjfykSqugIRPK4R_2VONWI23zgckJ4oqvk_tRtz5Te2Vi427NHIRK88PR-2lw1pU7cIyYV2cyHM6nkpl3XVVXZwY1gpmjdbWLa3LjHnll-nPKyNUMyG2WG7FTuW2PLRyrcf_w6nvzeP0VaICBS7Orqrue8vVeriC4XYjrWb8-td5_fp8nzyCpezeaz_J-v33qA4UdQJNm1QRlxLz57kG_yVFMyMrbvjpber1xIYHOvCucdtLoR5zAsZ0gVfS59u1rfILRLWafAPcrFv2ZTXAfj_G_ifsy2_VYvjaoFOOMhi-zJKPGsBmCTRxUzcks7qCGAvGfv7f3zV4LYgmLSh1FXKXAtPYjrArUNLtGm3VGstaoJ7oJHkRSywLdGxTVVUlfVt9JKOhng38qWXcQP04M7YPz11HEapEtlriuhqiDtVHXAmOv_fpo0vVe-dfrExoFVVFT2XwkU5wQmSpS40QfARaIn_Fd-xAdATXTvrxTWorrxAkJVmW6IclqWuzb4XZqT_R8foTjwEstqhA_qw17N3RMGFH_gWPThFgv6gyLc8ODShEKYrKCJhBxmVAkCU-UMxfc_XBdYUO72UL03i9RLmV2Ntu1bkY9wN_2qWVaeijcfpWqsuaIKA8eN_INCgRu5IyZzUm6-W7G6kK-Nd28PevROu6qr6rob2DLlADH0LxQE9o6uQnH_P04BY0KFEproyJIz4R0X5aUk1w0EfEhWIMWtjpSE3r4h3yjp3m1xf_YqU3GV3SbxAzCUcssxJgIatMEmQZGgZuDM_LJLgHM1WAUTjTnAM13fY8XZogr25VVUm-ULQ7-q6vw4nt3Y1OlrNduFOQY1jLhrUEzX5JZqEJah3AVjnvE-_TCo_-aOvmfY7oH5o_gmyYVi5MHUehctkw83MWkncqWwPKMCKrWJyXcEOaiulaXUZmoBWDjwXqNNUUWr4CESTAlsz07HaO2xqN-gg-Ehl4tyCLglr9VKENyGG5t7SNum0D5JOIFGcVWmPBUxEdlZS52lH3R9k9VgDzeempfn3CCDXYL6H33zaNC5Lx249zb666OES3duoJImF9186hzWywkALXZmqWOsaYitu7Il4XPPsJUvL8uMpx6SxYUbsdboxWGDGyiCiTe1UDMmfg40xaIrvrujpSyYw1qxgyTtG2nYDNeGJngXf10j0nYbcQliytMtXI9voJb0n7q1tTRaTicx3N7ym08c_9ngXdE2cSSe9EXqQlomUka4giFqquPssC4zss1GZlGdOEoi7_4HsrPhONPi1gsd14x5XhFaB9qjY7Yr0nleqDvf9QI9c1Gxfmm68r20yFkxBydwgrvRtAyxd2ptIBHnZbDkmTT6pKcxAopNtk4bemAMe-U8uEI_7lkvxDc6Y0ebalevQC_m6mhNa1tFUR8VLPgaf8YCcX8gLejOqvVINwd1731w7y1eXh7exfVv9I5iIFTO5YepWOhB_Dm8c6OPGrcuZ-5uylPEWz_YYVt2544cMjnJnxIQtXLep5gq1Xyd8vZLGppZlPMCWSqxje0wn_AgxQaSiMJvHWnLFgKe2wYsuw_yvsZV2g4T3JHKxQy3mqlZfKWw6nSueBg29QZdFa0lMzK-E7ccA9Kopbh0y0pXw15KjR0B07eOjA5pbnXYXZEZVj4isUwSExYy-cVeV_SXFHjcJ8sKBd-J0RVESoA603ajfMiRXdkdKxzkfP4U9nRxEkflC8J7ycjScS3LLYd6syXKimsTR8FsGWrwWsNNrVAP9wquh_YJiVRb88bS4w3nEJe0pCJ_VUzwwwght_3cE2biMPGHg9EzAULMRQqj0nEtC0bHSe6Jl4l3cMAViH5HPDBk8PnwfaQFZL5EN9aLTZHW0D331JbbboL1ctBsrAH_RTXOP1JMU3QDWC6Jb6EYjQRwaYaL84A_oc66WpL5BXbh3unBQiD4y0uappltwCps1IAAnheTk99maBOlpNehf9WR_85-frjW9-UYAgRljiig6QhCP2lAYT1OhKNEVYlIxaFpHEnpvLCvqqG8zii9960bXgBWahi6TOoPI6FnyD8lgYUANn-m8aVrb2fhDHgdSDx5CCdCy1T5pCZFvM7W7jYvWJJzj_eZVKnqTXcNLNVbXHXQ1qksFrN2nXDV2hC0ugTeFkpXwpmTgAeIMRo_PKwAgksM-2V-R1Of6UMdCvaVwgcEKi2gQBOYtkt1bFdRMwJzNAeOyVkDiZxMw13J6k6JUoBYGIxs6GRQD5n5EPjAyHr_P3qBS1doYC3UYCNXwqLrCoZl_oCyVcfBZRuZP-nDINALZCDknNWkY4EVCuEDd7a75OT0EsLqA7NC2f72dILQyr4OD6vIKSh71ow_99qYZJhbQRLsG8M-xacOdhJHVFk2ASL0GJBsral2cctuD4I_e2vFRM3V4lQEUDbJvdRZMesax_hUG_R2xb7BxxLfKwU3EEUHUyKblPb9ZRCH4OOdK4DpiqsbW8kn3rsh3W5l96cv6hccgCkD6kbLyD7st5Q5HgTXUq9XitXuo8FDPu7mEdlnmV7XD0vCPfJXAkpKHhGConessZdnwtbvMTVYct9ZF77wgJwHzdcFYCM8TNJRwSgqm_zC-HAfV4XiiCIaFcEy17Mv5YNT8MvzdWvoHMXHknBfOqXffkvLB3qPc9JDvVVcBQRxFmGHHZFbb5ev4_iahtWrBktK6res4uaGojlYcFTQfgGeSKalntRrpwPI33_dHuBR6x1lhAxMrxwf38HzQXZQp16I9LNhZVybQJ1yG6rw-bmsse1dFI0naRHkQNiwVz_mttyyt7O1DBGQLZ7jXwMrHPbqMayAaRkcHVgUVXVA3sWN7kB33DO3xMrWMjSjtTHHCrGpQ32f-P8YPG2e0pQNyOPvHtLsl_OV1NS4PYsxz8b_04H3uFkAHU2nBqUBO1xwtz7IZf8RlvTGArj4e9Z76FwCIIpnVkiK-HGaPbM1Gx9qMMAh8-GY='

    key = st.secrets['INSTRUCTION_KEY'].encode()
    f = Fernet(key)
    INSTRUCTION = f.decrypt(INSTRUCTION_ENCRYPTED).decode()
    
    # Set page layout and title.
    st.set_page_config(page_title="Ethics Chatbot", page_icon=":butterfly:", layout="wide")
    # st.header(":butterfly: Integrity AI")
    st.image("image.png", width=700)
    st.html(
        "<img src=\"image.png\" alt=\"edmse\" usemap=\"#imagemap\"><map name=\"imagemap\"><area shape=\"rect\" coords=\"900,30,1480,200\" alt=\"nasdtec\" href=\"https://www.nasdtec.net\"><area shape=\"circle\" coords=\"1210,365,140\" alt=\"ncaee\" href=\"https://www.educatorethics.org\"></map>"
    )
    # st.markdown("###### Advancing dialogue on ethics for educators.")
    # st.markdown("###### Your starting point for educator ethics")
    st.markdown("NASDTEC serves as a national advocate for the advancement of ethical practice within the education profession. To that end, the Model Code of Ethics for Educators (MCEE) was developed under NASDTEC’s leadership by a diverse and representative task force of educational practitioners and launched in 2015. Subsequently, NASDTEC established the National Council for the Advancement of Educator Ethics (NCAEE), which is charged with promoting and fostering awareness and understanding of the MCEE.")
    st.markdown("**Disclaimer**:\n*This application was developed as a tool for practitioners to explore ethical dilemmas within the context of the MCEE and to stimulate discussions about ethical decision-making. Please understand that while the guidance and responses provided by this application are informed by the Model Code of Ethics for Educators, supportive resources, and related professional standards, they are generated by artificial intelligence. All AI-generated responses are intended for informational and educational purposes only and do not constitute legal advice, official policy interpretation, or a substitute for professional judgment. Users should consult their school district policies, state regulations, qualified professionals, or legal counsel for authoritative guidance on ethical or compliance matters. This tool is designed to assist, not replace, professional decision-making or formal review processes and may have inherent limitations, such as providing incomplete or inaccurate information.  Users of this app must not rely upon or make any decisions solely based on AI-generated responses to the questions asked. The answers provided are for consideration and thus are only a small part of the process of determining the best practices.*")
    st.markdown("Review NASDTEC Ethics Chatbot: [link](https://www.surveymonkey.com/r/QB353X3)")
    
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
    with st.form(key="qa_form", clear_on_submit=False, height=300):
        query = st.text_area("**What would you like to discuss?**", height="stretch")
        submit = st.form_submit_button("Send")
        
    # If submit button is clicked, query the aitam library.            
    if submit:
        # If form is submitted without a query, stop.
        if not query:
            st.error("Enter a question for MCEE guidance!")
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
            st.markdown("For additional information and resources, please visit [www.educatorethics.org](http://www.educatorethics.org).")
        except (AttributeError, IndexError):
            st.markdown("**File(s): n/a**")
            st.markdown("For additional information and resources, please visit [www.educatorethics.org](http://www.educatorethics.org).")

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
