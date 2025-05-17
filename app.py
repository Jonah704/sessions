import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout='wide')

@st.cache_data
def load_data_for_instrument(instrument: str) -> pd.DataFrame:
    base = "https://raw.githubusercontent.com/TuckerArrants/sessions/main"
    fname = f"{instrument}_Session_Hits_With_Mids_Processed_from_2008.csv"
    url = f"{base}/{fname}"
    try:
        return pd.read_csv(url)
    except Exception:
        # fallback to empty DF if file not found or network hiccup
        return pd.DataFrame()

# ✅ Store username-password pairs
USER_CREDENTIALS = {
    "badboyz": "bangbang",
    "dreamteam" : "strike",
    "Almkuh"    : "Weidemilch",
}

segments = {
    "PRDR-ADR Transition":        (   0,  90),
    "ADR":            (  90, 480),
    "ADR-ODR Transition": ( 480, 540),
    "ODR":            ( 540, 870),
    "ODR-RDR Transition": ( 870, 930),
    "RDR":            ( 930,1380),
}

# ✅ Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# ✅ Login form (only shown if not authenticated)
if not st.session_state["authenticated"]:
    st.title("Login to Database")

    # Username and password fields
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    # Submit button
    if st.button("Login"):
        if username in USER_CREDENTIALS and password == USER_CREDENTIALS[username]:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username  # Store the username
            # ← Clear *all* @st.cache_data caches here:
            st.cache_data.clear()

            st.success(f"Welcome, {username}! Loading fresh data…")
            st.rerun()
        else:
            st.error("Incorrect username or password. Please try again.")

    # Stop execution if user is not authenticated
    st.stop()

# ✅ If authenticated, show the full app
st.title("Trompete Kostet Knete")

# ↓ in your sidebar:
instrument_options = ["ES", "NQ", "YM", "CL", "GC", "NG", "HG", "SI", "E6", "FDAX"]
selected_instrument = st.sidebar.selectbox("Instrument", instrument_options)

df = load_data_for_instrument(selected_instrument)
df['date'] = pd.to_datetime(df['session_date']).dt.date

rename_map = {'pre_adr' : 'PRDR-ADR Transition',
              'adr' : 'ADR',
              'adr_transition' : 'ADR-ODR Transition',
              'odr' : 'ODR',
              'odr_transition' : 'ODR-RDR Transition',
              'rdr' : 'RDR',
              'untouched' : 'Untouched',
}

df = df.replace(rename_map)

# 1) Make sure 'date' is a datetime column
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["session_date"])
else:
    st.sidebar.warning("No 'date' column found in your data!")


# SIDEBAR
day_options = ['All'] + ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
selected_day = st.sidebar.selectbox("Day of Week", day_options, key="selected_day")

min_date = df["date"].min().date()
max_date = df["date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_range"
)

# RESET BUTTON
default_filters = {
    "selected_day":                       "All",
    "date_range":                 (min_date, max_date),

    "prdr_mid_hit_filter":                "All",
    "adr_mid_hit_filter":                 "All",
    "odr_mid_hit_filter":                 "All",

    "prdr_mid_hit_filter_exclusion":      [],
    "adr_mid_hit_filter_exclusion":       [],
    "odr_mid_hit_filter_exclusion":       [],
    
    "prdr_high_filter":                   "All", 
    "prdr_adr_transition_high_filter":    "All",
    "adr_high_filter":                    "All", 
    "adr_odr_transition_high_filter":     "All",
    "odr_high_filter":                    "All",
    "odr_rdr_transition_high_filter":     "All",
    "prdr_low_filter":                    "All",
    "prdr_adr_transition_low_filter":     "All", 
    "adr_low_filter":                     "All", 
    "adr_odr_transition_low_filter":      "All", 
    "odr_low_filter":                     "All", 
    "odr_rdr_transition_low_filter":      "All",

    "prdr_high_filter_exclusion":                   [], 
    "prdr_adr_transition_high_filter_exclusion":    [], 
    "adr_high_filter_exclusion":                    [], 
    "adr_odr_transition_high_filter_exclusion":     [], 
    "odr_high_filter_exclusion":                    [], 
    "odr_rdr_transition_high_filter_exclusion":     [], 
    "prdr_low_filter_exclusion":                    [], 
    "prdr_adr_transition_low_filter_exclusion":     [],  
    "adr_low_filter_exclusion":                     [], 
    "adr_odr_transition_low_filter_exclusion":      [],  
    "odr_low_filter_exclusion":                     [], 
    "odr_rdr_transition_low_filter_exclusion":      [], 
}

# 2) Reset button with callback
def reset_all_filters():
    for key, default in default_filters.items():
        # only touch keys that actually exist
        if key in st.session_state:
            st.session_state[key] = default

st.sidebar.button("🔄 Reset all filters", on_click=reset_all_filters)

