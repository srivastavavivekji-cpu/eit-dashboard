import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="EIT Interactive Dashboard with Export", layout="wide")

st.title("⚡ Equivalent Interaction-Time (EIT) Dashboard & Export")
st.markdown("Analyze wearable sensor streams, compute biological exposure ($\tau_{EIT}$), and export your processed results instantly.")

# --- Sidebar: Data Source Selection ---
st.sidebar.header("📁 Data Source Configuration")
data_source = st.sidebar.radio("Choose Data Source", ["Simulated Scenarios", "Upload Custom CSV"])

time_steps = None
intensity_profile = None

if data_source == "Simulated Scenarios":
    activity_level = st.sidebar.selectbox(
        "Select Activity Scenario",
        ["Resting State", "Moderate Workout", "High-Intensity Interval Training (HIIT)"]
    )
    time_steps = np.array([0, 5, 10, 15, 20, 25, 30])
    if activity_level == "Resting State":
        intensity_profile = [1.0, 1.02, 0.98, 1.01, 1.0, 0.99, 1.0]
    elif activity_level == "Moderate Workout":
        intensity_profile = [1.0, 1.3, 1.8, 1.7, 1.4, 1.2, 1.0]
    else:
        intensity_profile = [1.0, 1.8, 2.7, 1.4, 2.9, 1.5, 1.0]

else:
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("Upload CSV file (Must contain Time and Sensor columns)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("CSV file uploaded successfully!")
        
        columns = df.columns.tolist()
        time_col = st.sidebar.selectbox("Select Time Column", columns)
        sensor_col = st.sidebar.selectbox("Select Intensity/Sensor Column", columns)
        
        if time_col and sensor_col:
            time_steps = df[time_col].to_numpy(dtype=float)
            raw_sensor_vals = df[sensor_col].to_numpy(dtype=float)
            
            baseline = np.median(raw_sensor_vals)
            if baseline == 0: baseline = 1.0
            intensity_profile = raw_sensor_vals / baseline
    else:
        st.info("👈 Please upload a CSV file from the sidebar to begin analysis.")
        st.stop()

# --- Core Calculations ---
cumulative_tau = []
for idx in range(1, len(time_steps) + 1):
    sub_t = time_steps[:idx]
    sub_i = intensity_profile[:idx]
    if len(sub_t) > 1:
        cumulative_tau.append(np.trapz(sub_i, sub_t))
    else:
        cumulative_tau.append(0.0)

total_clock_time = time_steps[-1] - time_steps[0] if len(time_steps) > 1 else 0
final_tau = cumulative_tau[-1]
diff_ratio = ((final_tau - total_clock_time) / total_clock_time * 100) if total_clock_time > 0 else 0

# --- Metrics Row ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Duration (T)", f"{total_clock_time:.1f} units")
col2.metric("Cumulative tau_EIT", f"{final_tau:.2f} units", f"{diff_ratio:+.1f}% vs Clock")
col3.metric("Average Intensity (I_avg)", f"{np.mean(intensity_profile):.2f}")

st.markdown("---")

# --- Matplotlib Visualization ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

ax1.plot(time_steps, intensity_profile, marker='o', color='#e53e3e', linewidth=2.5, label='Instant Intensity I(t)')
ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7, label='Baseline (I=1.0)')
ax1.set_ylabel('Intensity Index I(t)', fontsize=11, fontweight='bold')
ax1.set_title('EIT Sensor Stream Analysis', fontsize=13, fontweight='bold')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper left')

ax2.plot(time_steps, cumulative_tau, marker='s', color='#3182ce', linewidth=2.5, label='Cumulative tau_EIT')
ax2.plot(time_steps, time_steps - time_steps[0], color='black', linestyle=':', alpha=0.7, label='Clock Time (T) Baseline')
ax2.set_xlabel('Time Steps', fontsize=11, fontweight='bold')
ax2.set_ylabel('tau_EIT (Equivalent Units)', fontsize=11, fontweight='bold')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper left')

plt.tight_layout()
st.pyplot(fig)

st.markdown("---")

# --- Export Section ---
st.subheader("📥 Export Processed EIT Data")
st.markdown("Download the compiled time-series results including instantaneous intensity and cumulative biological exposure scores.")

# Create a clean DataFrame for export
export_df = pd.DataFrame({
    "Clock_Time": time_steps,
    "Instant_Intensity_I(t)": intensity_profile,
    "Cumulative_tau_EIT": cumulative_tau
})

csv_data = export_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Processed EIT Results as CSV",
    data=csv_data,
    file_name="processed_eit_results.csv",
    mime="text/csv",
    type="primary"
)

st.info("💡 **Tip:** You can open this exported CSV in Excel, Google Sheets, or any data science tool for deeper statistical validation.")
