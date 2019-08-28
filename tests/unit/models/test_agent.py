import builtins
import json
import random
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal
import pytest

from ttt.models.agent import Agent, CPUAgent, HumanAgent, State


def deterministic_test(seed):
    """Function wrapper to set a fixed seed.
    Arguments
    ---------
    seed: int

    Returns
    -------
        func: callable
            A function wrapping the input function.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            np.random.seed(np.array(seed, dtype=np.int64))
            random.seed(seed)
            output = func(*args, **kwargs)
            return output

        return wrapper

    return decorator


def test_agent_correct_initialization():
    agent = Agent()

    assert agent.current_state is None
    assert agent.grid is None


def test_agent_updates_grid_correctly():
    agent = Agent()
    new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
    agent.update_grid(new_grid)

    assert_array_equal(new_grid, agent.grid)
    assert_array_equal(new_grid, agent.current_state.grid)

    assert_array_equal(agent.current_state.next_states_values, np.array([0, 0]))
    assert_array_equal(agent.current_state.next_states_transitions, np.array([7, 8]))


def test_cpuagent_correct_initialization():
    agent = CPUAgent()

    assert agent.current_state is None
    assert agent.grid is None
    assert not agent.states


def test_cpuagent_updates_grid_correctly():
    agent = CPUAgent()
    new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
    agent.update_grid(new_grid)

    assert_array_equal(new_grid, agent.grid)
    assert_array_equal(new_grid, agent.current_state.grid)

    assert_array_equal(agent.current_state.next_states_values, np.array([0, 0]))
    assert_array_equal(agent.current_state.next_states_transitions, np.array([7, 8]))

    assert len(agent.states) == 1

    new_state = agent.states[0]
    assert_array_equal(new_grid, new_state.grid)
    assert_array_equal(new_state.next_states_values, np.array([0, 0]))
    assert_array_equal(new_state.next_states_transitions, np.array([7, 8]))


@deterministic_test(500)
def test_cpuagent_generates_random_moves():
    agent = CPUAgent()
    new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
    agent.update_grid(new_grid)

    generated_moves = set()
    for _ in range(10):
        generated_moves.add(agent.get_random_move())

    assert len(generated_moves) == 2
    assert 7 in generated_moves
    assert 8 in generated_moves


def test_cpuagent_generates_best_move_correctly():
    agent = CPUAgent()
    new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
    agent.update_grid(new_grid)

    agent.current_state.next_states_values = np.array([-1, 1])

    generated_moves = set()
    for _ in range(10):
        generated_moves.add(agent.get_best_move())

    assert len(generated_moves) == 1
    assert 7 not in generated_moves
    assert 8 in generated_moves


def test_cpuagent_serializes_correctly():
    agent = CPUAgent()
    agent.states = {
        0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])),
        1: State(np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0])),
    }

    serialized_agent = agent.serialize()

    assert 'states' in serialized_agent
    assert len(serialized_agent["states"]) == 2

    assert_array_equal(serialized_agent["states"]["0"]["grid"], np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    assert_array_equal(serialized_agent["states"]["1"]["grid"], np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0]))

    assert_array_equal(serialized_agent["states"]["0"]["next_states_values"], np.array([0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0]))
    assert_array_equal(serialized_agent["states"]["1"]["next_states_values"], np.array([0]))

    assert_array_equal(serialized_agent["states"]["0"]["next_states_transitions"],
                       np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))
    assert_array_equal(serialized_agent["states"]["1"]["next_states_transitions"], np.array([9]))


def test_cpuagent_deserializes_correctly():
    serialized_agent = {
        'states': {
            '0': {
                'grid': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'next_states_values': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'next_states_transitions': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            },
            '1': {
                'grid': [1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                'next_states_values': [0.0],
                'next_states_transitions': [9]
            }
        }
    }

    agent = CPUAgent()
    agent.deserialize(serialized_agent)

    assert_array_equal(agent.states[0].grid, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    assert_array_equal(agent.states[1].grid, np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0]))

    assert_array_equal(agent.states[0].next_states_values, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    assert_array_equal(agent.states[1].next_states_values, np.array([0]))

    assert_array_equal(agent.states[0].next_states_transitions, np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))
    assert_array_equal(agent.states[1].next_states_transitions, np.array([9]))


def test_cpuagent_saves_correctly(tmpdir):
    root = Path(tmpdir)
    weights_path = root / "agent.json"

    CPUAgent().save(weights_path)

    assert weights_path.exists()
    serialized_agent = json.loads(weights_path.read_text())

    assert "states" in serialized_agent
    assert not serialized_agent["states"]


def test_cpuagent_loads_correctly(tmpdir):
    root = Path(tmpdir)
    weights_path = root / "agent.json"

    agent = CPUAgent()
    weights_path.write_text('{"states": {}}')
    agent.load(weights_path)

    assert not agent.states


@pytest.mark.parametrize("states, grid, expected_results", [
    ({}, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), False),
    ({0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))}, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), True),
    ({0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))}, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]), False),
])
def test_cpuagent_has_state_correctness(states, grid, expected_results):
    agent = CPUAgent()
    agent.states = states

    assert agent.has_state(State(grid)) == expected_results


@pytest.mark.parametrize("states, grid, expected_results", [
    ({}, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 1),
    ({0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))}, np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]), 2)
])
def test_cpuagent_add_state_correctness(states, grid, expected_results):
    agent = CPUAgent()
    agent.states = states
    agent.add_state(State(grid))

    assert len(agent.states) == expected_results
    assert_array_equal(agent.states[len(agent.states) - 1].grid, grid)


def test_cpuagent_get_state_correctness():
    agent =CPUAgent()
    agent.states = {
        0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])),
        1: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])),
    }

    result = agent.get_state(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])).grid
    assert_array_equal(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), result)


def test_cpuagent_get_state_raises_value_error_if_state_not_found():
    agent = CPUAgent()

    with pytest.raises(ValueError, match="could not be found in saved states"):
        agent.get_state(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))


def test_cpuagent_update_state_correctness():
    agent = CPUAgent()
    agent.states = {
        0: State(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])),
        1: State(np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0])),
    }

    new_state = State(np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0]))
    new_state.next_states_values *= 2

    agent.update_state(new_state)

    assert_array_equal(agent.states[1].next_states_values, new_state.next_states_values)


def test_humanagent_correct_initialization():
    agent = HumanAgent()

    assert agent.current_state is None
    assert agent.grid is None


def test_humanagent_updates_grid_correctly():
    agent = HumanAgent()
    new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
    agent.update_grid(new_grid)

    assert_array_equal(new_grid, agent.grid)
    assert_array_equal(new_grid, agent.current_state.grid)

    assert_array_equal(agent.current_state.next_states_values, np.array([0, 0]))
    assert_array_equal(agent.current_state.next_states_transitions, np.array([7, 8]))


def test_humanagent_generates_move_correctly(mocker):
    agent = HumanAgent()

    with mocker.patch('builtins.input', return_value=8):
        new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
        agent.update_grid(new_grid)
        assert agent.get_next_move() == 7


def test_humanagent_loops_till_correct_move_correctly(mocker):
    agent = HumanAgent()

    with mocker.patch('builtins.input', side_effect=[0, 1, 2, 3, 4, 5, 6, 7, 8]):
        new_grid = np.array([1, 2, 1, 2, 1, 2, 1, 0, 0])
        agent.update_grid(new_grid)
        assert agent.get_next_move() == 7
        assert builtins.input.call_count == 9
