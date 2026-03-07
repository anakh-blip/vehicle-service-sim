import streamlit as st
import simpy
import pandas as pd
import os
from PIL import Image

# Import simulation modules
from src.environment import ServiceCenter
from src.simulation import simulation_manager, SIM_LOGS
from src import config
from src import analysis

# --- Page Configuration ---
st.set_page_config(
    page_title="Vehicle Service Center Simulation",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Title Header ---
st.title("🚗 Hybrid Simulation Dashboard: Vehicle Service Center")
st.markdown("""
This dashboard runs a **hybrid simulation** integrating **Agent-Based Simulation (ABS)** for psychological customer behavior and **Discrete Event Simulation (DES)** for the physical center's operations. 
Use the sidebar to adjust operational capacities and run the simulation!
""")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Simulation Settings")
    st.markdown("Adjust the constraints and environment of the service center.")
    
    sim_time = st.slider("Simulation Duration (Minutes)", min_value=120, max_value=2400, value=config.SIMULATION_TIME, step=60)
    general_bays = st.number_input("Number of General Bays", min_value=1, max_value=20, value=config.NUM_GENERAL_BAYS)
    express_bays = st.number_input("Number of Express Bays", min_value=0, max_value=10, value=config.NUM_EXPRESS_BAYS)
    inspection_bays = st.number_input("Number of Inspection Bays", min_value=1, max_value=5, value=config.NUM_INSPECTION_BAYS)
    
    st.divider()
    run_button = st.button("🚀 Run Simulation", use_container_width=True, type="primary")

# --- Main Logic ---
if run_button:
    with st.spinner('Running hybrid simulation logic... this may take a moment.'):
        # Override config
        config.SIMULATION_TIME = sim_time
        config.NUM_GENERAL_BAYS = general_bays
        config.NUM_EXPRESS_BAYS = express_bays
        config.NUM_INSPECTION_BAYS = inspection_bays
        
        # Clear previous global logs in case of re-runs
        SIM_LOGS.clear()
        
        # Execute Engine
        env = simpy.Environment()
        sc = ServiceCenter(env)
        env.process(simulation_manager(env, sc))
        env.run(until=sim_time)
        
        # Process visual outputs
        analysis.process_logs(SIM_LOGS, output_dir="outputs")
        
    st.toast('Simulation Completed Successfully!', icon='✅')

    # --- Display Metrics ---
    st.subheader("📊 Performance Metrics")
    
    df = pd.DataFrame(SIM_LOGS)
    total_customers = df['customer'].nunique()
    completed = df[df['event'].str.contains("Departed")].shape[0]
    balked = df[df['event'].str.contains("Balked")].shape[0]
    reneged = df[df['event'].str.contains("Reneged")].shape[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Customers Evaluated", f"{total_customers:,}")
    with col2:
        st.metric("Successfully Serviced Rate", f"{(completed/max(1, total_customers))*100:.1f}%", f"{completed} Vehicles")
    with col3:
        st.metric("Lost Customers (Balked)", f"{(balked/max(1, total_customers))*100:.1f}%", f"{balked} Walkouts", delta_color="inverse")
    with col4:
        st.metric("Lost Customers (Reneged)", f"{(reneged/max(1, total_customers))*100:.1f}%", f"{reneged} Lost Patience", delta_color="inverse")

    st.divider()

    # --- Display Visualizations ---
    st.subheader("📈 Visualization Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Customer Outcomes", "Queue Traffic Load", "Wait Time Distributions", "Raw Event Data"])
    
    outputs_dir = "outputs"
    
    with tab1:
        st.markdown("**Overview of behavioral outcomes based on customer patience and queue length.**")
        img_path = os.path.join(outputs_dir, "customer_outcomes.png")
        if os.path.exists(img_path):
             st.image(Image.open(img_path), use_container_width=True)
        else:
             st.info("Insufficient data variation to generate pie chart (No balking/reneging occurred).")
             
    with tab2:
        st.markdown("**Hourly flow of vehicles entering the various service queues.**")
        img_path = os.path.join(outputs_dir, "queue_traffic_hourly.png")
        if os.path.exists(img_path):
             st.image(Image.open(img_path), use_container_width=True)
        else:
            st.info("No queue joining events logged.")
            
    with tab3:
        st.markdown("**Statistical spread of waiting times inside each defined queue.**")
        img_path = os.path.join(outputs_dir, "wait_times_distribution.png")
        if os.path.exists(img_path):
             st.image(Image.open(img_path), use_container_width=True)
        else:
             st.info("Insufficient data to calculate wait times.")

    with tab4:
        st.markdown("**Raw Chronological Event Logs**")
        st.dataframe(df, use_container_width=True)

else:
    # If the app just loaded, show a placeholder
    st.info("👈 Adjust parameters in the sidebar and click **Run Simulation** to generate insights.", icon="ℹ️")
