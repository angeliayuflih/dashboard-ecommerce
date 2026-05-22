import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard E-Commerce",
    layout="wide"
)

# =====================================================
# LOAD DATA
# =====================================================
df_master = pd.read_csv("ecommerce/main_data.csv")
df_event = pd.read_csv("ecommerce/customer_behavior.csv")
customer_df = pd.read_csv("ecommerce/customer_segment.csv")
category_df = pd.read_csv("ecommerce/category_segment.csv")

# =====================================================
# DATE CONVERT
# =====================================================
df_master['transaction_time'] = pd.to_datetime(
    df_master['transaction_time'],
    format='ISO8601',
    errors='coerce'
)
df_master["date"] = df_master["transaction_time"].dt.date
df_master["year"] = df_master["transaction_time"].dt.year
df_master["month"] = df_master["transaction_time"].dt.month

# =====================================================
# AGE GROUP
# =====================================================
df_master["age_group"] = pd.cut(
    df_master["age"],
    bins=[0, 24, 40, 200],
    labels=["Young Adult", "Adult", "Older Adult"]
)

# =====================================================
# SIDEBAR FILTER
# =====================================================
st.sidebar.header("Time Filter")

available_years = sorted(df_master["year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect(
    "Pilih Tahun",
    options=available_years,
    default=available_years
)

month_map = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}
available_months = sorted(df_master["month"].dropna().unique().tolist())
selected_month_labels = st.sidebar.multiselect(
    "Pilih Bulan",
    options=[month_map[m] for m in available_months],
    default=[month_map[m] for m in available_months]
)
reverse_month_map = {v: k for k, v in month_map.items()}
selected_months = [reverse_month_map[label] for label in selected_month_labels]

# =====================================================
# FILTER df_master
# =====================================================
if selected_years and selected_months:
    df_filtered = df_master[
        df_master["year"].isin(selected_years) &
        df_master["month"].isin(selected_months)
    ]
else:
    df_filtered = df_master.copy()
    st.sidebar.warning("Pilih minimal satu tahun dan satu bulan.")

# =====================================================
# FILTER customer_df & category_df via user_id
# =====================================================
filtered_user_ids = df_filtered["user_id"].unique()

customer_filtered = customer_df[customer_df["user_id"].isin(filtered_user_ids)]
category_filtered = category_df[category_df["user_id"].isin(filtered_user_ids)] \
    if "user_id" in category_df.columns else category_df

# =====================================================
# TITLE
# =====================================================
st.title("Dashboard Analisis E-Commerce")
st.markdown("Analisis revenue dan penjualan produk")

if selected_years and selected_months:
    st.caption(
        f"Tahun **{', '.join(map(str, selected_years))}** | "
        f"Bulan **{', '.join(selected_month_labels)}**"
    )

# =====================================================
# KPI
# =====================================================
total_revenue = df_filtered["sale_price"].sum()
total_customer = df_filtered["user_id"].nunique()
total_orders = df_filtered["transaksi_id"].count()
top_traffic = df_filtered["traffic_source"].value_counts().idxmax()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"${total_revenue:,.0f}")
with col2:
    st.metric("Total Customer", f"{total_customer:,}")
with col3:
    st.metric("Total Orders", f"{total_orders:,}")
with col4:
    st.metric("Top Traffic Source", top_traffic)

# =====================================================
# BAR CHART + PIE CHART
# =====================================================
col1, col2 = st.columns(2)

# ---------------- BAR CHART ----------------
with col1:
    category_revenue = (
        df_filtered.groupby("category")["sale_price"]
        .sum()
        .reset_index()
        .rename(columns={"sale_price": "total_revenue_kategori"})
        .sort_values(by="total_revenue_kategori", ascending=False)
    )

    fig_bar = px.bar(
        category_revenue,
        x="category",
        y="total_revenue_kategori",
        title="Revenue per Category",
        text_auto=True
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ---------------- PIE CHART ----------------
with col2:
    age_transaction = (
        df_filtered.groupby("age_group")["transaksi_id"]
        .count()
        .reset_index()
        .rename(columns={"transaksi_id": "total_transaction"})
    )

    fig_donut = px.pie(
        age_transaction,
        names="age_group",
        values="total_transaction",
        hole=0.4,
        title="Proporsi Total Transaksi Berdasarkan Kelompok Umur"
    )
    fig_donut.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# =====================================================
# LINE CHART
# =====================================================
st.subheader("Trend Revenue")

trend_option = st.radio(
    "Pilih Analisis Trend",
    ["Keseluruhan", "Per Kategori"],
    horizontal=True
)

# ---------------- TREND KESELURUHAN ----------------
if trend_option == "Keseluruhan":
    daily_sales = (
    df_filtered.groupby(df_filtered['transaction_time'].dt.date)
    .agg(revenue=('sale_price', 'sum'), total_transaction=('transaksi_id', 'count'))
    .reset_index()
    .rename(columns={"transaction_time": "date"})
    )
    daily_sales["moving_avg"] = daily_sales["revenue"].rolling(window=7).mean()

    fig_line = px.line(
        daily_sales,
        x="date",
        y=["revenue", "moving_avg"],
        markers=True,
        title="Trend Revenue Keseluruhan"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ---------------- TREND PER KATEGORI ----------------
else:
    selected_category = st.selectbox(
        "Pilih Kategori",
        df_filtered["category"].unique()
    )

    category_trend = (
        df_filtered[df_filtered["category"] == selected_category]
        .groupby("date")["sale_price"]
        .sum()
        .reset_index()
        .rename(columns={"sale_price": "revenue"})
    )
    category_trend["moving_avg"] = category_trend["revenue"].rolling(window=7).mean()

    fig_line_category = px.line(
        category_trend,
        x="date",
        y=["revenue", "moving_avg"],
        markers=True,
        title=f"Trend Revenue Kategori: {selected_category}"
    )
    st.plotly_chart(fig_line_category, use_container_width=True)

