import simpy
import random
import logging
from src.config import *
from src.agents import CustomerAgent
from src.environment import ServiceCenter
from src import analysis

# Setup structured logger
logger = logging.getLogger("simulation")
logger.setLevel(logging.INFO)

SIM_LOGS = []

def record_log(env, customer_id, event_type, queue_type="None"):
    """Appends an event log to the global registry for analysis."""
    SIM_LOGS.append({
        "time": round(env.now, 2),
        "customer": customer_id,
        "event": event_type,
        "queue": queue_type
    })
    logger.debug(f"Time {env.now:>6.2f} | Customer {customer_id:>3} | {event_type:<30} | Queue: {queue_type}")

def reneging_timer(env, customer, process_to_interrupt):
    """
    ABS mechanism: Triggers when the customer's patience runs out before
    they acquire the resource they are waiting for.
    """
    try:
        # The customer waits until their patience limit
        patience = max(1.0, customer.patience_threshold)
        yield env.timeout(patience)
        # If the timeout completes, and they are still waiting... trigger interrupt
        if customer.status == "Waiting":
            process_to_interrupt.interrupt(cause=f"Reneging timer expired ({customer.personality}/{customer.emotion})")
    except simpy.Interrupt:
         # Timer stopped early (they got served!)
         pass

def customer_lifecycle(env, customer, service_center):
    """
    DES process integrating the ABS logic for a single customer.
    """
    customer.arrival_time = env.now
    
    # balking decision early on
    queue_len = service_center.current_inspection_queue_length()
    if customer.decide_balk(queue_len):
        customer.status = "Balked"
        record_log(env, customer.id, "Balked (Long Queue)", "Inspection")
        return
        
    customer.status = "Waiting"
    customer.queue_start_time = env.now
    record_log(env, customer.id, "Arrival / Joined Queue", "Inspection")
    
    # We create a reference to this main lifecycle process
    main_process = env.active_process
    
    # 1. Inspection Phase
    with service_center.inspection_bays.request() as inspection_req:
        # Start ABS Reneging monitor for the inspection queue
        patience_proc = env.process(reneging_timer(env, customer, main_process))
        
        try:
            # Yield either getting the resource, or being interrupted
            yield inspection_req 
            
            # If we get here, they successfully got the resource! Cancel reneging timer.
            patience_proc.interrupt(cause="Got Served")
            customer.status = "Servicing"
            record_log(env, customer.id, "Started Inspection", "Inspection")
            
            inspect_time = get_inspection_time()
            yield env.timeout(inspect_time)
            
        except simpy.Interrupt as i:
            # They lost patience! (ABS kicks in)
            customer.status = "Reneged"
            record_log(env, customer.id, "Reneged (Lost Patience)", "Inspection")
            return
            
    # Determine the repair needed based on some logic (e.g. 20% express)
    is_express = random.random() < 0.2
    req_queue = "Express" if is_express else "General"
    bay_resource = service_center.express_bays if is_express else service_center.general_bays
    
    # 2. Repair Phase
    customer.status = "Waiting"
    record_log(env, customer.id, f"Joined {req_queue} Queue", req_queue)
    
    with bay_resource.request() as bay_req:
        # Start a fresh patience clock for the actual repair queue
        patience_proc = env.process(reneging_timer(env, customer, main_process))
        
        try:
             yield bay_req
             patience_proc.interrupt(cause="Got Served")
             
             customer.status = "Servicing"
             customer.service_start_time = env.now
             record_log(env, customer.id, f"Started {req_queue} Service", req_queue)
             
             service_time = get_service_time(is_express)
             yield env.timeout(service_time)
             
             customer.status = "Completed"
             customer.departure_time = env.now
             record_log(env, customer.id, "Departed (Service Complete)", "None")
             
        except simpy.Interrupt:
             customer.status = "Reneged"
             record_log(env, customer.id, f"Reneged (Lost Patience)", req_queue)
             return


def simulation_manager(env, service_center):
    """
    Continuously generates new customers based on dynamic arrival distributions.
    """
    customer_id = 1
    while True:
        # Dynamic arrival rate based on the current simulation clock
        yield env.timeout(get_random_interarrival(env.now))
        curr_customer = CustomerAgent(customer_id)
        # Spin up the lifecycle for the new customer
        env.process(customer_lifecycle(env, curr_customer, service_center))
        customer_id += 1


if __name__ == "__main__":
    print(f"Vehicle Service Center Hybrid Simulation (ABS/DES) starting...")
    env = simpy.Environment()
    sc = ServiceCenter(env)
    
    # Start processes
    env.process(simulation_manager(env, sc))
    
    # Run
    env.run(until=SIMULATION_TIME)
    
    print("\nSimulation complete. Generating analysis...")
    analysis.process_logs(SIM_LOGS)
    print("Done!")
