# pacemaker.py
# Gandhar Mahadeshwar
# 2025-08-15
# This is a Streamlit app that allows you to build a PACE/PANCE campaign.
# It is a work in progress and is not yet functional.

import json, yaml, hashlib, os, io
from datetime import datetime, timezone, timedelta
from dateutil import tz
from jsonschema import Draft202012Validator
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# === Load schema (embed or read from file) ===
PACE_SCHEMA = {
    "$schema": "http://json-schema.org/draft/2020-12/schema#",
    "type": "object",
    "properties": {
        "schema_version": {"type": "string"},
        "campaign": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "title": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
                "starting_protein": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "dna_seq": {"type": "string"},
                        "aa_seq": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                        "vector_context": {"type": "string"}
                    }
                },
                "host_system": {
                    "type": "object",
                    "properties": {
                        "strain": {"type": "string"},
                        "genotype": {"type": "string"},
                        "F_prime_status": {"type": "string"},
                        "plasmids": {
                            "type": "object",
                            "properties": {
                                "AP": {"type": "string"},
                                "CP": {"type": "string"},
                                "MP": {"type": "string"},
                                "DP": {"type": "string"}
                            }
                        },
                        "resistances": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "arms": {"type": "object"},
                "segments": {"type": "array"},
                "selection_circuits": {"type": "object"},
                "analyses": {"type": "array"},
                "attachments": {"type": "array"},
                "ontologies": {"type": "object"},
                "notes": {"type": "string"}
            }
        }
    }
}

try:
    schema = json.loads(json.dumps(PACE_SCHEMA)) # Convert to JSON string and then load
except Exception:
    st.stop()

validator = Draft202012Validator(schema)

# ---- Helpers ----
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def empty_campaign():
    return {
        "schema_version": "0.1.0",
        "campaign": {
            "campaign_id": "",
            "title": "",
            "created_at": now_iso(),
            "created_by": "",
            "starting_protein": {
                "name": "",
                "dna_seq": "",
                "aa_seq": "",
                "features": [],
                "vector_context": ""
            },
            "host_system": {
                "strain": "",
                "genotype": "",
                "F_prime_status": "",
                "plasmids": {"AP": "", "CP": "", "MP": "", "DP": ""},
                "resistances": []
            },
            "arms": {},
            "segments": [],
            "selection_circuits": {},
            "analyses": [],
            "attachments": [],
            "ontologies": {},
            "notes": ""
        }
    }

def validate_doc(doc):
    return sorted(validator.iter_errors(doc), key=lambda e: e.path)

def show_errors(errors):
    if not errors:
        st.success("Valid ✓")
        return
    st.error(f"{len(errors)} validation error(s):")
    for e in errors:
        path = "$" + "".join([f".{p}" if isinstance(p, str) else f"[{p}]" for p in e.path])
        st.code(f"{path}: {e.message}")

def create_sample_campaign():
    """Create sample campaign data to demonstrate the schematic visualization"""
    base_time = datetime.now(timezone.utc)
    
    return {
        "schema_version": "0.1.0",
        "campaign": {
            "campaign_id": "sample-campaign",
            "title": "Sample PACE Campaign - T3 and SP6 Pathways",
            "created_at": base_time.isoformat(),
            "created_by": "demo-user",
            "starting_protein": {
                "name": "Sample_Protein_v0",
                "dna_seq": "ATG...TAA",
                "aa_seq": "M...*",
                "features": [],
                "vector_context": "pBAD-MCS"
            },
            "host_system": {
                "strain": "S2060",
                "genotype": "ΔendA ΔrecA F+",
                "F_prime_status": "F' lacIq",
                "plasmids": {"AP": "ap-pt7-v3", "CP": "cp-T7RNAP", "MP": "MP6", "DP": "DP6"},
                "resistances": ["ampicillin", "chloramphenicol"]
            },
            "arms": {
                "arm-t3": {
                    "arm_id": "arm-t3",
                    "label": "T3 Pathway",
                    "description": "T3 promoter evolution pathway",
                    "status": "active",
                    "timepoints": []
                },
                "arm-sp6": {
                    "arm_id": "arm-sp6", 
                    "label": "SP6 Pathway",
                    "description": "SP6 promoter evolution pathway",
                    "status": "active",
                    "timepoints": []
                }
            },
            "selection_circuits": {
                "sel-t3-pathway": {
                    "id": "sel-t3-pathway",
                    "type": "RNAP_promoter",
                    "ap_details": "pBAD variant; pIII under T7/T3 promoter",
                    "cp_details": "T7 RNAP expressed via arabinose",
                    "reporter_gene": "gIII",
                    "negative_selection": "gIII-neg",
                    "stepping_stones": ["T7/T3", "T3", "T3/final", "final"],
                    "version": "1.0"
                },
                "sel-sp6-pathway": {
                    "id": "sel-sp6-pathway",
                    "type": "RNAP_promoter", 
                    "ap_details": "pBAD variant; pIII under T7/SP6 promoter",
                    "cp_details": "T7 RNAP expressed via arabinose",
                    "reporter_gene": "gIII",
                    "negative_selection": "gIII-neg",
                    "stepping_stones": ["T7/SP6", "SP6", "SP6/final", "final"],
                    "version": "1.0"
                }
            },
            "segments": [
                {
                    "segment_id": "seg-01-t3-init",
                    "mode": "PACE",
                    "applied_to_arms": ["arm-t3"],
                    "start_time": base_time.isoformat(),
                    "end_time": (base_time + timedelta(hours=48)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-t3-pathway",
                        "stepping_stones": ["T7/T3"]
                    }
                },
                {
                    "segment_id": "seg-02-t3-evolve", 
                    "mode": "PACE",
                    "applied_to_arms": ["arm-t3"],
                    "start_time": (base_time + timedelta(hours=48)).isoformat(),
                    "end_time": (base_time + timedelta(hours=96)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-t3-pathway",
                        "stepping_stones": ["T3"]
                    }
                },
                {
                    "segment_id": "seg-03-t3-final",
                    "mode": "PACE", 
                    "applied_to_arms": ["arm-t3"],
                    "start_time": (base_time + timedelta(hours=96)).isoformat(),
                    "end_time": (base_time + timedelta(hours=144)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-t3-pathway",
                        "stepping_stones": ["T3/final", "final"]
                    }
                },
                {
                    "segment_id": "seg-01-sp6-init",
                    "mode": "PACE",
                    "applied_to_arms": ["arm-sp6"], 
                    "start_time": base_time.isoformat(),
                    "end_time": (base_time + timedelta(hours=48)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-sp6-pathway",
                        "stepping_stones": ["T7/SP6"]
                    }
                },
                {
                    "segment_id": "seg-02-sp6-evolve",
                    "mode": "PACE",
                    "applied_to_arms": ["arm-sp6"],
                    "start_time": (base_time + timedelta(hours=48)).isoformat(), 
                    "end_time": (base_time + timedelta(hours=96)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-sp6-pathway",
                        "stepping_stones": ["SP6"]
                    }
                },
                {
                    "segment_id": "seg-03-sp6-final",
                    "mode": "PACE",
                    "applied_to_arms": ["arm-sp6"],
                    "start_time": (base_time + timedelta(hours=96)).isoformat(),
                    "end_time": (base_time + timedelta(hours=144)).isoformat(),
                    "selection_design": {
                        "selection_circuit_id": "sel-sp6-pathway", 
                        "stepping_stones": ["SP6/final", "final"]
                    }
                }
            ],
            "analyses": [],
            "attachments": [],
            "ontologies": {},
            "notes": "Sample campaign demonstrating T3 and SP6 pathway visualization"
        }
    }

