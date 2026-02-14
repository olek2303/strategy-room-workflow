from workflows import Workflow, step, Context
from workflows.events import (
    Event,
    StartEvent,
    StopEvent,
)

from base_llm import BaseLLM
from src.models import StrategicDecision, ComplianceReport


class RedTeamEvent(Event):
    """ Formulating cons about some subject """
    query: str

class BlueTeamEvent(Event):
    """ Formulating pros about some subject """
    query: str

class BroadcastQueryEvent(Event):
    """ Sending query to red and blue team """
    query: str

class ComplianceEvent(Event):
    """ CEO decision is sent to legal for compliance check """
    proposed_decision: str
    reasoning: str

class RevisionEvent(Event):
    """ CEO receives legal feedback and is asked to revise the decision """
    legal_feedback: str
    violations_found: list[str]

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
    async def legal_compliance_step(self, ctx: Context, event: ComplianceEvent) -> StopEvent | RevisionEvent:
        print("[Compliance] Analiza prawna decyzji CEO...")

        compliance_prompt = f"""
                You are the Chief Legal Officer. Analyze the CEO's proposed decision:
                Decision: {event.proposed_decision}
                Reasoning: {event.reasoning}

                Check for labor law violations, discrimination, or massive financial risks.
            """

        response = await self.llm.scomplete(
            prompt=compliance_prompt,
            output_cls=ComplianceReport
        )
        report: ComplianceReport = response.model

        if not report.is_compliant:
            print(f"❌ [Compliance] Weto! Znaleziono naruszenia: {report.violations}")
            return RevisionEvent(
                legal_feedback=report.mandatory_changes,
                violations_found=report.violations
            )

        print("[Compliance] Decyzja zatwierdzona. Zakończenie procesu.")
        return StopEvent(result=event.proposed_decision)

    @step
    async def ceo_decision_step(self, ctx: Context, event: CEOEvent | RevisionEvent) -> ComplianceEvent | None:
        legal_feedback = "None"

        if isinstance(event, CEOEvent):
            finished_teams = await ctx.store.get("finished_teams", default=set())
            finished_teams.add(event.source)
            await ctx.store.set("finished_teams", finished_teams)

            required_teams = {"red", "blue"}
            if required_teams - finished_teams:
                return None

        elif isinstance(event, RevisionEvent):
            print(f"[CEO] Otrzymano wezwanie do poprawy! Uwagi: {event.legal_feedback}")
            legal_feedback = f"MANDATORY CHANGES: {event.legal_feedback} | VIOLATIONS: {event.violations_found}"

        subject = await ctx.store.get("subject")
        red_data = await ctx.store.get("red_team_output")
        blue_data = await ctx.store.get("blue_team_output")

        decision_prompt = f"""
            You are the CEO. Analyze the provided data.
            Subject: {subject}
            Red Team Data: {red_data}
            Blue Team Data: {blue_data}

            CRITICAL LEGAL FEEDBACK (You MUST adjust your decision based on this if not 'None'):
            {legal_feedback}
        """

        response = await self.llm.scomplete(
            prompt=decision_prompt,
            output_cls=StrategicDecision
        )

        decision: StrategicDecision = response.model

        print(f"CEO Verdict: {decision.final_verdict.value}")
        print(f"CEO Reasoning: {decision.reasoning}")

        return ComplianceEvent(
            proposed_decision=decision.final_verdict.value,
            reasoning=decision.reasoning
        )
