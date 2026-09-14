import streamlit as st
import json
import os
import fitz  # PyMuPDF
import google.generativeai as genai

# 1. 파일 경로 및 법령 DB 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "safety_law_data.json")

@st.cache_data
def load_law_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

law_data = load_law_data()

# 2. PDF/TXT 파일 텍스트 추출 함수
def extract_text(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    else:
        return uploaded_file.read().decode("utf-8")

# 3. UI 화면 구성
st.set_page_config(page_title="재해보고서 AI 자동 분석기 (Gemini)", page_icon="🚧", layout="wide")
st.title("🚧 재해보고서 AI 자동 분석기 (무료 Gemini 버전)")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
# value 항목에 발급받으신 실제 API 키를 큰따옴표("") 안에 넣습니다.
api_key = st.text_input("Google Gemini API Key를 입력하세요", value="AQ.Ab8RN6KXQkxLCnwfCHdMoPi2NT5U751_dnjXKULjVSsiCMEaOw", type="password")
st.info("API 키가 자동으로 세팅되어 바로 사용하실 수 있습니다.")

uploaded_file = st.file_uploader("재해보고서를 업로드하세요 (PDF, TXT)", type=["pdf", "txt"])

if st.button("AI 자동 분석 시작", type="primary"):
    if not api_key:
        st.error("왼쪽 사이드바에 Google Gemini API Key를 입력해 주세요!")
    elif uploaded_file is None:
        st.error("분석할 파일(PDF/TXT)을 먼저 업로드해 주세요!")
    else:
        with st.spinner("1/3 단계: 보고서 텍스트 추출 중..."):
            report_text = extract_text(uploaded_file)
            
        with st.spinner("2/3 단계: 법령 DB 매칭 및 Gemini 프롬프트 구성 중..."):
            genai.configure(api_key=api_key)
            
            # 수집된 법령 데이터 요약 반영 (최상위 50개 항목 예시)
            law_context = ""
            for item in law_data[:50]:
                law_context += f"[{item.get('법령명', '')} {item.get('조문번호', '')}] {item.get('조문제목', '')}: {item.get('본문', '')[:100]}...\n"

            prompt = f"""
너는 대한민국 산업안전보건법 및 중대재해처벌법 전문 안전관리 컨설턴트야.
아래 [재해보고서 내용]을 정밀 분석하고, [참고 법령 데이터]를 바탕으로 시정명령 및 분석 보고서를 작성해줘.

---
### 📋 1. 사고 개요 및 핵심 원인
- **사고 유형**: (예: 떨어짐, 끼임 등)
- **기인물**: (예: 비계, 사다리, 프레스 등)
- **핵심 원인 분석**: (3~4줄 요약)

### ⚖️ 2. 위반 및 적용 법령 조항
- 보고서 내용에 직접 해당하는 산업안전보건법 및 산업안전보건기준에 관한 규칙 조항을 법령명, 조항 번호, 내용과 함께 명시하고 위반 사유를 설명해줘.

### 🛡️ 3. 재발방지대책 (기술적/관리적)
- **기술적 대책**: (안전시설물, 방호장치 등)
- **관리적 대책**: (작업계획서, 교육, 점검 등)
---

[참고 법령 데이터 요약]:
{law_context[:2000]}

[재해보고서 내용]:
{report_text[:4000]}
"""

        with st.spinner("3/3 단계: Gemini AI가 법률 검토 및 대책을 작성하는 중..."):
            try:
                # 구글의 고성능 무료 모델 사용
                model = genai.GenerativeModel("gemini-3.6-flash")
                response = model.generate_content(prompt)
                
                st.success("분석 완료!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"AI 분석 중 오류가 발생했습니다: {e}")