def generate_pace_schematic(campaign_data):
    """Generate a real-time PACE/PANCE schematic visualization similar to the image"""
    if not campaign_data.get("arms") or not campaign_data.get("segments"):
        return None
    
    # Helper function to parse time to hours
    def parse_time_to_hours(time_str, base_time=None):
        """Convert ISO datetime string to hours from base time"""
        if not time_str:
            return 0
        
        try:
            # Handle different time formats
            if time_str.endswith('Z'):
                time_str = time_str.replace('Z', '+00:00')
            
            dt = datetime.fromisoformat(time_str)
            if base_time is None:
                base_time = datetime.now(timezone.utc)
            
            # Calculate hours difference
            hours = (dt - base_time).total_seconds() / 3600
            return max(0, hours)  # Ensure non-negative
        except:
            # Fallback: try to extract numeric value
            try:
                return float(time_str) if time_str.replace('.', '').replace('-', '').isdigit() else 0
            except:
                return 0
    
    # Create figure with subplots
    fig = make_subplots(
        rows=1, cols=1,
        subplot_titles=("PACE/PANCE Campaign Schematic"),
        specs=[[{"secondary_y": False}]]
    )
    
    # Color scheme for different promoter types (matching the image)
    color_map = {
        "T7/T3": "#ff6b6b",      # Light red/pink for T3 pathway
        "T3": "#ff7f0e",         # Orange for T3 promoter
        "T3/final": "#9acd32",   # Olive green for T3/final
        "T7/SP6": "#4ecdc4",     # Light blue for SP6 pathway
        "SP6": "#2ca02c",        # Green for SP6 promoter
        "SP6/final": "#20b2aa",  # Teal green for SP6/final
        "final": "#32cd32",      # Green for final promoter
        "default": "#9467bd"     # Purple for unknown
    }
    
    # Track time ranges for each arm
    arm_data = {}
    
    # Process segments to understand the experimental flow
    for segment in campaign_data.get("segments", []):
        segment_id = segment.get("segment_id", "")
        mode = segment.get("mode", "PACE")
        arms = segment.get("applied_to_arms", [])
        start_time = segment.get("start_time", "")
        end_time = segment.get("end_time", "")
        selection_circuit = segment.get("selection_design", {}).get("selection_circuit_id", "")
        stepping_stones = segment.get("selection_design", {}).get("stepping_stones", [])
        
        # Try to extract promoter type from selection circuit and stepping stones
        promoter_type = "default"
        if selection_circuit:
            circuit_data = campaign_data.get("selection_circuits", {}).get(selection_circuit, {})
            circuit_type = circuit_data.get("type", "")
            stepping_stones_circuit = circuit_data.get("stepping_stones", [])
            
            # Check stepping stones for promoter progression
            if stepping_stones:
                if "T3" in stepping_stones[0] if stepping_stones else False:
                    promoter_type = "T7/T3"
                elif "SP6" in stepping_stones[0] if stepping_stones else False:
                    promoter_type = "T7/SP6"
                elif "T3" in circuit_type or "T3" in selection_circuit:
                    promoter_type = "T3"
                elif "SP6" in circuit_type or "SP6" in selection_circuit:
                    promoter_type = "SP6"
                elif "T7" in circuit_type or "T7" in selection_circuit:
                    promoter_type = "T7/T3"  # Default to T3 pathway
        
        # Convert time strings to hours using improved parsing
        base_time = datetime.now(timezone.utc)
        start_hours = parse_time_to_hours(start_time, base_time)
        end_hours = parse_time_to_hours(end_time, base_time) if end_time else start_hours + 72
        
        # Ensure minimum duration and logical progression
        if end_hours <= start_hours:
            end_hours = start_hours + 72  # Default 72 hours if no valid end time
        
        # Add data for each arm
        for arm_id in arms:
            if arm_id not in arm_data:
                arm_data[arm_id] = []
            arm_data[arm_id].append({
                "segment": segment_id,
                "promoter": promoter_type,
                "mode": mode,
                "start": start_hours,
                "end": end_hours,
                "color": color_map.get(promoter_type, color_map["default"]),
                "stepping_stones": stepping_stones
            })
    
    # Create the visualization
    y_positions = {}
    current_y = 0
    
    # Sort arms for consistent ordering
    sorted_arms = sorted(arm_data.keys())
    
    for arm_id in sorted_arms:
        segments = arm_data[arm_id]
        if arm_id not in y_positions:
            y_positions[arm_id] = current_y
            current_y += 1
        
        y_pos = y_positions[arm_id]
        
        # Add arm label
        fig.add_annotation(
            x=-20, y=y_pos,
            text=f"<b>{arm_id}</b>",
            showarrow=False,
            font=dict(size=14, color="black"),
            xanchor="right",
            yanchor="middle"
        )
        
        # Add pathway background (similar to image)
        pathway_color = "rgba(255, 182, 193, 0.1)"  # Light pink for T3 pathway
        if any("SP6" in seg["promoter"] for seg in segments):
            pathway_color = "rgba(173, 216, 230, 0.1)"  # Light blue for SP6 pathway
        
        # Add pathway background rectangle
        if segments:
            min_time = min(seg["start"] for seg in segments)
            max_time = max(seg["end"] for seg in segments)
            fig.add_shape(
                type="rect",
                x0=min_time - 10, y0=y_pos - 0.4,
                x1=max_time + 10, y1=y_pos + 0.4,
                fillcolor=pathway_color,
                opacity=0.3,
                line=dict(color="gray", width=1, dash="dot")
            )
        
        # Add segments as rectangles with progression
        for i, seg in enumerate(segments):
            # Main segment rectangle
            fig.add_shape(
                type="rect",
                x0=seg["start"], y0=y_pos - 0.3,
                x1=seg["end"], y1=y_pos + 0.3,
                fillcolor=seg["color"],
                opacity=0.8,
                line=dict(color="black", width=2)
            )
            
            # Add segment label
            label_text = f"{seg['segment']}<br>({seg['mode']})"
            if seg["stepping_stones"]:
                label_text += f"<br>{', '.join(seg['stepping_stones'])}"
            
            fig.add_annotation(
                x=(seg["start"] + seg["end"]) / 2, y=y_pos,
                text=label_text,
                showarrow=False,
                font=dict(size=10, color="white"),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor="black",
                borderwidth=1
            )
            
            # Add arrows between segments (progression arrows)
            if i < len(segments) - 1:
                next_seg = segments[i + 1]
                fig.add_annotation(
                    x=seg["end"], y=y_pos,
                    xref="x", yref="y",
                    ax=seg["end"] + 8, ay=y_pos,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=3,
                    arrowcolor="black"
                )
                
                # Add transition label
                fig.add_annotation(
                    x=seg["end"] + 4, y=y_pos + 0.1,
                    text="→",
                    showarrow=False,
                    font=dict(size=16, color="black"),
                    xanchor="center",
                    yanchor="middle"
                )
    
    # Add time axis with proper scaling
    max_time = max([max([seg["end"] for seg in arm_segments]) for arm_segments in arm_data.values()]) if arm_data else 200
    
    # Add time markers every 24 hours
    for hour in range(0, int(max_time) + 25, 24):
        fig.add_annotation(
            x=hour, y=-0.8,
            text=f"{hour}h",
            showarrow=False,
            font=dict(size=10, color="gray"),
            xanchor="center",
            yanchor="top"
        )
        # Add vertical line
        fig.add_shape(
            type="line",
            x0=hour, y0=-0.5,
            x1=hour, y1=len(arm_data) - 0.5,
            line=dict(color="lightgray", width=1, dash="dot")
        )
    
    fig.update_layout(
        title="PACE/PANCE Campaign Schematic",
        xaxis_title="Time (hours)",
        yaxis_title="Experimental Arms",
        xaxis=dict(
            range=[-30, max_time + 30],
            showgrid=True,
            gridcolor="lightgray",
            zeroline=False
        ),
        yaxis=dict(
            range=[-1, len(arm_data)],
            showgrid=False,
            zeroline=False
        ),
        height=500 + len(arm_data) * 120,
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(l=100, r=50, t=100, b=100)
    )
    
    # Add legend for promoter types
    legend_y = 1.02
    legend_x = 0.02
    for promoter, color in color_map.items():
        if promoter != "default":
            fig.add_annotation(
                x=legend_x, y=legend_y,
                text=f"<b>{promoter}</b>",
                showarrow=False,
                font=dict(size=12, color=color),
                xanchor="left",
                yanchor="bottom",
                xref="paper", yref="paper"
            )
            legend_y -= 0.04
            if legend_y < 0.8:  # Start new column
                legend_x += 0.3
                legend_y = 1.02
    
    return fig

