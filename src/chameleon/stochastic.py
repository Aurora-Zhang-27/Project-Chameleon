"""Small finite-scenario stochastic PV+BESS contracts.

PV is observed at a scenario-tree node before that node's internal action is
chosen.  One action is shared by all descendants of the node, which enforces
nonanticipativity.  Reserve activation is sequential: the realized branch SOC
is carried to child nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import product
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from .charging import BidirectionalBatteryGeometry, energy_depletion
from .pv import HybridAction
from .sequential import Activation, ReserveSourcePolicy


@dataclass(frozen=True)
class ScenarioNode:
    name: str
    period: int
    parent: str | None
    conditional_probability: Fraction
    pv_available: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "conditional_probability",
            Fraction(self.conditional_probability),
        )
        object.__setattr__(self, "pv_available", Fraction(self.pv_available))
        if self.period < 0:
            raise ValueError("node period must be nonnegative")
        if not 0 < self.conditional_probability <= 1:
            raise ValueError("conditional probability must lie in (0, 1]")
        if self.pv_available < 0:
            raise ValueError("PV availability must be nonnegative")


@dataclass(frozen=True)
class FiniteScenarioTree:
    nodes: Tuple[ScenarioNode, ...]

    def __post_init__(self) -> None:
        by_name = {node.name: node for node in self.nodes}
        if len(by_name) != len(self.nodes):
            raise ValueError("scenario-node names must be unique")
        roots = [node for node in self.nodes if node.parent is None]
        if len(roots) != 1:
            raise ValueError("scenario tree must have exactly one root")
        root = roots[0]
        if root.period != 0 or root.conditional_probability != 1:
            raise ValueError("root must be period 0 with probability 1")

        for node in self.nodes:
            if node.parent is None:
                continue
            if node.parent not in by_name:
                raise ValueError(f"unknown parent for node {node.name}")
            if by_name[node.parent].period + 1 != node.period:
                raise ValueError("child period must follow parent period")

        for parent in self.nodes:
            children = [
                node for node in self.nodes if node.parent == parent.name
            ]
            if children and sum(
                node.conditional_probability for node in children
            ) != 1:
                raise ValueError(
                    "children conditional probabilities must sum to one"
                )

        leaf_periods = {self.node(name).period for name in self.leaf_names}
        if len(leaf_periods) != 1:
            raise ValueError("all leaves must have the same period")

    @property
    def root(self) -> ScenarioNode:
        return next(node for node in self.nodes if node.parent is None)

    @property
    def horizon(self) -> int:
        return max(node.period for node in self.nodes) + 1

    @property
    def leaf_names(self) -> Tuple[str, ...]:
        parent_names = {
            node.parent for node in self.nodes if node.parent is not None
        }
        return tuple(
            node.name for node in self.nodes if node.name not in parent_names
        )

    def node(self, name: str) -> ScenarioNode:
        for node in self.nodes:
            if node.name == name:
                return node
        raise KeyError(name)

    def children(self, name: str) -> Tuple[ScenarioNode, ...]:
        return tuple(node for node in self.nodes if node.parent == name)

    def path_to(self, name: str) -> Tuple[ScenarioNode, ...]:
        path = []
        current = self.node(name)
        while True:
            path.append(current)
            if current.parent is None:
                break
            current = self.node(current.parent)
        return tuple(reversed(path))

    def path_probability(self, name: str) -> Fraction:
        probability = Fraction(1)
        for node in self.path_to(name):
            probability *= node.conditional_probability
        return probability


@dataclass(frozen=True)
class StochasticContractPoint:
    scheduled_injection: Fraction
    upward_reserve: Fraction = Fraction(0)
    downward_reserve: Fraction = Fraction(0)
    activation: Activation = Activation.NONE
    upward_source: ReserveSourcePolicy = ReserveSourcePolicy.ANY
    downward_source: ReserveSourcePolicy = ReserveSourcePolicy.ANY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "scheduled_injection", Fraction(self.scheduled_injection)
        )
        object.__setattr__(
            self, "upward_reserve", Fraction(self.upward_reserve)
        )
        object.__setattr__(
            self, "downward_reserve", Fraction(self.downward_reserve)
        )
        object.__setattr__(self, "activation", Activation(self.activation))
        object.__setattr__(
            self, "upward_source", ReserveSourcePolicy(self.upward_source)
        )
        object.__setattr__(
            self, "downward_source", ReserveSourcePolicy(self.downward_source)
        )
        if self.upward_reserve < 0 or self.downward_reserve < 0:
            raise ValueError("reserve quantities must be nonnegative")


@dataclass(frozen=True)
class StochasticContract:
    by_node: Mapping[str, StochasticContractPoint]

    def validate(self, tree: FiniteScenarioTree) -> None:
        if set(self.by_node) != {node.name for node in tree.nodes}:
            raise ValueError("contract must contain exactly one point per node")


@dataclass(frozen=True)
class NodeReserveAction:
    base: HybridAction
    upward: HybridAction
    downward: HybridAction


@dataclass(frozen=True)
class StochasticPolicy:
    by_node: Mapping[str, NodeReserveAction]


@dataclass(frozen=True)
class StochasticReplayResult:
    node_start_energy: Mapping[str, Fraction]
    node_realized_end_energy: Mapping[str, Fraction]
    node_feasible: Mapping[str, bool]
    leaf_feasible: Mapping[str, bool]
    success_probability: Fraction

    @property
    def robust_feasible(self) -> bool:
        return self.success_probability == 1

    def chance_feasible(self, violation_probability: Fraction) -> bool:
        epsilon = Fraction(violation_probability)
        if not 0 <= epsilon <= 1:
            raise ValueError("violation probability must lie in [0, 1]")
        return self.success_probability >= 1 - epsilon


@dataclass(frozen=True)
class PolicySolution:
    maximum_success_probability: Fraction
    policy: StochasticPolicy

    @property
    def robust_feasible(self) -> bool:
        return self.maximum_success_probability == 1

    @property
    def existential_recourse_feasible(self) -> bool:
        return self.maximum_success_probability > 0

    def chance_feasible(self, violation_probability: Fraction) -> bool:
        epsilon = Fraction(violation_probability)
        if not 0 <= epsilon <= 1:
            raise ValueError("violation probability must lie in [0, 1]")
        return self.maximum_success_probability >= 1 - epsilon


@dataclass(frozen=True)
class NodeConditionedSOC:
    intervals: Mapping[str, Tuple[Fraction, Fraction]]
    probabilities: Mapping[str, Fraction]

    def __post_init__(self) -> None:
        if set(self.intervals) != set(self.probabilities):
            raise ValueError("SOC intervals and probabilities must share keys")
        normalized_intervals = {
            name: (Fraction(bounds[0]), Fraction(bounds[1]))
            for name, bounds in self.intervals.items()
        }
        normalized_probabilities = {
            name: Fraction(value)
            for name, value in self.probabilities.items()
        }
        if any(low > high for low, high in normalized_intervals.values()):
            raise ValueError("SOC interval lower bound exceeds upper bound")
        if sum(normalized_probabilities.values()) != 1:
            raise ValueError("node probabilities must sum to one")
        object.__setattr__(self, "intervals", normalized_intervals)
        object.__setattr__(self, "probabilities", normalized_probabilities)

    @property
    def unconditional_hull(self) -> Tuple[Fraction, Fraction]:
        return (
            min(bounds[0] for bounds in self.intervals.values()),
            max(bounds[1] for bounds in self.intervals.values()),
        )

    @property
    def singleton_marginal(self) -> Mapping[Fraction, Fraction]:
        marginal: Dict[Fraction, Fraction] = {}
        for name, (low, high) in self.intervals.items():
            if low != high:
                raise ValueError("marginal is defined only for singleton states")
            marginal[low] = marginal.get(low, Fraction(0)) + self.probabilities[
                name
            ]
        return marginal


def solve_nonanticipative_policy(
    tree: FiniteScenarioTree,
    battery: BidirectionalBatteryGeometry,
    contract: StochasticContract,
    step: Fraction = Fraction(1),
) -> PolicySolution:
    """Maximize feasible leaf probability over node-adapted policies."""

    _validate_tree_model(tree, battery, contract)

    @lru_cache(maxsize=None)
    def solve_node(
        node_name: str, start_energy: Fraction
    ) -> Tuple[Fraction, Tuple[Tuple[str, NodeReserveAction], ...]]:
        node = tree.node(node_name)
        point = contract.by_node[node_name]
        best_probability = Fraction(0)
        best_items: Tuple[Tuple[str, NodeReserveAction], ...] = tuple()

        for next_energy, action in _node_transitions(
            battery, node.pv_available, point, start_energy, step
        ):
            children = tree.children(node_name)
            if not children:
                probability = Fraction(1)
                items = ((node_name, action),)
            else:
                probability = Fraction(0)
                merged: Dict[str, NodeReserveAction] = {node_name: action}
                for child in children:
                    child_probability, child_items = solve_node(
                        child.name, next_energy
                    )
                    probability += (
                        child.conditional_probability * child_probability
                    )
                    merged.update(dict(child_items))
                items = tuple(merged.items())
            if probability > best_probability:
                best_probability = probability
                best_items = items

        return best_probability, best_items

    probability, items = solve_node(
        tree.root.name, battery.initial_energy
    )
    return PolicySolution(
        maximum_success_probability=probability,
        policy=StochasticPolicy(dict(items)),
    )


def full_information_success_probability(
    tree: FiniteScenarioTree,
    battery: BidirectionalBatteryGeometry,
    contract: StochasticContract,
    step: Fraction = Fraction(1),
) -> Fraction:
    """Leaf-wise anticipative benchmark that drops nonanticipativity."""

    _validate_tree_model(tree, battery, contract)
    success = Fraction(0)
    for leaf_name in tree.leaf_names:
        energies = {battery.initial_energy}
        for node in tree.path_to(leaf_name):
            next_energies = set()
            for energy in energies:
                for next_energy, _ in _node_transitions(
                    battery,
                    node.pv_available,
                    contract.by_node[node.name],
                    energy,
                    step,
                ):
                    next_energies.add(next_energy)
            energies = next_energies
            if not energies:
                break
        if energies:
            success += tree.path_probability(leaf_name)
    return success


def replay_stochastic_policy(
    tree: FiniteScenarioTree,
    battery: BidirectionalBatteryGeometry,
    contract: StochasticContract,
    policy: StochasticPolicy,
) -> StochasticReplayResult:
    """Independently replay one nonanticipative policy over the whole tree."""

    _validate_tree_model(tree, battery, contract)
    starts: Dict[str, Fraction] = {}
    ends: Dict[str, Fraction] = {}
    feasible: Dict[str, bool] = {}

    for node in sorted(tree.nodes, key=lambda item: item.period):
        if node.parent is None:
            start = battery.initial_energy
            ancestors_feasible = True
        else:
            ancestors_feasible = feasible.get(node.parent, False)
            start = ends.get(node.parent, battery.initial_energy)
        starts[node.name] = start
        action = policy.by_node.get(node.name)
        if not ancestors_feasible or action is None:
            feasible[node.name] = False
            ends[node.name] = start
            continue
        transition = _replay_node_transition(
            battery,
            node.pv_available,
            contract.by_node[node.name],
            start,
            action,
        )
        if transition is None:
            feasible[node.name] = False
            ends[node.name] = start
        else:
            feasible[node.name] = True
            ends[node.name] = transition

    leaf_feasible = {
        name: feasible.get(name, False) for name in tree.leaf_names
    }
    probability = sum(
        tree.path_probability(name)
        for name, is_feasible in leaf_feasible.items()
        if is_feasible
    )
    return StochasticReplayResult(
        node_start_energy=starts,
        node_realized_end_energy=ends,
        node_feasible=feasible,
        leaf_feasible=leaf_feasible,
        success_probability=probability,
    )


def continuation_success_probability(
    battery: BidirectionalBatteryGeometry,
    state: NodeConditionedSOC,
    future_pv: Mapping[str, Fraction],
    upward_reserve: Fraction,
) -> Fraction:
    """Evaluate one immediate upward call from singleton node states."""

    reserve = Fraction(upward_reserve)
    if set(future_pv) != set(state.intervals):
        raise ValueError("future PV mapping must match state nodes")
    success = Fraction(0)
    for name, (low, high) in state.intervals.items():
        if low != high:
            raise ValueError("counterexample evaluator requires singleton SOC")
        energy = low
        w_t = Fraction(future_pv[name])
        power_low = max(-battery.charge_power_max, reserve - w_t)
        power_high = min(battery.discharge_power_max, reserve)
        if power_low > power_high:
            continue
        end_low = (
            energy
            - energy_depletion(battery, power_high)
            * battery.reserve_duration_hours
        )
        end_high = (
            energy
            - energy_depletion(battery, power_low)
            * battery.reserve_duration_hours
        )
        if not (
            end_high < battery.energy_min
            or end_low > battery.energy_max
        ):
            success += state.probabilities[name]
    return success


def _node_transitions(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    point: StochasticContractPoint,
    start_energy: Fraction,
    step: Fraction,
) -> Iterable[Tuple[Fraction, NodeReserveAction]]:
    actions = tuple(_period_actions(battery, pv_available, step))
    base_options = tuple(
        action
        for action in actions
        if action.hybrid_injection == point.scheduled_injection
    )
    up_options = tuple(
        action
        for action in actions
        if action.hybrid_injection
        == point.scheduled_injection + point.upward_reserve
    )
    down_options = tuple(
        action
        for action in actions
        if action.hybrid_injection
        == point.scheduled_injection - point.downward_reserve
    )

    for base in base_options:
        base_rate = _soc_rate(battery, base)
        pre = (
            start_energy
            + base_rate
            * (battery.interval_hours - battery.reserve_duration_hours)
        )
        base_end = (
            start_energy + base_rate * battery.interval_hours
        )
        if not (_inside(battery, pre) and _inside(battery, base_end)):
            continue
        actual_up = (base,) if point.upward_reserve == 0 else up_options
        actual_down = (
            (base,) if point.downward_reserve == 0 else down_options
        )
        for up in actual_up:
            if not _source_allowed(base, up, point.upward_source):
                continue
            up_end = (
                pre + _soc_rate(battery, up) * battery.reserve_duration_hours
            )
            if not _inside(battery, up_end):
                continue
            for down in actual_down:
                if not _source_allowed(
                    base, down, point.downward_source
                ):
                    continue
                down_end = (
                    pre
                    + _soc_rate(battery, down)
                    * battery.reserve_duration_hours
                )
                if not _inside(battery, down_end):
                    continue
                if point.activation is Activation.UP:
                    realized = up_end
                elif point.activation is Activation.DOWN:
                    realized = down_end
                else:
                    realized = base_end
                yield realized, NodeReserveAction(base, up, down)


def _replay_node_transition(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    point: StochasticContractPoint,
    start_energy: Fraction,
    action: NodeReserveAction,
) -> Fraction | None:
    for internal in (action.base, action.upward, action.downward):
        if not _action_valid(battery, pv_available, internal):
            return None
    if not (
        action.base.hybrid_injection == point.scheduled_injection
        and action.upward.hybrid_injection
        == point.scheduled_injection + point.upward_reserve
        and action.downward.hybrid_injection
        == point.scheduled_injection - point.downward_reserve
    ):
        return None
    if not _source_allowed(
        action.base, action.upward, point.upward_source
    ):
        return None
    if not _source_allowed(
        action.base, action.downward, point.downward_source
    ):
        return None

    base_rate = _soc_rate(battery, action.base)
    pre = (
        start_energy
        + base_rate
        * (battery.interval_hours - battery.reserve_duration_hours)
    )
    base_end = start_energy + base_rate * battery.interval_hours
    up_end = (
        pre
        + _soc_rate(battery, action.upward)
        * battery.reserve_duration_hours
    )
    down_end = (
        pre
        + _soc_rate(battery, action.downward)
        * battery.reserve_duration_hours
    )
    if not all(
        _inside(battery, value)
        for value in (pre, base_end, up_end, down_end)
    ):
        return None
    if point.activation is Activation.UP:
        return up_end
    if point.activation is Activation.DOWN:
        return down_end
    return base_end


def _period_actions(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    step: Fraction,
) -> Iterable[HybridAction]:
    if step <= 0:
        raise ValueError("step must be positive")
    pv_count, pv_remainder = divmod(pv_available, step)
    charge_count, charge_remainder = divmod(
        battery.charge_power_max, step
    )
    discharge_count, discharge_remainder = divmod(
        battery.discharge_power_max, step
    )
    if pv_remainder or charge_remainder or discharge_remainder:
        raise ValueError("grid step must divide PV and power limits")
    for g_index, p_index in product(
        range(int(pv_count) + 1),
        range(-int(charge_count), int(discharge_count) + 1),
    ):
        p_t = p_index * step
        yield HybridAction(
            g_index * step,
            max(Fraction(0), -p_t),
            max(Fraction(0), p_t),
        )


def _soc_rate(
    battery: BidirectionalBatteryGeometry, action: HybridAction
) -> Fraction:
    return (
        battery.charge_efficiency * action.charge_power
        - action.discharge_power / battery.discharge_efficiency
    )


def _inside(
    battery: BidirectionalBatteryGeometry, energy: Fraction
) -> bool:
    return battery.energy_min <= energy <= battery.energy_max


def _action_valid(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    action: HybridAction,
) -> bool:
    return (
        0 <= action.pv_delivered <= pv_available
        and 0 <= action.charge_power <= battery.charge_power_max
        and 0 <= action.discharge_power <= battery.discharge_power_max
        and not (
            action.charge_power > 0 and action.discharge_power > 0
        )
    )


def _source_allowed(
    base: HybridAction,
    branch: HybridAction,
    policy: ReserveSourcePolicy,
) -> bool:
    if policy is ReserveSourcePolicy.ANY:
        return True
    if policy is ReserveSourcePolicy.PV_ONLY:
        return (
            branch.charge_power == base.charge_power
            and branch.discharge_power == base.discharge_power
        )
    if policy is ReserveSourcePolicy.BATTERY_ONLY:
        return branch.pv_delivered == base.pv_delivered
    raise ValueError(f"unknown source policy: {policy}")


def _validate_tree_model(
    tree: FiniteScenarioTree,
    battery: BidirectionalBatteryGeometry,
    contract: StochasticContract,
) -> None:
    contract.validate(tree)
    if battery.horizon != tree.horizon:
        raise ValueError("battery horizon must equal tree horizon")
