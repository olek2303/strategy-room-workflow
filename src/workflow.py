from workflows import Workflow, step, Context
from workflows.events import (
    Event,
    StartEvent,
    StopEvent,
)

from base_llm import BaseLLM


class RedTeamEvent(Event):
    """ Formulating cons about some subject """
    query: str

class BlueTeamEvent(Event):
    """ Formulating pros about some subject """
    query: str

class BroadcastQueryEvent(Event):
    """ Sending query to red and blue team """
    query: str

class CEOEvent(Event):
    """ Making final decision based on Red and Blue team inputs """
    source: str

class StrategyFlow(Workflow):
    """ Workflow for Red Team, Blue Team and CEO decision making process """

    llm = BaseLLM(model_name='openai/gpt-oss-120b')

    @step
    async def start(self, ctx: Context, event: StartEvent) -> BroadcastQueryEvent | None:
        """parallel execution of red and blue team steps"""
        print("Starting Strategy Flow...")
        print(f"received query: {event.get('query')}")

        subject = event.get("query")
        await ctx.store.set("subject", subject)

        try:
            return BroadcastQueryEvent(query=subject)
        except Exception as e:
            print(f"Error sending events: {e}")
            return None


    @step
    async def red_team_step(self, ctx: Context, event: BroadcastQueryEvent) -> CEOEvent:

        red_team_prompt = """
            You are the Red Team. Your task is to critically analyze the given subject and 
            identify potential risks, weaknesses, and downsides. 
            Provide a detailed report highlighting these aspects.
            
            Here is the subject for analysis:
            {subject}
        """

        red_team_analysis = await self.llm.acomplete(red_team_prompt.format(subject=event.query))

        print(f'red team analysis: {red_team_analysis}')
        await ctx.store.set("red_team_output", red_team_analysis)

        return CEOEvent(source='red')

    @step
    async def blue_team_step(self, ctx: Context, event: BroadcastQueryEvent) -> CEOEvent:

        blue_team_prompt = """
            You are the Blue Team. Your task is to thoroughly evaluate the given subject and 
            identify potential benefits, strengths, and opportunities. 
            Provide a comprehensive report highlighting these positive aspects.
            
            Here is the subject for analysis:
            {subject}
        """

        blue_team_analysis = await self.llm.acomplete(blue_team_prompt.format(subject=event.query))

        print(f"blue team analysis: {blue_team_analysis}")
        await ctx.store.set('blue_team_output', blue_team_analysis)

        return CEOEvent(source='blue')

    @step
    async def ceo_decision_step(self, ctx: Context, event: CEOEvent) -> StopEvent | None:

        finished_teams = await ctx.store.get("finished_teams", default=[])
        finished_teams.append(event.source)
        await ctx.store.set("finished_teams", finished_teams)

        if "red" not in finished_teams or "blue" not in finished_teams:
            return None

        subject = await ctx.store.get("subject")
        red_team_input = await ctx.store.get("red_team_output")
        blue_team_input = await ctx.store.get("blue_team_output")

        decision_prompt = """
            You are the CEO. Based on the analyses provided by the Red Team and Blue Team, 
            make a final decision regarding the subject. 
            Weigh the pros and cons carefully and provide a well-reasoned conclusion.
            
            Subject:
            {subject}
            
            Red Team Analysis:
            {red_team_input}
            
            Blue Team Analysis:
            {blue_team_input}
        """

        decision = await self.llm.acomplete(decision_prompt.format(
            subject=subject,
            red_team_input=red_team_input,
            blue_team_input=blue_team_input
        ))

        print(f'CEO response: {decision}')
        return StopEvent()
