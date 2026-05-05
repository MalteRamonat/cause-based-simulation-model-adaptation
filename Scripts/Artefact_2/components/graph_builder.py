"""
Graph construction and management module for the AVEDAS system.
This module handles AML parsing and graph creation in a modular way.
"""

import igraph as ig
from xml.etree import ElementTree as ET
import re
from typing import Dict, List, Tuple, Optional

from config.constants import (
    CarrierTypes, EdgeTypes, AMLTags, InterfaceSuffixes, 
    NodeColors, ValveConstants
)
from config.rules import RuleSetManager, GraphRule
from components.valve_manager import ValveManager


class GraphBuilder:
    """
    Handles the construction of graphs from AML files.
    """
    
    def __init__(self):
        """Initialize the graph builder."""
        self.graph = ig.Graph(directed=True)
        self.valve_manager = ValveManager()
        self.rule_manager = RuleSetManager()
        
        # Node types that should be recognized
        self.node_types = [
            CarrierTypes.TEMPERATURE, CarrierTypes.PRESSURE, CarrierTypes.FLOW, 
            CarrierTypes.LEVEL, CarrierTypes.POWER, CarrierTypes.MEASUREMENT_POWER,
            CarrierTypes.MEASUREMENT_TEMPERATURE, CarrierTypes.MEASUREMENT_PRESSURE,
            CarrierTypes.MEASUREMENT_FLOW, CarrierTypes.MEASUREMENT_LEVEL, 
            CarrierTypes.STATE, CarrierTypes.MEASUREMENT_STATE, CarrierTypes.HEIGHT,
            CarrierTypes.ROTATIONAL_SPEED, CarrierTypes.PUMP_VOLUME, CarrierTypes.AREA,
            CarrierTypes.LENGTH, CarrierTypes.DIAMETER, CarrierTypes.ROUGHNESS,
            CarrierTypes.HDIFF, CarrierTypes.PDROP_NOM, CarrierTypes.MF_NOMINAL,
            CarrierTypes.CLOGGING, CarrierTypes.HLOSS, CarrierTypes.PRIMARY_CA,
            CarrierTypes.PRIMARY_HTRANSFER, CarrierTypes.SECONDARY_CSURFACE,
            CarrierTypes.SECONDARY_HEATT, CarrierTypes.ALPHA
        ]
        
        # Parameter types for labeling
        self.parameter_types = {
            CarrierTypes.HEIGHT, CarrierTypes.ROTATIONAL_SPEED, CarrierTypes.PUMP_VOLUME,
            CarrierTypes.AREA, CarrierTypes.LENGTH, CarrierTypes.DIAMETER,
            CarrierTypes.ROUGHNESS, CarrierTypes.HDIFF, CarrierTypes.PDROP_NOM,
            CarrierTypes.MF_NOMINAL, CarrierTypes.CLOGGING, CarrierTypes.PRIMARY_CA,
            CarrierTypes.PRIMARY_HTRANSFER, CarrierTypes.SECONDARY_CSURFACE,
            CarrierTypes.SECONDARY_HEATT, CarrierTypes.ALPHA
        }
    
    def build_graph_from_aml(self, aml_file_path: str) -> ig.Graph:
        """
        Build a complete graph from an AML file.
        
        Args:
            aml_file_path: Path to the AML file
            
        Returns:
            The constructed graph
        """
        # Parse AML file
        tree = ET.parse(aml_file_path)
        root = tree.getroot()
        
        # Extract structure information
        parent_map, attribute_map, elements_id, interface_map = self._parse_aml_structure(root)
        
        # Build hierarchy
        self._build_hierarchy_nodes(parent_map, elements_id)
        
        # Add attribute nodes (parameters)
        self._build_attribute_nodes(attribute_map, elements_id)
        
        # Create connections based on interfaces
        self._build_interface_connections(root, interface_map)
        
        # Adjust edge hierarchies
        self._adjust_edge_hierarchies()
        
        # Find paths for rule application
        vertex_paths = self._find_vertex_paths()
        alarm_paths = self._find_alarm_paths()
        
        # Apply rules to create the functional graph
        self._apply_all_rules(alarm_paths)
        
        # Initialize valve management
        self._initialize_valve_system()
        
        print(f"Graph created successfully with {self.graph.vcount()} vertices and {self.graph.ecount()} edges")
        return self.graph
    
    def _parse_aml_structure(self, root) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Parse the AML structure to extract hierarchy and interface information.
        
        Args:
            root: Root element of the AML XML
            
        Returns:
            Tuple of (parent_map, attribute_map, elements_id, interface_map)
        """
        parent_map = {}
        attribute_map = {}
        elements_id = {}
        interface_map = {}
        
        def process_element(parent):
            for child in parent:
                try:
                    if child.tag == AMLTags.INTERNAL_ELEMENT:
                        elements_id[child.attrib['Name']] = child.attrib['ID']
                        if parent.attrib['Name'] != child.attrib['Name']:
                            parent_map[child.attrib['Name']] = parent.attrib['Name']
                            process_element(child)
                    
                    elif child.tag == AMLTags.ATTRIBUTE:
                        if (child.attrib['Name'] in self.node_types or 
                            "Concentration" in child.attrib['Name']):
                            temp_str = parent.attrib['Name'] + '_' + child.attrib['Name']
                            attribute_map[temp_str] = True
                    
                    elif child.tag == AMLTags.EXTERNAL_INTERFACE:
                        if parent.attrib['Name'] not in interface_map:
                            interface_map[parent.attrib['Name']] = {}
                        interface_map[parent.attrib['Name']][child.attrib['ID']] = child.attrib['Name']
                
                except Exception as e:
                    print(f"Error processing element: {e}")
        
        # Process all internal elements
        for elem in root.iter(AMLTags.INTERNAL_ELEMENT):
            process_element(elem)
        
        return parent_map, attribute_map, elements_id, interface_map
    
    def _build_hierarchy_nodes(self, parent_map: Dict, elements_id: Dict) -> None:
        """
        Build hierarchy nodes based on parent-child relationships.
        
        Args:
            parent_map: Mapping of child to parent relationships
            elements_id: Mapping of element names to IDs
        """
        for child_name, parent_name in parent_map.items():
            # Add child node
            self._add_vertex(child_name, CarrierTypes.HIERARCH, elements_id[child_name])
            
            # Add parent node if not exists and not "Plant"
            if child_name != 'Plant' and parent_name in elements_id:
                if not self._vertex_exists(parent_name):
                    self._add_vertex(parent_name, CarrierTypes.HIERARCH, elements_id[parent_name])
                
                # Add hierarchy edges
                self._add_hierarchy_edges(child_name, parent_name)
    
    def _build_attribute_nodes(self, attribute_map: Dict, elements_id: Dict) -> None:
        """
        Build attribute nodes (parameters) and connect them to their parents.
        
        Args:
            attribute_map: Mapping of attributes
            elements_id: Mapping of element names to IDs
        """
        node_list_with_prefix = ['_' + node_type for node_type in self.node_types]
        pattern = '|'.join(node_list_with_prefix)
        
        for attr in attribute_map:
            # Extract parent name by removing the attribute suffix
            parent_name = re.sub(pattern, '', attr)
            
            if parent_name in elements_id:
                carrier_string = attr.replace(parent_name + '_', '')
                self._add_vertex(attr, carrier_string, None)
                self._add_hierarchy_edges(attr, parent_name)
    
    def _build_interface_connections(self, root, interface_map: Dict) -> None:
        """
        Build connections based on interface definitions in the AML.
        
        Args:
            root: Root element of the AML XML
            interface_map: Mapping of interfaces
        """
        for connect in root.iter(AMLTags.INTERNAL_LINK):
            partner_a = self._find_partner_name(connect.attrib['RefPartnerSideA'], interface_map)
            partner_b = self._find_partner_name(connect.attrib['RefPartnerSideB'], interface_map)
            
            if partner_a and partner_b:
                self._create_interface_connection(connect, partner_a, partner_b, interface_map)
    
    def _create_interface_connection(self, connect, partner_a: str, partner_b: str, interface_map: Dict) -> None:
        """
        Create a connection between two interface partners.
        
        Args:
            connect: Connection element from AML
            partner_a: First partner name
            partner_b: Second partner name
            interface_map: Interface mapping
        """
        interface_a = interface_map[partner_a][connect.attrib['RefPartnerSideA']]
        interface_b = interface_map[partner_b][connect.attrib['RefPartnerSideB']]
        
        # Handle different interface types
        if InterfaceSuffixes.OUT in interface_a and InterfaceSuffixes.OUT not in interface_b:
            carrier = interface_a.replace(InterfaceSuffixes.OUT, '')
            self._add_edge(partner_a, partner_b, carrier)
        
        elif InterfaceSuffixes.INOUT in interface_a:
            carrier = interface_a.replace(InterfaceSuffixes.INOUT, '')
            if InterfaceSuffixes.INOUT in interface_b:
                # Bidirectional connection
                self._add_edge(partner_a, partner_b, carrier)
                self._add_edge(partner_b, partner_a, carrier)
            elif InterfaceSuffixes.IN in interface_b:
                self._add_edge(partner_a, partner_b, carrier)
        
        elif InterfaceSuffixes.OUT in interface_a and InterfaceSuffixes.OUT in interface_b:
            carrier = interface_a.replace(InterfaceSuffixes.OUT, '')
            self._add_edge(partner_a, partner_b, carrier)
        
        elif InterfaceSuffixes.IN in interface_a and InterfaceSuffixes.OUT in interface_b:
            carrier = interface_a.replace(InterfaceSuffixes.IN, '')
            self._add_edge(partner_b, partner_a, carrier)
    
    def _add_vertex(self, tag: str, carrier_type: str, aml_id: Optional[str] = None,
                   alarm_tag: bool = False, alarm_state: bool = False,
                   alarm_limits: bool = False, deviation: float = 0.0) -> None:
        """
        Add a vertex to the graph with proper attributes.
        
        Args:
            tag: Unique tag for the vertex
            carrier_type: Type of carrier (Temperature, Pressure, etc.)
            aml_id: AML ID if available
            alarm_tag: Whether this is an alarm tag
            alarm_state: Alarm state
            alarm_limits: Alarm limits
            deviation: Deviation value
        """
        # Determine color based on carrier type
        color = self._get_node_color(carrier_type)
        
        # Determine labels
        parameter_label = 1 if carrier_type in self.parameter_types else 0
        sensor_label = 1 if "Measurement" in carrier_type else 0
        
        self.graph.add_vertex(
            Tag=tag,
            Carrier=carrier_type,
            AMLID=aml_id,
            AT=alarm_tag,
            AS=alarm_state,
            AL=alarm_limits,
            color=color,
            aktorinfluence=False,
            parameterlabel=parameter_label,
            sensorlabel=sensor_label,
            deviation=deviation
        )
    
    def _add_edge(self, source_tag: str, target_tag: str, carrier: str, weight: float = 0) -> None:
        """
        Add an edge between two vertices.
        
        Args:
            source_tag: Tag of source vertex
            target_tag: Tag of target vertex
            carrier: Edge carrier type
            weight: Edge weight
        """
        try:
            source_idx = self.graph.vs["Tag"].index(source_tag)
            target_idx = self.graph.vs["Tag"].index(target_tag)
            self.graph.add_edge(source_idx, target_idx, carrier=carrier, weight=weight)
        except ValueError as e:
            print(f"Error adding edge from {source_tag} to {target_tag}: {e}")
    
    def _add_hierarchy_edges(self, child_name: str, parent_name: str) -> None:
        """
        Add hierarchy edges between child and parent.
        
        Args:
            child_name: Name of child vertex
            parent_name: Name of parent vertex
        """
        self._add_edge(child_name, parent_name, EdgeTypes.HAS_PARENT)
        self._add_edge(parent_name, child_name, EdgeTypes.HAS_CHILD)
    
    def _vertex_exists(self, tag: str) -> bool:
        """Check if a vertex with the given tag exists."""
        try:
            self.graph.vs["Tag"].index(tag)
            return True
        except ValueError:
            return False
    
    def _find_partner_name(self, partner_ref: str, interface_map: Dict) -> Optional[str]:
        """Find partner name from interface reference."""
        for name, interfaces in interface_map.items():
            if partner_ref in interfaces:
                return name
        return None
    
    def _get_node_color(self, carrier_type: str) -> str:
        """Get the color for a node based on its carrier type."""
        color_mapping = {
            CarrierTypes.TEMPERATURE: NodeColors.TEMPERATURE,
            CarrierTypes.PRESSURE: NodeColors.PRESSURE,
            CarrierTypes.FLOW: NodeColors.FLOW,
            CarrierTypes.LEVEL: NodeColors.LEVEL,
            CarrierTypes.STATE: NodeColors.STATE,
            CarrierTypes.HIERARCH: NodeColors.HIERARCH,
        }
        return color_mapping.get(carrier_type, NodeColors.DEFAULT)
    
    def _adjust_edge_hierarchies(self) -> None:
        """Adjust edge hierarchies by changing hasparent to hashierarchieparent where needed."""
        for vertex in self.graph.vs:
            edges = self.graph.es.select(_source=vertex.index)
            target_edges = self.graph.es.select(_target=vertex.index)
            
            # Check if Product edges exist
            has_product = any(e['carrier'] == EdgeTypes.PRODUCT for e in edges + target_edges)
            
            if has_product:
                hasparent_edges = [e for e in edges if e['carrier'] == EdgeTypes.HAS_PARENT]
                if hasparent_edges:
                    hasparent_edges[0]['carrier'] = EdgeTypes.HASH_HIERARCHY_PARENT
    
    def _find_vertex_paths(self) -> List[List[int]]:
        """Find vertex paths for rule application."""
        return self._find_paths([EdgeTypes.HAS_PARENT, EdgeTypes.PRODUCT, EdgeTypes.HAS_CHILD], [3, 1, 3])
    
    def _find_alarm_paths(self) -> List[List[int]]:
        """Find alarm paths for sensor connections."""
        return self._find_paths([EdgeTypes.HAS_PARENT, EdgeTypes.HAS_CHILD], [3, 3])
    
    def _find_paths(self, carrier_condition: List[str], carrier_max: List[int]) -> List[List[int]]:
        """
        Find paths in the graph matching specific carrier conditions.
        
        Args:
            carrier_condition: List of required carriers in order
            carrier_max: Maximum usage of each carrier
            
        Returns:
            List of paths (each path is a list of vertex indices)
        """
        all_paths = []
        
        for i in range(len(self.graph.vs)):
            paths = self._explore_edges(i, carrier_condition, carrier_max)
            if paths:
                all_paths.extend(paths)
        
        # Filter out paths where start == end
        return [p for p in all_paths if p and p[0] != p[-1]]
    
    def _explore_edges(self, source_vertex_id: int, carrier_list: List[str], 
                      carrier_max: List[int], used_carriers: Optional[List[str]] = None,
                      vertex_path: Optional[List[int]] = None, carrier_index: int = 0,
                      carrier_count: int = 0) -> List[List[int]]:
        """
        Recursively explore edges to find valid paths.
        
        Args:
            source_vertex_id: Starting vertex ID
            carrier_list: List of carriers to follow
            carrier_max: Maximum count for each carrier
            used_carriers: Already used carriers
            vertex_path: Current vertex path
            carrier_index: Current carrier index
            carrier_count: Current carrier count
            
        Returns:
            List of valid paths
        """
        all_paths = []
        if vertex_path is None:
            vertex_path = []
        if used_carriers is None:
            used_carriers = []
        
        vertex_path.append(source_vertex_id)
        
        # Check if all required carriers have been used
        if set(used_carriers) == set(carrier_list):
            all_paths.append(list(vertex_path))
        
        # Explore outgoing edges
        for edge in self.graph.es.select(_source=source_vertex_id):
            current_carrier = carrier_list[carrier_index] if carrier_index < len(carrier_list) else None
            
            if current_carrier and edge['carrier'] == current_carrier and carrier_count < carrier_max[carrier_index]:
                new_used_carriers = used_carriers.copy()
                new_used_carriers.append(edge['carrier'])
                
                new_paths = self._explore_edges(
                    edge.target, carrier_list, carrier_max,
                    new_used_carriers, vertex_path.copy(),
                    carrier_index, carrier_count + 1
                )
                if new_paths:
                    all_paths.extend(new_paths)
            
            # Allow transition to next carrier
            next_carrier = carrier_list[carrier_index + 1] if carrier_index + 1 < len(carrier_list) else None
            if (carrier_count >= 1 and next_carrier and 
                edge['carrier'] == next_carrier):
                
                new_used_carriers = used_carriers.copy()
                new_used_carriers.append(edge['carrier'])
                
                new_paths = self._explore_edges(
                    edge.target, carrier_list, carrier_max,
                    new_used_carriers, vertex_path.copy(),
                    carrier_index + 1, 1
                )
                if new_paths:
                    all_paths.extend(new_paths)
        
        return all_paths
    
    def _apply_all_rules(self, alarm_paths: List[List[int]]) -> None:
        """
        Apply all rules to create the functional graph.
        
        Args:
            alarm_paths: Paths for alarm rule application
        """
        all_rules = self.rule_manager.get_all_rules()
        
        for rule in all_rules:
            self._apply_single_rule(rule, alarm_paths)
        
        # Create reverse alarm edges
        self._create_reverse_alarm_edges()
    
    def _apply_single_rule(self, rule: GraphRule, alarm_paths: List[List[int]]) -> None:
        """
        Apply a single rule to the graph.
        
        Args:
            rule: The rule to apply
            alarm_paths: Alarm paths for rule application
        """
        searchpath = alarm_paths if rule.shortest else self._find_vertex_paths()
        
        # Find source vertices
        source_vertices = self.graph.vs.select(Carrier_eq=rule.source_type)
        
        for source_vertex in source_vertices:
            valid_paths = [p for p in searchpath if p and p[0] == source_vertex.index]
            
            if rule.shortest and valid_paths:
                valid_paths.sort(key=len)
            
            # Find target vertices
            target_vertices = self.graph.vs.select(Carrier_eq=rule.target_type)
            
            for target_vertex in target_vertices:
                for path in valid_paths:
                    if path and path[-1] == target_vertex.index:
                        self._create_rule_edge(rule, source_vertex, target_vertex, path)
                        if rule.shortest:
                            break
                if rule.shortest:
                    break
    
    def _create_rule_edge(self, rule: GraphRule, source_vertex, target_vertex, path: List[int]) -> None:
        """
        Create an edge based on a rule.
        
        Args:
            rule: The rule defining the edge
            source_vertex: Source vertex
            target_vertex: Target vertex
            path: Path connecting the vertices
        """
        # Determine carrier
        if source_vertex["Carrier"] == target_vertex["Carrier"]:
            carrier = source_vertex["Carrier"]
        elif rule.apply_carrier:
            carrier = rule.apply_carrier
        else:
            carrier = EdgeTypes.MIXED
        
        # Find actors if needed
        actors = self._find_actors_in_path(path) if rule.find_valves else None
        
        # Create edge
        if rule.inverse:
            self.graph.add_edge(
                target_vertex.index, source_vertex.index,
                carrier=carrier, weight=rule.strength, rulenumber=rule.rule_number,
                tau=rule.time_constant, lambda_factor=rule.effect_factor,
                rationale=rule.rationale, Actors=actors
            )
        else:
            self.graph.add_edge(
                source_vertex.index, target_vertex.index,
                carrier=carrier, weight=rule.strength, rulenumber=rule.rule_number,
                tau=rule.time_constant, lambda_factor=rule.effect_factor,
                rationale=rule.rationale, Actors=actors
            )
    
    def _find_actors_in_path(self, path: List[int]) -> List[str]:
        """Find actors (State nodes) in a path."""
        actors = []
        
        for vertex_id in path[1:-1]:  # Exclude start and end
            for child_id in self.graph.successors(vertex_id):
                edge = self.graph.es[self.graph.get_eid(vertex_id, child_id)]
                if edge["carrier"] == EdgeTypes.HAS_CHILD:
                    child = self.graph.vs[child_id]
                    if CarrierTypes.STATE in child["Tag"]:
                        actors.append(child["Tag"])
        
        return actors
    
    def _create_reverse_alarm_edges(self) -> None:
        """Create reverse edges for alarm connections."""
        for edge in self.graph.es:
            if edge['carrier'] == EdgeTypes.IS_ALARM:
                self.graph.add_edge(
                    edge.target, edge.source,
                    carrier=EdgeTypes.HAS_ALARM,
                    weight=1, tau=0, lambda_factor=1
                )
    
    def _initialize_valve_system(self) -> None:
        """Initialize the valve management system."""
        self.valve_manager.initialize_valves_from_graph(self.graph)
        self.valve_manager.find_all_relations(self.graph)
        self.valve_manager.apply_all_weights(self.graph)
    
    def get_graph(self) -> ig.Graph:
        """Get the constructed graph."""
        return self.graph
    
    def get_valve_manager(self) -> ValveManager:
        """Get the valve manager."""
        return self.valve_manager
