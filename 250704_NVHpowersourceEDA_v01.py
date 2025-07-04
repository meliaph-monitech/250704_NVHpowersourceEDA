import streamlit as st
import pandas as pd
import zipfile
import io
import re
import plotly.express as px

st.title("Welding Machine Power Source Data Merger and EDA")

with st.sidebar:
    uploaded_zip = st.file_uploader("Upload ZIP containing CSV files", type="zip")
    merge_button = st.button("Merge Data")

if uploaded_zip and merge_button:
    merged_df_list = []
    with zipfile.ZipFile(uploaded_zip) as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                match = re.match(r"(\d{4}-\d{2}-\d{2})_(\d+)", filename.split('/')[-1])
                if match:
                    file_date = match.group(1)
                    file_serial = match.group(2)
                else:
                    continue
                with z.open(filename) as f:
                    df = pd.read_csv(f, header=None)
                    df.columns = ['Timestamp', 'MachineStatus', 'Value']
                    df['Timestamp'] = df['Timestamp'].astype(str).str.replace('Z','', regex=False)
                    df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
                    df['Time'] = pd.to_datetime(df['Timestamp']).dt.time
                    stat_split = df['MachineStatus'].astype(str).str.split('.', n=1, expand=True)
                    df['Stat1'] = stat_split[0]
                    df['Stat2'] = stat_split[1]
                    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
                    df['FileDate'] = file_date
                    df['FileSerial'] = file_serial
                    merged_df_list.append(df)
    if merged_df_list:
        merged_df = pd.concat(merged_df_list, ignore_index=True)
        merged_df = merged_df[['FileDate', 'FileSerial', 'Date', 'Time', 'Timestamp', 'MachineStatus', 'Stat1', 'Stat2', 'Value']]
        st.dataframe(merged_df)
        csv_buffer = io.StringIO()
        merged_df.to_csv(csv_buffer, index=False)
        st.download_button("Download Merged CSV", data=csv_buffer.getvalue(), file_name="merged_welding_data.csv", mime="text/csv")

        with st.sidebar:
            agg_option = st.selectbox("Aggregation for Visualization", ["SUM", "AVERAGE"])

        st.subheader("Global EDA Visualization")
        for stat1 in merged_df['Stat1'].dropna().unique():
            with st.expander(f"Stat1: {stat1}"):
                filtered_df = merged_df[merged_df['Stat1'] == stat1]
                if agg_option == "SUM":
                    agg_df = filtered_df.groupby('Stat2')['Value'].sum().reset_index()
                else:
                    agg_df = filtered_df.groupby('Stat2')['Value'].mean().reset_index()
                fig = px.bar(agg_df, x='Stat2', y='Value', title=f"{stat1} - {agg_option} of Value by Stat2")
                st.plotly_chart(fig, use_container_width=True)
