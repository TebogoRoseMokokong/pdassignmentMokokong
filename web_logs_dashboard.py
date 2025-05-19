import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os, shutil
from datetime import datetime
st.set_page_config(page_title="Sales Dashboard", layout="wide")
@st.cache_data
def load_data(file=None):
    try:
        if file:
            df = pd.read_csv(file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            df = pd.read_json('web_logs.json', lines=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['country'] = df['country'].fillna('Unknown') # Mock IP-to-country
        df['job_type'] = df['job_type'].fillna('Unknown')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
def backup_data():
    try:
        os.makedirs("backups", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy("web_logs.json", f"backups/web_logs_{ts}.json")
        return True
    except:
        return False
df = load_data()
st.sidebar.title("Sales Analytics")
uploaded_file = st.sidebar.file_uploader("Upload CSV Log", type="csv")
if uploaded_file:
    df = load_data(uploaded_file)
if not df.empty:
    csv_path = 'web_logs.csv'
    df.to_csv(csv_path, index=False)
    dashboard_type = st.sidebar.selectbox("Select Dashboard", ["Team Dashboard", "Single User Dashboard"])
    dr = st.sidebar.date_input("Date Range", [df['timestamp'].min().date(), df['timestamp'].max().date()])
    c = st.sidebar.selectbox("Country", ['All'] + list(df['country'].unique()))
    r = st.sidebar.selectbox("Request", ['All'] + list(df['url'].unique()))
    dp = st.sidebar.selectbox("Dept", ['All'] + list(df['department'].unique()))
    df_f = df[(df['timestamp'].dt.date >= dr[0]) & (df['timestamp'].dt.date <= dr[1])]
    if c != 'All': df_f = df_f[df_f['country'] == c]
    if r != 'All': df_f = df_f[df_f['url'] == r]
    if dp != 'All': df_f = df_f[df_f['department'] == dp]
    if df_f.empty:
        st.warning("No data for filters.")
        df_f = df
    if dashboard_type == "Team Dashboard":
        st.title("Team Sales Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            product_dept = df_f.groupby(['product', 'department']).size().reset_index(name='count')
            fig1 = px.bar(product_dept, x='product', y='count', color='department', title="Product Requests by Dept", height=200)
            fig1.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            country_dist = df_f['country'].value_counts().reset_index()
            country_dist.columns = ['country', 'count']
            fig2 = px.pie(country_dist, names='country', values='count', title="Requests by Country", height=200)
            fig2.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig2, use_container_width=True)
        with col3:
            job_counts = df_f[df_f['url'] == '/jobs']['job_type'].value_counts().reset_index()
            job_counts.columns = ['job_type', 'count']
            fig3 = px.bar(job_counts, x='job_type', y='count', title="Job Types Requested", height=200)
            fig3.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            fig4 = px.line(df_f.groupby(df_f['timestamp'].dt.date).size().reset_index(name='count'), x='timestamp', y='count', title="Daily Trends", height=200)
            fig4.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig4, use_container_width=True)
        total_requests = len(df_f)
        jobs_placed = len(df_f[df_f['url'] == '/jobs'])
        demos = len(df_f[df_f['url'] == '/shop'])
        errors = len(df_f[df_f['status'] >= 400])
        st.markdown(f"*Requests:* {total_requests:,} *Jobs:* {jobs_placed:,} *Demos:* {demos:,} *Errors:* {errors:,}")
        report_data = df_f.groupby(['product', 'department', 'country', 'job_type', 'url']).size().reset_index(name='count')
        report_path = 'team_report.csv'
        report_data.to_csv(report_path, index=False)
        st.subheader("Phase 2 Insights")
        col5, col6 = st.columns(2)
        with col5:
            errors_by_url = df_f[df_f['status'] >= 400]['url'].value_counts().reset_index()
            errors_by_url.columns = ['url', 'count']
            fig5 = px.bar(errors_by_url, x='url', y='count', title="Errors by URL", height=200)
            fig5.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig5, use_container_width=True)
        with col6:
            rel_data = df_f.groupby(['country', 'product']).size().unstack(fill_value=0)
            fig6 = px.imshow(rel_data, title="Country vs Product", height=200)
            fig6.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig6, use_container_width=True)
    else:
        user_id = st.sidebar.selectbox("Select User", df_f['user_id'].unique())
        user_df = df_f[df_f['user_id'] == user_id]
        if user_df.empty:
            st.warning(f"No data for user {user_id}.")
            user_df = df[df['user_id'] == user_id]
        st.title(f"User {user_id} Sales Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            product_count = user_df['product'].value_counts().reset_index()
            product_count.columns = ['product', 'count']
            fig1 = px.bar(product_count, x='product', y='count', title=f"Products by {user_id}", height=200)
            fig1.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            country_dist = user_df['country'].value_counts().reset_index()
            country_dist.columns = ['country', 'count']
            fig2 = px.pie(country_dist, names='country', values='count', title="Country", height=200)
            fig2.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig2, use_container_width=True)
        with col3:
            job_counts = user_df[user_df['url'] == '/jobs']['job_type'].value_counts().reset_index()
            job_counts.columns = ['job_type', 'count']
            fig3 = px.bar(job_counts, x='job_type', y='count', title="Jobs", height=200)
            fig3.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10))
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            nav = user_df.sort_values('timestamp')[['url']].head(5)
            nav['seq'] = nav['url'].cumsum().apply(lambda x: '→'.join(x.split()[:2]))
            fig4 = px.bar(nav, x='url', y=[1]*len(nav), text='seq', title="Navigation", height=200)
            fig4.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=10), showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)
        total_requests = len(user_df)
        jobs_placed = len(user_df[user_df['url'] == '/jobs'])
        demos = len(user_df[user_df['url'] == '/shop'])
        errors = len(user_df[user_df['status'] >= 400])
        st.markdown(f"*Requests:* {total_requests:,} *Jobs:* {jobs_placed:,} *Demos:* {demos:,} *Errors:* {errors:,}")
        report_data = user_df.groupby(['product', 'country', 'job_type', 'url']).size().reset_index(name='count')
        report_path = f'user_report_{user_id}.csv'
        report_data.to_csv(report_path, index=False)
    for file_path in [csv_path, report_path]:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                st.download_button(label=f"Download {os.path.basename(file_path)}", data=f, file_name=os.path.basename(file_path), mime='text/csv')
    if st.sidebar.button("Backup Data"):
        if backup_data(): st.success("Backup successful!")
        else: st.error("Backup failed.")
    st.sidebar.markdown("[User Manual](user_manual.docx)", unsafe_allow_html=True)
else:
    st.error("No data loaded. Please upload a CSV or ensure web_logs.json exists.")