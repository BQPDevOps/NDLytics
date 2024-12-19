"""
Usage Examples:

1. Basic State Management:
    state_manager = StateManager("component_name")
    [count, set_count] = state_manager.use_state(0)
    print(count())  # Output: 0
    set_count(5)
    print(count())  # Output: 5

2. Function State:
    def calculate_total(x, y):
        return x + y

    [calculator, set_calculator] = state_manager.use_state(calculate_total)
    result = calculator(5, 3)  # Output: 8

    # Update function
    def new_calculator(x, y):
        return x * y
    set_calculator(new_calculator)
    result = calculator(5, 3)  # Output: 15

3. Object State:
    [user, set_user] = state_manager.use_state({"name": "John", "age": 30})
    print(user())  # Output: {"name": "John", "age": 30}
    set_user({"name": "Jane", "age": 25})

4. Multiple States:
    [name, set_name] = state_manager.use_state("John")
    [age, set_age] = state_manager.use_state(30)
    print(f"{name()} is {age()} years old")  # Output: John is 30 years old
"""

from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Generic, Union
from dataclasses import dataclass
from collections import defaultdict

T = TypeVar("T")


@dataclass
class StateChangeEvent:
    key: str
    old_value: Any
    new_value: Any
    state_name: str


class StateContainer(Generic[T]):
    def __init__(self, value: T, state_manager: "StateManager", key: str):
        self._value = value
        self._state_manager = state_manager
        self._key = key

    def __call__(self, *args, **kwargs):
        if callable(self._value):
            return self._value(*args, **kwargs)
        return self._value

    def __repr__(self):
        return repr(self._value)

    def get(self) -> T:
        return self._value


class StateManager:
    def __init__(self, state_name: str):
        self.state_name = state_name
        self._state: Dict[str, Any] = {}
        self._listeners: Dict[str, list[Callable]] = defaultdict(list)
        self._validators: Dict[str, list[Callable]] = defaultdict(list)
        self._state_counter = 0

    def use_state(
        self, initial_value: T
    ) -> Tuple[StateContainer[T], Callable[[T], None]]:
        key = f"state_{self._state_counter}"
        self._state_counter += 1

        if key not in self._state:
            self._state[key] = initial_value

        def setter(new_value: T) -> None:
            old_value = self._state[key]
            self._state[key] = new_value
            event = StateChangeEvent(key, old_value, new_value, self.state_name)
            self._notify_listeners(event)

        return StateContainer(self._state[key], self, key), setter

    def _notify_listeners(self, event: StateChangeEvent) -> None:
        for listener in self._listeners[event.key]:
            listener(event)

    def add_listener(
        self, key: str, callback: Callable[[StateChangeEvent], None]
    ) -> None:
        self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback: Callable) -> None:
        if key in self._listeners:
            self._listeners[key].remove(callback)

    def clear(self) -> None:
        self._state.clear()
        self._state_counter = 0
