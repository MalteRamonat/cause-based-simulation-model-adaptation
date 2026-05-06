"""
Parallel matrix computation module for the AVEDAS system.
This module provides multiprocessing capabilities for matrix calculations.
"""

import numpy as np
import multiprocessing as mp
from multiprocessing import Pool
import pickle
import time
from typing import List, Tuple, Optional
import heapq

from config.constants import MultiprocessingConstants, ProcessingConstants


def dijkstra_worker(args: Tuple) -> Tuple[int, List[float]]:
    """
    Worker function for parallel Dijkstra computations.
    
    Args:
        args: Tuple containing (row_index, vertex_list, graph_pickle, computation_type)
        
    Returns:
        Tuple of (row_index, computed_row)
    """
    row_index, vertex_list, graph_pickle, computation_type = args
    
    try:
        # Deserialize the graph
        graph = pickle.loads(graph_pickle)
    except Exception as e:
        print(f"Error deserializing graph: {e}")
        return row_index, [0] * len(vertex_list)
    
    row = []
    
    if computation_type == "distance":
        row = _compute_distance_row(graph, row_index, vertex_list)
    elif computation_type == "statevariable":
        row = _compute_statevariable_row(graph, row_index, vertex_list)
    else:
        row = [0] * len(vertex_list)
    
    return row_index, row


def parameter_dijkstra_worker(args: Tuple) -> Tuple[int, List[float], List[int], int]:
    """
    Worker function for parameter influence matrix computations.

    Args:
        args: Tuple containing (param_index, parameter_list, sensor_list, graph_pickle)

    Returns:
        Tuple of (param_index, computed_row, path_lengths, neutral_count)
    """
    param_index, parameter_list, sensor_list, graph_pickle = args

    try:
        graph = pickle.loads(graph_pickle)
    except Exception as e:
        print(f"Error deserializing graph: {e}")
        return param_index, [0] * len(sensor_list), [1] * len(sensor_list), 0

    row = []
    path_lengths = []
    neutral_count = 0

    for j in range(len(sensor_list)):
        if sensor_list[j]["AS"] is not None:
            try:
                distance, path = _modified_dijkstra_parameter(
                    graph,
                    parameter_list[param_index].index,
                    sensor_list[j].index
                )

                path_lengths.append(len(path) if len(path) > 0 else 1)

                if distance == -np.inf:
                    neutral_count += 1
                    row.append(0)
                elif distance > 0:
                    row.append(np.exp(-distance))
                else:
                    row.append(-np.exp(distance))

            except Exception as e:
                print(f"Error in parameter Dijkstra ({param_index}, {j}): {e}")
                row.append(0)
                path_lengths.append(1)
        else:
            row.append(0)
            path_lengths.append(1)

    return param_index, row, path_lengths, neutral_count


def _compute_distance_row(graph, row_index: int, vertex_list: List) -> List[float]:
    """Compute a row for the distance matrix."""
    row = []
    
    for j in range(len(vertex_list)):
        if row_index != j:
            try:
                distance = _modified_dijkstra_variable(
                    graph,
                    vertex_list[row_index].index,
                    vertex_list[j].index
                )
                row.append(np.exp(-distance))
            except Exception:
                row.append(0)
        else:
            row.append(0)  # Diagonal
    
    return row


def _compute_statevariable_row(graph, row_index: int, vertex_list: List) -> List[float]:
    """Compute a row for the state variable influence matrix."""
    row = []
    
    for j in range(len(vertex_list)):
        if row_index != j:
            if vertex_list[row_index]["AS"] != 0 and vertex_list[j]["AS"] != 0:
                try:
                    distance = _modified_dijkstra_variable(
                        graph,
                        vertex_list[row_index].index,
                        vertex_list[j].index
                    )
                    if distance == -np.inf:
                        row.append(0)
                    elif distance > 0:
                        row.append(np.exp(-distance))
                    else:
                        row.append(0)
                except Exception:
                    row.append(0)
            else:
                row.append(0)
        else:
            row.append(1)  # Diagonal for state variable matrix
    
    return row


def _modified_dijkstra_variable(graph, source_id: int, target_id: int) -> float:
    """Modified Dijkstra for variable computations."""
    return _modified_dijkstra_core(graph, source_id, target_id, "Variable")[0]


def _modified_dijkstra_parameter(graph, source_id: int, target_id: int) -> Tuple[float, List[int]]:
    """Modified Dijkstra for parameter computations."""
    return _modified_dijkstra_core(graph, source_id, target_id, "parameter")


