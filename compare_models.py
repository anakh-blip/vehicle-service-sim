"""
Comparison: Pure DES vs Hybrid (ABS+DES) Model
Shows how the hybrid model reduces waiting times and queue lengths.
"""

import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Shared config ────────────────────────────────────────────────────────────
RANDOM_SEED         = 42
SIMULATION_TIME     = 600      # minutes
NUM_INSPECTION_BAYS = 2
NUM_GENERAL_BAYS    = 5
NUM_EXPRESS_BAYS    = 1
INTERARRIVAL_MEAN   = 15.0
INSPECTION_MEAN     = 10.0
INSPECTION_STD      = 2.0
SERVICE_MEAN        = 60.0
SERVICE_STD         = 15.0
EXPRESS_MEAN        = 20.0
EXPRESS_STD         = 5.0

PERSONALITY_PROBS = [0.2, 0.5, 0.3]
EMOTION_PROBS     = [0.4, 0.4, 0.15, 0.05]
PATIENCE_LIMITS   = {'Conservative': (60, 120), 'Steady': (45, 90), 'Aggressive': (15, 45)}
EMOTION_MULT      = {'Positive': 1.2, 'Neutral': 1.0, 'Negative': 0.6, 'Unstable': 0.8}
BALK_THRESHOLDS   = {'Aggressive': 3, 'Steady': 6, 'Conservative': 10}


def get_interarrival(current_time):
    t = current_time % 1440
    rate = INTERARRIVAL_MEAN * 0.4 if (0 <= t <= 120 or 300 <= t <= 420) else INTERARRIVAL_MEAN
    return np.random.exponential(rate)

def get_service_time(is_express=False):
    t = np.random.normal(EXPRESS_MEAN, EXPRESS_STD) if is_express else np.random.normal(SERVICE_MEAN, SERVICE_STD)
    return max(1.0, t)

def get_inspection_time():
    return max(1.0, np.random.normal(INSPECTION_MEAN, INSPECTION_STD))


# ── Pure DES model ────────────────────────────────────────────────────────────
def des_customer(env, cid, sc, logs):
    arrival = env.now
    logs['queue_snapshots'].append((env.now, len(sc['inspection'].queue)))

    with sc['inspection'].request() as req:
        yield req
        wait = env.now - arrival
        logs['inspection_waits'].append(wait)
        yield env.timeout(get_inspection_time())

    is_express = random.random() < 0.2
    bay = sc['express'] if is_express else sc['general']
    q_start = env.now

    with bay.request() as req:
        yield req
        wait = env.now - q_start
        logs['service_waits'].append(wait)
        logs['total_waits'].append((env.now - arrival - get_inspection_time()))
        yield env.timeout(get_service_time(is_express))

    logs['served'] += 1
    logs['total_times'].append(env.now - arrival)


def des_generator(env, sc, logs):
    cid = 1
    while True:
        yield env.timeout(get_interarrival(env.now))
        env.process(des_customer(env, cid, sc, logs))
        logs['arrivals'] += 1
        cid += 1


def run_des():
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    sc = {
        'inspection': simpy.Resource(env, NUM_INSPECTION_BAYS),
        'general':    simpy.Resource(env, NUM_GENERAL_BAYS),
        'express':    simpy.Resource(env, NUM_EXPRESS_BAYS),
    }
    logs = {'inspection_waits': [], 'service_waits': [], 'total_waits': [],
            'total_times': [], 'queue_snapshots': [], 'served': 0, 'arrivals': 0,
            'balked': 0, 'reneged': 0}
    env.process(des_generator(env, sc, logs))
    env.run(until=SIMULATION_TIME)
    return logs


# ── Hybrid (ABS+DES) model ───────────────────────────────────────────────────
def get_patience(personality, emotion):
    base_min, base_max = PATIENCE_LIMITS[personality]
    patience = random.uniform(base_min, base_max) * EMOTION_MULT[emotion]
    if emotion == 'Unstable' and random.random() < 0.2:
        patience *= 0.2
    return max(1.0, patience)

def decide_balk(personality, emotion, queue_len):
    threshold = BALK_THRESHOLDS[personality]
    if emotion == 'Negative':
        threshold = max(1, threshold - 2)
    return queue_len >= threshold

def reneging_timer(env, patience, target_proc):
    try:
        yield env.timeout(patience)
        target_proc.interrupt('renege')
    except simpy.Interrupt:
        pass

