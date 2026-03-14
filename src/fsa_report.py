import inspect
from enum import Enum
from typing import Dict, Any, Optional, Iterable, List, Type

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

    @fsa_step(transitions=[(WorkflowState.OK, [BroadcastQueryEvent]),
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

def _inspect_workflow_class(cls, enum_types: Type[Enum]):
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


def validate_fsa(
        fsa: Dict[Any, Any],
        require_transition_labels: Optional[Iterable[Any]] = None,
        require_all_states_have_transitions: bool = False,
        start_node: str = "StartEvent"
):
    errors: List[str] = []

    for state, transitions in fsa.items():
        if not isinstance(transitions, dict):
            errors.append(f"Error parsing `{state}` - not a dict.")
            continue
        if require_all_states_have_transitions and len(transitions) == 0:
            errors.append(f"State `{state}` doesn't have any transitions.")
        if require_transition_labels is not None:
            missing = [lbl for lbl in require_transition_labels if lbl not in transitions]
            if missing:
                errors.append(f"State `{state}` missing transitions: {missing}.")

    if start_node in fsa:
        reachable = {start_node}
        stack = [start_node]

        while stack:
            current = stack.pop()
            for targets in fsa[current].values():
                for target in targets:
                    if target not in reachable:
                        reachable.add(target)
                        stack.append(target)

        all_states = set(fsa.keys())
        unreachable = all_states - reachable
        if unreachable:
            errors.append(f"Unreachable states from `{start_node}`: {unreachable}")
    else:
        errors.append(f"Start node `{start_node}` not found in FSA.")

    valid = len(errors) == 0
    return valid, errors


def draw_fsa_graph(fsa_transitions):
    from pyvis.network import Network
    # notebook=False, directed=True
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
        node_style = {
            "label": event_name,
            "color": {"background": "#ffffff", "border": "#000000"},
            "shape": "ellipse",
            "borderWidth": 1,
            "font": {"color": "#000000"}
        }

        if event_name == "StopEvent":
            node_style["borderWidth"] = 4
            node_style["color"]["highlight"] = {"border": "#000000", "background": "#ffffff"}

        net.add_node(event_name, **node_style)

    net.add_node("START_NODE", label=" ", shape="dot", size=3, color="#000000")
    net.add_edge("START_NODE", "StartEvent", width=1, color="#000000", arrows="to")

    for (src, dst), states in edge_map.items():
        full_label = " / ".join(states)

        net.add_edge(
            src,
            dst,
            label=full_label,
            font={
                'size': 10,
                'align': 'horizontal',
                'color': '#000000',
                'background': '#ffffff'
            },
            color="#000000",
            width=1,
            arrows="to"
        )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "repulsion",
        "repulsion": { "nodeDistance": 150 }
      }
    }
    """)

    return net

def draw_fsa_report(workflow_obj, workflow_state_obj, filename="fsa_report.html", notebook=False):

    fsa_transitions = inspect_workflow_class(workflow_obj, workflow_state_obj)
    dot = draw_fsa_graph(fsa_transitions)
    dot.show("fsa_graph.html", notebook=False)

    ok, errors = validate_fsa(fsa_transitions, require_transition_labels=workflow_state_obj)
    if not ok:
        print(errors)
    else:
        print("FSA is valid.")


if __name__ == "__main__":
    draw_fsa_report(WorkflowTemplate, WorkflowState, filename="fsa_report.html")
