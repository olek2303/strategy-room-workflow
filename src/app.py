from workflow import StrategyFlow
import asyncio
from llama_index.utils.workflow import draw_all_possible_flows

async def main():
    subject = "Implementing a new remote work policy in a tech company."

    flow = StrategyFlow(timeout=120, verbose=True)

    # Visualize the workflow
    draw_all_possible_flows(flow, "strategy_flow_workflow.html")

    result = await flow.run(query=subject)

    print("final CEO Decision based on Red and Blue Team analyses:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