def hybrid_customer(env, cid, sc, logs):
    personality = np.random.choice(['Conservative', 'Steady', 'Aggressive'], p=PERSONALITY_PROBS)
    emotion     = np.random.choice(['Positive', 'Neutral', 'Negative', 'Unstable'], p=EMOTION_PROBS)
    patience    = get_patience(personality, emotion)
    arrival     = env.now

    logs['queue_snapshots'].append((env.now, len(sc['inspection'].queue)))

    # Balking check
    if decide_balk(personality, emotion, len(sc['inspection'].queue)):
        logs['balked'] += 1
        return

    with sc['inspection'].request() as req:
        timer = env.process(reneging_timer(env, patience, env.active_process))
        try:
            yield req
            timer.interrupt('served')
            wait = env.now - arrival
            logs['inspection_waits'].append(wait)
            yield env.timeout(get_inspection_time())
        except simpy.Interrupt:
            logs['reneged'] += 1
            return

    is_express = random.random() < 0.2
    bay = sc['express'] if is_express else sc['general']
    q_start = env.now
    patience2 = get_patience(personality, emotion)

    with bay.request() as req:
        timer = env.process(reneging_timer(env, patience2, env.active_process))
        try:
            yield req
            timer.interrupt('served')
            wait = env.now - q_start
            logs['service_waits'].append(wait)
            logs['total_waits'].append(env.now - arrival)
            yield env.timeout(get_service_time(is_express))
        except simpy.Interrupt:
            logs['reneged'] += 1
            return

    logs['served'] += 1
    logs['total_times'].append(env.now - arrival)


def hybrid_generator(env, sc, logs):
    cid = 1
    while True:
        yield env.timeout(get_interarrival(env.now))
        env.process(hybrid_customer(env, cid, sc, logs))
        logs['arrivals'] += 1
        cid += 1


def run_hybrid():
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    sc = {
        'inspection': simpy.Resource(env, NUM_INSPECTION_BAYS),
        'general':    simpy.Resource(env, NUM_GENERAL_BAYS),
        'express':    simpy.Resource(env, NUM_EXPRESS_BAYS),
    }
    logs = {'inspection_waits': [], 'service_waits': [], 'total_waits': [],
            'total_times': [], 'queue_snapshots': [], 'served': 0, 'arrivals': 0,
            'balked': 0, 'reneged': 0}
    env.process(hybrid_generator(env, sc, logs))
    env.run(until=SIMULATION_TIME)
    return logs


