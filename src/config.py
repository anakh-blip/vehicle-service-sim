# Central Configuration file for the Vehicle Service Center Simulation

import numpy as np

# --- General Simulation Settings ---
SIMULATION_TIME = 600  # Total simulation time in minutes (e.g., 10 hours)
RANDOM_SEED = 42       # For reproducibility

# --- Facility Resources ---
NUM_INSPECTION_BAYS = 3
NUM_GENERAL_BAYS = 13
NUM_EXPRESS_BAYS = 2

# --- Arrival Rates (Customers per minute) ---
# Example: 1 customer arrives every roughly 15 minutes
INTERARRIVAL_TIME_MEAN = 15.0

# --- Service Time Distributions (in minutes) ---
INSPECTION_TIME_MEAN = 7.0
INSPECTION_TIME_STD = 2.0

# General Service times are longer for heavy-duty
SERVICE_TIME_MEAN = 60.0    
SERVICE_TIME_STD = 15.0     

# Express service for minor repairs
EXPRESS_SERVICE_TIME_MEAN = 20.0
EXPRESS_SERVICE_TIME_STD = 5.0

# --- Psychological Parameters ---
# Defines the base patience before reneging (in minutes) based on personality
BASE_PATIENCE_LIMITS = {
    'Conservative': (60, 120),
    'Steady': (45, 90),
    'Aggressive': (15, 45)
}

# Modifiers to patience base limit based on emotion
EMOTION_MULTIPLIERS = {
    'Positive': 1.2,    # Increases patience
    'Neutral': 1.0,     # No change
    'Negative': 0.6,    # Decreases patience
    'Unstable': 0.8     # Decreases patience sporadically
}

# Probabilities of customer distributions
PERSONALITY_PROBS = [0.2, 0.5, 0.3]  # Conservative, Steady, Aggressive
EMOTION_PROBS = [0.4, 0.4, 0.15, 0.05]   # Positive, Neutral, Negative, Unstable

def get_random_interarrival(current_time):
    """
    Calculates exponential inter-arrival time based on time of day.
    Rush hours have significantly shorter interarrival times (more traffic).
    Returns the time until the next arrival.
    """
    # Assuming the simulation starts at a theoretical 08:00 AM (0 minutes)
    # 0 - 120 mins (8am - 10am): Morning Rush Hour
    # 300 - 420 mins (1pm - 3pm): Afternoon Rush Hour
    
    current_time_mod = current_time % 1440  # Support multi-day by modulo
    
    if (0 <= current_time_mod <= 120) or (300 <= current_time_mod <= 420):
        # Rush Hour: High traffic
        rate = INTERARRIVAL_TIME_MEAN * 0.4
    else:
        # Normal operations
        rate = INTERARRIVAL_TIME_MEAN
        
    return np.random.exponential(rate)

def get_service_time(is_express=False):
    """Gaussian service time."""
    if is_express:
        time = np.random.normal(EXPRESS_SERVICE_TIME_MEAN, EXPRESS_SERVICE_TIME_STD)
    else:
        time = np.random.normal(SERVICE_TIME_MEAN, SERVICE_TIME_STD)
    return max(1.0, time) # Ensure positive service time

def get_inspection_time():
    time = np.random.normal(INSPECTION_TIME_MEAN, INSPECTION_TIME_STD)
    return max(1.0, time)
