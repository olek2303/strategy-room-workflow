import inspect
from enum import Enum
from workflow import StartEvent, BroadcastQueryEvent, CEOEvent, RevisionEvent, \
    ComplianceEvent, RedTeamEvent, BlueTeamEvent, StopEvent
import enum

class WorkflowState(Enum):
    OK = "OK"
    REVISION_NEEDED = "REVISION_NEEDED"
    ERROR = "ERROR"


def fsa_step(transitions):
    def decorator(func):
        signature = inspect.signature(func)
        event_param = signature.parameters.get('event')

        func._expected_event_class = event_param.annotation if event_param else None
        func._fsa_transitions = transitions

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._fsa_transitions = transitions
        wrapper._expected_event_class = func._expected_event_class
        return wrapper

    return decorator

class WorkflowTemplate:
    """ Template for a workflow with parallel steps and legal compliance check """

    @fsa_step(transitions=[(WorkflowState.OK, [RedTeamEvent, BlueTeamEvent]),
                           (WorkflowState.REVISION_NEEDED, [StartEvent]),
                           (WorkflowState.ERROR, [StartEvent])])
    def start(self, query: str, event: StartEvent):
        """ Start the workflow with a given query """
        pass

    @fsa_step(transitions=[(WorkflowState.OK, [CEOEvent]),
                           (WorkflowState.REVISION_NEEDED, [BroadcastQueryEvent]),
                           (WorkflowState.ERROR, [BroadcastQueryEvent])])
    def red_team_step(self, query: str, event: BroadcastQueryEvent):
        """ Red Team analyzes the query and identifies risks """
        pass


    @fsa_step(transitions=[(WorkflowState.OK, [CEOEvent]),
                           (WorkflowState.REVISION_NEEDED, [BroadcastQueryEvent]),
                           (WorkflowState.ERROR, [BroadcastQueryEvent])])
    def blue_team_step(self, query: str, event: BroadcastQueryEvent):
        """ Blue Team analyzes the query and identifies benefits """
        pass

    @fsa_step(transitions=[(WorkflowState.OK, [RevisionEvent]),
                           (WorkflowState.REVISION_NEEDED, [CEOEvent]),
                           (WorkflowState.ERROR, [CEOEvent])])
    def ceo_decision_step(self, red_data: str, blue_data: str, event: CEOEvent, legal_feedback: str = "None"):
        """ CEO makes a decision based on Red and Blue team analyses and legal feedback """
        pass

    @fsa_step(transitions=[(WorkflowState.OK, [StopEvent]),
                           (WorkflowState.REVISION_NEEDED, [CEOEvent]),
                           (WorkflowState.ERROR, [RevisionEvent])])
    def legal_compliance_step(self, proposed_decision: str, reasoning: str, event: ComplianceEvent):
        """ Legal team checks the CEO's decision for compliance and provides feedback """
        pass

def inspect_workflow_class(cls, enum_types: enum):
    fsa_transitions = {}

    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if hasattr(attr, "_fsa_transitions"):
            event_class = getattr(attr, "_expected_event_class", None)

            if event_class is None:
                raise ValueError(f"Method {attr_name} doesn't have event argument.")

            event_name = event_class.__name__ if hasattr(event_class, "__name__") else "Unknown"
            fsa_transitions[event_name] = {}

            for state, events in attr._fsa_transitions:
                allowed = [e.__name__ for e in events]
                fsa_transitions[event_name][state] = allowed

    # fill in missing states with empty lists
    states_from_cls = set(fsa_transitions.keys())

    missing_events = {
        e
        for transitions in fsa_transitions.values()
        for events in transitions.values()
        for e in events
        if e not in states_from_cls
    }

    new_fsa_entries = {
        event_name: {s: [event_name] for s in enum_types}
        for event_name in missing_events
    }

    fsa_transitions.update(new_fsa_entries)

    return fsa_transitions


def draw_fsa_graph(fsa_transitions):
    from pyvis.network import Network
    net = Network(directed=True, height="750px", width="100%", notebook=False)

    edge_map = {}

    for event_name, transitions in fsa_transitions.items():
        for state, allowed_events in transitions.items():
            state_label = state.name if hasattr(state, 'name') else str(state)
            for allowed_event in allowed_events:
                pair = (event_name, allowed_event)
                if pair not in edge_map:
                    edge_map[pair] = []
                if state_label not in edge_map[pair]:
                    edge_map[pair].append(state_label)

    for event_name in fsa_transitions.keys():
        net.add_node(event_name, label=event_name, color="#90EE90", shape="ellipse")

    net.add_node("START_NODE", label=" ", shape="dot", size=5, color="black")
    net.add_edge("START_NODE", "StartEvent", width=2, color="gray")

    for (src, dst), states in edge_map.items():
        full_label = "\n".join(states)

        net.add_edge(
            src,
            dst,
            label=full_label,
            font={
                'size': 8,
                'align': 'top',
                'multi': True,
                'vadjust': -7
            },
            color="#666666",
            arrows="to"
        )

    net.toggle_physics(True)
    return net

def draw_fsa_report(workflow_obj, workflow_state_obj, filename="fsa_report.html", notebook=False):

    fsa_transitions = inspect_workflow_class(workflow_obj, workflow_state_obj)
    dot = draw_fsa_graph(fsa_transitions)
    dot.show("fsa_graph.html", notebook=False)


if __name__ == "__main__":
    draw_fsa_report(WorkflowTemplate, WorkflowState, filename="fsa_report.html")