# ---- App State ----
if "doc" not in st.session_state:
    st.session_state.doc = empty_campaign()

st.set_page_config(page_title="PACE Pacemaker", layout="wide")
st.title("PACEmaker — PACE/PANCE Campaign Builder")

# === Sidebar: Import/Export ===
with st.sidebar:
    st.header("Import / Export")
    uploaded_json = st.file_uploader("Import existing JSON", type=["json"])
    if uploaded_json:
        try:
            st.session_state.doc = json.loads(uploaded_json.read().decode("utf-8"))
            st.success("Loaded JSON.")
        except Exception as ex:
            st.error(f"Failed to parse JSON: {ex}")

    if st.button("Validate Now"):
        show_errors(validate_doc(st.session_state.doc))

    st.download_button(
        "Download JSON",
        data=json.dumps(st.session_state.doc, indent=2).encode("utf-8"),
        file_name="campaign.json",
        mime="application/json",
    )
    st.download_button(
        "Download YAML",
        data=yaml.safe_dump(st.session_state.doc, sort_keys=False).encode("utf-8"),
        file_name="campaign.yaml",
        mime="text/yaml",
    )

# === Tabs ===
tabs = st.tabs([
    "Campaign", "Selection Circuits", "Arms & Timepoints",
    "Lagoons & Samples", "Segments", "Analyses", "Attachments", "Ontologies", "Schematic", "Validate"
])

