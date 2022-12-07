import logging

import azure.functions as func
import azure.durable_functions as df


async def main(mytimer: func.TimerRequest, starter: str) -> None:
    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new("ACUPD-DurableFunctionsOrchestrator", None, None)
    
    logging.info(f"Started orchestration with ID = '{instance_id}'.")