# ── Plotting ─────────────────────────────────────────────────────────────────
def plot_comparison(des, hyb):
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Pure DES vs Hybrid (ABS+DES) Model — Waiting Time Comparison',
                 fontsize=15, fontweight='bold', y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    DES_COLOR = '#E74C3C'
    HYB_COLOR = '#2ECC71'

    # ── 1. Average wait time comparison (bar chart) ───────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    categories = ['Inspection\nWait', 'Service Bay\nWait', 'Total System\nTime']
    des_means  = [
        np.mean(des['inspection_waits']) if des['inspection_waits'] else 0,
        np.mean(des['service_waits'])    if des['service_waits']    else 0,
        np.mean(des['total_times'])      if des['total_times']      else 0,
    ]
    hyb_means  = [
        np.mean(hyb['inspection_waits']) if hyb['inspection_waits'] else 0,
        np.mean(hyb['service_waits'])    if hyb['service_waits']    else 0,
        np.mean(hyb['total_times'])      if hyb['total_times']      else 0,
    ]
    x = np.arange(len(categories))
    w = 0.35
    b1 = ax1.bar(x - w/2, des_means, w, label='Pure DES', color=DES_COLOR, alpha=0.85, edgecolor='white')
    b2 = ax1.bar(x + w/2, hyb_means, w, label='Hybrid (ABS+DES)', color=HYB_COLOR, alpha=0.85, edgecolor='white')
    ax1.bar_label(b1, fmt='%.1f min', padding=3, fontsize=8)
    ax1.bar_label(b2, fmt='%.1f min', padding=3, fontsize=8)
    ax1.set_title('Average Wait Times', fontweight='bold')
    ax1.set_ylabel('Minutes')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()
    ax1.set_ylim(0, max(des_means + hyb_means) * 1.3 + 5)

    # ── 2. Wait time distribution box plot ────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    data_to_plot = [
        des['inspection_waits'] or [0],
        hyb['inspection_waits'] or [0],
        des['service_waits']    or [0],
        hyb['service_waits']    or [0],
    ]
    bp = ax2.boxplot(data_to_plot, patch_artist=True, widths=0.5,
                     medianprops=dict(color='black', linewidth=2))
    colors = [DES_COLOR, HYB_COLOR, DES_COLOR, HYB_COLOR]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    ax2.set_xticks([1, 2, 3, 4])
    ax2.set_xticklabels(['DES\nInspection', 'Hybrid\nInspection',
                          'DES\nService Bay', 'Hybrid\nService Bay'], fontsize=8)
    ax2.set_title('Wait Time Distribution', fontweight='bold')
    ax2.set_ylabel('Wait Time (Minutes)')

    # ── 3. Queue length over time ─────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    if des['queue_snapshots']:
        dt, dq = zip(*des['queue_snapshots'])
        ax3.plot(dt, dq, color=DES_COLOR, alpha=0.7, linewidth=1.2, label='Pure DES')
    if hyb['queue_snapshots']:
        ht, hq = zip(*hyb['queue_snapshots'])
        ax3.plot(ht, hq, color=HYB_COLOR, alpha=0.7, linewidth=1.2, label='Hybrid (ABS+DES)')
    ax3.set_title('Inspection Queue Length Over Time', fontweight='bold')
    ax3.set_xlabel('Simulation Time (minutes)')
    ax3.set_ylabel('Queue Length')
    ax3.legend()
    ax3.set_xlim(0, SIMULATION_TIME)

    # ── 4. Outcome summary stacked bar ────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    models   = ['Pure DES', 'Hybrid (ABS+DES)']
    served   = [des['served'],  hyb['served']]
    balked   = [des['balked'],  hyb['balked']]
    reneged  = [des['reneged'], hyb['reneged']]
    x = np.arange(len(models))
    ax4.bar(x, served,  label='Served',  color='#2ECC71', alpha=0.85, edgecolor='white')
    ax4.bar(x, reneged, label='Reneged', color='#E74C3C', alpha=0.85, edgecolor='white',
            bottom=served)
    ax4.bar(x, balked,  label='Balked',  color='#F39C12', alpha=0.85, edgecolor='white',
            bottom=[s + r for s, r in zip(served, reneged)])
    for i, (s, b, r) in enumerate(zip(served, balked, reneged)):
        total = s + b + r
        ax4.text(i, total + 0.5, f'{s/(total)*100:.1f}% served', ha='center', fontsize=9, fontweight='bold')
    ax4.set_title('Customer Outcome Breakdown', fontweight='bold')
    ax4.set_ylabel('Number of Customers')
    ax4.set_xticks(x)
    ax4.set_xticklabels(models)
    ax4.legend()

    plt.savefig('outputs/des_vs_hybrid_comparison.png', dpi=150, bbox_inches='tight')
    print("\nComparison chart saved to: outputs/des_vs_hybrid_comparison.png")

    # Print summary
    print("\n" + "="*50)
    print("  MODEL COMPARISON SUMMARY")
    print("="*50)
    for label, logs in [("Pure DES", des), ("Hybrid", hyb)]:
        total = logs['served'] + logs['balked'] + logs['reneged']
        avg_insp = np.mean(logs['inspection_waits']) if logs['inspection_waits'] else 0
        avg_svc  = np.mean(logs['service_waits'])    if logs['service_waits']    else 0
        avg_tot  = np.mean(logs['total_times'])       if logs['total_times']      else 0
        print(f"\n  [{label}]")
        print(f"  Customers evaluated : {total}")
        print(f"  Served              : {logs['served']} ({logs['served']/max(total,1)*100:.1f}%)")
        print(f"  Balked              : {logs['balked']}")
        print(f"  Reneged             : {logs['reneged']}")
        print(f"  Avg inspection wait : {avg_insp:.1f} min")
        print(f"  Avg service wait    : {avg_svc:.1f} min")
        print(f"  Avg total time      : {avg_tot:.1f} min")
    print("="*50)


if __name__ == "__main__":
    print("Running Pure DES simulation...")
    des_logs = run_des()
    print("Running Hybrid (ABS+DES) simulation...")
    hyb_logs = run_hybrid()
    print("Generating comparison chart...")
    plot_comparison(des_logs, hyb_logs)
    plt.show()