c = st.session_state.doc["campaign"]

# --- Campaign tab ---
with tabs[0]:
    st.subheader("Campaign Header")
    col1, col2 = st.columns(2)
    with col1:
        c["campaign_id"] = st.text_input(
            "Campaign ID (slug)", c.get("campaign_id", ""),
            placeholder="cmp-2025-mdh-evolution"
        )
        c["title"] = st.text_input(
            "Title", c.get("title", ""),
            placeholder="Evolving Mdh variants to promoter X"
        )
        c["created_by"] = st.text_input(
            "Created by", c.get("created_by", ""),
            placeholder="liu-lab"
        )
    with col2:
        c["created_at"] = st.text_input(
            "Created at (ISO8601)", c.get("created_at", now_iso()),
            placeholder="2025-08-15T19:22:00-04:00"
        )
        c["notes"] = st.text_area(
            "Notes", c.get("notes", ""), height=80,
            placeholder="Observations, deviations, etc."
        )

    st.markdown("**Starting Protein**")
    sp = c["starting_protein"]
    sp["name"] = st.text_input("Starting protein name", sp.get("name", ""), placeholder="Mdh_v0", key="sp_name_input")
    sp["dna_seq"] = st.text_area("DNA sequence", sp.get("dna_seq", ""), height=100, placeholder="ATG...TAA", key="sp_dna_seq_input")
    sp["aa_seq"] = st.text_area("AA sequence", sp.get("aa_seq", ""), height=100, placeholder="M...*", key="sp_aa_seq_input")
    sp["vector_context"] = st.text_input("Vector context", sp.get("vector_context", ""), placeholder="pBAD-MCS; N-term 6xHis", key="sp_vector_context_input")

    st.markdown("**Host System**")
    hs = c["host_system"]
    hs["strain"] = st.text_input("Strain", hs.get("strain", ""), placeholder="S2060", key="hs_strain_input")
    hs["genotype"] = st.text_input("Genotype", hs.get("genotype", ""), placeholder="ΔendA ΔrecA F+", key="hs_genotype_input")
    hs["F_prime_status"] = st.text_input("F’ status", hs.get("F_prime_status", ""), placeholder="F' lacIq")
    cols = st.columns(4)
    hs["plasmids"]["AP"] = cols[0].text_input("AP plasmid", hs["plasmids"].get("AP", ""), placeholder="ap-pt7-v3")
    hs["plasmids"]["CP"] = cols[1].text_input("CP plasmid", hs["plasmids"].get("CP", ""), placeholder="cp-T7RNAP")
    hs["plasmids"]["MP"] = cols[2].text_input("MP plasmid", hs["plasmids"].get("MP", ""), placeholder="MP6")
    hs["plasmids"]["DP"] = cols[3].text_input("DP plasmid", hs["plasmids"].get("DP", ""), placeholder="DP6")
    hs_res_txt = st.text_input("Resistances (comma-separated)", ",".join(hs.get("resistances", [])), placeholder="ampicillin, chloramphenicol")
    hs["resistances"] = [v.strip() for v in hs_res_txt.split(",") if v.strip()]

# --- Selection Circuits ---
with tabs[1]:
    st.subheader("Selection Circuits")
    sc_map = c["selection_circuits"]
    with st.expander("Add selection circuit", expanded=True):
        col1, col2 = st.columns(2)
        sc_id = col1.text_input("Circuit ID (slug)", "", placeholder="sel-rnap-final-v3", key="sc_id_input")
        sc_type = col2.selectbox("Type", ["RNAP_promoter","one_hybrid","two_hybrid","protease_split","base_editing","gVI","other"], key="sc_type_select")
        st.caption("e.g., RNAP_promoter for pIII under an engineered promoter")
        apd = st.text_input("AP details", placeholder="pBAD variant; pIII under T7 promoter", key="sc_ap_details_input")
        cpd = st.text_input("CP details", placeholder="T7 RNAP expressed via arabinose", key="sc_cp_details_input")
        rep = st.selectbox("Reporter gene", ["gIII","gVI","other"], key="sc_reporter_select")
        st.caption("e.g., gIII")
        neg = st.text_input("Negative selection", placeholder="gIII-neg (AraC-pIIIneg)", key="sc_neg_selection_input")
        stones = st.text_input("Stepping stones (comma-separated)", placeholder="T7/T3, T3, final", key="sc_stones_input")
        ver = st.text_input("Version", placeholder="3.1", key="sc_version_input")
        if st.button("Add circuit"):
            if not sc_id:
                st.warning("Provide circuit ID.")
            elif sc_id in sc_map:
                st.warning("ID already exists.")
            else:
                sc_map[sc_id] = {
                    "id": sc_id, "type": sc_type, "ap_details": apd, "cp_details": cpd,
                    "reporter_gene": rep, "negative_selection": neg,
                    "stepping_stones": [s.strip() for s in stones.split(",") if s.strip()],
                    "version": ver
                }
                st.success(f"Added selection circuit {sc_id}")

    if sc_map:
        st.json(sc_map)

