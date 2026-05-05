import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import igraph as ig
from xml.etree import ElementTree as ET
import time
import re
import numpy as np
import heapq
import networkx as nx
from pyvis.network import Network
import Config


class Valve:
    """Represents a process valve, storing its state history and computing edge weights via kernel functions."""

    def __init__(self, Tag) -> None:
        """
        Args:
            Tag: Unique valve tag identifier.
        """
        self.history_length = 3
        self.state_history = [1.0] * self.history_length
        self.Tag = Tag

        # Maps carrier types to the edge indices in the graph that this valve controls.
        self.relationDict = {
            "Temperature": [],
            "Pressure": [],
            "Flow": [],
            "Level": []
        }

        self.kernelDict = {
            "Temperature": self.history_kernel(1, 1, 1, 1),
            "Pressure":    self.history_kernel(1, 1, 1, 1),
            "Flow":        self.history_kernel(1, 1, 1, 1),
            "Level":       self.history_kernel(1, 1, 1, 1)
        }

        # Scales valve state (0–1) to the edge-weight range used by the kernels.
        self.valuekernelDict = {
            "Temperature": self.history_kernel(0.01, 0.99, 1, 2),
            "Pressure":    self.history_kernel(0.01, 0.99, 1, 2),
            "Flow":        self.history_kernel(0.01, 0.99, 1, 2),
            "Level":       self.history_kernel(0.01, 0.99, 1, 2)
        }

    def find_relations(self, igraph):
        """Populate relationDict with edge indices for carrier types (Temperature, Pressure, Flow, Level).

        Args:
            igraph: The igraph.Graph to search.
        """
        valve_index = igraph.vs["Tag"].index(self.Tag)
        child_indices = igraph.successors(valve_index)

        for carriertype in self.relationDict:
            for child in child_indices:
                # Outgoing edges from the child
                for edge in igraph.es.select(_source=child):
                    if edge["carrier"] == carriertype:
                        self.relationDict[carriertype].append(edge.index)

                # Incoming edges to the child
                for edge in igraph.es.select(_target=child):
                    if edge["carrier"] == carriertype:
                        self.relationDict[carriertype].append(edge.index)

    def apply_weights(self, igraph):
        """Compute new edge weights from state_history via kernel functions and write them to the graph.

        Args:
            igraph: The igraph.Graph whose edges will be updated.
        """
        for carrier in self.relationDict:
            temp_history = self.state_history
            temp_value_history = [1] * self.history_length

            for idx, hist_val in enumerate(temp_history):
                scaled_val = int(np.round(hist_val * self.history_length))
                if scaled_val < 0:
                    hist_index = 0
                elif scaled_val <= 0.5:
                    max_idx = len(self.valuekernelDict[carrier]) - 1
                    hist_index = int(np.round(scaled_val / 0.5 * max_idx))
                else:
                    hist_index = len(self.valuekernelDict[carrier]) - 1
                temp_value_history[idx] = self.valuekernelDict[carrier][hist_index]

            numerator = np.sum(
                np.array(temp_value_history) * np.array(self.kernelDict[carrier])
            )
            denominator = np.sum(self.kernelDict[carrier]) or 1.0
            current_weight = np.round(numerator / denominator, 2)

            for e_idx in self.relationDict[carrier]:
                igraph.es[e_idx]["weight"] = current_weight
                igraph.es[e_idx]["Actors"] = self.Tag

    def update_state(self, in_state):
        """Append a new valve state to the history, dropping the oldest entry.

        Args:
            in_state: New valve state (e.g. opening degree 0–1).
        """
        self.state_history.append(in_state)
        self.state_history.pop(0)

    def find_relations_old(self, in_carriertype, igraph):
        """Legacy edge-search method kept for reference.

        Args:
            in_carriertype: Carrier type string, e.g. 'Temperature', 'Pressure'.
            igraph: The igraph.Graph to search.
        """
        valve_index = igraph.vs["Tag"].index(self.Tag)
        child_indices = igraph.successors(valve_index)

        for child in child_indices:
            for relation in igraph.successors(child):
                if igraph.es[relation]["carrier"] == in_carriertype:
                    self.relationDict[in_carriertype].append(relation)

    def history_kernel(self, start_value, stop_value, ramp_startpoint, ramplength):
        """Build a kernel vector of length history_length with a linear ramp from start_value to stop_value.

        Args:
            start_value: Constant value before the ramp.
            stop_value: Constant value after the ramp.
            ramp_startpoint: Index at which the ramp begins.
            ramplength: Number of ramp steps.

        Returns:
            List of length history_length.
        """
        kernellength = self.history_length
        kernel = (
            [start_value] * ramp_startpoint
            + list(np.round(np.linspace(start_value, stop_value, ramplength), 2))
            + [stop_value] * max(0, (kernellength - ramp_startpoint - ramplength))
        )
        return kernel[:kernellength]


def flatten(nested_list):
    """Recursively flatten a nested list of integers into a list of lists."""
    def flatten_helper(nested, flat):
        for item in nested:
            if isinstance(item, int):
                flat[-1].append(item)
            else:
                flat.append([])
                flatten_helper(item, flat)
    result = [[]]
    flatten_helper(nested_list, result)
    return result


