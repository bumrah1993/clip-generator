import streamlit as st
import anthropic

st.set_page_config(page_title="Resume Bullet Optimizer", page_icon="📝", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f8f9fa; }

    .header {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .header h1 { font-size: 2rem; margin: 0; color: white !important; }
    .header p { color: #aaa; margin: 0.5rem 0 0; }
    .header .credit { color: #00ff88; font-size: 0.95rem; margin-top: 0.75rem; font-weight: 600; letter-spacing: 1px; }

    .bullet-box {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .bullet-label { font-size: 0.75rem; font-weight: 700; color: #888; text-transform: uppercase; margin-bottom: 0.4rem; }
    .bullet-old { color: #e74c3c; font-size: 0.95rem; }
    .bullet-new { color: #27ae60; font-size: 0.95rem; font-weight: 600; }
    .arrow { color: #aaa; font-size: 1.2rem; text-align: center; margin: 0.5rem 0; }

    .tip-box {
        background: #eafaf1;
        border-left: 4px solid #27ae60;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #1e8449;
    }
    .stButton>button {
        background: #1a1a2e !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
    }
    .stTextArea textarea { border-radius: 8px !important; font-size: 0.9rem !important; }
    .stTextInput input { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div class="header">
    <h1>📝 Resume Bullet Optimizer</h1>
    <p>Paste your weak resume bullets → Claude AI rewrites them with impact & metrics</p>
    <div class="credit">Made by MOKSH SHAH</div>
</div>
""", unsafe_allow_html=True)

# ── API KEY ──
with st.sidebar:
    st.markdown("### 🔑 Setup")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.markdown("---")
    st.markdown("### 🎯 Optimization Goal")
    job_role = st.text_input("Target Job Role", placeholder="e.g. Data Science Intern, ML Engineer")
    tone = st.selectbox("Tone", ["Professional", "Technical", "Leadership-focused", "Research-oriented"])
    st.markdown("---")
    st.markdown("<small style='color:#888'>Built by Moksh Shah</small>", unsafe_allow_html=True)

# ── MAIN ──
st.markdown("### ✍️ Enter Your Resume Bullets")
st.caption("Enter one bullet point per line. Don't worry if they're weak — Claude will fix them!")

bullets_input = st.text_area(
    "Your current bullets",
    placeholder="• Worked on machine learning projects\n• Helped team with data analysis\n• Made a voice assistant using Python",
    height=200
)

col1, col2 = st.columns(2)
with col1:
    include_metrics = st.checkbox("Add impact metrics (%, numbers)", value=True)
with col2:
    include_action = st.checkbox("Start with strong action verbs", value=True)

if st.button("🚀 Optimize My Bullets"):
    if not api_key:
        st.error("❌ Please enter your Anthropic API key in the sidebar.")
    elif not bullets_input.strip():
        st.error("❌ Please enter at least one bullet point.")
    else:
        bullets = [b.strip().lstrip("•-").strip() for b in bullets_input.strip().split("\n") if b.strip()]

        system_prompt = f"""You are an expert resume writer specializing in tech and AI/ML roles.
Your job is to rewrite weak resume bullet points into powerful, ATS-friendly bullets.

Rules:
{"- Start every bullet with a strong action verb (e.g. Developed, Built, Engineered, Designed, Implemented, Optimized, Led, Deployed)" if include_action else ""}
{"- Add realistic impact metrics where possible (e.g. reduced processing time by 40%, improved accuracy by 15%)" if include_metrics else ""}
- Keep bullets concise (max 20 words)
- Make them specific and results-oriented
- Target role: {job_role if job_role else "AI/ML & Data Science"}
- Tone: {tone}

For each bullet, respond ONLY in this exact format (no extra text):
ORIGINAL: <original bullet>
IMPROVED: <improved bullet>
TIP: <one short tip about why this is better>
---"""

        with st.spinner("✨ Claude is optimizing your bullets..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": f"Rewrite these resume bullets:\n\n" + "\n".join(f"• {b}" for b in bullets)
                    }],
                    system=system_prompt
                )

                raw = response.content[0].text
                sections = [s.strip() for s in raw.split("---") if s.strip()]

                st.markdown("---")
                st.markdown("### ✅ Optimized Bullets")

                all_improved = []
                for section in sections:
                    lines = section.strip().split("\n")
                    original, improved, tip = "", "", ""
                    for line in lines:
                        if line.startswith("ORIGINAL:"):
                            original = line.replace("ORIGINAL:", "").strip()
                        elif line.startswith("IMPROVED:"):
                            improved = line.replace("IMPROVED:", "").strip()
                        elif line.startswith("TIP:"):
                            tip = line.replace("TIP:", "").strip()

                    if improved:
                        all_improved.append(improved)
                        st.markdown(f"""
                        <div class="bullet-box">
                            <div class="bullet-label">Before</div>
                            <div class="bullet-old">• {original}</div>
                            <div class="arrow">↓</div>
                            <div class="bullet-label">After</div>
                            <div class="bullet-new">• {improved}</div>
                            {"<div class='tip-box'>💡 " + tip + "</div>" if tip else ""}
                        </div>
                        """, unsafe_allow_html=True)

                # ── COPY ALL ──
                if all_improved:
                    st.markdown("---")
                    st.markdown("### 📋 All Improved Bullets")
                    all_text = "\n".join(f"• {b}" for b in all_improved)
                    st.text_area("Copy and paste into your resume:", value=all_text, height=150)
                    st.download_button("⬇️ Download as .txt", data=all_text, file_name="optimized_bullets.txt", mime="text/plain")

            except Exception as e:
                st.error(f"❌ Error: {e}")