def _modified_dijkstra_core(graph, source_id: int, target_id: int, dijkstra_type: str) -> Tuple[float, List[int]]:
    """
    Core implementation of modified Dijkstra algorithm.
    
    Args:
        graph: The graph to search
        source_id: Source vertex ID
        target_id: Target vertex ID
        dijkstra_type: Type of computation ("Variable" or "parameter")
        
    Returns:
        Tuple of (distance, path)
    """
    def has_duplicate_pattern(path):
        """Check for duplicate patterns in path to avoid cycles."""
        for i in range(len(path) - 3):
            if path[i:i+2] == path[i+2:i+4] or path[i] == path[i+2]:
                return True
        return False
    
    # Determine source vertex value
    if dijkstra_type == "parameter":
        source_vertex_value = graph.vs[source_id]["parameterlabel"]
    else:
        source_vertex_value = graph.vs[source_id]['AS']
    
    target_vertex_value = graph.vs[target_id]['AS']
    
    # Initialize distance arrays
    positive_dist = [np.inf] * len(graph.vs)
    negative_dist = [np.inf] * len(graph.vs)
    positive_path = [[] for _ in range(len(graph.vs))]
    negative_path = [[] for _ in range(len(graph.vs))]
    
    # Set initial distances
    if source_vertex_value > 0:
        positive_dist[source_id] = 0
    elif source_vertex_value < 0:
        negative_dist[source_id] = 0
    
    # Priority queue: (distance, vertex, sign, path)
    queue = [(0, source_id, source_vertex_value, [source_id])]
    
    while queue:
        d, v, sign, path_so_far = heapq.heappop(queue)
        
        # Explore successors
        for u in graph.successors(v):
            edge_id = graph.get_eid(v, u)
            edge_weight = graph.es[edge_id]['weight']
            edge_lambda = graph.es[edge_id].get("lambda_factor")
            
            # Skip invalid edges
            if (edge_weight <= ProcessingConstants.MIN_EDGE_WEIGHT or 
                edge_lambda is None or 
                len(path_so_far) > ProcessingConstants.MAX_PATH_LENGTH):
                continue
            
            # Log transformation
            edge_weight = -np.log(edge_weight)
            new_sign = sign * edge_lambda
            new_path = path_so_far + [u]
            
            # Avoid cycles
            if has_duplicate_pattern(new_path):
                continue
            
            # Update distances
            new_dist = d + edge_weight
            
            if new_sign >= 0 and new_dist < positive_dist[u]:
                positive_dist[u] = new_dist
                positive_path[u] = new_path
                heapq.heappush(queue, (new_dist, u, 1, new_path))
            
            if new_sign <= 0 and new_dist < negative_dist[u]:
                negative_dist[u] = new_dist
                negative_path[u] = new_path
                heapq.heappush(queue, (new_dist, u, -1, new_path))
    
    # Determine final distance and path
    path = []
    distance = np.inf
    
    if target_vertex_value > 0:
        if (positive_dist[target_id] >= negative_dist[target_id] and 
            negative_dist[target_id] < np.inf):
            distance = positive_dist[target_id]
            path = positive_path[target_id]
        else:
            distance = -negative_dist[target_id]
            path = negative_path[target_id]
    
    elif target_vertex_value < 0:
        if (positive_dist[target_id] > negative_dist[target_id] and 
            positive_dist[target_id] < np.inf):
            distance = -positive_dist[target_id]
            path = positive_path[target_id]
        else:
            distance = negative_dist[target_id]
            path = negative_path[target_id]
    
    else:  # target_vertex_value == 0
        if (positive_dist[target_id] < np.inf or negative_dist[target_id] < np.inf):
            # Choose shortest path
            if (not negative_path[target_id] and positive_path[target_id]):
                path = positive_path[target_id]
            elif (negative_path[target_id] and not positive_path[target_id]):
                path = negative_path[target_id]
            elif (negative_path[target_id] and positive_path[target_id]):
                path = (negative_path[target_id] if len(negative_path[target_id]) <= len(positive_path[target_id])
                       else positive_path[target_id])
            
            distance = -np.inf if len(path) > 0 else np.inf
        else:
            distance = np.inf
    
    return distance, path if path else []


