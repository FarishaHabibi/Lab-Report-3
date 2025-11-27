# labreport3.py
# Single-file Streamlit app with the rule engine and UI
# Save and run with: streamlit run labreport3.py

import streamlit as st
import json
from typing import Any, Dict, List

st.set_page_config(page_title="Scholarship Advisory (Single File)", layout="centered")

# ---------------------------------------------------------------------
# DEFAULT RULES (use EXACTLY these as required by the assignment)
# ---------------------------------------------------------------------
DEFAULT_RULES = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    }
]

# ---------------------------------------------------------------------
# Helpers: safe type conversions and condition checks
# ---------------------------------------------------------------------
def _safe_numeric_convert(value: Any):
    """Try to convert strings to int/float; keep numbers unchanged; return None for None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return None
        # try int then float
        try:
            if '.' in s:
                return float(s)
            return int(s)
        except Exception:
            try:
                return float(s)
            except Exception:
                return s  # return original string if cannot convert
    return value

def _check_condition(value: Any, operator: str, threshold: Any) -> bool:
    """Evaluate single condition safely. Returns False for incompatible types or missing values."""
    v = _safe_numeric_convert(value)
    t = threshold
    if v is None:
        return False

    try:
        if operator == ">=":
            return v >= t
        if operator == "<=":
            return v <= t
        if operator == ">":
            return v > t
        if operator == "<":
            return v < t
        if operator == "==":
            return v == t
    except Exception:
        return False

    return False

# ---------------------------------------------------------------------
# Rule evaluation functions
# ---------------------------------------------------------------------
def evaluate_applicant_with_rules(applicant: Dict[str, Any], rules: List[Dict[str, Any]]):
    """
    Evaluate applicant against rules.
    Returns:
      - action dict (decision + reason) for the selected rule
      - matched_rules list for transparency (ordered by priority desc)
    """
    matched = []
    for rule in rules:
        conds = rule.get("conditions", [])
        all_ok = True
        for cond in conds:
            if len(cond) != 3:
                all_ok = False
                break
            attr, op, val = cond
            if not _check_condition(applicant.get(attr), op, val):
                all_ok = False
                break
        if all_ok:
            matched.append(rule)

    if not matched:
        return {"decision": "NO_MATCH", "reason": "No available rule matched."}, []

    selected = max(matched, key=lambda r: r.get("priority", 0))
    matched_sorted = sorted([(r["name"], r.get("priority", 0)) for r in matched], key=lambda x: -x[1])
    return selected["action"], matched_sorted

# ---------------------------------------------------------------------
# Session state: store rules (allow editing in sidebar)
# ---------------------------------------------------------------------
if "rules" not in st.session_state:
    st.session_state["rules"] = DEFAULT_RULES.copy()

# ---------------------------------------------------------------------
# Page UI
# ---------------------------------------------------------------------
st.title("Scholarship Advisory — Rule-Based Decision Support (Single File)")
st.markdown(
    "This app evaluates scholarship applicants using a transparent rule-based engine. "
    "You can view or edit the rules in the sidebar (JSON) — **be careful to keep structure valid**."
)

# Sidebar: JSON editor for rules
with st.sidebar.expander("Rules (JSON editor)"):
    st.write("Edit rules here if needed. Use valid JSON array syntax and maintain the rule structure.")
    rules_json_str = st.text_area(
        "Rules JSON",
        value=json.dumps(st.session_state["rules"], indent=2),
        height=380
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load rules"):
            try:
                parsed = json.loads(rules_json_str)
                if not isinstance(parsed, list):
                    st.error("Rules must be a JSON array (list of rule objects).")
                else:
                    st.session_state["rules"] = parsed
                    st.success("Rules loaded into session.")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
    with col2:
        if st.button("Reset to DEFAULT"):
            st.session_state["rules"] = DEFAULT_RULES.copy()
            st.experimental_rerun()
    st.download_button("Download rules JSON", data=json.dumps(st.session_state["rules"], indent=2), file_name="rules.json", mime="application/json")

# Main: applicant form
st.subheader("Applicant Facts")
with st.form("app_form"):
    cgpa = st.number_input("Cumulative GPA (CGPA)", min_value=0.0, max_value=4.0, value=3.0, step=0.01)
    family_income = st.number_input("Monthly Family Income (RM)", min_value=0, value=5000, step=100)
    co_curricular_score = st.number_input("Co-curricular Involvement Score (0–100)", min_value=0, max_value=100, value=50)
    community_service = st.number_input("Community Service Hours", min_value=0, value=0)
    current_semester = st.number_input("Current Semester", min_value=1, value=1)
    disciplinary_actions = st.number_input("Number of Disciplinary Actions", min_value=0, value=0)
    submit = st.form_submit_button("Evaluate Applicant")

if submit:
    applicant = {
        "cgpa": cgpa,
        "family_income": family_income,
        "co_curricular_score": co_curricular_score,
        "community_service": community_service,
        "current_semester": current_semester,
        "disciplinary_actions": disciplinary_actions
    }

    action, matched_rules = evaluate_applicant_with_rules(applicant, st.session_state["rules"])

    st.markdown("---")
    st.subheader("Decision")
    st.write(f"**{action.get('decision', '—')}**")
    st.write("**Reason:**", action.get("reason", ""))

    st.subheader("Matched Rules (transparency)")
    if matched_rules:
        for name, pr in matched_rules:
            st.write(f"- {name} (priority {pr})")
    else:
        st.write("No rules matched this applicant (NO_MATCH).")

    result_record = {
        "cgpa": cgpa,
        "family_income": family_income,
        "co_curricular_score": co_curricular_score,
        "community_service": community_service,
        "current_semester": current_semester,
        "disciplinary_actions": disciplinary_actions,
        "decision": action.get("decision"),
        "reason": action.get("reason"),
        "matched_rules": "; ".join([f"{n} (p={p})" for n,p in matched_rules]) if matched_rules else ""
    }
    csv_line = ",".join(map(str, result_record.values()))
    csv_header = ",".join(result_record.keys())
    csv_content = csv_header + "\n" + csv_line

    st.download_button("Download evaluation (CSV)", data=csv_content, file_name="evaluation.csv", mime="text/csv")

# Footer / notes
st.caption("Rules follow the structure: {name, priority, conditions: [[attr, op, val], ...], action: {decision, reason}}")
st.caption("Operators supported: >=, <=, >, <, ==. Keep data types compatible (numbers for comparisons).")
