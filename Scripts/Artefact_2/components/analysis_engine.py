"""
Enhanced analysis engine for the AVEDAS Root Cause Analysis system.
This module provides a cleaner and more maintainable implementation of the analysis functionality.
"""

import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any

from components.graph_builder import GraphBuilder
from components.parallel_matrix import ParallelMatrixCalculator
from config.constants import (
    CarrierTypes, MatrixConstants, ProcessingConstants, StringPatterns
)


class AnalysisEngine:
    """
    Main analysis engine that coordinates graph building and matrix computations.
    """
    
    def __init__(self, max_processes: Optional[int] = None):
        """
        Initialize the analysis engine.
        
        Args:
            max_processes: Maximum number of processes for parallel computations
        """
        self.graph_builder = GraphBuilder()
        self.matrix_calculator = ParallelMatrixCalculator(max_processes)
        
        # Current state
        self.current_graph = None
        self.current_matrices = {}
        self.current_metadata = {}
    
    def initialize_from_aml(self, aml_file_path: str) -> None:
        """
        Initialize the analysis engine with an AML file.
        
        Args:
            aml_file_path: Path to the AML file
        """
        print("Initializing analysis engine from AML...")
        self.current_graph = self.graph_builder.build_graph_from_aml(aml_file_path)
        print(f"Graph initialized with {self.current_graph.vcount()} vertices and {self.current_graph.ecount()} edges")
    
    def update_system_state(self, valve_states: Dict[str, float], 
                          alarm_states: Dict[str, int],
                          deviations: Dict[str, float]) -> None:
        """
        Update the system state with new valve positions, alarms, and deviations.
        
        Args:
            valve_states: Dictionary of valve names to their states
            alarm_states: Dictionary of sensor names to their alarm states
            deviations: Dictionary of sensor names to their deviation values
        """
        if self.current_graph is None:
            raise RuntimeError("Analysis engine not initialized. Call initialize_from_aml first.")
        
        # Update valve states
        self._update_valve_states(valve_states)
        
        # Update alarm states
        self._update_alarm_states(alarm_states)
        
        # Update deviations
        self._update_deviations(deviations)
    
    def compute_influence_matrices(self, use_parallel: bool = True) -> Dict[str, np.ndarray]:
        """
        Compute all influence matrices.
        
        Args:
            use_parallel: Whether to use parallel computation
            
        Returns:
            Dictionary containing all computed matrices
        """
        if self.current_graph is None:
            raise RuntimeError("Analysis engine not initialized.")
        
        print("Computing influence matrices...")
        t0 = time.time()
        
        # Get vertex lists
        active_alarms = self._get_active_alarm_vertices()
        possible_alarms = self._get_possible_alarm_vertices()
        parameters = self._get_parameter_vertices()
        
        print(f"Found {len(active_alarms)} active alarms, {len(possible_alarms)} possible alarms, {len(parameters)} parameters")
        
        matrices = {}
        
        if use_parallel:
            # Parallel computation
            matrices['statevariable'] = self.matrix_calculator.compute_statevariable_matrix_parallel(
                self.current_graph, possible_alarms
            )
            
            matrices['parameter'], matrices['parameter_pathlength'] = (
                self.matrix_calculator.compute_parameter_matrix_parallel(
                    self.current_graph, parameters, possible_alarms
                )
            )
            
            if len(active_alarms) > 0:
                matrices['distance'] = self.matrix_calculator.compute_distance_matrix_parallel(
                    self.current_graph, active_alarms
                )
        else:
            # Sequential computation
            matrices['statevariable'] = self._compute_statevariable_matrix_sequential(possible_alarms)
            matrices['parameter'], matrices['parameter_pathlength'] = (
                self._compute_parameter_matrix_sequential(parameters, possible_alarms)
            )
            
            if len(active_alarms) > 0:
                matrices['distance'] = self._compute_distance_matrix_sequential(active_alarms)
        
        # Post-process parameter matrix
        matrices['parameter'] = self._postprocess_parameter_matrix(
            matrices['parameter'], matrices['parameter_pathlength'], possible_alarms
        )
        
        # Compute combined matrix
        matrices['combined'] = self._compute_combined_matrix(
            matrices['parameter'], matrices['statevariable']
        )
        
        # Store matrices and metadata
        self.current_matrices = matrices
        self.current_metadata = {
            'active_alarms': active_alarms,
            'possible_alarms': possible_alarms,
            'parameters': parameters,
            'computation_time': time.time() - t0
        }
        
        print(f"Matrix computation completed in {self.current_metadata['computation_time']:.2f} seconds")
        return matrices
    
    def get_parameter_ranking(self, top_n: int = ProcessingConstants.TOP_PARAMETERS_COUNT) -> List[Tuple[str, float]]:
        """
        Get ranked list of parameters by influence.
        
        Args:
            top_n: Number of top parameters to return
            
        Returns:
            List of (parameter_name, influence_score) tuples
        """
        if 'combined' not in self.current_matrices:
            raise RuntimeError("Matrices not computed. Call compute_influence_matrices first.")
        
        matrix = self.current_matrices['combined']
        parameters = self.current_metadata['parameters']
        
        # Calculate row sums (total influence per parameter)
        row_sums = np.sum(matrix, axis=1)
        
        # Get parameter names and influences
        param_influences = []
        for i, param_vertex in enumerate(parameters):
            param_influences.append((param_vertex['Tag'], row_sums[i]))
        
        # Sort by absolute influence (descending)
        param_influences.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return param_influences[:top_n]
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current analysis.
        
        Returns:
            Dictionary containing analysis summary
        """
        if not self.current_metadata:
            return {"status": "No analysis performed"}
        
        ranking = self.get_parameter_ranking()
        
        return {
            "status": "Analysis complete",
            "graph_statistics": {
                "vertices": self.current_graph.vcount(),
                "edges": self.current_graph.ecount()
            },
            "matrix_statistics": {
                "active_alarms": len(self.current_metadata['active_alarms']),
                "possible_alarms": len(self.current_metadata['possible_alarms']),
                "parameters": len(self.current_metadata['parameters'])
            },
            "computation_time": self.current_metadata['computation_time'],
            "top_parameters": ranking[:10],
            "matrix_shapes": {
                name: matrix.shape for name, matrix in self.current_matrices.items()
                if isinstance(matrix, np.ndarray)
            }
        }
    
    def _update_valve_states(self, valve_states: Dict[str, float]) -> None:
        """Update valve states in the graph."""
        valve_manager = self.graph_builder.get_valve_manager()
        
        # Convert valve names to expected format
        processed_states = {}
        for valve_name, state in valve_states.items():
            # Remove _State suffix if present
            clean_name = valve_name.replace(StringPatterns.STATE_SUFFIX, "")
            processed_states[clean_name] = state / 100.0 if state > 1 else state
        
        valve_manager.update_valve_states(processed_states)
        valve_manager.apply_all_weights(self.current_graph)
    
    def _update_alarm_states(self, alarm_states: Dict[str, int]) -> None:
        """Update alarm states in the graph."""
        for sensor_name, alarm_state in alarm_states.items():
            # Convert sensor name format
            processed_name = sensor_name.replace(*StringPatterns.V_TO_YIC).replace(*StringPatterns.UNDERSCORE_TO_MEASUREMENT)
            
            try:
                vertex_idx = self.current_graph.vs["Tag"].index(processed_name)
                self.current_graph.vs[vertex_idx]["AS"] = alarm_state
                self.current_graph.vs[vertex_idx]["sensorlabel"] = 1
            except ValueError:
                # Sensor not found in graph
                continue
    
    def _update_deviations(self, deviations: Dict[str, float]) -> None:
        """Update deviation values in the graph."""
        for sensor_name, deviation in deviations.items():
            # Convert sensor name format
            processed_name = sensor_name.replace(*StringPatterns.V_TO_YIC).replace(*StringPatterns.UNDERSCORE_TO_MEASUREMENT)
            
            try:
                vertex_idx = self.current_graph.vs["Tag"].index(processed_name)
                self.current_graph.vs[vertex_idx]["deviation"] = deviation
            except ValueError:
                # Sensor not found in graph
                continue
    
    def _get_active_alarm_vertices(self) -> List:
        """Get vertices with active alarms (AS != 0)."""
        return [v for v in self.current_graph.vs if v["AS"] != 0]
    
    def _get_possible_alarm_vertices(self) -> List:
        """Get vertices that can have alarms (sensorlabel != 0)."""
        return [v for v in self.current_graph.vs if v["sensorlabel"] != 0]
    
    def _get_parameter_vertices(self) -> List:
        """Get parameter vertices (parameterlabel != 0)."""
        return [v for v in self.current_graph.vs if v["parameterlabel"] != 0]
    
    def _compute_statevariable_matrix_sequential(self, possible_alarms: List) -> np.ndarray:
        """Compute state variable matrix sequentially."""
        n = len(possible_alarms)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    if possible_alarms[i]["AS"] != 0 and possible_alarms[j]["AS"] != 0:
                        # Implement sequential Dijkstra here
                        pass  # Placeholder
                else:
                    matrix[i, j] = MatrixConstants.DIAGONAL_VALUE_STATEVARIABLE
        
        return matrix
    
    def _compute_parameter_matrix_sequential(self, parameters: List, possible_alarms: List) -> Tuple[np.ndarray, np.ndarray]:
        """Compute parameter matrix sequentially."""
        param_matrix = np.zeros((len(parameters), len(possible_alarms)))
        path_matrix = np.zeros((len(parameters), len(possible_alarms)))
        
        # Placeholder for sequential implementation
        return param_matrix, path_matrix
    
    def _compute_distance_matrix_sequential(self, active_alarms: List) -> np.ndarray:
        """Compute distance matrix sequentially."""
        n = len(active_alarms)
        matrix = np.zeros((n, n))
        
        # Placeholder for sequential implementation
        return matrix
    
    def _postprocess_parameter_matrix(self, param_matrix: np.ndarray, 
                                    path_matrix: np.ndarray, 
                                    possible_alarms: List) -> np.ndarray:
        """
        Post-process the parameter matrix with scaling factors.
        
        Args:
            param_matrix: Raw parameter influence matrix
            path_matrix: Path length matrix
            possible_alarms: List of possible alarm vertices
            
        Returns:
            Post-processed parameter matrix
        """
        if param_matrix.size == 0:
            return param_matrix
        
        # Calculate factor influence for each column
        factor_influence = np.sum(np.abs(param_matrix), axis=0)
        factor_influence[factor_influence <= 1] = 1
        
        # Calculate range factor for each parameter
        range_factors = np.mean(path_matrix, axis=1) if path_matrix.size > 0 else np.ones(param_matrix.shape[0])
        
        # Apply post-processing
        for j in range(param_matrix.shape[1]):
            if j < len(possible_alarms):
                deviation = abs(possible_alarms[j].get("deviation", 0))
                
                for i in range(param_matrix.shape[0]):
                    value = param_matrix[i, j]
                    
                    # Apply scaling factors
                    value *= deviation
                    value *= np.power(MatrixConstants.RANGE_INFLUENCE_POWER, range_factors[i])
                    value /= factor_influence[j]
                    
                    param_matrix[i, j] = value
        
        return param_matrix
    
    def _compute_combined_matrix(self, param_matrix: np.ndarray, 
                               state_matrix: np.ndarray) -> np.ndarray:
        """
        Compute the combined influence matrix.
        
        Args:
            param_matrix: Parameter influence matrix
            state_matrix: State variable influence matrix
            
        Returns:
            Combined influence matrix
        """
        if param_matrix.size == 0 or state_matrix.size == 0:
            return param_matrix
        
        combined_matrix = np.zeros_like(param_matrix)
        
        # Calculate ratios for each column
        for j in range(state_matrix.shape[1]):
            sum_col = np.sum(state_matrix[:, j])
            sum_row = np.sum(state_matrix[j, :]) if j < state_matrix.shape[0] else 0
            
            if sum_col < MatrixConstants.MIN_FACTOR_INFLUENCE:
                sum_col = MatrixConstants.MIN_FACTOR_INFLUENCE
            
            ratio = sum_row / sum_col
            
            if j < param_matrix.shape[1]:
                combined_matrix[:, j] = param_matrix[:, j] * (ratio + 1)
        
        return combined_matrix
    
    def export_matrices(self, file_prefix: str) -> None:
        """
        Export computed matrices to files.
        
        Args:
            file_prefix: Prefix for output files
        """
        if not self.current_matrices:
            raise RuntimeError("No matrices to export")
        
        for name, matrix in self.current_matrices.items():
            if isinstance(matrix, np.ndarray):
                np.savetxt(f"{file_prefix}_{name}_matrix.csv", matrix, delimiter=",")
                print(f"Exported {name} matrix to {file_prefix}_{name}_matrix.csv")
    
    def get_graph(self):
        """Get the current graph."""
        return self.current_graph
    
    def get_matrices(self) -> Dict[str, np.ndarray]:
        """Get the current matrices."""
        return self.current_matrices
