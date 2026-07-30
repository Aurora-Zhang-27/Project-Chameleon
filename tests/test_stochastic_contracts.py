from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import product

from chameleon.charging import BidirectionalBatteryGeometry
from chameleon.sequential import Activation, ReserveSourcePolicy
from chameleon.stochastic import (
    FiniteScenarioTree,
    NodeConditionedSOC,
    ScenarioNode,
    StochasticContract,
    StochasticContractPoint,
    continuation_success_probability,
    full_information_success_probability,
    replay_stochastic_policy,
    solve_nonanticipative_policy,
)


def _two_leaf_tree(horizon: int) -> FiniteScenarioTree:
    nodes = [
        ScenarioNode("root", 0, None, Fraction(1), Fraction(1)),
        ScenarioNode("left", 1, "root", Fraction(1, 2), Fraction(0)),
        ScenarioNode("right", 1, "root", Fraction(1, 2), Fraction(0)),
    ]
    left_parent = "left"
    right_parent = "right"
    for period in range(2, horizon):
        left_name = f"left_{period}"
        right_name = f"right_{period}"
        nodes.extend(
            (
                ScenarioNode(
                    left_name,
                    period,
                    left_parent,
                    Fraction(1),
                    Fraction(0),
                ),
                ScenarioNode(
                    right_name,
                    period,
                    right_parent,
                    Fraction(1),
                    Fraction(0),
                ),
            )
        )
        left_parent = left_name
        right_parent = right_name
    return FiniteScenarioTree(tuple(nodes))


def _battery(horizon: int) -> BidirectionalBatteryGeometry:
    return BidirectionalBatteryGeometry(
        horizon=horizon,
        initial_energy=Fraction(1),
        energy_min=Fraction(0),
        energy_max=Fraction(1),
        charge_power_max=Fraction(1),
        discharge_power_max=Fraction(1),
    )


def _branch_contract(
    tree: FiniteScenarioTree,
    left_activation: Activation,
    right_activation: Activation,
    *,
    root_source: ReserveSourcePolicy = ReserveSourcePolicy.ANY,
) -> StochasticContract:
    points = {
        "root": StochasticContractPoint(
            0,
            upward_reserve=1,
            activation=Activation.UP,
            upward_source=root_source,
        ),
        "left": StochasticContractPoint(
            0,
            upward_reserve=1
            if left_activation is Activation.UP
            else 0,
            downward_reserve=1
            if left_activation is Activation.DOWN
            else 0,
            activation=left_activation,
        ),
        "right": StochasticContractPoint(
            0,
            upward_reserve=1
            if right_activation is Activation.UP
            else 0,
            downward_reserve=1
            if right_activation is Activation.DOWN
            else 0,
            activation=right_activation,
        ),
    }
    for node in tree.nodes:
        points.setdefault(node.name, StochasticContractPoint(0))
    return StochasticContract(points)


