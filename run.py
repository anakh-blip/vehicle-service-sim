import argparse
import logging
import simpy
from src.environment import ServiceCenter
from src.simulation import simulation_manager, SIM_LOGS
from src import config
from src import analysis

# Configure root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimulationRunner")

def print_banner():
    banner = """
    ========================================================
     🚗 VEHICLE SERVICE CENTER HYBRID SIMULATION
        (Agent-Based & Discrete Event Simulation)
    ========================================================
    """
    print(banner)

def main():
    parser = argparse.ArgumentParser(description="Run the Vehicle Service Center Simulation.")
    parser.add_argument('--time', type=int, default=config.SIMULATION_TIME, 
                        help='Total simulation time in minutes (default from config)')
    parser.add_argument('--bays', type=int, default=config.NUM_GENERAL_BAYS, 
                        help='Number of general service bays available')
    parser.add_argument('--express', type=int, default=config.NUM_EXPRESS_BAYS, 
                        help='Number of express service bays available')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed debug logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Override config logic via CLI arguments
    if args.time: config.SIMULATION_TIME = args.time
    if args.bays: config.NUM_GENERAL_BAYS = args.bays
    if args.express: config.NUM_EXPRESS_BAYS = args.express

    print_banner()
    logger.info(f"Initializing Environment parameters:")
    logger.info(f"- Simulation Time:     {config.SIMULATION_TIME} minutes")
    logger.info(f"- General Bays:        {config.NUM_GENERAL_BAYS}")
    logger.info(f"- Express Bays:        {config.NUM_EXPRESS_BAYS}")
    logger.info(f"- Inspection Bays:     {config.NUM_INSPECTION_BAYS}")
    
    logger.info("Starting simulation engine. Generating behavioral agents and processing DES Queues...")
    
    env = simpy.Environment()
    sc = ServiceCenter(env)
    
    # Start the core background process
    env.process(simulation_manager(env, sc))
    
    # Run simulation
    env.run(until=config.SIMULATION_TIME)
    
    print("⏳ Simulation sequence completed!")
    
    # Output to the root outputs folder
    analysis.process_logs(SIM_LOGS, output_dir="outputs")

if __name__ == "__main__":
    main()