# --- Arms & Timepoints ---
with tabs[2]:
    st.subheader("Arms")
    arms = c["arms"]
    with st.expander("Add arm", expanded=True):
        a_id = st.text_input("Arm ID (slug)", "", placeholder="arm-A", key="arm_id_input")
        a_label = st.text_input("Label", "", placeholder="High stringency", key="arm_label_input")
        a_desc = st.text_input("Description", "", placeholder="Ramp dilution to 2.0 vol/h", key="arm_desc_input")
        if st.button("Create arm"):
            if not a_id:
                st.warning("Provide arm ID.")
            elif a_id in arms:
                st.warning("Arm ID exists.")
            else:
                arms[a_id] = {
                    "arm_id": a_id,
                    "label": a_label,
                    "description": a_desc,
                    "status": "active",
                    "timepoints": []
                }
                st.success(f"Added arm {a_id}")

    if arms:
        arm_choice = st.selectbox("Select arm to edit", list(arms.keys()))
        arm = arms[arm_choice]
        st.write(f"**{arm_choice}** — {arm.get('label','')}")
        with st.expander("Add timepoint", expanded=True):
            t_idx = st.number_input("t (integer)", min_value=0, step=1, value=0)
            st.caption("e.g., 0 for baseline, 1, 2, …")
            t_stamp = st.text_input("timestamp (ISO8601)", now_iso(), placeholder="2025-08-16T09:00:00Z", key="timepoint_timestamp_input")
            if st.button("Add timepoint"):
                arm["timepoints"].append({
                    "t": int(t_idx),
                    "timestamp": t_stamp,
                    "global_events": [],
                    "lagoons": {}
                })
                st.success(f"Timepoint t={t_idx} added.")

        if arm["timepoints"]:
            tp_labels = [f"idx {i}: t={tp['t']}" for i, tp in enumerate(arm["timepoints"])]
            tp_idx = st.selectbox("Select timepoint", list(range(len(arm["timepoints"]))), format_func=lambda i: tp_labels[i])
            st.json(arm["timepoints"][tp_idx])

