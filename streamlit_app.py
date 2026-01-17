# streamlit_app.py
import streamlit as st
from rules import RuleEngine
from estimator import estimate_block_runtime, complexity_score
from carbon import estimate_energy_and_co2
from suggester import generate_suggestions, naive_apply_patch
import base64
import textwrap

st.set_page_config(page_title="Digital Waste Analyzer", layout="wide")

st.title("🌿 Digital Waste Analyzer — Code Carbon Checker (Prototype)")

with st.sidebar:
    st.header("Quick help")
    st.markdown("""
    1. Upload a Python `.py` file or paste code.
    2. Click **Analyze**.
    3. Review findings, suggested fixes, and estimated energy/CO₂.
    4. Apply naive patches (optional) and download optimized file.
    """)
    cpu_watts = st.number_input("Assumed CPU watts (for estimation)", value=15.0, step=1.0)
    carbon_intensity = st.number_input("Carbon intensity (g CO₂/kWh)", value=475.0, step=1.0)

uploaded = st.file_uploader("Upload a Python file", type=["py"])
code_input = st.text_area("Or paste Python code here", height=200)

source_code = None
if uploaded is not None:
    try:
        source_code = uploaded.getvalue().decode("utf-8")
    except Exception:
        source_code = uploaded.getvalue().decode("latin-1")
elif code_input.strip() != "":
    source_code = code_input

if source_code is None:
    st.info("Upload a .py file or paste code to analyze.")
    st.stop()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Code")
    st.code(source_code, language="python")

with col2:
    st.subheader("Actions")
    if st.button("Analyze"):
        engine = RuleEngine(source_code)
        findings = engine.get_findings()
        # estimator
        est_seconds = estimate_block_runtime(findings)
        complexity = complexity_score(findings)
        energy = estimate_energy_and_co2(est_seconds, cpu_watts=cpu_watts, carbon_intensity_g_per_kwh=carbon_intensity)

        # score (simple)
        base = 100.0
        penalty = complexity  # heuristic
        final_score = max(0, base - penalty)
        grade = "A+"
        if final_score >= 90:
            grade = "A+"
        elif final_score >= 80:
            grade = "A"
        elif final_score >= 70:
            grade = "B"
        elif final_score >= 60:
            grade = "C"
        elif final_score >= 50:
            grade = "D"
        else:
            grade = "F"

        st.metric("Code Carbon Grade", grade)
        st.write(f"Estimated runtime per run: **{est_seconds:.6f} s**")
        st.write(f"Estimated energy per run: **{energy['kwh']:.8f} kWh**")
        st.write(f"Estimated CO₂ per run: **{energy['co2_g']:.4f} g**")
        st.write("**Findings**")
        if not findings:
            st.success("No issues detected by the rule engine (nice!).")
        else:
            for f in findings:
                with st.expander(f"{f['rule_id']} | {f['severity'].upper()} | line {f['lineno']}"):
                    st.write(f"**Snippet:** `{f['snippet']}`")
                    st.write(f"**Message:** {f['message']}")
                    st.write(f"**Suggestion:** {f['suggestion']}")

        st.write("---")
        st.write("**Suggestions (templated)**")
        suggs = generate_suggestions(findings)
        if not suggs:
            st.info("No template suggestions available.")
        else:
            for s in suggs:
                st.markdown(f"**{s['rule_id']} — {s['title']}**")
                st.code(s['suggestion'])
                st.write("---")

        # patched file
        patched = naive_apply_patch(source_code, findings)
        st.write("**Optimized (naive) file**")
        st.code(patched, language="python")

        # download button
        b = patched.encode("utf-8")
        b64 = base64.b64encode(b).decode()
        href = f'<a href="data:file/text;base64,{b64}" download="optimized.py">Download optimized.py</a>'
        st.markdown(href, unsafe_allow_html=True)

        # small comparison
        st.write("### Estimated Impact (heuristic)")
        runs = 1000
        co2_per_run = energy["co2_g"]
        st.write(f"CO₂ per run: {co2_per_run:.4f} g")
        st.write(f"CO₂ for {runs} runs: {co2_per_run * runs:.2f} g ({(co2_per_run * runs)/1000:.3f} kg)")

        # present simple before/after note (we didn't actually re-estimate patched code)
        st.info("Note: The naive patcher adds inline suggestions/comments. For real impact, you'd replace code with optimized snippets. This prototype is conservative.")
