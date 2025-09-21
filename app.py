import streamlit as st
from openai import OpenAI
import uuid
from datetime import datetime
import json

# 페이지 설정
st.set_page_config(
    page_title="마음 코칭 선생님 🌱",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 적용
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("⚠️ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에서 OPENAI_API_KEY를 설정해주세요.")
    st.stop()

# 세션 상태 초기화
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.coaching_phase = "greeting"  # greeting, goal, reality, options, will

# GROW 모델 기반 시스템 프롬프트
SYSTEM_PROMPT = """당신은 대한민국 고등학생들의 마음을 깊이 이해하는 따뜻한 상담 코치입니다.
GROW 코칭 모델을 활용하되, 자연스럽고 편안한 대화로 진행해주세요.

🌱 대화 원칙:
1. 학생의 감정을 먼저 인정하고 공감해주세요
2. "~해야 해"보다 "~해보는 건 어떨까?"로 부드럽게 제안
3. 섣부른 조언보다 열린 질문으로 학생 스스로 생각하도록 유도
4. 비판이나 평가 없이 있는 그대로 받아들이기
5. 한국 고등학생의 입시, 학업 스트레스 상황을 충분히 이해

🎯 GROW 단계별 접근:

[Goal - 목표 탐색]
- "오늘은 어떤 이야기를 나누고 싶니?"
- "이 문제가 해결되면 어떤 모습이었으면 좋겠어?"
- "네가 정말 원하는 건 뭐야?"

[Reality - 현실 파악]
- "지금 상황을 좀 더 자세히 들려줄 수 있을까?"
- "이 일로 가장 힘든 점은 뭐야?"
- "지금까지 어떤 시도를 해봤어?"

[Options - 선택지 탐색]
- "다른 방법은 없을까?"
- "만약 네 친한 친구가 같은 고민을 한다면 뭐라고 말해주고 싶어?"
- "아무 제약이 없다면 어떻게 하고 싶어?"

[Will - 실행 의지]
- "그중에서 가장 먼저 시도해보고 싶은 건 뭐야?"
- "작은 것부터 시작한다면 뭘 해볼 수 있을까?"
- "언제부터 시작하면 좋을 것 같아?"

💬 대화 스타일:
- 편안하고 친근한 반말 사용 (고등학생 눈높이)
- 이모지 적절히 활용하여 딱딱하지 않게
- 한 번에 1-2개 질문만 (부담스럽지 않게)
- 학생의 속도에 맞추기"""

# 타이틀
st.title("🌱 마음 코칭 선생님")
st.caption(f"편하게 이야기해보세요 | 세션: {st.session_state.session_id[:8]}...")

# 안내 메시지
with st.expander("💡 이용 안내", expanded=False):
    st.write("""
    - 이 공간은 여러분의 고민을 들어주는 AI 상담 코치입니다
    - 진로, 학업, 친구관계 등 어떤 이야기든 편하게 나눠보세요
    - 대화 내용은 저장되지 않으며, 브라우저를 닫으면 사라집니다
    - 판단하지 않고 여러분의 이야기를 들어드립니다
    """)

# 대화 기록이 비어있으면 환영 메시지 추가
if not st.session_state.messages:
    welcome_message = {
        "role": "assistant",
        "content": "안녕! 반가워 😊 나는 너의 이야기를 들어주는 마음 코칭 선생님이야.\n\n오늘은 어떤 이야기를 나누고 싶니? 진로, 공부, 친구관계... 무엇이든 편하게 말해줘."
    }
    st.session_state.messages.append(welcome_message)

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🌱"):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant", avatar="🌱"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # OpenAI API 호출 (스트리밍)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + st.session_state.messages
            
            stream = client.chat.completions.create(
                model="gpt-5-mini",  # 새 모델 사용
                messages=messages,
                stream=True,
                temperature=0.8,  # 더 자연스러운 대화를 위해
                max_tokens=500,
                presence_penalty=0.3,  # 반복 줄이기
                frequency_penalty=0.3
            )
            
            # 스트리밍으로 응답 표시
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"죄송해요, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요. (오류: {str(e)})"
            message_placeholder.markdown(full_response)
    
    # AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 하단 정보
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 새 대화 시작"):
        st.session_state.clear()
        st.rerun()
with col2:
    st.caption("💚 항상 당신 곁에")
with col3:
    st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")
