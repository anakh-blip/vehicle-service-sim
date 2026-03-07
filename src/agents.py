import numpy as np
import random
from src import config

class CustomerAgent:
    """
    Represents an autonomous customer agent with psychological traits 
    affecting their behavior in the simulation (Balking and Reneging).
    """
    def __init__(self, agent_id):
        self.id = agent_id
        
        # Assign personality and emotion based on configured probabilities
        self.personality = np.random.choice(
            ['Conservative', 'Steady', 'Aggressive'], 
            p=config.PERSONALITY_PROBS
        )
        self.emotion = np.random.choice(
            ['Positive', 'Neutral', 'Negative', 'Unstable'], 
            p=config.EMOTION_PROBS
        )
        
        self.patience_threshold = self._calculate_patience()
        
        # Metrics to track
        self.arrival_time = None
        self.queue_start_time = None
        self.service_start_time = None
        self.departure_time = None
        self.status = "Created" # Options: Created, Waiting, Servicing, Completed, Reneged, Balked

    def _calculate_patience(self):
        """
        Calculates how long the customer is willing to wait in queue
        before reneging, using their personality base and emotional multiplier.
        """
        # Base limits
        base_min, base_max = config.BASE_PATIENCE_LIMITS[self.personality]
        base_patience = random.uniform(base_min, base_max)
        
        # Apply emotional modifier
        multiplier = config.EMOTION_MULTIPLIERS[self.emotion]
        
        # If unstable, they might randomly act irrationally short or long
        if self.emotion == 'Unstable' and random.random() < 0.2:
            multiplier = 0.2 # Sudden drop in patience
            
        final_patience = base_patience * multiplier
        return final_patience

    def decide_balk(self, current_queue_length):
        """
        Balking: Decides if they refuse to join the queue upon arrival.
        Returns True if they leave immediately, False to stay.
        """
        # A simple balking threshold based on personality
        if self.personality == 'Aggressive':
            threshold = 3
        elif self.personality == 'Steady':
            threshold = 6
        else: # Conservative
            threshold = 10
            
        if self.emotion == 'Negative':
            threshold = max(1, threshold - 2)
            
        return current_queue_length >= threshold

    def update_emotion(self, wait_time):
        """
        Dynamic emotional state mapping. The longer they wait, the worse they feel.
        """
        if wait_time > self.patience_threshold * 0.5:
            if self.emotion in ['Positive', 'Neutral']:
                self.emotion = 'Negative'
                # Re-calculate patience with worse emotion
                self.patience_threshold = self._calculate_patience()
                
    def __str__(self):
        return f"Customer {self.id} ({self.personality}, {self.emotion}) | Patience: {self.patience_threshold:.1f}m"
