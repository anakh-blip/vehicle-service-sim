import simpy
from src import config

class ServiceCenter:
    """
    The physical environment of the Discrete Event Simulation (DES).
    Holds the resources that incoming vehicles compete for.
    """
    def __init__(self, env):
        self.env = env
        
        # Defined resources
        self.inspection_bays = simpy.Resource(env, capacity=config.NUM_INSPECTION_BAYS)
        self.general_bays = simpy.Resource(env, capacity=config.NUM_GENERAL_BAYS)
        self.express_bays = simpy.Resource(env, capacity=config.NUM_EXPRESS_BAYS)
        
    def current_general_queue_length(self):
        """Returns the number of vehicles currently waiting for a general bay."""
        return len(self.general_bays.queue)

    def current_express_queue_length(self):
        """Returns the number of vehicles currently waiting for an express bay."""
        return len(self.express_bays.queue)

    def current_inspection_queue_length(self):
         return len(self.inspection_bays.queue)