class ParallelMatrixCalculator:
    """
    Handles parallel matrix calculations for the AVEDAS system.
    """
    
    def __init__(self, max_processes: Optional[int] = None):
        """
        Initialize the parallel calculator.
        
        Args:
            max_processes: Maximum number of processes to use
        """
        self.max_processes = max_processes or min(
            mp.cpu_count(), 
            MultiprocessingConstants.DEFAULT_MAX_PROCESSES
        )
    
    def compute_distance_matrix_parallel(self, graph, active_alarm_list: List) -> np.ndarray:
        """
        Compute distance matrix in parallel.
        
        Args:
            graph: The graph object
            active_alarm_list: List of active alarm vertices
            
        Returns:
            Computed distance matrix
        """
        if len(active_alarm_list) == 0:
            return np.array([])
        
        print(f"Computing distance matrix with {self.max_processes} processes...")
        
        # Serialize graph
        graph_pickle = pickle.dumps(graph)
        
        # Prepare arguments
        args_list = [
            (i, active_alarm_list, graph_pickle, "distance")
            for i in range(len(active_alarm_list))
        ]
        
        t0 = time.time()
        
        # Parallel computation
        with Pool(processes=self.max_processes) as pool:
            results = pool.map(dijkstra_worker, args_list)
        
        t1 = time.time()
        print(f"Parallel distance matrix computation: {t1-t0:.2f} seconds")
        
        # Assemble matrix
        distance_matrix = np.zeros((len(active_alarm_list), len(active_alarm_list)))
        for row_index, row_data in results:
            if row_data:
                distance_matrix[row_index] = row_data
        
        return distance_matrix
    
    def compute_statevariable_matrix_parallel(self, graph, possible_alarm_list: List) -> np.ndarray:
        """
        Compute state variable influence matrix in parallel.
        
        Args:
            graph: The graph object
            possible_alarm_list: List of possible alarm vertices
            
        Returns:
            Computed state variable matrix
        """
        if len(possible_alarm_list) == 0:
            return np.array([])
        
        print(f"Computing state variable matrix with {self.max_processes} processes...")
        
        # Serialize graph
        graph_pickle = pickle.dumps(graph)
        
        # Prepare arguments
        args_list = [
            (i, possible_alarm_list, graph_pickle, "statevariable")
            for i in range(len(possible_alarm_list))
        ]
        
        t0 = time.time()
        
        # Parallel computation
        with Pool(processes=self.max_processes) as pool:
            results = pool.map(dijkstra_worker, args_list)
        
        t1 = time.time()
        print(f"Parallel state variable matrix computation: {t1-t0:.2f} seconds")
        
        # Assemble matrix
        matrix = np.zeros((len(possible_alarm_list), len(possible_alarm_list)))
        for row_index, row_data in results:
            if row_data:
                matrix[row_index] = row_data
        
        return matrix
    
    def compute_parameter_matrix_parallel(self, graph, parameter_list: List,
                                        possible_alarm_list: List) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        Compute parameter influence matrix in parallel.

        Args:
            graph: The graph object
            parameter_list: List of parameter vertices
            possible_alarm_list: List of possible alarm vertices

        Returns:
            Tuple of (parameter_matrix, path_length_matrix, neutral_counts)
        """
        if len(parameter_list) == 0 or len(possible_alarm_list) == 0:
            return np.array([]), np.array([]), []

        print(f"Computing parameter matrix with {self.max_processes} processes...")

        # Serialize graph
        graph_pickle = pickle.dumps(graph)

        # Prepare arguments
        args_list = [
            (i, parameter_list, possible_alarm_list, graph_pickle)
            for i in range(len(parameter_list))
        ]

        t0 = time.time()

        # Parallel computation
        with Pool(processes=self.max_processes) as pool:
            results = pool.map(parameter_dijkstra_worker, args_list)

        t1 = time.time()
        print(f"Parallel parameter matrix computation: {t1-t0:.2f} seconds")

        # Assemble matrices
        parameter_matrix = np.zeros((len(parameter_list), len(possible_alarm_list)))
        path_length_matrix = np.zeros((len(parameter_list), len(possible_alarm_list)))
        neutral_counts = [0] * len(parameter_list)

        for param_index, row_data, path_lengths, neutral_count in results:
            if row_data and path_lengths:
                parameter_matrix[param_index] = row_data
                path_length_matrix[param_index] = path_lengths
                neutral_counts[param_index] = neutral_count

        return parameter_matrix, path_length_matrix, neutral_counts
    
    def compute_timestep_batch_parallel(self, timestep_data_list: List, 
                                       graph_builder_func, compute_func) -> List:
        """
        Compute multiple timesteps in parallel.
        
        Args:
            timestep_data_list: List of timestep data
            graph_builder_func: Function to build graph for each timestep
            compute_func: Function to compute results for each timestep
            
        Returns:
            List of computation results
        """
        print(f"Computing {len(timestep_data_list)} timesteps with {self.max_processes} processes...")
        
        # Prepare arguments for each timestep
        args_list = [
            (i, data, graph_builder_func, compute_func)
            for i, data in enumerate(timestep_data_list)
        ]
        
        t0 = time.time()
        
        # Parallel computation
        with Pool(processes=self.max_processes) as pool:
            results = pool.map(self._timestep_worker, args_list)
        
        t1 = time.time()
        print(f"Parallel timestep computation: {t1-t0:.2f} seconds")
        
        return results
    
    def _timestep_worker(self, args: Tuple) -> Tuple[int, any]:
        """
        Worker function for timestep computations.
        
        Args:
            args: Tuple containing (timestep_index, data, graph_builder_func, compute_func)
            
        Returns:
            Tuple of (timestep_index, result)
        """
        timestep_index, data, graph_builder_func, compute_func = args
        
        try:
            # Build graph for this timestep
            graph = graph_builder_func(data)
            
            # Compute result
            result = compute_func(graph, data)
            
            return timestep_index, result
        
        except Exception as e:
            print(f"Error in timestep {timestep_index}: {e}")
            return timestep_index, None
