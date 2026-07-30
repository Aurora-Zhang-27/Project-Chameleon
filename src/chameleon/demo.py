"""Run the manually verifiable two-period counterexample."""

from __future__ import annotations

from .contracts import ContractKind
from .model import BatterySpec, DispatchCase, solve_dispatch
from .replay import replay_base_and_single_calls


def main() -> None:
    battery = BatterySpec(
        horizon=2,
        initial_energy_mwh=1.0,
        power_max_mw=1.0,
    )
    case = DispatchCase(
        battery=battery,
        load_mw=(1.0, 0.0),
        reserve_requirement_mw=(0.0, 1.0),
    )

    for contract in (
        ContractKind.C0_EXACT_MARGINAL,
        ContractKind.C1_PREFIX,
        ContractKind.C_FULL_DET,
    ):
        result = solve_dispatch(case, contract)
        replay = replay_base_and_single_calls(
            battery,
            result.hybrid_energy_mw,
            result.hybrid_reserve_mw,
        )
        print(contract.value)
        print(f"  objective: {result.objective:.2f}")
        print(f"  hybrid energy: {result.hybrid_energy_mw}")
        print(f"  hybrid reserve: {result.hybrid_reserve_mw}")
        print(f"  replay SOC end: {replay.soc_base_end_mwh}")
        print(f"  reserve shortfall: {replay.reserve_shortfall_mw}")


if __name__ == "__main__":
    main()

