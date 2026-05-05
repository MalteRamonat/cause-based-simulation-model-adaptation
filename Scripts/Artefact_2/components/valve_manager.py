"""
Enhanced valve management for the AVEDAS system.
This module provides a cleaner implementation of valve functionality.
"""

import numpy as np
from typing import Dict, List
from config.constants import CarrierTypes, ValveConstants


class EnhancedValve:
    """
    Enhanced valve implementation with better structure and maintainability.
    """
    
    def __init__(self, tag: str, history_length: int = ValveConstants.DEFAULT_HISTORY_LENGTH):
        """
        Initialize valve with given tag and history length.
        
        Args:
            tag: Unique identifier for the valve
            history_length: Number of historical states to maintain
        """
        self.tag = tag
        self.history_length = history_length
        self.state_history = [ValveConstants.DEFAULT_VALVE_STATE] * history_length
        
        # Initialize relation dictionaries for different carrier types
        self.relations = {
            CarrierTypes.TEMPERATURE: [],
            CarrierTypes.PRESSURE: [],
            CarrierTypes.FLOW: [],
            CarrierTypes.LEVEL: []
        }
        
        # Initialize kernel dictionaries for temporal weighting
        self.temporal_kernels = {
            carrier: self._create_history_kernel(1, 1, 1, 1) 
            for carrier in self.relations.keys()
        }
        
        # Initialize value kernels for state scaling
        self.value_kernels = {
            carrier: self._create_history_kernel(0.01, 0.99, 1, 2)
            for carrier in self.relations.keys()
        }
    
    def _create_history_kernel(self, start_value: float, stop_value: float, 
                              ramp_start: int, ramp_length: int) -> List[float]:
        """
        Create a kernel vector for temporal weighting.
        
        Args:
            start_value: Initial value of the kernel
            stop_value: Final value of the kernel
            ramp_start: Index where the ramp begins
            ramp_length: Length of the ramp
            
        Returns:
            List of kernel values
        """
        kernel = (
            [start_value] * ramp_start +
            list(np.round(np.linspace(start_value, stop_value, ramp_length), 2)) +
            [stop_value] * max(0, self.history_length - ramp_start - ramp_length)
        )
        return kernel[:self.history_length]
    
    def find_related_edges(self, graph) -> None:
        """
        Find edges related to this valve in the graph.
        
        Args:
            graph: The igraph Graph object
        """
        try:
            valve_index = graph.vs["Tag"].index(self.tag)
            child_indices = graph.successors(valve_index)
            
            for carrier_type in self.relations.keys():
                self.relations[carrier_type].clear()
                
                for child in child_indices:
                    # Check outgoing edges from child
                    for edge in graph.es.select(_source=child):
                        if edge["carrier"] == carrier_type:
                            self.relations[carrier_type].append(edge.index)
                    
                    # Check incoming edges to child
                    for edge in graph.es.select(_target=child):
                        if edge["carrier"] == carrier_type:
                            self.relations[carrier_type].append(edge.index)
                            
        except ValueError:
            # Valve not found in graph
            pass
    
    def apply_weights_to_graph(self, graph) -> None:
        """
        Apply valve state-based weights to related edges in the graph.
        
        Args:
            graph: The igraph Graph object
        """
        for carrier in self.relations:
            current_weight = self._calculate_edge_weight(carrier)
            
            # Apply weight to all related edges
            for edge_index in self.relations[carrier]:
                graph.es[edge_index]["weight"] = current_weight
                graph.es[edge_index]["Actors"] = self.tag
    
    def _calculate_edge_weight(self, carrier: str) -> float:
        """
        Calculate the edge weight for a specific carrier type.
        
        Args:
            carrier: The carrier type
            
        Returns:
            Calculated weight value
        """
        # Scale state history to value kernel indices
        value_history = []
        for hist_val in self.state_history:
            scaled_val = int(np.round(hist_val * self.history_length))
            
            if scaled_val <= 0:
                hist_index = 0
            elif scaled_val <= 0.5:
                max_idx = len(self.value_kernels[carrier]) - 1
                hist_index = int(np.round(scaled_val / 0.5 * max_idx))
            else:
                hist_index = len(self.value_kernels[carrier]) - 1
            
            value_history.append(self.value_kernels[carrier][hist_index])
        
        # Calculate weighted average
        numerator = np.sum(np.array(value_history) * np.array(self.temporal_kernels[carrier]))
        denominator = np.sum(self.temporal_kernels[carrier]) or 1.0
        
        return round(numerator / denominator, 2)
    
    def update_state(self, new_state: float) -> None:
        """
        Update the valve state history with a new state value.
        
        Args:
            new_state: New valve state value
        """
        self.state_history.append(new_state)
        self.state_history.pop(0)
    
    def get_current_state(self) -> float:
        """Get the current (most recent) valve state."""
        return self.state_history[-1]
    
    def reset_state_history(self, initial_state: float = ValveConstants.DEFAULT_VALVE_STATE) -> None:
        """
        Reset the state history to initial values.
        
        Args:
            initial_state: State to initialize the history with
        """
        self.state_history = [initial_state] * self.history_length


class ValveManager:
    """
    Manages multiple valves in the system.
    """
    
    def __init__(self):
        """Initialize the valve manager."""
        self.valves: Dict[str, EnhancedValve] = {}
    
    def create_valve(self, tag: str, history_length: int = ValveConstants.DEFAULT_HISTORY_LENGTH) -> EnhancedValve:
        """
        Create a new valve and add it to the manager.
        
        Args:
            tag: Unique tag for the valve
            history_length: History length for the valve
            
        Returns:
            The created valve
        """
        valve = EnhancedValve(tag, history_length)
        self.valves[tag] = valve
        return valve
    
    def get_valve(self, tag: str) -> EnhancedValve:
        """
        Get a valve by its tag.
        
        Args:
            tag: Tag of the valve to retrieve
            
        Returns:
            The valve object
            
        Raises:
            KeyError: If valve is not found
        """
        return self.valves[tag]
    
    def update_valve_states(self, state_dict: Dict[str, float]) -> None:
        """
        Update multiple valve states at once.
        
        Args:
            state_dict: Dictionary mapping valve tags to new state values
        """
        for tag, state in state_dict.items():
            if tag in self.valves:
                self.valves[tag].update_state(state)
    
    def initialize_valves_from_graph(self, graph) -> None:
        """
        Initialize valves based on State nodes found in the graph.
        
        Args:
            graph: The igraph Graph object
        """
        for vertex in graph.vs:
            if vertex['Carrier'] == CarrierTypes.STATE:
                valve_tag = vertex['Tag'].replace(ValveConstants.VALVE_STATE_SUFFIX, "")
                
                if valve_tag not in self.valves:
                    self.create_valve(valve_tag)
    
    def find_all_relations(self, graph) -> None:
        """
        Find relations for all valves in the graph.
        
        Args:
            graph: The igraph Graph object
        """
        for valve in self.valves.values():
            valve.find_related_edges(graph)
    
    def apply_all_weights(self, graph) -> None:
        """
        Apply weights for all valves to the graph.
        
        Args:
            graph: The igraph Graph object
        """
        for valve in self.valves.values():
            valve.apply_weights_to_graph(graph)
    
    def get_valve_count(self) -> int:
        """Get the number of managed valves."""
        return len(self.valves)
    
    def get_valve_tags(self) -> List[str]:
        """Get a list of all valve tags."""
        return list(self.valves.keys())
    
    def clear_all_valves(self) -> None:
        """Remove all valves from the manager."""
        self.valves.clear()