class DCDG_Class:
    """Directed Cause-Dependency Graph (DCDG) engine.

    Builds and extends a directed igraph.Graph from an AutomationML (AML) file,
    assigns node/edge attributes, and applies causal influence rules for root cause analysis.
    """

    def __init__(self) -> None:
        self.counter = 0
        self.boolInitComplete = False
        self.NumberOfElements = 0
        self.g = ig.Graph(0, directed=True)

    def add_myvertex(self, in_tag, in_carriertype, in_amlID, in_alarmtag, in_alarmstate, in_alarmlimits, in_deviation):
        """Add a vertex to the graph with all required attributes.

        Args:
            in_tag: Unique node tag / name.
            in_carriertype: Physical carrier type, e.g. 'Temperature', 'Pressure', 'Flow'.
            in_amlID: AML element ID from the source file, or None.
            in_alarmtag: Whether the node carries an alarm tag.
            in_alarmstate: Whether an alarm state is currently active.
            in_alarmlimits: Alarm limit values, or None.
            in_deviation: Numerical deviation value for this node.

        Notes:
            - Node colour is assigned by carrier type.
            - parameterlabel=1 for recognised parameter carrier types.
            - sensorlabel=1 when in_carriertype=='Measurement'.
        """
        if in_carriertype == "Temperature":
            color = "red"
        elif in_carriertype == "Pressure":
            color = "green"
        elif in_carriertype == "Flow":
            color = "blue"
        elif in_carriertype == "Level":
            color = "yellow"
        else:
            color = "slategray"
        
        if in_carriertype in [
            "Height", "Rotational_Speed", "PumpVolume", "Area", "Height", "Length", 
            "Diameter", "Roughness", "HDiff", "PDropNom", "MFlowNom",
            #changed for GAS
            "Clogging", "CSurface", 
            #"HTransfer", "HLoss" # Changed to accound for primary and secondary heat exchangers
            "Primary_CA", "Primary_HTransfer", "Secondary_CSurface", "Secondary_HeatT", "Alpha"
        ]:
            parameterlabel = 1
        else:
            parameterlabel = 0

        if in_carriertype == "Measurement":
            sensorlabel = 1
        else:
            sensorlabel = 0

        self.g.add_vertex(
            Tag=in_tag,
            Carrier=in_carriertype,
            AMLID=in_amlID,
            AT=in_alarmtag,
            AS=in_alarmstate,
            AL=in_alarmlimits,
            color=color,
            aktorinfluence=False,
            parameterlabel=parameterlabel,
            sensorlabel=sensorlabel,
            deviation=in_deviation
        )

    def find_routes(self, vertex1_id, vertex2_type):
        """Find all 4-node paths from vertex1_id to vertices of vertex2_type following ['hasparent', 'Product', 'haschild'].

        Args:
            vertex1_id: Start vertex index.
            vertex2_type: Target vertex carrier type, e.g. 'Temperature'.

        Returns:
            List of (start_vertex_id, end_vertex_id) tuples matching the route criteria.
        """
        vertices2_ids = [v.index for v in self.g.vs if v['Carrier'] == vertex2_type]
        valid_routes = []
        edge_order = ['hasparent', 'Product', 'haschild']

        for vertex2_id in vertices2_ids:
            all_paths = self.g.get_all_simple_paths(vertex1_id, to=vertex2_id)
            for path in all_paths:
                if len(path) != 4:
                    continue
                edges = [(path[i], path[i+1]) for i in range(len(path) - 1)]
                edge_types = [self.g.es[self.g.get_eid(*edge_pair)]["Carrier"] for edge_pair in edges]
                if edge_types == edge_order:
                    vertices = [self.g.vs[vid]["Carrier"] for vid in path]
                    if vertices[0] == vertices[3] == 'Temperature' and vertices[1] == 'Any Type':
                        valid_routes.append((path[0], path[3]))
        return valid_routes

    def change_edge_hierarchieparents(self):
        """Rename the first 'hasparent' edge of any vertex adjacent to a 'Product' edge to 'hashierarchieparent'."""
        for vertex in self.g.vs:
            edges = self.g.es.select(_source=vertex.index)
            target_edges = self.g.es.select(_target=vertex.index)
            if any(e['carrier'] == "Product" for e in edges) or any(e['carrier'] == "Product" for e in target_edges):
                hasparent_edges = [edge for edge in edges if edge['carrier'] == "hasparent"]
                if len(hasparent_edges) > 0:
                    hasparent_edges[0]['carrier'] = "hashierarchieparent"

    def generate_graphfromAML(self, amlfilepath):
        """Parse an AML file and build the DCDG graph from its structure.

        Args:
            amlfilepath: Path to the AML file.
        """
        tree = ET.parse(amlfilepath)
        root = tree.getroot()
        
        node_list = [
            "Temperature", "Pressure", "Flow", "Level", "Power",
            "Measurement_Power", "Measurement_Temperature", "Measurement_Pressure",
            "Measurement_Flow", "Measurement_Level", "State", "Measurement_State",
            "Height", "Rotational_Speed", "PumpVolume", "Area", "Length", 
            "Diameter", "Roughness", "HDiff", "PDropNom", "MFNominal",
            #Changed for GAS
            "Clogging", "HLoss",
            # "CSurface", "HTransfer", # Changed to accound for primary and secondary heat exchangers
            "Primary_CA", "Primary_HTransfer", "Secondary_CSurface", "Secondary_HeatT", "Alpha"
        ]
        node_list_with_ = ['_' + element for element in node_list]

        parent_map = {}
        attribute_map = {}
        elementsID = {}
        interface_map = {}

        # -------------------------------------------------
        # Hilfsfunktion, die die AML-Struktur rekursiv liest
        # -------------------------------------------------
        def process_element(parent):
            for child in parent:
                try:
                    if child.tag == "{http://www.dke.de/CAEX}InternalElement":
                        elementsID[child.attrib['Name']] = child.attrib['ID']
                        if parent.attrib['Name'] != child.attrib['Name']:
                            parent_map[child.attrib['Name']] = parent.attrib['Name']
                            process_element(child)

                    elif child.tag == "{http://www.dke.de/CAEX}Attribute":
                        if child.attrib['Name'] in node_list or "Concentration" in child.attrib['Name']:
                            temp_str = parent.attrib['Name'] + '_' + child.attrib['Name']
                            attribute_map[temp_str] = True

                    elif child.tag == "{http://www.dke.de/CAEX}ExternalInterface":
                        if parent.attrib['Name'] not in interface_map:
                            interface_map[parent.attrib['Name']] = {}
                        interface_map[parent.attrib['Name']][child.attrib['ID']] = child.attrib['Name']

                except Exception as e:
                    print(f"Error processing element: {e}")

        for elem in root.iter('{http://www.dke.de/CAEX}InternalElement'):
            process_element(elem)

        for key in parent_map:
            self.add_myvertex(key, 'hierarch', elementsID[key], False, False, False, False)
            if key != 'Plant':
                if parent_map[key] in elementsID:
                    if len(self.g.vs.select(Tag=parent_map[key])) == 0:
                        self.add_myvertex(parent_map[key], 'hierarch', elementsID[parent_map[key]], False, False, False)

                    self.g.add_edge(
                        self.g.vs["Tag"].index(key), 
                        self.g.vs["Tag"].index(parent_map[key]),
                        carrier='hasparent',
                        weight=0
                    )
                    self.g.add_edge(
                        self.g.vs["Tag"].index(parent_map[key]),
                        self.g.vs["Tag"].index(key),
                        carrier='haschild',
                        weight=0
                    )

        remove_list = node_list_with_
        pattern = '|'.join(remove_list)

        for attr in attribute_map:
            # z.B. if attr="Pump_Height" -> key="Pump"
            key = re.sub(pattern, '', attr)
            if key in elementsID:
                carrierstring = attr.replace(key + '_', '')
                self.add_myvertex(attr, carrierstring, None, False, False, False, False)
                self.g.add_edge(
                    self.g.vs["Tag"].index(attr),
                    self.g.vs["Tag"].index(key),
                    carrier='hasparent',
                    weight=0
                )
                self.g.add_edge(
                    self.g.vs["Tag"].index(key),
                    self.g.vs["Tag"].index(attr),
                    carrier='haschild',
                    weight=0
                )

        for connect in root.iter('{http://www.dke.de/CAEX}InternalLink'):
            name_partnerA = next((n for n, ifaces in interface_map.items() if connect.attrib['RefPartnerSideA'] in ifaces), None)
            name_partnerB = next((n for n, ifaces in interface_map.items() if connect.attrib['RefPartnerSideB'] in ifaces), None)

            if name_partnerA is not None and name_partnerB is not None:
                connect_partnerA = interface_map[name_partnerA][connect.attrib['RefPartnerSideA']]
                connect_partnerB = interface_map[name_partnerB][connect.attrib['RefPartnerSideB']]

                # Einige Cases unterscheiden zwischen *_OUT, INOUT, IN usw.
                if '_OUT' in connect_partnerA and not 'OUT' in connect_partnerB:
                    self.g.add_edge(
                        self.g.vs["Tag"].index(name_partnerA),
                        self.g.vs["Tag"].index(name_partnerB),
                        carrier=connect_partnerA.replace("_OUT", ''),
                        weight=0
                    )
                else:
                    if 'INOUT' in connect_partnerA:
                        if 'INOUT' in connect_partnerB:
                            # Bidirectional edge
                            self.g.add_edge(
                                self.g.vs["Tag"].index(name_partnerA),
                                self.g.vs["Tag"].index(name_partnerB),
                                carrier=connect_partnerA.replace("_INOUT", ''),
                                weight=0
                            )
                            self.g.add_edge(
                                self.g.vs["Tag"].index(name_partnerB),
                                self.g.vs["Tag"].index(name_partnerA),
                                carrier=connect_partnerA.replace("_INOUT", ''),
                                weight=0
                            )
                        elif 'IN' in connect_partnerB:
                            self.g.add_edge(
                                self.g.vs["Tag"].index(name_partnerA),
                                self.g.vs["Tag"].index(name_partnerB),
                                carrier=connect_partnerA.replace("_INOUT", ''),
                                weight=0
                            )
                        else:
                            print('ERROR: Case3 NOT IMPLEMENTED')

                    else:
                        if '_OUT' in connect_partnerA and 'OUT' in connect_partnerB:
                            self.g.add_edge(
                                self.g.vs["Tag"].index(name_partnerA),
                                self.g.vs["Tag"].index(name_partnerB),
                                carrier=connect_partnerA.replace("_OUT", ''),
                                weight=0
                            )
                        else:
                            if '_IN' in connect_partnerA and '_OUT' in connect_partnerB:
                                self.g.add_edge(
                                    self.g.vs["Tag"].index(name_partnerB),
                                    self.g.vs["Tag"].index(name_partnerA),
                                    carrier=connect_partnerA.replace("_IN", ''),
                                    weight=0
                                )
                            else:
                                print('ERROR: Case4 NOT IMPLEMENTED')

        self.change_edge_hierarchieparents()

        self.vertexpaths, loop1length = self.find_paths(['hasparent', 'Product', 'haschild'], [3,1,3])
        alarmpaths, loop2length = self.find_paths(['hasparent', 'haschild'], [3,3])
        cooling_loops = self.find_paths(['hasparent', 'Product_ThermalContact', 'haschild'], [5,1,5])[0:-1]
        cooling_loops = flatten(cooling_loops)[2:-1]

        # Alarm Rules - Sensors
        self.apply_rule("Measurement_Temperature", "Temperature", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=15)
        self.apply_rule("Measurement_Pressure", "Pressure", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=16)
        self.apply_rule("Measurement_Flow", "Flow", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=17)
        self.apply_rule("Measurement_Level", "Level", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=18)
        self.apply_rule("Measurement_State", "State", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=19)
        self.apply_rule("Measurement_Power", "Power", strength=1.00, time_constant=0.0, effect_factor=1,
                        apply_carrier='isalarm', searchpath=alarmpaths, shortest=True, findValves=False, rulenumber=20)

        # Add reverse edges for alarms (hasalarm direction)
        for edge in self.g.es:
            if edge['carrier'] == 'isalarm':
                self.g.add_edge(edge.target, edge.source, carrier="hasalarm", weight=1, tau=0, lambda_factor=1)


        # State Variable Rule Set for Gases
        # Forward Propagation
        ## Temperature is propagated via product connections
        self.apply_rule("Temperature", "Temperature", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=1)
        ## Flow is propagated via product connections
        self.apply_rule("Flow", "Flow", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=2)
        ## Pressure is propagated via product connections
        self.apply_rule("Pressure", "Pressure", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=3)
        
        # Backward Propagation
        ## Temperature is propagated via product connections
        self.apply_rule("Temperature", "Temperature", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=4, inverse=True)
        ## Flow is propagated via product connections
        self.apply_rule("Flow", "Flow", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=5, inverse=True)
        ## Pressure is propagated via product connections
        self.apply_rule("Pressure", "Pressure", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=6, inverse=True)
        
        # Gas-specific state variable rules
        ## Pressure drives Flow
        self.apply_rule("Pressure", "Flow", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=7, inverse=False)
        ## Temperature drives Pressure
        self.apply_rule("Temperature", "Pressure", strength=0.95, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=8, inverse=False)
        ## Lower flow results in higher gas temperature (specific to this plant)
        self.apply_rule("Flow", "Temperature", strength=0.99, time_constant=0.0, effect_factor=-1, findValves=False, rulenumber=9, inverse=False)
        # The lower the flow, the higher the gas temperature due to heat transfer
        self.apply_rule("Flow", "Temperature",  strength=0.99, time_constant=0.0, effect_factor=-1, findValves=False, rulenumber=9, inverse=False)
        # Actuators drive Flow
        self.apply_rule("State", "Flow", strength=0.99, time_constant=0.0, effect_factor=1, findValves=False, rulenumber=10, apply_carrier='State')

        
        # Parameter Rule Set for Gases
        high_probability = 0.99
        medium_probability = 0.7
        low_probability = 0.3
        probability_indexes = {
            "Diameter": low_probability,
            "Length": low_probability,               
            "Roughness": low_probability,
            "HDiff": low_probability,
            "PDropNom": low_probability,
            "MFNominal": low_probability,
            "Rotational_Speed": low_probability,
            "Area": low_probability,
            "Clogging": low_probability,
            "CSurface": high_probability,
            "HTransfer": high_probability,
            "HLoss": high_probability,
            "Alpha": high_probability
        }

        # Diameter: larger diameter reduces friction losses and increases flow
        self.apply_rule("Diameter", "Flow", strength=probability_indexes["Diameter"], time_constant=0.0, effect_factor=1, findValves=False, searchpath=alarmpaths, rulenumber=101, apply_carrier='Diameter')

        # Length: longer pipe increases friction losses and reduces flow
        self.apply_rule("Length", "Flow", strength=probability_indexes["Length"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=104, apply_carrier='Length')

        # Roughness: not modelled in simulation — rules omitted

        # Clogging: increases flow resistance, reducing flow and downstream pressure
        self.apply_rule("Clogging", "Flow", strength=probability_indexes["Clogging"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=110, apply_carrier='Clogging')
        self.apply_rule("Clogging", "Pressure", strength=probability_indexes["Clogging"], time_constant=0.0, effect_factor=-1, findValves=False, rulenumber=111, apply_carrier='Clogging')
        self.apply_rule("Pressure", "Clogging", strength=probability_indexes["Clogging"], time_constant=0.0, effect_factor=1, findValves=False, rulenumber=112, inverse=True, apply_carrier='Clogging')

        # Pressure Drop Nominal: higher nominal drop reduces flow and downstream pressure
        self.apply_rule("PDropNom", "Flow", strength=probability_indexes["PDropNom"], time_constant=0.0, effect_factor=-1, searchpath=alarmpaths,
                        findValves=False, rulenumber=18, inverse=False, apply_carrier='PressureDropNominal')
        self.apply_rule("PDropNom", "Pressure", strength=probability_indexes["PDropNom"], time_constant=0.0, effect_factor=-1, findValves=False, rulenumber=111, apply_carrier='PressureDropNominal')
        self.apply_rule("Pressure", "PDropNom", strength=probability_indexes["PDropNom"], time_constant=0.0, effect_factor=1, findValves=False, rulenumber=112, inverse=True, apply_carrier='PressureDropNominal')

        # CSurface (pipe-wall fouling): increases heat transfer
        # Primary side: fouling increases gas temperature
        self.apply_rule("Primary_CA", "Temperature", strength=probability_indexes["CSurface"], time_constant=0.0, effect_factor=1, findValves=False, searchpath=alarmpaths, rulenumber=113, apply_carrier='CSurface')
        # Secondary side: fouling reduces water temperature
        self.apply_rule("Secondary_CSurface", "Temperature", strength=probability_indexes["CSurface"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=114, apply_carrier='CSurface')

        # HTransfer (heat transfer coefficient)
        # Primary side: higher transfer raises gas temperature
        self.apply_rule("Primary_HTransfer", "Temperature", strength=probability_indexes["HTransfer"], time_constant=0.0, effect_factor=1, findValves=False, searchpath=alarmpaths, rulenumber=116, apply_carrier='HTransfer')
        # Secondary side: higher transfer lowers water temperature
        self.apply_rule("Secondary_HeatT", "Temperature", strength=probability_indexes["HTransfer"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=117, apply_carrier='HTransfer')

        # HLoss: heat losses lower gas temperature
        self.apply_rule("HLoss", "Temperature", strength=probability_indexes["HLoss"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=118, apply_carrier='HLoss')

        # Alpha (heat transfer coefficient): lowers gas temperature
        self.apply_rule("Alpha", "Temperature", strength=probability_indexes["Alpha"], time_constant=0.0, effect_factor=-1, findValves=False, searchpath=alarmpaths, rulenumber=118, apply_carrier='Alpha')

        # Create Valve objects for all State-type nodes
        self.valves = []
        for v in self.g.vs:
            if v['Carrier'] == 'State':
                temp_name = v['Tag'].replace("_State", "")
                self.valves.append(Valve(temp_name))

        # Initialize valve edge weights after graph construction
        for valve in self.valves:
            valve.find_relations(self.g)
            valve.apply_weights(self.g)

        print("Graph created")
            
        
        

    def update_valves(self, in_valvedict):
        """Update valve states and recompute edge weights for all valves present in the dict.

        Args:
            in_valvedict: Mapping of valve tag to new state value (e.g. opening degree).
        """
        for valve in self.valves:
            if valve.Tag in in_valvedict:
                valve.update_state(in_valvedict[valve.Tag])
                valve.apply_weights(self.g)

    def evaluate_valvestate(self, in_valuedict):
        """Update state and recompute edge weights for every valve in the graph.

        Args:
            in_valuedict: Mapping of valve tag to new state value (e.g. opening degree).
        """
        for valve in self.valves:
            valve.update_state(in_valuedict[valve.Tag])
            valve.apply_weights(self.g)

    def modified_dijkstra(self, source_vertex_id, target_vertex_id, print_paths=True, dijkstra_type="Variable"):
        """Dijkstra variant that tracks both positive and negative influence paths simultaneously.

        Args:
            source_vertex_id: Index of the source vertex.
            target_vertex_id: Index of the target vertex.
            print_paths: Unused; reserved for future debug output.
            dijkstra_type: ``"Variable"`` reads the ``AS`` attribute of the source;
                ``"parameter"`` reads ``parameterlabel`` and returns ``(distance, path)``.

        Returns:
            float or tuple: Computed path distance, or ``(distance, path)`` when
            ``dijkstra_type="parameter"``.
        """

        def has_duplicate_pattern(path):
            """Return True if any 2-node pattern A→B repeats immediately (A→B→A→B)."""
            for i in range(len(path) - 3):
                if path[i:i+2] == path[i+2:i+4] or path[i] == path[i+2]:
                    return True
            return False

        edge_details = []

        if dijkstra_type == "parameter":
            source_vertex_value = self.g.vs[source_vertex_id]["parameterlabel"]
        elif dijkstra_type == "Variable":
            source_vertex_value = self.g.vs[source_vertex_id]['AS']
        else:
            print("something went wrong with the type of dijkstra")
            source_vertex_value = 0

        target_vertex_value = self.g.vs[target_vertex_id]['AS']

        positive_dist = [np.inf] * len(self.g.vs)
        negative_dist = [np.inf] * len(self.g.vs)
        positive_path = [[] for _ in range(len(self.g.vs))]
        negative_path = [[] for _ in range(len(self.g.vs))]

        if source_vertex_value > 0:
            positive_dist[source_vertex_id] = 0
        elif source_vertex_value < 0:
            negative_dist[source_vertex_id] = 0

        queue = [(0, source_vertex_id, source_vertex_value, [source_vertex_id])]

        while queue:
            (d, v, sign, path_so_far) = heapq.heappop(queue)

            for u in self.g.successors(v):
                edge_id = self.g.get_eid(v, u)
                edge_weight = self.g.es[edge_id]['weight']
                edge_lambda = self.g.es[edge_id]["lambda_factor"]

                if edge_weight <= 0.01 or edge_lambda is None or len(path_so_far) > 20:
                    continue

                edge_weight_logged = edge_weight
                edge_weight = -np.log(edge_weight_logged)

                new_sign = sign * edge_lambda
                new_path = path_so_far + [u]

                if has_duplicate_pattern(new_path):
                    continue

                edge_details.append({
                    'source': self.g.vs[v]['Tag'],
                    'target': self.g.vs[u]['Tag'],
                    'weight': edge_weight,
                    'log_weight': edge_weight_logged,
                })

                new_dist = d + edge_weight
                if new_sign >= 0 and new_dist < positive_dist[u]:
                    positive_dist[u] = new_dist
                    positive_path[u] = new_path
                    heapq.heappush(queue, (new_dist, u, 1, new_path))
                if new_sign <= 0 and new_dist < negative_dist[u]:
                    negative_dist[u] = new_dist
                    negative_path[u] = new_path
                    heapq.heappush(queue, (new_dist, u, -1, new_path))

        path = []
        distance = np.inf

        if target_vertex_value > 0:
            if positive_dist[target_vertex_id] >= negative_dist[target_vertex_id] and negative_dist[target_vertex_id] < np.inf:
                distance = positive_dist[target_vertex_id]
                path = positive_path[target_vertex_id]
            else:
                distance = -negative_dist[target_vertex_id]
                path = negative_path[target_vertex_id]

        elif target_vertex_value < 0:
            if positive_dist[target_vertex_id] > negative_dist[target_vertex_id] and positive_dist[target_vertex_id] < np.inf:
                distance = -positive_dist[target_vertex_id]
                path = positive_path[target_vertex_id]
            else:
                distance = negative_dist[target_vertex_id]
                path = negative_path[target_vertex_id]

        else:
            if (positive_dist[target_vertex_id] < np.inf or negative_dist[target_vertex_id] < np.inf):
                if negative_path[target_vertex_id] and not positive_path[target_vertex_id]:
                    path = negative_path[target_vertex_id]
                elif not negative_path[target_vertex_id] and positive_path[target_vertex_id]:
                    path = positive_path[target_vertex_id]
                elif negative_path[target_vertex_id] and positive_path[target_vertex_id]:
                    min_path = [0]*100
                    if positive_path[target_vertex_id] and len(positive_path[target_vertex_id]) < len(min_path):
                        min_path = positive_path[target_vertex_id]
                    if negative_path[target_vertex_id] and len(negative_path[target_vertex_id]) < len(min_path):
                        min_path = negative_path[target_vertex_id]
                    path = min_path
                distance = -np.inf if len(path) > 0 else np.inf
            else:
                distance = np.inf
                if negative_path[target_vertex_id] and not positive_path[target_vertex_id]:
                    path = negative_path[target_vertex_id]
                elif not negative_path[target_vertex_id] and positive_path[target_vertex_id]:
                    path = positive_path[target_vertex_id]
                elif negative_path[target_vertex_id] and positive_path[target_vertex_id]:
                    min_path = [0]*100
                    if positive_path[target_vertex_id] and len(positive_path[target_vertex_id]) < len(min_path):
                        min_path = positive_path[target_vertex_id]
                    if negative_path[target_vertex_id] and len(negative_path[target_vertex_id]) < len(min_path):
                        min_path = negative_path[target_vertex_id]
                    path = min_path

        if dijkstra_type == "parameter":
            return (distance, path if path else [""])
        else:
            return distance

    def dfs(self, source_vertex_id, target_vertex_id, visited, weight):
        """Depth-first search that multiplies edge weights along the path.

        Args:
            source_vertex_id: Starting vertex index.
            target_vertex_id: Target vertex index.
            visited: Boolean mask to prevent revisiting nodes.
            weight: Cumulative weight at the current node (start with 1.0).

        Returns:
            Tuple of (best path as vertex-index list, maximum path weight found).
        """
        visited[source_vertex_id] = True
        path = [source_vertex_id]
        if source_vertex_id == target_vertex_id:
            return path, weight
        else:
            max_weight = weight
            best_path = []

            exclude_carriers = ["hasparent", "haschild", "Product"]

            for v in self.g.successors(source_vertex_id):
                edge_id = self.g.get_eid(source_vertex_id, v)
                edge_weight = self.g.es[edge_id]['weight']
                edge_carrier = self.g.es[edge_id]['carrier']

                if edge_weight != 0 and edge_carrier not in exclude_carriers:
                    new_weight = weight * edge_weight
                    if not visited[v] and abs(new_weight) >= 0.1:
                        new_path, new_weight = self.dfs(v, target_vertex_id, visited, new_weight)
                        if new_weight > max_weight:
                            max_weight = new_weight
                            best_path = path + new_path

            visited[source_vertex_id] = False
            return best_path, max_weight

    def evaluate_alarm(self, source_vertex_id, target_vertex_id):
        """Run DFS from source to target and return the best path and its cumulative weight.

        Args:
            source_vertex_id: Starting vertex index.
            target_vertex_id: Target vertex index.

        Returns:
            Tuple of (best path as vertex-index list, maximum path weight).
        """
        visited = [False] * self.g.vcount()
        best_path, max_weight = self.dfs(source_vertex_id, target_vertex_id, visited, 1.0)
        return best_path, max_weight

    def generate_alarmPLUT(self):
        """Build a pairwise lookup table (matrix) over all active alarm nodes (AS != 0).

        Each cell [i][j] is the Dijkstra distance between alarm i and alarm j,
        scaled by both nodes' AS values.

        Returns:
            2-D list of float: N×N weight matrix where N is the number of active alarms.
        """
        vertices = [v for v in self.g.vs if v["AS"] != 0]
        weight_matrix = [[0]*len(vertices) for _ in range(len(vertices))]

        for i in range(len(vertices)):
            for j in range(len(vertices)):
                if i != j:
                    dist = self.modified_dijkstra(vertices[i].index, vertices[j].index)
                    weight_matrix[i][j] = vertices[i]["AS"] * dist * vertices[j]["AS"]

        return weight_matrix

    def find_paths(self, carriercondition, carriermax):
        """Find all graph paths that traverse the given carrier types up to their allowed counts.

        Args:
            carriercondition: Ordered list of carrier types to traverse, e.g.
                ``['hasparent', 'Product', 'haschild']``.
            carriermax: Maximum number of times each carrier may be used, e.g. ``[3, 1, 3]``.

        Returns:
            Tuple of (list of paths as vertex-index lists, total cumulative path length).
        """
        def check_path(g, path, carrier):
            carrier_count = 0
            for i in range(1, len(path)):
                edge_id = g.get_eid(path[i-1], path[i])
                if g.es[edge_id]['carrier'] == carrier:
                    carrier_count += 1
            return carrier_count if carrier_count > 1 else 0

        totallength = 0
        list_of_all_paths = []

        for i in range(len(self.g.vs)):
            paths = self.explore_edges(i, carriercondition, carriermax)
            if paths:
                for path in paths:
                    if check_path(self.g, path, "Product"):
                        pass
                    totallength += len(path)
                    list_of_all_paths.append(path)

        return [p for p in list_of_all_paths if p[0] != p[-1]], totallength

    def explore_edges(self, source_vertex_id, carrierlist, carriermax,
                      used_carriers=None, vertex_path=None, carrier_index=0, carrier_count=0):
        """Recursively search for paths that satisfy the carrier sequence and usage limits.

        Args:
            source_vertex_id: Current vertex index.
            carrierlist: Ordered carrier types to traverse, e.g. ``['hasparent', 'Product', 'haschild']``.
            carriermax: Maximum usage count per carrier, matching the order of ``carrierlist``.
            used_carriers: Carriers already traversed in the current path.
            vertex_path: Vertex indices visited so far.
            carrier_index: Position in ``carrierlist`` currently being matched.
            carrier_count: How many times the current carrier has been used in this path.

        Returns:
            List of valid paths, each represented as a list of vertex indices.
        """
        all_paths = []
        if vertex_path is None:
            vertex_path = []
        if used_carriers is None:
            used_carriers = []

        vertex_path.append(source_vertex_id)

        if set(used_carriers) == set(carrierlist):
            all_paths.append(list(vertex_path))

        for edge in self.g.es.select(_source=source_vertex_id):
            if edge['carrier'] == carrierlist[carrier_index] and carrier_count < carriermax[carrier_index]:
                new_used_carriers = used_carriers.copy()
                new_used_carriers.append(edge['carrier'])

                new_paths = self.explore_edges(
                    edge.target, carrierlist, carriermax,
                    new_used_carriers, vertex_path.copy(),
                    carrier_index, carrier_count + 1
                )
                if new_paths:
                    all_paths.extend(new_paths)

            # Advance to the next carrier type once the current one has been used at least once
            if carrier_count >= 1 and carrier_index + 1 < len(carrierlist) and edge['carrier'] == carrierlist[carrier_index + 1]:
                new_used_carriers = used_carriers.copy()
                new_used_carriers.append(edge['carrier'])

                new_paths = self.explore_edges(
                    edge.target, carrierlist, carriermax,
                    new_used_carriers, vertex_path.copy(),
                    carrier_index + 1, 1
                )
                if new_paths:
                    all_paths.extend(new_paths)

        return all_paths

    def apply_rule(self, source_type: str, target_type: str, rulenumber: int,
                   strength=0.99, effect_factor=1, time_constant=0,
                   rationale=None, apply_carrier=None, searchpath=None,
                   shortest=False, findValves=False, inverse=False):
        """Add edges from all source_type nodes to all target_type nodes reachable via searchpath.

        Args:
            source_type: Carrier type of the source vertex (e.g. ``"Temperature"``).
            target_type: Carrier type of the target vertex (e.g. ``"Flow"``).
            rulenumber: Identifier for this rule (stored on the edge).
            strength: Base edge weight.
            effect_factor: Sign and magnitude of the causal effect (stored as ``lambda_factor``).
            time_constant: Propagation delay (stored as ``tau``).
            rationale: Optional free-text description stored on the edge.
            apply_carrier: Override carrier label for the new edge; falls back to the shared
                carrier of source and target, or ``"mixed"`` if they differ.
            searchpath: List of vertex-index paths to search. Defaults to ``self.vertexpaths``.
            shortest: If ``True``, use only the shortest matching path per target vertex.
            findValves: If ``True``, collect intermediate ``State`` nodes as ``Actors`` on the edge.
            inverse: If ``True``, add the edge in reverse (target → source).

        Returns:
            Number of edges added.
        """
        def determine_carrier(source_vertex, target_vertex, applied_carrier):
            if source_vertex["Carrier"] == target_vertex["Carrier"]:
                return source_vertex["Carrier"]
            elif applied_carrier is not None:
                return applied_carrier
            else:
                return "mixed"

        if searchpath is None:
            searchpath = self.vertexpaths

        num_edges_added = 0

        for source_vertex in self.g.vs.select(Carrier_eq=source_type):
            written = False
            valid_paths = [p for p in searchpath if p and p[0] == source_vertex.index]
            if not valid_paths:
                continue

            if shortest:
                valid_paths.sort(key=len)

            for target_vertex in self.g.vs.select(Carrier_eq=target_type):
                for path in valid_paths:
                    if path and path[-1] == target_vertex.index:
                        actors = []
                        if findValves:
                            for vertex_id in path[1:-1]:
                                for child_id in self.g.successors(vertex_id):
                                    edge = self.g.es[self.g.get_eid(vertex_id, child_id)]
                                    if edge["carrier"] == "haschild":
                                        child = self.g.vs[child_id]
                                        if "State" in child["Tag"]:
                                            actors.append(child["Tag"])
                        else:
                            actors = None

                        current_carrier = determine_carrier(source_vertex, target_vertex, apply_carrier)

                        if inverse:
                            self.g.add_edge(
                                path[-1], path[0],
                                carrier=current_carrier,
                                weight=strength,
                                rulenumber=rulenumber,
                                tau=time_constant,
                                lambda_factor=effect_factor,
                                rationale=rationale,
                                Actors=actors
                            )
                        else:
                            self.g.add_edge(
                                path[0], path[-1],
                                carrier=current_carrier,
                                weight=strength,
                                rulenumber=rulenumber,
                                tau=time_constant,
                                lambda_factor=effect_factor,
                                rationale=rationale,
                                Actors=actors
                            )
                        num_edges_added += 1
                        written = True
                        if shortest:
                            break
                if shortest and written:
                    break

        return num_edges_added

    def generate_distancematrix(self):
        """Build an N×N pairwise distance matrix over all active alarm nodes (AS != 0).

        Each cell stores ``exp(-distance)`` computed by ``modified_dijkstra``.

        Returns:
            Tuple of (distance_matrix as numpy ndarray, edge_details_matrix as list-of-lists).
        """
        active_alarm_list = [v for v in self.g.vs if v["AS"] != 0]

        distance_matrix = np.zeros((len(active_alarm_list), len(active_alarm_list)))
        edge_details_matrix = [[[] for _ in range(len(active_alarm_list))] for _ in range(len(active_alarm_list))]

        for i in range(len(active_alarm_list)):
            for j in range(len(active_alarm_list)):
                if i != j:
                    distance, edge_details, path = self.modified_dijkstra(active_alarm_list[i].index,
                                                                          active_alarm_list[j].index)
                    distance_matrix[i, j] = np.exp(-distance)
                    edge_details_matrix[i][j] = edge_details
                else:
                    distance_matrix[i, j] = 0

        self.current_distancematrix = distance_matrix
        self.current_activealarmlist = active_alarm_list
        return distance_matrix, edge_details_matrix

    def generate_statevariable_influence_matrix(self):
        """Build a square influence matrix over all sensor nodes (sensorlabel == 1).

        Only pairs where both nodes are active (AS != 0) receive non-zero entries.
        Active pairs are filled with ``exp(-distance)`` from ``modified_dijkstra``.
        The diagonal is set to 1.

        Returns:
            numpy.ndarray: N×N influence matrix where N is the number of sensor nodes.
        """
        possible_alarm_list = [v for v in self.g.vs if v["sensorlabel"] == 1]
        active_alarm_list = [v for v in possible_alarm_list if v["AS"] != 0]

        statevariable_influence_matrix = np.zeros((len(possible_alarm_list), len(possible_alarm_list)))

        for i in range(len(possible_alarm_list)):
            for j in range(len(possible_alarm_list)):
                if i != j:
                    if possible_alarm_list[i]["AS"] != 0 and possible_alarm_list[j]["AS"] != 0:
                        distance = self.modified_dijkstra(possible_alarm_list[i].index,
                                                          possible_alarm_list[j].index)
                        if distance == -np.inf:
                            statevariable_influence_matrix[i, j] = 0
                        elif distance > 0:
                            statevariable_influence_matrix[i, j] = np.exp(-distance)
                        else:
                            statevariable_influence_matrix[i, j] = 0
                else:
                    statevariable_influence_matrix[i, j] = 1

        self.current_statevariable_influence_matrix = statevariable_influence_matrix
        self.current_activealarmlist = active_alarm_list
        return statevariable_influence_matrix

    def generate_parameterinfluence_matrix(self):
        """Build a parameter×sensor influence matrix using Dijkstra distances.

        Each raw cell is filled with ``exp(-distance)`` (or ``-exp(distance)`` for
        negative distances) from ``modified_dijkstra`` in parameter mode.  The matrix
        is then scaled by the sensor deviation, a neutrality penalty, and a
        range-from-sensor factor.

        Returns:
            numpy.ndarray: 2-D matrix with shape ``[#parameters, #sensors]``.
        """
        active_alarm_list = [v for v in self.g.vs if v["AS"] != 0]
        possible_alarm_list = [v for v in self.g.vs if v["sensorlabel"] != 0]
        parameter_list = [v for v in self.g.vs if v["parameterlabel"] != 0]

        parameter_influence_matrix = np.zeros((len(parameter_list), len(possible_alarm_list)))
        parameter_pathlength_matrix = np.zeros((len(parameter_list), len(possible_alarm_list)))

        # Count of times a parameter has no influence on any sensor
        parameter_neutral_influencelist = [0] * len(parameter_list)

        # Step 1: fill raw Dijkstra distances
        for i in range(len(parameter_list)):
            for j in range(len(possible_alarm_list)):
                if possible_alarm_list[j]["AS"] is not None:
                    distance, path = self.modified_dijkstra(parameter_list[i].index,
                                                            possible_alarm_list[j].index,
                                                            dijkstra_type="parameter")
                    parameter_pathlength_matrix[i, j] = len(path) if len(path) > 0 else 1

                    if distance == -np.inf:
                        parameter_neutral_influencelist[i] += 1
                        parameter_influence_matrix[i, j] = 0
                    elif distance > 0:
                        parameter_influence_matrix[i, j] = np.exp(-distance)
                    else:
                        parameter_influence_matrix[i, j] = -np.exp(distance)

            # Column-wise sum for later normalisation
            factor_influence = [0] * len(possible_alarm_list)
            for col_idx in range(len(possible_alarm_list)):
                factor_influence[col_idx] = sum(abs(parameter_influence_matrix[:, col_idx]))
                if factor_influence[col_idx] <= 1:
                    factor_influence[col_idx] = 1

            # Mean path length per parameter row
            range_from_sensor_factor = [0] * len(parameter_list)
            for pi in range(len(parameter_list)):
                range_from_sensor_factor[pi] = np.mean(parameter_pathlength_matrix[pi, :])

        # Step 2: scale by deviation, neutrality penalty, and range factor
        for j in range(len(possible_alarm_list)):
            for i in range(len(parameter_list)):
                dev = abs(possible_alarm_list[j]["deviation"])
                param_influence = parameter_influence_matrix[i, j]
                # 0.9^(neutral_count): penalise parameters that rarely propagate
                # 1.1^(mean_path_length): reward parameters that are further away
                param_influence *= dev
                param_influence *= np.power(0.9, parameter_neutral_influencelist[i])
                param_influence *= np.power(1.1, range_from_sensor_factor[i])
                param_influence /= factor_influence[j]
                parameter_influence_matrix[i, j] = param_influence

        self.current_parameter_influence_matrix = parameter_influence_matrix
        self.current_activealarmlist = active_alarm_list
        self.current_parameter_list = parameter_list
        self.possible_alarm_list = possible_alarm_list
        self.current_parameter_neutral_influencelist = parameter_neutral_influencelist

        return parameter_influence_matrix

    def generate_distance(self, i, active_alarm_list, distance_matrix):
        """Compute one row of the distance matrix (designed for multithreaded use).

        Fills ``distance_matrix[i, j]`` with ``exp(-distance)`` for all j ≠ i.

        Args:
            i: Row index to compute.
            active_alarm_list: List of active alarm vertices.
            distance_matrix: Shared numpy array to write results into.
        """
        for j in range(len(active_alarm_list)):
            if i != j:
                dist = self.modified_dijkstra(active_alarm_list[i].index, 
                                              active_alarm_list[j].index)
                distance_matrix[i, j] = np.exp(-dist)
            else:
                distance_matrix[i, j] = 0

    def evaluate_distance_matrix(self, distance_limit, update_distance=False):
        """Compute and combine state-variable and parameter influence matrices.

        Generates both influence matrices, combines them into a single distance
        matrix (weighting each column by the row/column ratio of the state-variable
        matrix), and returns name lists for parameters and sensors.

        Args:
            distance_limit: Distance threshold (reserved for future use).
            update_distance: If ``True``, triggers an optional multithreaded
                distance recomputation (not yet wired up).

        Returns:
            Tuple of (combined_distance_matrix, parameter_influence_matrix,
            parameter_names_total, statevariable_names_total,
            parameter_names_with_influence, statevariable_names_with_influence).
        """
        self.generate_statevariable_influence_matrix()
        self.generate_parameterinfluence_matrix()

        parameter_influence_matrix = self.current_parameter_influence_matrix
        statevariable_influence_matrix = self.current_statevariable_influence_matrix

        combined_distance_matrix = np.zeros((parameter_influence_matrix.shape[0],
                                             parameter_influence_matrix.shape[1]))

        ratio = [0]*statevariable_influence_matrix.shape[1]
        for j in range(statevariable_influence_matrix.shape[1]):
            sum_col = np.sum(statevariable_influence_matrix[:, j])
            sum_row = np.sum(statevariable_influence_matrix[j, :])
            if sum_col < 0.1:
                sum_col = 0.1
            ratio[j] = sum_row / sum_col
            combined_distance_matrix[:, j] = parameter_influence_matrix[:, j] * (ratio[j] + 1)

        self.current_combined_distance_matrix = combined_distance_matrix
        distance_matrix = self.current_combined_distance_matrix

        if distance_matrix is None:
            return "Invalid distance matrix"

        parameter_names_total = []
        parameter_names_with_influence = []

        for row_idx in range(distance_matrix.shape[0]):
            param_tag = self.current_parameter_list[row_idx]["Tag"]
            parameter_names_total.append(param_tag)
            if sum(distance_matrix[row_idx, :]) != 0:
                parameter_names_with_influence.append(param_tag)

        statevariable_names_total = []
        statevariable_names_with_influence = []

        for col_idx in range(distance_matrix.shape[1]):
            sensor_tag = self.possible_alarm_list[col_idx]["Tag"]
            statevariable_names_total.append(sensor_tag)
            if sum(distance_matrix[:, col_idx]) != 0:
                statevariable_names_with_influence.append(sensor_tag)

        return (distance_matrix,
                parameter_influence_matrix,
                parameter_names_total,
                statevariable_names_total,
                parameter_names_with_influence,
                statevariable_names_with_influence)

    def add_sensorlabels(self, alarmstates_dict):
        """Mark all vertices present in the dict as sensor nodes (sensorlabel = 1).

        Args:
            alarmstates_dict: Mapping whose keys are vertex tags to label.
        """
        for key in alarmstates_dict:
            idx = self.g.vs["Tag"].index(key)
            self.g.vs[idx]["sensorlabel"] = 1

    def set_alarmstates(self, alarmstates_dict):
        """Set the alarm state (AS) attribute for each vertex listed in the dict.

        Args:
            alarmstates_dict: Mapping of vertex tag to alarm state value.
        """
        for key in alarmstates_dict:
            idx = self.g.vs["Tag"].index(key)
            self.g.vs[idx]["AS"] = alarmstates_dict[key]

    def set_deviations(self, deviation_dict):
        """Set the deviation attribute for each vertex listed in the dict.

        Args:
            deviation_dict: Mapping of vertex tag to deviation value.
        """
        for key in deviation_dict:
            idx = self.g.vs["Tag"].index(key)
            self.g.vs[idx]["deviation"] = deviation_dict[key]
    
    def generate_interactive_graph(self, output_file="interactive_graph.html", height="1100px"):
        """Export the DCDG as an interactive PyVis HTML file.

        Args:
            output_file: Path of the output HTML file.
            height: CSS height string for the network canvas.
        """
        G_nx = nx.DiGraph()
        for v in self.g.vs:
            G_nx.add_node(v.index, label=v["Tag"], carrier=v["Carrier"])
        for e in self.g.es:
            G_nx.add_edge(e.source, e.target, carrier=e["carrier"], weight=e["weight"])

        net = Network(notebook=False, directed=True, width="100%", height=height,
                      cdn_resources='in_line', select_menu=True, filter_menu=True)
        net.force_atlas_2based()

        color_dict = {
            "Temperature": "red",
            "Pressure": "green",
            "Flow": "blue",
            "Level": "yellow",
            "State": "gray",
            "hierarch": "lightgray",
            "hasparent": "orange",
            "haschild": "purple",
            "Product": "cyan",
            "hasalarm": "pink",
            "isalarm": "brown",
            "thermal_connection": "olive",
            "control": "navy",
            "PumpRotationalSpeed": "teal",
            "PressureDropNominal": "gold",
            "Diameter": "darkgreen",
            "HeightDifference": "darkred",
            "Roughness": "darkblue",
            "Length": "darkorange",
            "Area": "darkviolet",
            "MFlowNominal": "darkgray",
            "Clogging": "darkviolet",
            "CSurface": "darkorange",
            "HTransfer": "darkred",
            "HLoss": "darkgreen",
            "Alpha": "darkviolet",
        }

        for node, data in G_nx.nodes(data=True):
            net.add_node(
                node,
                label=data["label"],
                title=f"Carrier: {data['carrier']}",
                color=color_dict.get(data["carrier"], "lightgray")
            )

        for source, target, data in G_nx.edges(data=True):
            weight = data.get('weight', 1)
            edge_color = 'green' if weight >= 0 else 'red'
            net.add_edge(
                source,
                target,
                title=f"Carrier: {data['carrier']}<br>Weight: {weight}",
                label=str(weight),
                color=edge_color
            )

        net.set_edge_smooth('dynamic')

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(net.generate_html())

if __name__ == "__main__":
    t0 = time.time()
    aml_file = Config.AML_FILE
    graph_output_path = str(Config.RCA_INITIAL_GRAPH_OUTPUT)
    dcdg = DCDG_Class()
    dcdg.generate_graphfromAML(aml_file)
    dcdg.generate_interactive_graph(output_file=graph_output_path)
    print(f"Number of vertices: {dcdg.g.vcount()}")
    print(f"Number of edges:    {dcdg.g.ecount()}")
    print(f"Graph saved to '{graph_output_path}' in {time.time() - t0:.1f}s")
    