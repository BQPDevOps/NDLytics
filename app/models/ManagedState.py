from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class StateChangeEvent:
    key: str
    old_value: Any
    new_value: Any
    state_name: str


class ManagedState:
    def __init__(self, state_name: str):
        self.state_name = state_name
        self._state: Dict[str, Any] = {}
        self._listeners: Dict[str, list[Callable]] = defaultdict(list)
        self._validators: Dict[str, list[Callable]] = defaultdict(list)
        self._connected_states: Dict[str, "ManagedState"] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state with an optional default."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the state with validation and notification."""
        # Run validators
        for validator in self._validators[key]:
            if not validator(value):
                raise ValueError(f"Invalid value for {key}: {value}")

        old_value = self._state.get(key)
        self._state[key] = value

        # Notify listeners
        event = StateChangeEvent(key, old_value, value, self.state_name)
        self._notify_listeners(event)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values at once."""
        for key, value in updates.items():
            self.set(key, value)

    def add_listener(
        self, key: str, callback: Callable[[StateChangeEvent], None]
    ) -> None:
        """Add a listener for state changes on a specific key."""
        self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback: Callable) -> None:
        """Remove a listener for a specific key."""
        if key in self._listeners:
            self._listeners[key].remove(callback)

    def add_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """Add a validator function for a specific key."""
        self._validators[key].append(validator)

    def _notify_listeners(self, event: StateChangeEvent) -> None:
        """Notify all listeners of a state change."""
        for listener in self._listeners[event.key]:
            listener(event)

    def clear(self) -> None:
        """Clear all state values."""
        self._state.clear()

    def keys(self) -> list[str]:
        """Get all keys in the state."""
        return list(self._state.keys())

    def values(self) -> list[Any]:
        """Get all values in the state."""
        return list(self._state.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs in the state."""
        return list(self._state.items())

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator to check if key exists in state."""
        return key in self._state

    def __len__(self) -> int:
        """Return the number of items in the state."""
        return len(self._state)

    def connect_external_state(
        self, external_state: "ManagedState", connection_name: Optional[str] = None
    ) -> None:
        """
        Connect an external ManagedState instance and mirror its changes.

        Args:
            external_state: Another ManagedState instance to connect to
            connection_name: Optional name for the connection. Defaults to external state's name
        """
        # Use the provided connection name or the external state's name
        state_name = connection_name or external_state.state_name

        # Store the connected state
        self._connected_states[state_name] = external_state

        # Create a property to access the connected state
        setattr(
            self.__class__,
            state_name,
            property(lambda self: self._connected_states.get(state_name)),
        )

        # Create a listener that mirrors all state changes
        def mirror_state_changes(event: StateChangeEvent) -> None:
            # Create a namespaced key to avoid conflicts
            namespaced_key = f"{state_name}.{event.key}"
            # Mirror the change in our state
            self._state[namespaced_key] = event.new_value
            # Notify our own listeners
            mirror_event = StateChangeEvent(
                key=namespaced_key,
                old_value=event.old_value,
                new_value=event.new_value,
                state_name=self.state_name,
            )
            self._notify_listeners(mirror_event)

        # Add listener for all existing keys in the external state
        for key in external_state.keys():
            external_state.add_listener(key, mirror_state_changes)
            # Initialize our state with the current values
            namespaced_key = f"{state_name}.{key}"
            self._state[namespaced_key] = external_state.get(key)

    def disconnect_external_state(self, state_name: str) -> None:
        """
        Disconnect a previously connected external state.

        Args:
            state_name: The name of the connected state to disconnect
        """
        if state_name in self._connected_states:
            # Remove the property
            delattr(self.__class__, state_name)
            # Remove the connected state
            del self._connected_states[state_name]
            # Remove all namespaced keys from our state
            keys_to_remove = [
                key for key in self._state.keys() if key.startswith(f"{state_name}.")
            ]
            for key in keys_to_remove:
                del self._state[key]