# --- Lagoons & Samples ---
with tabs[3]:
    if not c["arms"]:
        st.info("Create an arm and timepoint first.")
    else:
        arm_id = st.selectbox("Arm", list(c["arms"].keys()))
        arm = c["arms"][arm_id]
        if not arm["timepoints"]:
            st.info("Add a timepoint in the previous tab.")
        else:
            tp_idx = st.selectbox("Timepoint", list(range(len(arm["timepoints"]))), format_func=lambda i: f"t={arm['timepoints'][i]['t']}")
            tp = arm["timepoints"][tp_idx]
            lagoons = tp["lagoons"]

            with st.expander("Add lagoon", expanded=True):
                lg_id = st.text_input("Lagoon ID (slug)", "", placeholder="lg-1", key="lagoon_id_input")
                cond_label = st.text_input("Condition label", "", placeholder="Step1_T7/T3_low_stringency", key="lagoon_cond_label_input")
                mut_on = st.checkbox("Mutagenesis ON?", value=False)
                mode = st.selectbox("Mode", ["PACE","PANCE"])
                st.caption("Select PACE or PANCE")
                volume = st.number_input("Volume (ml)", min_value=0.0, value=40.0)
                st.caption("e.g., 40.0")
                drate = st.number_input("Dilution rate (vol/hr) [PACE]", min_value=0.0, value=1.0, help="Required for PACE")
                pfrac = st.number_input("Passage fraction [PANCE]", min_value=0.0, max_value=1.0, value=0.0, help="Required for PANCE")
                tempc = st.number_input("Temp (°C)", value=37.0)
                st.caption("e.g., 37.0")
                media = st.text_input("Media", "2xYT+glucose", placeholder="2xYT+glucose", key="lagoon_media_input")

                inducers = st.text_input("Inducers (name:conc_mM; comma-separated)", "", placeholder="arabinose:10, IPTG:0.5", key="lagoon_inducers_input")
                abx = st.text_input("Antibiotics (name:ug_per_ml; comma-separated)", "", placeholder="ampicillin:100, chloramphenicol:25", key="lagoon_antibiotics_input")

                titer_val = st.number_input("Phage titer (PFU/ml)", min_value=0.0, value=1e8)
                st.caption("e.g., 3.2e8")
                titer_method = st.selectbox("Titer method", ["plaque","qPCR","spectro","other"])

                if st.button("Add lagoon"):
                    if not lg_id:
                        st.warning("Provide lagoon ID.")
                    elif lg_id in lagoons:
                        st.warning("Lagoon ID exists.")
                    else:
                        # Parse lists
                        ind_list, abx_list = [], []
                        for tok in [t.strip() for t in inducers.split(",") if t.strip()]:
                            if ":" in tok:
                                n, v = tok.split(":", 1)
                                try:
                                    ind_list.append({"name": n.strip(), "concentration_mM": float(v)})
                                except:  # noqa: E722
                                    pass
                        for tok in [t.strip() for t in abx.split(",") if t.strip()]:
                            if ":" in tok:
                                n, v = tok.split(":", 1)
                                try:
                                    abx_list.append({"name": n.strip(), "concentration_ug_per_ml": float(v)})
                                except:  # noqa: E722
                                    pass
                        cond = {
                            "mode": mode,
                            "volume_ml": volume,
                            "temp_c": tempc,
                            "media": media,
                            "antibiotics": abx_list,
                            "inducers": ind_list
                        }
                        if mode == "PACE":
                            cond["dilution_rate_vol_per_hr"] = drate
                        else:
                            cond["passage_fraction"] = pfrac
                        lagoons[lg_id] = {
                            "lagoon_id": lg_id,
                            "condition_label": cond_label,
                            "mutagenesis_on": bool(mut_on),
                            "conditions": cond,
                            "measurements": {
                                "phage_titer_pfu_per_ml": {"value": titer_val, "method": titer_method}
                            },
                            "samples": []
                        }
                        st.success(f"Added lagoon {lg_id}")

            if lagoons:
                lg_sel = st.selectbox("Edit lagoon", list(lagoons.keys()))
                lagoon = lagoons[lg_sel]

                st.markdown("**Add sample**")
                smp_id = st.text_input("Sample ID (slug)", "", placeholder="s-armA-t000-lg1", key="sample_id_input")
                smp_type = st.selectbox("Sample type", ["phage_supernatant","cells","DNA","RNA"])
                if st.button("Add sample to lagoon"):
                    if not smp_id:
                        st.warning("Provide sample ID.")
                    else:
                        lagoon["samples"].append({"sample_id": smp_id, "sample_type": smp_type, "library_preps": []})
                        st.success(f"Added sample {smp_id}")

                if lagoon["samples"]:
                    s_opts = [s["sample_id"] for s in lagoon["samples"]]
                    s_idx = st.selectbox("Select sample", list(range(len(s_opts))), format_func=lambda i: s_opts[i])
                    sample = lagoon["samples"][s_idx]

                    st.markdown("**Add library prep**")
                    lib_id = st.text_input("Library ID (slug)", "", placeholder="lib-001", key="lib_id_input")
                    protocol = st.text_input("Protocol name/version", "", placeholder="Amplicon-v1", key="lib_protocol_input")
                    amplicons = st.text_input("Amplicon targets (free text)", "", placeholder="mdh_region1; primers XYZ", key="lib_amplicons_input")
                    if st.button("Add library"):
                        if not lib_id:
                            st.warning("Provide library ID.")
                        else:
                            sample["library_preps"].append({
                                "library_id": lib_id,
                                "protocol": protocol,
                                "amplicon_targets": amplicons,
                                "sequencing_runs": []
                            })
                            st.success(f"Added library {lib_id}")

                    if sample["library_preps"]:
                        l_opts = [l["library_id"] for l in sample["library_preps"]]
                        l_idx = st.selectbox("Select library", list(range(len(l_opts))), format_func=lambda i: l_opts[i])
                        lib = sample["library_preps"][l_idx]

                        st.markdown("**Add sequencing run**")
                        run_id = st.text_input("Run ID (slug)", "", placeholder="nsq-240815", key="seq_run_id_input")
                        platform = st.text_input("Platform", "", placeholder="NextSeq2000 P2 100x100", key="seq_platform_input")
                        r1 = st.file_uploader("Upload R1 FASTQ (.gz)", type=["fastq", "fq", "gz"])
                        r2 = st.file_uploader("Upload R2 FASTQ (.gz)", type=["fastq", "fq", "gz"])
                        if st.button("Attach run"):
                            if not run_id:
                                st.warning("Provide run ID.")
                            else:
                                fastqs = []
                                out_dir = "attached_fastqs"
                                os.makedirs(out_dir, exist_ok=True)
                                for label, up in [("R1", r1), ("R2", r2)]:
                                    if up is None:
                                        continue
                                    data = up.getvalue()
                                    sha = hashlib.sha256(data).hexdigest()
                                    size = len(data)
                                    out_path = os.path.join(out_dir, up.name)
                                    with open(out_path, "wb") as f:
                                        f.write(data)
                                    fastqs.append({
                                        "read": label,
                                        "uri": f"file://{os.path.abspath(out_path)}",
                                        "sha256": sha,
                                        "size_bytes": size
                                    })
                                lib.setdefault("sequencing_runs", []).append({
                                    "run_id": run_id,
                                    "platform": platform,
                                    "fastq": fastqs
                                })
                                st.success(f"Attached run {run_id} with {len(fastqs)} FASTQs")