class StochasticInformationCounterexampleTests(unittest.TestCase):
    def test_unconditional_interval_and_soc_belief_lose_node_correlation(
        self,
    ) -> None:
        battery = _battery(3)
        probabilities = {
            "cloudy_next": Fraction(1, 2),
            "sunny_next": Fraction(1, 2),
        }
        aligned = NodeConditionedSOC(
            intervals={
                "cloudy_next": (Fraction(1), Fraction(1)),
                "sunny_next": (Fraction(0), Fraction(0)),
            },
            probabilities=probabilities,
        )
        swapped = NodeConditionedSOC(
            intervals={
                "cloudy_next": (Fraction(0), Fraction(0)),
                "sunny_next": (Fraction(1), Fraction(1)),
            },
            probabilities=probabilities,
        )
        future_pv = {
            "cloudy_next": Fraction(0),
            "sunny_next": Fraction(1),
        }

        self.assertEqual(
            aligned.unconditional_hull, swapped.unconditional_hull
        )
        self.assertEqual(
            aligned.singleton_marginal, swapped.singleton_marginal
        )
        self.assertEqual(
            continuation_success_probability(
                battery, aligned, future_pv, Fraction(1)
            ),
            Fraction(1),
        )
        self.assertEqual(
            continuation_success_probability(
                battery, swapped, future_pv, Fraction(1)
            ),
            Fraction(1, 2),
        )

    def test_full_information_is_strictly_optimistic_without_nonanticipativity(
        self,
    ) -> None:
        tree = _two_leaf_tree(3)
        battery = _battery(3)
        contract = _branch_contract(
            tree, Activation.DOWN, Activation.UP
        )

        nonanticipative = solve_nonanticipative_policy(
            tree, battery, contract
        )
        anticipative = full_information_success_probability(
            tree, battery, contract
        )
        replay = replay_stochastic_policy(
            tree, battery, contract, nonanticipative.policy
        )

        self.assertEqual(
            nonanticipative.maximum_success_probability, Fraction(1, 2)
        )
        self.assertEqual(anticipative, Fraction(1))
        self.assertEqual(replay.success_probability, Fraction(1, 2))
        self.assertFalse(nonanticipative.robust_feasible)
        self.assertTrue(nonanticipative.chance_feasible(Fraction(1, 2)))
        self.assertFalse(nonanticipative.chance_feasible(Fraction(1, 4)))
        self.assertTrue(nonanticipative.existential_recourse_feasible)


class ScenarioTreeEnumerationTests(unittest.TestCase):
    def test_robust_chance_and_full_information_for_three_to_four_periods(
        self,
    ) -> None:
        for horizon in (3, 4):
            tree = _two_leaf_tree(horizon)
            battery = _battery(horizon)
            robust_count = 0
            chance_count = 0
            anticipative_count = 0

            for left, right in product(
                (Activation.UP, Activation.DOWN), repeat=2
            ):
                contract = _branch_contract(tree, left, right)
                solution = solve_nonanticipative_policy(
                    tree, battery, contract
                )
                full_info = full_information_success_probability(
                    tree, battery, contract
                )
                replay = replay_stochastic_policy(
                    tree, battery, contract, solution.policy
                )
                self.assertEqual(
                    replay.success_probability,
                    solution.maximum_success_probability,
                )
                if solution.robust_feasible:
                    robust_count += 1
                if solution.chance_feasible(Fraction(1, 2)):
                    chance_count += 1
                if full_info == 1:
                    anticipative_count += 1

            with self.subTest(horizon=horizon):
                self.assertEqual(robust_count, 2)
                self.assertEqual(chance_count, 4)
                self.assertEqual(anticipative_count, 4)

    def test_source_label_selects_the_surviving_scenario(self) -> None:
        tree = _two_leaf_tree(3)
        battery = _battery(3)
        pv_first = _branch_contract(
            tree,
            Activation.DOWN,
            Activation.UP,
            root_source=ReserveSourcePolicy.PV_ONLY,
        )
        battery_first = _branch_contract(
            tree,
            Activation.DOWN,
            Activation.UP,
            root_source=ReserveSourcePolicy.BATTERY_ONLY,
        )
        pv_solution = solve_nonanticipative_policy(
            tree, battery, pv_first
        )
        battery_solution = solve_nonanticipative_policy(
            tree, battery, battery_first
        )
        pv_replay = replay_stochastic_policy(
            tree, battery, pv_first, pv_solution.policy
        )
        battery_replay = replay_stochastic_policy(
            tree, battery, battery_first, battery_solution.policy
        )

        self.assertEqual(pv_solution.maximum_success_probability, Fraction(1, 2))
        self.assertEqual(
            battery_solution.maximum_success_probability, Fraction(1, 2)
        )
        self.assertFalse(pv_replay.leaf_feasible["left_2"])
        self.assertTrue(pv_replay.leaf_feasible["right_2"])
        self.assertTrue(battery_replay.leaf_feasible["left_2"])
        self.assertFalse(battery_replay.leaf_feasible["right_2"])


if __name__ == "__main__":
    unittest.main()
