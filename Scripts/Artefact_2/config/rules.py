"""
Rule configuration for the AVEDAS system.
This module defines all graph rules externally to improve maintainability.
"""

from dataclasses import dataclass
from typing import Optional, List
from config.constants import CarrierTypes, RuleProbabilities


@dataclass
class GraphRule:
    """Represents a single graph rule."""
    source_type: str
    target_type: str
    rule_number: int
    strength: float = 0.99
    effect_factor: float = 1
    time_constant: float = 0.0
    apply_carrier: Optional[str] = None
    shortest: bool = False
    find_valves: bool = False
    inverse: bool = False
    rationale: Optional[str] = None


class RuleSetManager:
    """Manages different rule sets for the graph generation."""
    
    def __init__(self):
        self.gas_state_variable_rules = self._create_gas_state_variable_rules()
        self.gas_parameter_rules = self._create_gas_parameter_rules()
        self.alarm_rules = self._create_alarm_rules()
        
    def _create_gas_state_variable_rules(self) -> List[GraphRule]:
        """Create state variable rules for gas systems."""
        rules = []
        
        # Forward Propagation Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.TEMPERATURE,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=1,
                strength=0.99,
                rationale="Temperature propagated via product connections"
            ),
            GraphRule(
                source_type=CarrierTypes.FLOW,
                target_type=CarrierTypes.FLOW,
                rule_number=2,
                strength=0.99,
                rationale="Flow propagated via product connections"
            ),
            GraphRule(
                source_type=CarrierTypes.PRESSURE,
                target_type=CarrierTypes.PRESSURE,
                rule_number=3,
                strength=0.99,
                rationale="Pressure propagated via product connections"
            )
        ])
        
        # Backward Propagation Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.TEMPERATURE,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=4,
                strength=0.99,
                inverse=True,
                rationale="Temperature backward propagation"
            ),
            GraphRule(
                source_type=CarrierTypes.FLOW,
                target_type=CarrierTypes.FLOW,
                rule_number=5,
                strength=0.99,
                inverse=True,
                rationale="Flow backward propagation"
            ),
            GraphRule(
                source_type=CarrierTypes.PRESSURE,
                target_type=CarrierTypes.PRESSURE,
                rule_number=6,
                strength=0.99,
                inverse=True,
                rationale="Pressure backward propagation"
            )
        ])
        
        # Gas-specific Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.PRESSURE,
                target_type=CarrierTypes.FLOW,
                rule_number=7,
                strength=0.99,
                rationale="Pressure drives flow in gas systems"
            ),
            GraphRule(
                source_type=CarrierTypes.TEMPERATURE,
                target_type=CarrierTypes.PRESSURE,
                rule_number=8,
                strength=0.95,
                rationale="Temperature drives pressure in gas systems"
            ),
            GraphRule(
                source_type=CarrierTypes.FLOW,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=9,
                strength=0.99,
                effect_factor=-1,
                rationale="Lower flow results in higher temperature due to heat transfer"
            ),
            GraphRule(
                source_type=CarrierTypes.STATE,
                target_type=CarrierTypes.FLOW,
                rule_number=10,
                strength=0.99,
                apply_carrier=CarrierTypes.STATE,
                rationale="Actuators drive flow"
            )
        ])
        
        return rules
    
    def _create_gas_parameter_rules(self) -> List[GraphRule]:
        """Create parameter rules for gas systems."""
        rules = []
        
        # Parameter probability mapping
        probability_map = {
            CarrierTypes.DIAMETER: RuleProbabilities.HIGH,
            CarrierTypes.LENGTH: RuleProbabilities.HIGH,
            CarrierTypes.ROUGHNESS: RuleProbabilities.HIGH,
            CarrierTypes.HDIFF: RuleProbabilities.LOW,
            CarrierTypes.PDROP_NOM: RuleProbabilities.HIGH,
            CarrierTypes.MF_NOMINAL: RuleProbabilities.LOW,
            CarrierTypes.ROTATIONAL_SPEED: RuleProbabilities.LOW,
            CarrierTypes.AREA: RuleProbabilities.LOW,
            CarrierTypes.CLOGGING: RuleProbabilities.HIGH,
            "CSurface": RuleProbabilities.HIGH,
            "HTransfer": RuleProbabilities.HIGH,
            CarrierTypes.HLOSS: RuleProbabilities.HIGH,
            CarrierTypes.ALPHA: RuleProbabilities.HIGH
        }
        
        # Diameter Rules
        rules.append(GraphRule(
            source_type=CarrierTypes.DIAMETER,
            target_type=CarrierTypes.FLOW,
            rule_number=101,
            strength=probability_map[CarrierTypes.DIAMETER],
            apply_carrier=CarrierTypes.DIAMETER,
            rationale="Larger diameter reduces friction losses and increases flow"
        ))
        
        # Length Rules
        rules.append(GraphRule(
            source_type=CarrierTypes.LENGTH,
            target_type=CarrierTypes.FLOW,
            rule_number=104,
            strength=probability_map[CarrierTypes.LENGTH],
            effect_factor=-1,
            apply_carrier=CarrierTypes.LENGTH,
            rationale="Longer pipes increase friction losses and decrease flow"
        ))
        
        # Clogging Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.CLOGGING,
                target_type=CarrierTypes.FLOW,
                rule_number=110,
                strength=probability_map[CarrierTypes.CLOGGING],
                effect_factor=-1,
                apply_carrier=CarrierTypes.CLOGGING,
                rationale="Clogging increases flow resistance and decreases flow"
            ),
            GraphRule(
                source_type=CarrierTypes.CLOGGING,
                target_type=CarrierTypes.PRESSURE,
                rule_number=111,
                strength=probability_map[CarrierTypes.CLOGGING],
                effect_factor=-1,
                apply_carrier=CarrierTypes.CLOGGING,
                rationale="Clogging increases pressure drop"
            ),
            GraphRule(
                source_type=CarrierTypes.PRESSURE,
                target_type=CarrierTypes.CLOGGING,
                rule_number=112,
                strength=probability_map[CarrierTypes.CLOGGING],
                effect_factor=1,
                inverse=True,
                apply_carrier=CarrierTypes.CLOGGING,
                rationale="Pressure influences clogging detection"
            )
        ])
        
        # Pressure Drop Nominal Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.PDROP_NOM,
                target_type=CarrierTypes.FLOW,
                rule_number=120,
                strength=probability_map[CarrierTypes.PDROP_NOM],
                effect_factor=-1,
                apply_carrier="PressureDropNominal",
                rationale="Higher pressure drop decreases flow"
            ),
            GraphRule(
                source_type=CarrierTypes.PDROP_NOM,
                target_type=CarrierTypes.PRESSURE,
                rule_number=121,
                strength=probability_map[CarrierTypes.PDROP_NOM],
                effect_factor=-1,
                apply_carrier="PressureDropNominal",
                rationale="Higher pressure drop affects pressure distribution"
            ),
            GraphRule(
                source_type=CarrierTypes.PRESSURE,
                target_type=CarrierTypes.PDROP_NOM,
                rule_number=122,
                strength=probability_map[CarrierTypes.PDROP_NOM],
                effect_factor=1,
                inverse=True,
                apply_carrier="PressureDropNominal",
                rationale="Pressure influences nominal pressure drop detection"
            )
        ])
        
        # Heat Transfer Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.PRIMARY_CA,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=113,
                strength=probability_map["CSurface"],
                apply_carrier="CSurface",
                rationale="Larger surface area increases heat transfer (gas heating)"
            ),
            GraphRule(
                source_type=CarrierTypes.SECONDARY_CSURFACE,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=114,
                strength=probability_map["CSurface"],
                effect_factor=-1,
                apply_carrier="CSurface",
                rationale="Larger surface area increases heat transfer (water cooling)"
            ),
            GraphRule(
                source_type=CarrierTypes.PRIMARY_HTRANSFER,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=116,
                strength=probability_map["HTransfer"],
                apply_carrier="HTransfer",
                rationale="Enhanced heat transfer heats gas"
            ),
            GraphRule(
                source_type=CarrierTypes.SECONDARY_HEATT,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=117,
                strength=probability_map["HTransfer"],
                effect_factor=-1,
                apply_carrier="HTransfer",
                rationale="Enhanced heat transfer cools water"
            )
        ])
        
        # Heat Loss Rules
        rules.extend([
            GraphRule(
                source_type=CarrierTypes.HLOSS,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=118,
                strength=probability_map[CarrierTypes.HLOSS],
                effect_factor=-1,
                apply_carrier=CarrierTypes.HLOSS,
                rationale="Heat losses decrease gas temperature"
            ),
            GraphRule(
                source_type=CarrierTypes.ALPHA,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=119,
                strength=probability_map[CarrierTypes.ALPHA],
                effect_factor=-1,
                apply_carrier=CarrierTypes.ALPHA,
                rationale="Heat transfer coefficient affects heat losses"
            )
        ])
        
        return rules
    
    def _create_alarm_rules(self) -> List[GraphRule]:
        """Create alarm-related rules."""
        return [
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_TEMPERATURE,
                target_type=CarrierTypes.TEMPERATURE,
                rule_number=15,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="Temperature sensor alarm connection"
            ),
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_PRESSURE,
                target_type=CarrierTypes.PRESSURE,
                rule_number=16,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="Pressure sensor alarm connection"
            ),
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_FLOW,
                target_type=CarrierTypes.FLOW,
                rule_number=17,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="Flow sensor alarm connection"
            ),
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_LEVEL,
                target_type=CarrierTypes.LEVEL,
                rule_number=18,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="Level sensor alarm connection"
            ),
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_STATE,
                target_type=CarrierTypes.STATE,
                rule_number=19,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="State sensor alarm connection"
            ),
            GraphRule(
                source_type=CarrierTypes.MEASUREMENT_POWER,
                target_type=CarrierTypes.POWER,
                rule_number=20,
                strength=1.00,
                apply_carrier='isalarm',
                shortest=True,
                rationale="Power sensor alarm connection"
            )
        ]
    
    def get_all_rules(self) -> List[GraphRule]:
        """Get all rules combined."""
        all_rules = []
        all_rules.extend(self.gas_state_variable_rules)
        all_rules.extend(self.gas_parameter_rules)
        all_rules.extend(self.alarm_rules)
        return all_rules
    
    def get_rules_by_category(self, category: str) -> List[GraphRule]:
        """Get rules by category."""
        if category == "state_variables":
            return self.gas_state_variable_rules
        elif category == "parameters":
            return self.gas_parameter_rules
        elif category == "alarms":
            return self.alarm_rules
        else:
            raise ValueError(f"Unknown rule category: {category}")
            
    def add_custom_rule(self, rule: GraphRule, category: str = "custom"):
        """Add a custom rule to the appropriate category."""
        if category == "state_variables":
            self.gas_state_variable_rules.append(rule)
        elif category == "parameters":
            self.gas_parameter_rules.append(rule)
        elif category == "alarms":
            self.alarm_rules.append(rule)
        else:
            # Create custom category if needed
            if not hasattr(self, f"{category}_rules"):
                setattr(self, f"{category}_rules", [])
            getattr(self, f"{category}_rules").append(rule)