# --- Segments ---
with tabs[4]:
    st.subheader("Segments (PACE/PANCE phases)")
    arms = list(c["arms"].keys())
    with st.expander("Add segment", expanded=True):
        seg_id = st.text_input("Segment ID (slug)", "", placeholder="seg-01", key="seg_id_input")
        seg_mode = st.selectbox("Mode", ["PACE","PANCE"], key="seg_mode_select")
        st.caption("Select PACE or PANCE")
        seg_arms = st.multiselect("Applied to arms", arms, key="seg_arms_multiselect")
        seg_start = st.text_input("Start time (ISO8601)", now_iso(), placeholder="2025-08-16T09:00:00Z", key="seg_start_time")
        seg_end = st.text_input("End time (ISO8601, optional)", "", placeholder="2025-08-17T09:00:00Z", key="seg_end_time")
        sel_circuits = list(c["selection_circuits"].keys())
        if sel_circuits:
            sel_id = st.selectbox("Selection circuit", sel_circuits, key="seg_sel_circuit_select")
        else:
            sel_id = st.text_input("Selection circuit ID", "", placeholder="sel-rnap-final-v3", key="seg_sel_circuit_input")
        stones = st.text_input("Stepping stones (comma-separated)", "", placeholder="T7/T3, T3, final", key="seg_stones_input")
        if st.button("Add segment"):
            if not seg_id or not seg_arms or not sel_id:
                st.warning("Provide segment ID, arms, and selection circuit.")
            else:
                seg = {
                    "segment_id": seg_id,
                    "mode": seg_mode,
                    "applied_to_arms": seg_arms,
                    "start_time": seg_start,
                    "selection_design": {
                        "selection_circuit_id": sel_id,
                        "stepping_stones": [s.strip() for s in stones.split(",") if s.strip()]
                    }
                }
                if seg_end.strip():
                    seg["end_time"] = seg_end.strip()
                c["segments"].append(seg)
                st.success(f"Added segment {seg_id}")

    if c["segments"]:
        st.json(c["segments"])

# --- Analyses ---
with tabs[5]:
    st.subheader("Analyses")
    with st.expander("Add analysis", expanded=True):
        an_id = st.text_input("Analysis ID (slug)", "", placeholder="an-amplicon-01", key="an_id_input")
        pipe = st.text_input("Pipeline (name@version)", "", placeholder="pace-amplicon@0.1.0", key="an_pipeline_input")
        code_hash = st.text_input("Code hash (git or sha)", "", placeholder="a1b2c3d", key="an_code_hash_input")
        env = st.text_area("Env lock (text/URI)", "", placeholder="conda-lock.yaml or s3://bucket/env.yaml", key="an_env_input")
        ref = st.text_input("Reference seq ID", "", placeholder="Mdh_v0", key="an_ref_input")
        inputs = st.text_input("Inputs (IDs; comma-separated)", "", placeholder="lib-001, lib-002", key="an_inputs_input")
        out_align = st.file_uploader("Alignments file(s) (optional)", accept_multiple_files=True)
        out_var = st.file_uploader("Variant table(s) (optional)", accept_multiple_files=True)
        out_cons = st.file_uploader("Consensus FASTA(s) (optional)", accept_multiple_files=True)
        out_sel = st.file_uploader("Selection score table(s) (optional)", accept_multiple_files=True)
        notes = st.text_area("Notes", "", placeholder="Parameters, commits, run context…", key="an_notes_input")

        def stage_files(files):
            outs = []
            if not files:
                return outs
            out_dir = "attached_outputs"
            os.makedirs(out_dir, exist_ok=True)
            for up in files:
                data = up.getvalue()
                sha = hashlib.sha256(data).hexdigest()
                size = len(data)
                out_path = os.path.join(out_dir, up.name)
                with open(out_path, "wb") as f:
                    f.write(data)
                outs.append({"uri": f"file://{os.path.abspath(out_path)}", "sha256": sha, "size_bytes": size})
            return outs

        if st.button("Add analysis"):
            if not an_id or not inputs.strip():
                st.warning("Provide analysis ID and at least one input.")
            else:
                outputs = {
                    "alignments": stage_files(out_align),
                    "variant_tables": stage_files(out_var),
                    "consensus_sequences": stage_files(out_cons),
                    "selection_scores": stage_files(out_sel)
                }
                c["analyses"].append({
                    "analysis_id": an_id,
                    "pipeline_id": pipe,
                    "code_hash": code_hash,
                    "env": env,
                    "ref_seq_id": ref,
                    "params": {},
                    "inputs": [s.strip() for s in inputs.split(",") if s.strip()],
                    "outputs": outputs,
                    "provenance": {"who": c.get("created_by",""), "when": now_iso()},
                    "notes": notes
                })
                st.success(f"Added analysis {an_id}")

    if c["analyses"]:
        st.json(c["analyses"])

# --- Attachments ---
with tabs[6]:
    st.subheader("Attachments (SOPs, plasmid maps, figures)")
    attach = st.file_uploader("Attach files", accept_multiple_files=True)
    if st.button("Add attachments") and attach:
        out_dir = "attachments"
        os.makedirs(out_dir, exist_ok=True)
        for up in attach:
            data = up.getvalue()
            sha = hashlib.sha256(data).hexdigest()
            size = len(data)
            out_path = os.path.join(out_dir, up.name)
            with open(out_path, "wb") as f:
                f.write(data)
            c["attachments"].append({
                "uri": f"file://{os.path.abspath(out_path)}",
                "sha256": sha,
                "size_bytes": size,
                "description": up.name
            })
        st.success(f"Attached {len(attach)} file(s).")
    if c["attachments"]:
        st.json(c["attachments"])

