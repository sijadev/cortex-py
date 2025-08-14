from pathlib import Path
import pytest

from cortex_neo.tests.graph_test_utils import get_driver, reset_graph, load_yaml, apply_initial, run_actions, snapshot_graph, compare_graph

PROFILES_DIR = Path(__file__).parent / "profiles"


def discover_profiles():
    return sorted([p for p in PROFILES_DIR.glob("*.yaml")])


@pytest.mark.parametrize("profile_path", discover_profiles())
def test_profile(profile_path):
    # Load profile
    profile = load_yaml(str(profile_path))
    initial = profile.get("initial", {})
    actions = profile.get("actions", [])
    expected = profile.get("expected", {})

    # Execute profile
    driver = get_driver()
    with driver.session() as session:
        reset_graph(session)
        apply_initial(session, initial)
        run_actions(session, actions)
        actual = snapshot_graph(session)

    ok, diff = compare_graph(actual, expected)
    assert ok, f"Profile failed: {profile_path.name}\n{diff}\nActual={actual}\nExpected={expected}"