if isinstance(start_date, tuple):
    # sometimes date_input returns a single date if you pass a single default
    start_date, end_date = start_date

# FILTERS
st.markdown("### Session High / Low Inclusions")

segment_order = list(segments.keys())          # ["pre_adr","adr","adr_transition",…,"rdr"]
segment_order_with_no = segment_order + ["Untouched"]

row1_cols = st.columns([1, 1, 1, 1, 1, 1])
row2_cols = st.columns([1, 1, 1, 1, 1, 1])

with row1_cols[0]:
    prev_rdr_high_filter = st.selectbox(
        "PRDR High Touch",
        options=["All"] + ["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_high_filter"
    )
with row1_cols[1]:
    pre_adr_high_filter = st.selectbox(
        "PRDR-ADR Transition High Touch",
        options=["All"] + ["ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_adr_transition_high_filter"
    )
with row1_cols[2]:
    adr_high_filter = st.selectbox(
        "ADR High Touch",
        options=["All"] + ["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_high_filter"
    )
with row1_cols[3]:
    adr_transition_high_filter = st.selectbox(
        "ADR-ODR Transition High Touch",
        options=["All"] + ["ODR", "ODR-RDR Transition", "RDR"],
        key="adr_odr_transition_high_filter"
    )
with row1_cols[4]:
    odr_high_filter = st.selectbox(
        "ODR High Touch",
        options=["All"] + ["ODR-RDR Transition", "RDR"],
        key="odr_high_filter"
    )
with row1_cols[5]:
    odr_transition_high_filter = st.selectbox(
        "ODR-RDR Transition High Touch",
        options=["All"] + ["RDR"],
        key="odr_rdr_transition_high_filter"
    )

# Second Row
with row2_cols[0]:
    prev_rdr_low_filter = st.selectbox(
        "PRDR Low Touch",
        options=["All"] + ["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_low_filter"
    )
with row2_cols[1]:
    pre_adr_low_filter = st.selectbox(
        "PRDR-ADR Transition Low Touch",
        options=["All"] + ["ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_adr_transition_low_filter"
    )
with row2_cols[2]:
    adr_low_filter = st.selectbox(
        "ADR Low Touch",
        options=["All"] + ["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_low_filter"
    )
with row2_cols[3]:
    adr_transition_low_filter = st.selectbox(
        "ADR-ODR Transition Low Touch",
        options=["All"] + ["ODR", "ODR-RDR Transition", "RDR"],
        key="adr_odr_transition_low_filter"
    )
with row2_cols[4]:
    odr_low_filter = st.selectbox(
        "ODR Low Touch",
        options=["All"] + ["ODR-RDR Transition", "RDR"],
        key="odr_low_filter"
    )
with row2_cols[5]:
    odr_transition_low_filter = st.selectbox(
        "ODR-RDR Transition Low Touch",
        options=["All"] + ["RDR"],
        key="odr_rdr_transition_low_filter"
    )

st.markdown("### Session High / Low Exclusions")

row3_cols = st.columns([1, 1, 1, 1, 1, 1])
row4_cols = st.columns([1, 1, 1, 1, 1, 1])

with row3_cols[0]:
    prev_rdr_high_filter_exclusion = st.multiselect(
        "PRDR High Touch",
        options=["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_high_filter_exclusion"
    )
with row3_cols[1]:
    pre_adr_high_filter_exclusion = st.multiselect(
        "PRDR-ADR Transition High Touch",
        options=["ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_adr_transition_high_filter_exclusion"
    )
with row3_cols[2]:
    adr_high_filter_exclusion = st.multiselect(
        "ADR High Touch",
        options=["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_high_filter_exclusion"
    )
with row3_cols[3]:
    adr_transition_high_filter_exclusion = st.multiselect(
        "ADR-ODR Transition High Touch",
        options=["ODR", "ODR-RDR Transition", "RDR"],
        key="adr_odr_transition_high_filter_exclusion"
    )
with row3_cols[4]:
    odr_high_filter_exclusion = st.multiselect(
        "ODR High Touch",
        options=["ODR-RDR Transition", "RDR"],
        key="odr_high_filter_exclusion"
    )
with row3_cols[5]:
    odr_transition_high_filter_exclusion = st.multiselect(
        "ODR-RDR Transition High Touch",
        options=["RDR"],
        key="odr_rdr_transition_high_filter_exclusion"
    )

# Second Row
with row4_cols[0]:
    prev_rdr_low_filter_exclusion = st.multiselect(
        "PRDR Low Touch",
        options=["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_low_filter_exclusion"
    )
with row4_cols[1]:
    pre_adr_low_filter_exclusion = st.multiselect(
        "PRDR-ADR Transition Low Touch",
        options=["ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_adr_transition_low_filter_exclusion"
    )
with row4_cols[2]:
    adr_low_filter_exclusion = st.multiselect(
        "ADR Low Touch",
        options=["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_low_filter_exclusion"
    )
with row4_cols[3]:
    adr_transition_low_filter_exclusion = st.multiselect(
        "ADR-ODR Transition Low Touch",
        options=["ODR", "ODR-RDR Transition", "RDR"],
        key="adr_odr_transition_low_filter_exclusion"
    )
with row4_cols[4]:
    odr_low_filter_exclusion = st.multiselect(
        "ODR Low Touch",
        options=["ODR-RDR Transition", "RDR"],
        key="odr_low_filter_exclusion"
    )
with row4_cols[5]:
    odr_transition_low_filter_exclusion = st.multiselect(
        "ODR-RDR Transition Low Touch",
        options=["RDR"],
        key="odr_rdr_transition_low_filter_exclusion"
    )

# MIDLINES
st.markdown("### Session IDR Midline Inclusions")
row5_cols = st.columns([1, 1, 1])

with row5_cols[0]:
    prev_rdr_midline_hit = st.selectbox(
        "PRDR Mid Touch",
        options=["All"] + ["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_mid_hit_filter"
    )
with row5_cols[1]:
    adr_midline_hit = st.selectbox(
        "ADR Mid Touch",
        options=["All"] + ["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_mid_hit_filter"
    )
with row5_cols[2]:
    odr_midline_hit = st.selectbox(
        "ODR Mid Touch",
        options=["All"] + ["ODR-RDR Transition", "RDR"],
        key="odr_mid_hit_filter"
    )
    
st.markdown("### Session IDR Midline Exclusions")
row6_cols = st.columns([1, 1, 1])
with row6_cols[0]:
    prev_rdr_midline_hit_exclusion = st.multiselect(
        "PRDR Mid Touch",
        options=["PRDR-ADR Transition", "ADR", "ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="prdr_mid_hit_filter_exclusion"
    )
with row6_cols[1]:
    adr_midline_hit_exclusion = st.multiselect(
        "ADR Mid Touch",
        options=["ADR-ODR Transition", "ODR", "ODR-RDR Transition", "RDR"],
        key="adr_mid_hit_filter_exclusion"
    )
with row6_cols[2]:
    odr_midline_hit_exclusion = st.multiselect(
        "ODR Mid Touch",
        options=["ODR-RDR Transition", "RDR"],
        key="odr_mid_hit_filter_exclusion"
    )


# Apply filters
st.markdown("### Distributions")

# map each filter to its column
inclusion_map = {
    "prev_rdr_high_touch_time_bucket":       "prdr_high_filter",
    "pre_adr_high_touch_time_bucket":        "prdr_adr_transition_high_filter",
    "adr_high_touch_time_bucket":            "adr_high_filter",
    "adr_transition_high_touch_time_bucket": "adr_odr_transition_high_filter",
    "odr_high_touch_time_bucket":            "odr_high_filter",
    "odr_transition_high_touch_time_bucket": "odr_rdr_transition_high_filter",

    "prev_rdr_low_touch_time_bucket":        "prdr_low_filter",
    "pre_adr_low_touch_time_bucket":         "prdr_adr_transition_low_filter",
    "adr_low_touch_time_bucket":             "adr_low_filter",
    "adr_transition_low_touch_time_bucket":  "adr_odr_transition_low_filter",
    "odr_low_touch_time_bucket":             "odr_low_filter",
    "odr_transition_low_touch_time_bucket":  "odr_rdr_transition_low_filter",

    "prev_rdr_idr_midline_touch_time_bucket":       "prdr_mid_hit_filter",
    "adr_idr_midline_touch_time_bucket":       "adr_mid_hit_filter",
    "odr_idr_midline_touch_time_bucket":       "odr_mid_hit_filter",
}

exclusion_map = {
    "prev_rdr_high_touch_time_bucket":       "prdr_high_filter_exclusion",
    "pre_adr_high_touch_time_bucket":        "prdr_adr_transition_high_filter_exclusion",
    "adr_high_touch_time_bucket":            "adr_high_filter_exclusion",
    "adr_transition_high_touch_time_bucket": "adr_odr_transition_high_filter_exclusion",
    "odr_high_touch_time_bucket":            "odr_high_filter_exclusion",
    "odr_transition_high_touch_time_bucket": "odr_rdr_transition_high_filter_exclusion",

    "prev_rdr_low_touch_time_bucket":        "prdr_low_filter_exclusion",
    "pre_adr_low_touch_time_bucket":         "prdr_adr_transition_low_filter_exclusion",
    "adr_low_touch_time_bucket":             "adr_low_filter_exclusion",
    "adr_transition_low_touch_time_bucket":  "adr_odr_transition_low_filter_exclusion",
    "odr_low_touch_time_bucket":             "odr_low_filter_exclusion",
    "odr_transition_low_touch_time_bucket":  "odr_rdr_transition_low_filter_exclusion",

    "prev_rdr_idr_midline_touch_time_bucket":       "prdr_mid_hit_filter_exclusion",
    "adr_idr_midline_touch_time_bucket":            "adr_mid_hit_filter_exclusion",
    "odr_idr_midline_touch_time_bucket":            "odr_mid_hit_filter_exclusion",
}


# APPLY FILTERS
df_filtered = df.copy()

# — Day-of-week (shifted by +1 day) —
sel_day = st.session_state["selected_day"]
if sel_day != "All":
    df_filtered = df_filtered[
        (df_filtered["date"] + pd.Timedelta(days=1)).dt.day_name() == sel_day
    ]

# — Date range —
start_date, end_date = st.session_state["date_range"]
df_filtered = df_filtered[
    (df_filtered["date"] >= pd.to_datetime(start_date)) &
    (df_filtered["date"] <= pd.to_datetime(end_date))
]

for col, state_key in inclusion_map.items():
    sel = st.session_state[state_key]
    if sel != "All":
        df_filtered = df_filtered[df_filtered[col] == sel]

for col, state_key in exclusion_map.items():
    excludes = st.session_state[state_key]
    if excludes:
        df_filtered = df_filtered[~df_filtered[col].isin(excludes)]
        
# GRAPHS
df_plot = df.copy()

# MIDS touch-time buckets
mid_cols = [
    "prev_rdr_idr_midline_touch_time_bucket",
    "adr_idr_midline_touch_time_bucket",
    "odr_idr_midline_touch_time_bucket",
]
mid_titles = [
    "PRDR Mid",
    "ADR Mid",
    "ODR Mid",
]

row1 = st.columns(3)
for idx, col in enumerate(mid_cols):
    if col in df_filtered:
        counts = (
            df_filtered[col]
            .value_counts(normalize=True)
            .reindex(segment_order_with_no, fill_value=0)
        )
        perc = counts * 100

        fig = px.bar(
            x=perc.index,
            y=perc.values,
            text=[f"{v:.1f}%" for v in perc.values],
            labels={"x": "", "y": "% of Sessions"},
            title=mid_titles[idx],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": segment_order_with_no},
            margin=dict(l=10, r=10, t=30, b=10),
        )

        row1[idx].plotly_chart(fig, use_container_width=True)



# HIGH touch‐time buckets
high_cols = [
    "prev_rdr_high_touch_time_bucket",
    "pre_adr_high_touch_time_bucket",
    "adr_high_touch_time_bucket",
    "adr_transition_high_touch_time_bucket",
    "odr_high_touch_time_bucket",
    "odr_transition_high_touch_time_bucket",
]
high_titles = [
    "PRDR High",
    "PRDR-ADR Transition High",
    "ADR High",
    "ADR-ODR Transition High",
    "ODR High",
    "ODR-RDR Transition High",
]

row2 = st.columns(6)
for idx, col in enumerate(high_cols):
    if col in df_filtered:
        counts = (
            df_filtered[col]
            .value_counts(normalize=True)
            .reindex(segment_order_with_no, fill_value=0)
        )
        perc = counts * 100

        fig = px.bar(
            x=perc.index,
            y=perc.values,
            text=[f"{v:.1f}%" for v in perc.values],
            labels={"x": "", "y": "% of Sessions"},
            title=high_titles[idx],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": segment_order_with_no},
            margin=dict(l=10, r=10, t=30, b=10),
        )

        row2[idx].plotly_chart(fig, use_container_width=True)


# LOW touch‐time buckets
low_cols = [
    "prev_rdr_low_touch_time_bucket",
    "pre_adr_low_touch_time_bucket",
    "adr_low_touch_time_bucket",
    "adr_transition_low_touch_time_bucket",
    "odr_low_touch_time_bucket",
    "odr_transition_low_touch_time_bucket",
]
low_titles = [
    "PRDR Low",
    "PRDR-ADR Transition Low",
    "ADR Low",
    "ADR-ODR Transition Low",
    "ODR Low",
    "ODR-RDR Transition Low",
]

row3 = st.columns(6)
for idx, col in enumerate(low_cols):
    if col in df_filtered:
        counts = (
            df_filtered[col]
            .value_counts(normalize=True)
            .reindex(segment_order_with_no, fill_value=0)
        )
        perc = counts * 100

        fig = px.bar(
            x=perc.index,
            y=perc.values,
            text=[f"{v:.1f}%" for v in perc.values],
            labels={"x": "", "y": "% of Sessions"},
            title=low_titles[idx],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": segment_order_with_no},
            margin=dict(l=10, r=10, t=30, b=10),
        )

        row3[idx].plotly_chart(fig, use_container_width=True)

st.caption(f"Sample size: {len(df_filtered):,} rows")