# --- Ontologies ---
with tabs[7]:
    st.subheader("Ontologies (controlled term lists)")
    onto_key = st.text_input("Ontology key", "", placeholder="condition_label", key="onto_key_input")
    onto_vals = st.text_input("Values (comma-separated)", "", placeholder="Step1_T7/T3_low_stringency, Step2_T3, final", key="onto_vals_input")
    if st.button("Add/Replace ontology"):
        if onto_key:
            c.setdefault("ontologies", {})[onto_key] = [v.strip() for v in onto_vals.split(",") if v.strip()]
            st.success(f"Set ontology '{onto_key}'")
    if c.get("ontologies"):
        st.json(c["ontologies"])

# --- Schematic ---
with tabs[8]:
    st.subheader("Real-time PACE/PANCE Campaign Schematic")
    
    # Add controls for visualization
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        **Campaign Visualization** - This schematic shows your PACE/PANCE campaign structure in real-time as you build it.
        The visualization updates automatically as you add arms, segments, and selection circuits.
        """)
    
    with col2:
        # Add refresh button
        if st.button("🔄 Refresh Schematic"):
            st.rerun()
        
        # Add sample data button
        if st.button("📊 Load Sample Data"):
            st.session_state.doc = create_sample_campaign()
            st.success("Sample campaign loaded! The schematic should now display.")
            st.rerun()
    
    # Generate the schematic
    fig = generate_pace_schematic(c)
    
    if fig is None:
        st.info("📊 **No schematic data available yet**")
        st.markdown("""
        **To create a schematic visualization:**
        
        1. **Create Experimental Arms**: Go to "Arms & Timepoints" tab and create experimental arms
        2. **Add Selection Circuits**: Go to "Selection Circuits" tab and define your promoter systems
        3. **Define Segments**: Go to "Segments" tab and add PACE/PANCE phases with time progression
        4. **View Schematic**: Return here to see the real-time visualization
        
        The schematic will show promoter progression over time, similar to the image you provided.
        """)
        
        # Show current campaign status
        st.markdown("### Current Campaign Status")
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            arm_count = len(c.get("arms", {}))
            st.metric("Experimental Arms", arm_count)
        
        with status_col2:
            segment_count = len(c.get("segments", []))
            st.metric("Segments", segment_count)
        
        with status_col3:
            circuit_count = len(c.get("selection_circuits", {}))
            st.metric("Selection Circuits", circuit_count)
            
    else:
        # Display the schematic
        st.plotly_chart(fig, use_container_width=True)
        
        # Add detailed information and controls
        st.markdown("---")
        
        # Campaign summary
        st.markdown("### Campaign Summary")
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            arm_count = len(c.get("arms", {}))
            st.metric("Experimental Arms", arm_count)
        
        with summary_col2:
            segment_count = len(c.get("segments", []))
            st.metric("Segments", segment_count)
        
        with summary_col3:
            circuit_count = len(c.get("selection_circuits", {}))
            st.metric("Selection Circuits", circuit_count)
        
        with summary_col4:
            total_time = 0
            if c.get("segments"):
                for segment in c["segments"]:
                    if segment.get("start_time") and segment.get("end_time"):
                        try:
                            start = datetime.fromisoformat(segment["start_time"].replace('Z', '+00:00'))
                            end = datetime.fromisoformat(segment["end_time"].replace('Z', '+00:00'))
                            total_time = max(total_time, (end - start).total_seconds() / 3600)
                        except:
                            pass
            st.metric("Max Duration (hrs)", f"{total_time:.0f}")
        
        # Detailed legend and interpretation
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🎨 Color Legend")
            st.markdown("""
            **Promoter Types:**
            - **🔴 T7/T3**: Initial T3 pathway (light red/pink)
            - **🟠 T3**: T3 promoter phase (orange)
            - **🟢 T3/final**: T3 to final transition (olive green)
            - **🔵 T7/SP6**: Initial SP6 pathway (light blue)
            - **🟢 SP6**: SP6 promoter phase (green)
            - **🔷 SP6/final**: SP6 to final transition (teal)
            - **🟢 Final**: Final promoter (green)
            - **🟣 Default**: Unknown/other promoters (purple)
            """)
        
        with col2:
            st.markdown("### 📖 How to Interpret")
            st.markdown("""
            **Visual Elements:**
            - **Horizontal rows**: Experimental arms
            - **Colored rectangles**: Time periods for each segment
            - **Arrows (→)**: Progression between segments
            - **Background shading**: Pathway grouping (T3 vs SP6)
            - **Time markers**: 24-hour intervals on x-axis
            - **Labels**: Segment ID, mode, and stepping stones
            
            **Time Progression:**
            - X-axis shows time in hours
            - Segments progress from left to right
            - Multiple arms can run in parallel
            """)
        
        # Show current segments data
        if c.get("segments"):
            st.markdown("### 📋 Current Segments")
            for i, segment in enumerate(c["segments"]):
                with st.expander(f"Segment {i+1}: {segment.get('segment_id', 'Unknown')} ({segment.get('mode', 'Unknown')})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Applied to arms:** {', '.join(segment.get('applied_to_arms', []))}")
                        st.write(f"**Start time:** {segment.get('start_time', 'Not set')}")
                        st.write(f"**End time:** {segment.get('end_time', 'Not set')}")
                    with col2:
                        selection_circuit = segment.get('selection_design', {}).get('selection_circuit_id', 'Not set')
                        st.write(f"**Selection circuit:** {selection_circuit}")
                        stepping_stones = segment.get('selection_design', {}).get('stepping_stones', [])
                        st.write(f"**Stepping stones:** {', '.join(stepping_stones) if stepping_stones else 'None'}")

# --- Validate ---
with tabs[9]:
    st.subheader("Validate against schema")
    show_errors(validate_doc(st.session_state.doc))
