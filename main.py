#################################################################################
# Copyright (c) 2026 victor256sd
# All rights reserved.
#
# 06.13.2026 - Initiate New Dawn Specialists AI Assistant for investigative information.
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
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_embedded_frame, unsafe_allow_html=True)

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
    INSTRUCTION_ENCRYPTED = b'gAAAAABqLb2m9K-hM89uRjC4s7JPV2w4gHMVt8SQB6V70FL7zP-psDXqFGUxXzcS27UKvKN_e1idx5kYUxKOR5dYZNepT3RahdwF0GQP2aTqdkuuRIVeo6sOZT9b3exi4MIbi4u5ubAQcnwlSImAE2i1ZSyOmonc1msZnDmt26jjVS-8gURfRMe-3N9Ptxs90jQQqGeNVQjuiZ1Zp3pb2rvmpvcwNlehvcOqJRHQ9ZPj7VTgzhjqJ2EBC_cYaMLL_GWO28-psrjRJmTU8yt5abGvSV9iLhNLFDciJuI_a_nKahfAZrL_7SDpTSknPS8tWaSEZk3N9iTuKxlV1LzLpd7QOItvESs_pcaMeELSRX79I3srEZ5mysxqAhv5LTZNK859bxkGzXbdpiVFah0A9sT6Ptg66QbzVctCWdhKL5tdzC84Tv9NVmcDfWSdRy-UbmAVRK6UcLx93ffFT013XQaFfyg66P2ttoqDSJWw47grqbA_E1bLc3jy05hng9HdFasIMCl0zJhtPQJ--bxS0W68cIzrYWKxu5t0JaArcRLKrextnBOGlGEpAIKOjHb0TeJrtPGCiaie9M3Gn3NdC9PL_SnVUMqCG_RYRYtwyiGC1wzaVW0USxTxGoyOYLjvHlGLImeLJmeagxCiGhvT8kipZp0qKwBT7XOsmMR4BDSiSaXHm_btrTFOreG2mQJxuOb2_J5ENf0IVWGIFS83eim9o9-s97p5LIGcYPitBfNIAOn1AUjm4D2E-oP1LaQB4QaJSaC7snEaNNxTHTkB2o5OoDUkmEgt1cQVuqLLwPvqnNnFyw5cbHaKYupcv_5AWoEYfiFW9o31rBaJZtruUt9WCd3Hw64drqxAzNhyhk8IlcmOaUYX2cp0_LkT4sbLVe1kyA7pk7-LoGTJKiME5VchETsLyDOtUkgGeTRwpXpohKJO4I-vX01ZvARDjZMKvQmchG1t2v0Ci8e2m1VSus35Mq3TBvemfprdSpQnw_02QEoK07_IkdPhj8M9hDzdHuchVWHePd0uXiRNh16M4E5CI93u3gVOoBBVPCfGIzOmQOhbBwD3QSexdymsR-KGADvhmj9siax_pT8USmaiDxRvG_qSQ6mc9vlVmds0nSSlYbeiFTG2iENbG57mu67Psf_1EgBCFs4Ce3o8XxtnAEjJHVeFynIxwcF4l6TCkdidV-8Gv3k8twPzBfPA2O2QkGIXJhHdkvX9phm-YNMu4tshydt9eKe9y90jrTKS0mpq8QnZ1k4yTdG08MFoJo-Ke-tK2J7TUl14rf2VjGzqDGLbqtqZQnafAc4HExPE9W7Otn_sQjx8nLPluKuCQvAhD-Sw07kuDXZGuh0oFwtNauAoR5iv_qFQeTC3MoTOjcBZGrs8FFDaebkGlQGzAES0KdxSwt9puPZzyQsrGB2bka3F7_rgo6pS51mCLdHusM3Fcky3_3cammde6BFp3VAmnuxhYDH8jGzszFadn3THMsnx6IbIUrh-1aUBtcIFMFVRHU8mESCMVTSCMQcVsXQLSTubw1Eu9q_ee6RqUxQtfbxCgzYAYg4LZPE2rrjpcMqfiG_C0uBiuDdzphzbiO3b1xtflg6YT7t1ztdkhmK17w3-emGjflXUYbD3FAAy8KL8cQT-ATP6LmgPr12O_Ale9BuO8s-RQf_j9jwvPWAq7XC6O6T5Cwa7lgHfcog6JzmPgCrT4ttyPFpdW_pR2oL0iXTnOkV7ve96p8wmxm1kxTau5FiH_xnT3fNzrbiuhynKyOWLTT6rqBt0DUbZMAE-bBpI2gMH-GiwTG8tfi1LXjJ_57yikz0vWlAFS-KxlMkRi14HWOI8BPGr8xM0EWTZj8Wj5fnxZo6GqZTvTkRQ1YusCaROQZHQgjPqSvFzfpKYjxB09inpTLLbJo3tXvaW1cqn79E2HCA98CfsbPHS_tJLkZQ6JawO1N3lMBTKMIqhL3K2Nnc0S3_DGsdSwHQvEc8Phh5X2hoFosy-xOb8YcCAzhqgmNXrcwNgN5AqejqYfkTDGO1cBX7ceuvux6LOR4wIc-dQmK7yBuU_he-PX_XU5GkGTfOLAo6H9G_gFkjthc52e9_H7Rj0VNV_kJ-q1vkJVp3mfjAjKiCv38hehc5Vjdcei62uuze1P-PggFnAUcdVzdK7VkF0p5jGNYf-qAulbgpLZ1LxJns-84M7G89vf44ZyURHT5GBwX2iXJK78RTIKPU787dGOISh7cvbkEDT7F7VIqVmBs1cY7zZMxlKRIgZj8Sb4-sM7TmfBLRVtSv6dt9as-dZzxjLT05L5e6YmU66-wA4KkcWDxO-LB5W23SGt0hMvKmO3rXC6AUI2o20L3rzVpyS6FM8NUT2GCwedOgxJeYrBuThphsIGBGelpoGI7FYHylpj3hpWNsgrvqiKrHL9i9lg6Wu26NLXHIiJz9aocPaX0fzJnl4sVlbQDEKJvkCM0paxtbMjvLPSPv1FgmayNzojeExfnt9WnampvV9KY6g9ByjXEaC_HBBIiSh2_PdrgTqh03dg_NCk_QVowpkx4m5iWK729IE2KwVvTmXkvoSDxNknW5dhxhRqmslYGriRMlQ-rTc81FGQzy8XLh4unaGl3Y69rli4fOzQrQn1ltUfK1c9ikkWgHkupFKg3sNe__AjQjdiBk4aliyJZS_moyPEKrp2fxSNIHHt__eKmAy014t-dMG59LIMNKOUOpv9kM6MxNe3hMDPX6irNMoYYqswk88jzPOFcpm6kqfLgTa0-es__2XObtEU84joyoOOFfjRxF8E6cgbCozgW0pnCb_xMLKOND_lMeGRUPHX2d2wydu_5z9zl2HZeFNNsR_X5CIOUSxXRRRehzjftMhpWmpnX1ju54ZuVx9ECx-z8pkAoR-eC0Eer4JhpsMY_5t5blWVp64FGLMvFJYGjklYXKBXC2Zk5MdYa7iAky1t_Pt8-TAEK9I9KLn5NAniI9IZbTDYW-4_krKAwEq4BE1la774RfO95gJlKNC1LAH0WHfy077viLrwP6Q7b5xGDryrpK9S_8NiwrhR27tldRQQybs_TRJTbS_twbgtiebzcfKHEwuCZ5JpOGRzCxeC2-f2wCnfc2wwUIRraRmI1s-EVfiO3iVezSnaebr6zsDH-KPNe3xmdkTaZzyHNpnhNSwFErPPIW7JWW_B88JFFk-vg0ZJsWYYyfgY4eiLNm_hsN23fgu4Uu5FseD6RtDoFW5B2xcSe8sVNhHKjj25sVHbLqo6M2EzY8_TwXfAObz8p4F5jrzaOVt4Qq93PGUq9YF8Y3dJZKGrRGH4UqlIRHKrAVO4MFYSi5cpTObDMiU4WmPZyXt9FABUVSdElf_7YZs-3eEtl4WV_e2JOspV9HeMirTmILip_OTP62YXXANHKkHR_XB0ct6QX-TEjJailZ27f3jEMhiI1IbhNX-rdbHejUJGjirgU9RoOEP59PhcmNCOjzJi7Ayxo70DTv0b0fY1gdO387Fl2ireHRTxelaNIQKa9T6GWQyCrrdncCKDuW5IPsFeQdpN96Vy4LJuukb6qI1v1CQxrhiIiE69VEtwGZC0rgoe-517TXtt79DjOjAuIvyV04HavwNjUO_hdr8qxcPHYSxYA9Nm-TqBRKO_4lA85whqx4jhsaW-IpooIOmAlW7LA17h0zEMjMq9xKHY_yqCdGAmehphxBNUgM2z2ZIDYaaHC2SWZz18wQFj9TMJFydc_jGiovU3nOs-dIzSp7jldb8QZ158KBxIo5uB7Mu4l6-gbABQ01097LSB0T1FOG5oX4HCggNhQwBFThPGPhXymDlSbL4mijX28ddaHmfLtaHfWxCucYwwVXaOev-G5AmT2f7JP_QMMr7zS_-YuI8TXlnCJ-JFewHi_JczFe0aZ-Nuk2_H5o18gqcw15zTSB38bD2ZWRoq3rSOLd9LS8X9UA2HTeVlhN1MwL1fN9W0SWjJyY9Hl4YWtc_C-UiAC1fcIt_-DUYcJ3D4J37nh7SeFNR6cXOEq5Oe9efyL_oRidjv1SXLk1IV8sUUEOumfZwSL6ZxJCiTjJnhvkZtMlgHsx9IYYSahf6pgCsgxK2_p4nD5VhrwNes2gPQjV5v-YaGec_sGbC6WNkkEwMDDxmzPrzs-4t4mNehNOnMt8K4yObD1SSiUZANTsaKq_Cnoc61R8ixczdLTw47JkRoOVxPncngyxwTEwEy6Vjv5qS8MhxNdyx0vJ22_xp-_dYJVwhJrt5SMhC-_J97fhcsve39hDWvpaAF49dYVQ-eMQ6Ghn2SUyyD5ZoFm1Aylwc7A8kz0XJAS3p3nr9V-sTlOd8HTnz1QpdvmtiRisNWeHroVSKelZYGVwrXNTa4KkqcqVTkYUtsemLztvOLleym0F9UJu__uTbgPcfSAA1h7XwutQGyu4_g6jn-daDc2pBEcSy1PLL6PsMOhzbXqG27HqnUyetZqeLgy3ssQ3O5a0QlfR-pcvVvtVHgGQE7RVt9rSuXWMh3Fqn97qk3uJ82PbfFhYLvK6f8eXPLuixww50qW-w50310ARc4iZXaa084eLir8mNTWxQXeTizmeXh-evLVKYMC8xlNyAzZ2ySUSxctB2v61huAMfPCYhCmdIWym-Vb45p3qrwLVnrQ2T6oPxn32AIqdWI6idSt5_fm2Tev79GjCcDJxemBye6WNlun95pIzta691VbFCbVXU5rkgr4dET0vPGu7i1FGfrfW3leTa4EkMIq2Nhjr2PbZBP_MZq65wHJwsmZt4DJ4ThSthx6EqLTHp_FpeGrsbIOM25G9KO0MhrGOKHgxW61TcmFPxYOSCKeQ--aT873vEtLk9BoEaSNx_S0yjoQpyVlA9xhPpJlJqPsR3yN8T_mfDj5sb85NWlSrfq7gvVyln0OT7JuLS0LFaPvHgu0QU4Fvr2ZoVozeT318mcI63u2mqmwOlZG5af248eRG4OgLvH2sh3SfqGDtxYTCGsAPgzVOfuodf-ghMZT9ogqOt2SNR6xekqMiP0auj43Da4iVadidXMVbAoBND8V9BAEbm-WN1B1EzSxgo5IyNgm2gij2hKbbdAab2qRKlMIUUCNmg_PupYYZRpxvSeFqQg88-j11lLnns0Px2djpdaj2q6VMzsKDwUgykHwYVpFUrJak_RFT-LwRIgLYDDO0udeyGu6n_5-19qmlFKE5xKolLHKxug2u7kfT9GJ9YTAT2LtDSTGsJ974_XWzK10RDJoWMhu0-oeXyRp-Ryuvus_gmITTgx14z4x4uFVtSzpMGQJY6ewarp-dLDDUGOVADkBqiL5Syj534aZktzLTVbEKwOFFCdF-u7LXBLLMrLtXIEG5mQSXmQdFqrKryDk_vj-h8emMv7XQO9ynLrSbWD5TjlbFrgw-wS95DB65DJZgROQ3ldrqvpSloAC0n3wqHVyed2Xo55tMKB5Ebu7e6IewoRgdY1IGfuFpQxT3XQKY9nnyDzW7pze43id5cCcTP2BawYxRcfMwwZDwBjTueXhfW50rk09ed3XD_vWuseQEEHtFVuBwI1IBHgd3y9EFojUGsrSsK2iq97t8zH63iRSH9Xn1D94eZFpUvnHBQejOANJjKKKAFWKfUGXjF_Gh-fgXY1zRDRiCe7PhvBQf6NIVfU0E_ya4SCVsdo4jei1ey04XbnUp-3ccON6jxy_IcmpaPD4aR6U8Vowm_B_xip4yEXvKdBSzyCrophlFfMhNaKMA_FdV1Z9YpfUyYR34Ocl62Sfo182T5OC8TDMtt5P0ZjMzJtjTkClA2YT3Xic95vfQmDfMuVHt2nHa2Hi447THMST6GZggXyRsS5rDmlpJUQpqeawYzH5EK38IEDvoDZ4sQI1H6YotcZhzeQ3KKJLc1mEmh6WOjJiOWYofrkmuOO5lcegRWouxkD3p20a6MrypCVEAGJqDL-zGXYvg1Z-zhrXby3U1H3WWQJ-mlnPDctEn_k0081Do2MOJyxCSjZ9uZoaVHl7a9LENfi9QsxuCLg0ShQ0k2hFXLH7TdKdFizRm01FzI-Cmcvs7uubP0r4KwyjR6lSNHP4qBwqhvX7AC6-CT1fF8oQqBXLlu1PdxSfN_MMydE8Jp251dpAEnX2MkbgDPj4_jebjXjp3Vhm3wR8nDSkmTWdYFneN_MrXUS7ZaagiXpD1n4B3TusSI-gKAMAcr8YPNgG_uirqaCuUbEKBa-fkiMgj2GCwhlVfqxgz8oAD6ILZ0ReSSSZ-79VIiv7JYqe0yZQskyuuyoyrowuhs2oR0qPdU9Eu1yBvBTVFB90v97QwuwEaJY73UU-luqVvdJdRKLG4e7jRlOKY9300FNl_rn5FK2bQP5xH9r5g-DHUJNaqD9fWiKa-w53z4jg=='

    key = st.secrets['INSTRUCTION_KEY'].encode()
    f = Fernet(key)
    INSTRUCTION = f.decrypt(INSTRUCTION_ENCRYPTED).decode()
    
    # Set page layout and title.
    st.set_page_config(page_title="New Dawn Chatbot", page_icon=":sunrise:", layout="wide")
    st.header(":sunrise: New Dawn AI")
    # st.image("image.png", width=700)
    # st.markdown("###### Advancing dialogue on ethics for educators.")
    # st.markdown("###### Your starting point for educator ethics")
    st.markdown("An AI-powered chatbot that helps users quickly find and understand insights from Chicago Public Schools Office of Inspector General reports and related resources on child exploitation.")
    
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
