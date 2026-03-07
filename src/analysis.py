import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def process_logs(logs, output_dir="outputs"):
    """
    Process raw simulation event dictionaries into a Pandas DataFrame,
    prints base metrics, and generates visualizations.
    """
    if not logs:
        print("No simulation logs to process.")
        return
        
    df = pd.DataFrame(logs)
    
    # Save raw data
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "sim_logs.csv")
    df.to_csv(out_file, index=False)
    
    # --- Metrics Processing ---
    total_customers = df['customer'].nunique()
    completed = df[df['event'].str.contains("Departed")].shape[0]
    balked = df[df['event'].str.contains("Balked")].shape[0]
    reneged = df[df['event'].str.contains("Reneged")].shape[0]
    
    print("\n" + "="*40)
    print("=== FINAL SIMULATION PERFORMANCE REPORT ===")
    print("="*40)
    print(f"Total Unique Customers Evaluated: {total_customers}")
    print(f"✅ Successfully Serviced: {completed} ({(completed/total_customers)*100:.1f}%)")
    print(f"❌ Customers Lost (Immediate Balking): {balked} ({(balked/total_customers)*100:.1f}%)")
    print(f"❌ Customers Lost (Reneging/Patience): {reneged} ({(reneged/total_customers)*100:.1f}%)")
    print("="*40)
    print(f"\nRaw event logs saved to: {out_file}")
    
    # --- Visualizations ---
    print("\nGenerating visual analysis reports in the 'outputs' folder...")
    _generate_visualizations(df, output_dir)
    print("Done! Check the 'outputs/' directory for generated charts.")

def _generate_visualizations(df, output_dir):
    """Generates charts for system evaluation using Seaborn and Matplotlib."""
    # 1. Status Distribution Pie Chart
    plt.figure(figsize=(8, 8))
    
    completed = df[df['event'].str.contains("Departed")].shape[0]
    balked = df[df['event'].str.contains("Balked")].shape[0]
    reneged = df[df['event'].str.contains("Reneged")].shape[0]
    
    cases = [completed, balked, reneged]
    labels = ['Serviced', 'Balked (Queues too long)', 'Reneged (Lost Patience)']
    colors = ['#4CAF50', '#FF9800', '#F44336'] # Green, Orange, Red
    
    # Only keep non-zero slices
    cases_clean = [c for c in cases if c > 0]
    labels_clean = [l for i, l in enumerate(labels) if cases[i] > 0]
    colors_clean = [c for i, c in enumerate(colors) if cases[i] > 0]
    
    if cases_clean:
        plt.pie(cases_clean, labels=labels_clean, autopct='%1.1f%%', startangle=140, colors=colors_clean)
        plt.title('Final Customer Outcomes Breakdown')
        plt.savefig(os.path.join(output_dir, 'customer_outcomes.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Events over Time (Queue Load Visualization)
    plt.figure(figsize=(12, 6))
    # Count general queue arrivals
    q_joins = df[df['event'].str.contains("Joined")].copy()
    if not q_joins.empty:
        q_joins['hour'] = (q_joins['time'] / 60).astype(int)
        hourly_traffic = q_joins.groupby(['hour', 'queue']).size().reset_index(name='count')
        
        sns.barplot(data=hourly_traffic, x='hour', y='count', hue='queue', palette='viridis')
        plt.title('Vehicle Traffic Volume per Hour by Queue Type')
        plt.xlabel('Simulation Time (Hour)')
        plt.ylabel('Number of Vehicles Entering Queue')
        plt.legend(title='Queue Type')
        plt.savefig(os.path.join(output_dir, 'queue_traffic_hourly.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Wait Times (Derived from Arrival and Service Start pairs)
    # We trace each customer's lifecycle to calculate actual wait times
    service_starts = df[df['event'].str.contains("Started")]
    arrivals = df[df['event'].str.contains("Joined")]
    
    wait_times = []
    for c in df['customer'].unique():
        c_events = df[df['customer'] == c]
        # Simplistic calculation: Arrival at queue vs started service
        for q_type in ['Inspection', 'General', 'Express']:
             q_join = c_events[(c_events['event'] == 'Arrival / Joined Queue') | (c_events['event'].str.contains(f"Joined {q_type}"))]
             q_start = c_events[c_events['event'].str.contains(f"Started {q_type}")]
             if not q_join.empty and not q_start.empty:
                 wait_t = q_start.iloc[0]['time'] - q_join.iloc[0]['time']
                 wait_times.append({'customer': c, 'queue': q_type, 'wait_time_minutes': wait_t})
                 
    if wait_times:
        wait_df = pd.DataFrame(wait_times)
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=wait_df, x='queue', y='wait_time_minutes', palette='pastel')
        plt.title('Distribution of Customer Wait Times per Queue')
        plt.ylabel('Wait Time (Minutes)')
        plt.xlabel('Queue / Service Bay Type')
        plt.savefig(os.path.join(output_dir, 'wait_times_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()

