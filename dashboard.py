import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(
    page_title="Learning Content Dashboard",
    page_icon=":material/school:",
    layout="wide",
)

@st.cache_data
def load_base():
    df = pd.read_excel("Testingg.xlsx", sheet_name="query (4)")
    df.columns = df.columns.str.strip()
    df["Published date"] = pd.to_datetime(df["Published date"], errors="coerce")
    df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
    df["Course Expiry Date"] = pd.to_datetime(df["Course Expiry Date"], errors="coerce")
    df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")
    return df

@st.cache_data
def parse_uploaded(file_bytes, file_name):
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip()
    df["Published date"] = pd.to_datetime(df["Published date"], errors="coerce")
    df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
    df["Course Expiry Date"] = pd.to_datetime(df["Course Expiry Date"], errors="coerce")
    df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")
    return df

base_df = load_base()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/folder_open: Add more data")
    uploaded_files = st.file_uploader(
        "Upload additional Excel file(s) — same format",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    extra_dfs = []
    for uf in uploaded_files:
        try:
            extra_dfs.append(parse_uploaded(uf.read(), uf.name))
            st.success(f":material/check_circle: {uf.name}")
        except Exception as e:
            st.error(f":material/error: {uf.name} — {e}")

    df = pd.concat([base_df] + extra_dfs, ignore_index=True) if extra_dfs else base_df

    st.divider()
    st.markdown("### :material/tune: Filters")

    statuses = sorted(df["Status"].dropna().unique().tolist())
    selected_status = st.multiselect("Status", statuses, default=statuses)

    formats = sorted(df["Learning Format"].dropna().unique().tolist())
    selected_format = st.multiselect("Learning format", formats, default=formats)

    owners = sorted(df["Content Owner"].dropna().unique().tolist())
    selected_owner = st.multiselect("Content owner", owners, default=owners)

filtered = df[
    df["Status"].isin(selected_status)
    & df["Learning Format"].isin(selected_format)
    & df["Content Owner"].isin(selected_owner)
]

# ── Title card ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(90deg, #1a73e8 0%, #0d47a1 100%);
            padding: 24px 32px; border-radius: 12px; margin-bottom: 8px;">
    <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: 0.5px;">
        📚 Learning Dashboard
    </h1>
    <p style="color: rgba(255,255,255,0.75); margin: 6px 0 0 0; font-size: 1rem;">
        Upload your Excel file to explore learning content KPIs and insights
    </p>
</div>
""", unsafe_allow_html=True)

source_label = f"Base file + {len(extra_dfs)} additional file(s)" if extra_dfs else "Base file"
st.caption(f"Showing {len(filtered):,} of {len(df):,} records — {source_label}")

st.divider()

# ── KPI row ──────────────────────────────────────────────────────────────────
total = len(filtered)
published = (filtered["Status"] == "Published in SML").sum()
changes_published = (filtered["Status"] == "Changes Published").sum()
on_hold = (filtered["Status"] == "On Hold").sum()
avg_duration = filtered["Duration"].mean()
total_duration = filtered["Duration"].sum()

with st.container(horizontal=True):
    st.metric("Total records", f"{total:,}", border=True)
    st.metric("Published in SML", f"{published:,}", border=True)
    st.metric("Changes published", f"{changes_published:,}", border=True)
    st.metric("On hold", f"{on_hold:,}", border=True)
    st.metric("Avg duration (min)", f"{avg_duration:.1f}" if not pd.isna(avg_duration) else "N/A", border=True)
    st.metric("Total duration (min)", f"{total_duration:,.0f}", border=True)

st.divider()

# ── Row 1: Status breakdown + Learning format ─────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Status breakdown")
        status_counts = filtered["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.bar(
            status_counts,
            x="Count",
            y="Status",
            orientation="h",
            color="Count",
            color_continuous_scale="Blues",
            text="Count",
        )
        fig.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
            margin=dict(l=0, r=0, t=0, b=0),
            height=320,
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, key="status_bar")

with col2:
    with st.container(border=True):
        st.subheader("Learning format distribution")
        fmt_counts = filtered["Learning Format"].value_counts().reset_index()
        fmt_counts.columns = ["Format", "Count"]
        fig2 = px.pie(
            fmt_counts,
            names="Format",
            values="Count",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=320)
        st.plotly_chart(fig2, key="format_pie")

# ── Row 2: Content owner + Monthly publications ───────────────────────────────
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("Top content owners")
        owner_counts = (
            filtered["Content Owner"]
            .value_counts()
            .head(10)
            .reset_index()
        )
        owner_counts.columns = ["Owner", "Count"]
        owner_counts["Owner"] = owner_counts["Owner"].apply(
            lambda x: x.split(",")[0] if isinstance(x, str) else x
        )
        fig3 = px.bar(
            owner_counts,
            x="Count",
            y="Owner",
            orientation="h",
            color="Count",
            color_continuous_scale="Teal",
            text="Count",
        )
        fig3.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
            margin=dict(l=0, r=0, t=0, b=0),
            height=340,
        )
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, key="owner_bar")

with col4:
    with st.container(border=True):
        st.subheader("Publications over time")
        pub_df = filtered.dropna(subset=["Published date"]).copy()
        if not pub_df.empty:
            pub_df["Month"] = pub_df["Published date"].dt.to_period("M").astype(str)
            monthly = pub_df.groupby("Month").size().reset_index(name="Count")
            fig4 = px.line(
                monthly,
                x="Month",
                y="Count",
                markers=True,
                color_discrete_sequence=["#4A90D9"],
            )
            fig4.update_layout(
                xaxis_tickangle=-45,
                margin=dict(l=0, r=0, t=0, b=0),
                height=340,
            )
            st.plotly_chart(fig4, key="monthly_line")
        else:
            st.info("No published date data available for current filters.")

# ── Row 3: Learning processor workload + Duration distribution ────────────────
col5, col6 = st.columns(2)

with col5:
    with st.container(border=True):
        st.subheader("Learning processor workload")
        proc_counts = (
            filtered["Learning Processor"]
            .dropna()
            .value_counts()
            .reset_index()
        )
        proc_counts.columns = ["Processor", "Count"]
        proc_counts["Processor"] = proc_counts["Processor"].apply(
            lambda x: x.split(",")[0] if isinstance(x, str) else x
        )
        fig5 = px.bar(
            proc_counts,
            x="Count",
            y="Processor",
            orientation="h",
            color="Count",
            color_continuous_scale="Purples",
            text="Count",
        )
        fig5.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
            margin=dict(l=0, r=0, t=0, b=0),
            height=280,
        )
        fig5.update_traces(textposition="outside")
        st.plotly_chart(fig5, key="proc_bar")

with col6:
    with st.container(border=True):
        st.subheader("Course duration distribution (minutes)")
        dur_df = filtered["Duration"].dropna()
        if not dur_df.empty:
            fig6 = px.histogram(
                dur_df,
                nbins=20,
                color_discrete_sequence=["#F4A261"],
                labels={"value": "Duration (min)", "count": "Courses"},
            )
            fig6.update_layout(
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                height=280,
                xaxis_title="Duration (min)",
                yaxis_title="Number of courses",
            )
            st.plotly_chart(fig6, key="duration_hist")
        else:
            st.info("No duration data available for current filters.")

# ── Row 4: Courses expiring soon ──────────────────────────────────────────────
st.divider()
with st.container(border=True):
    st.subheader(":material/schedule: Courses expiring within 90 days")
    today = pd.Timestamp(datetime.today().date())
    expiring = filtered[
        (filtered["Course Expiry Date"] >= today)
        & (filtered["Course Expiry Date"] <= today + pd.Timedelta(days=90))
    ][["Course Title", "Status", "Learning Format", "Content Owner", "Course Expiry Date"]].copy()
    expiring = expiring.sort_values("Course Expiry Date")
    if expiring.empty:
        st.success("No courses expiring in the next 90 days.")
    else:
        st.dataframe(
            expiring,
            hide_index=True,
            column_config={
                "Course Expiry Date": st.column_config.DateColumn("Expiry date", format="YYYY-MM-DD"),
            },
        )

# ── Row 5: Full data table ────────────────────────────────────────────────────
with st.expander(":material/table: View full data table"):
    cols_to_show = [
        "Course Title", "Status", "Learning Format", "Content Owner",
        "Learning Processor", "Duration", "Published date", "Course Expiry Date",
    ]
    st.dataframe(
        filtered[cols_to_show],
        hide_index=True,
        column_config={
            "Published date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Course Expiry Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Duration": st.column_config.NumberColumn("Duration (min)", format="%.1f"),
        },
    )
