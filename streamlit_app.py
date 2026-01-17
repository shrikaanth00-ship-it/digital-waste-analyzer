# streamlit_app.py
import streamlit as st
from rules import RuleEngine
from estimator import estimate_block_runtime, complexity_score
from carbon import estimate_energy_and_co2
from suggester import generate_suggestions, naive_apply_patch
import base64

# -----------------------------
# Human-readable impact helpers
# -----------------------------

def energy_to_human(kwh):
    if kwh < 0.005:
        return "Less than charging a smartphone for a few minutes"
    elif kwh < 0.02:
        return "Equivalent to running a laptop for about 20 minutes"
    elif kwh < 0.1:
        return "Equivalent to charging a smartphone once"
    else:
        return "Equivalent to running an LED bulb for several hours"


def co2_to_human(co2_g):
    if co2_g < 1:
        return "Comparable to keeping a small LED bulb ON for a few minutes"
    elif co2_g < 10:
        return "Comparable to keeping a light ON for about 1 hour"
    elif co2_g < 50:
        return "Comparable to driving a petrol car for a short distance"
    else:
        return "Comparable to multiple everyday household activities"


st.set_page_config(page_title="Digital Waste Analyzer", layout="wide")
st.title("🌿 Digital Waste Analyzer — Code Carbon Checker (Prototype)")

with st.sidebar:
    st.header("Quick help")
    st.markdown("""
    1. Upload a Python `.py` file or paste code.
    2. Click **Analyze**.
    3. Review findings and suggestions.
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

# Run analysis when user clicks
if st.button("Analyze"):
    # create engine and get findings
    try:
        engine = RuleEngine(source_code)
        findings = engine.get_findings()
    except Exception as e:
        st.error("An unexpected error occurred during analysis.")
        st.write("Error:", str(e))
        st.stop()

    # Safety: if parser reported syntax error, show friendly message
    if findings and findings[0].get("rule_id") == "SYNTAX_ERROR":
        st.error("❌ Invalid Python syntax detected. Please fix your code and try again.")
        st.code(findings[0].get("snippet", "Syntax error"))
        st.stop()

    # proceed with estimator and suggestions
    est_seconds = estimate_block_runtime(findings)
    complexity = complexity_score(findings)
    energy = estimate_energy_and_co2(est_seconds, cpu_watts=cpu_watts, carbon_intensity_g_per_kwh=carbon_intensity)

    base = 100.0
    penalty = complexity
    final_score = max(0, base - penalty)
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
    st.subheader("🌱 Human-Readable Environmental Impact")
    st.write(f"🔌 **Energy Impact:** {energy_to_human(energy['kwh'])}")
    st.write(f"🌍 **Carbon Impact:** {co2_to_human(energy['co2_g'])}")
    st.caption("These equivalents are approximate and shown for intuitive understanding.")


    st.write("**Findings**")
    if not findings:
        st.success("No issues detected.")
    else:
        for f in findings:
            with st.expander(f"{f['rule_id']} | {f['severity'].upper()} | line {f.get('lineno')}"):
                st.write(f"**Snippet:** `{f.get('snippet')}`")
                st.write(f"**Message:** {f.get('message')}")
                st.write(f"**Suggestion:** {f.get('suggestion')}")

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

    patched = naive_apply_patch(source_code, findings)
    st.write("**Optimized (naive) file**")
    st.code(patched, language="python")

    b = patched.encode("utf-8")
    b64 = base64.b64encode(b).decode()
    href = f'<a href="data:file/text;base64,{b64}" download="optimized.py">Download optimized.py</a>'
    st.markdown(href, unsafe_allow_html=True)

