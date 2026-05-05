model ModVA_online_stable
  //input Real Test =4;
  /*
    Documentation of Simulation Runs and changes to the model
    run 1:        according to documentation to my best knowledge
    result run 1: found that 1) B203 is filled much faster that B201 with B202 in the middle
                  This will be due to the shorter lenght of the pipes to B203 in comparison to B201
                  in reality, however it is the other way around. B201 is filled faster than B203
                  This is due to the Tee no receiving as much of the fast moving water
                  Thus is not modeled correctly in Modelica. I have adjusted this in reality by slightly closing the vavles above the tanks
                  I will try do do something similar for the simulation in run 2.
                  Hopefully I can fix this issue by installing automatic valves in the real plant
                  Another issue that I found is that P202 pumps much faster than P201 in reality.
                  This might be due to differences in pressure drops after the two pumps. I will try to ammend for this in run 2.
      
    run 2:       reduced V204.m_flow_nominal and V205.m_flow_nominal, changed N_in for P202
    result run 2:
    */
  replaceable package Medium = Modelica.Media.Water.StandardWaterOnePhase constrainedby Modelica.Media.Interfaces.PartialMedium;
  inner Modelica.Fluid.System system(dp_small = 100, energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, massDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, p_ambient = 101325, T_ambient = 293.15, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-140, -36}, extent = {{-10, -10}, {10, 10}})));
  // Tanks
  Modelica.Fluid.Examples.AST_BatchPlant.BaseClasses.TankWithTopPorts tank_B201(redeclare package Medium = Medium, V0 = 0.0001, crossArea = 0.01431355, height = 0.22, level_start = 0.1119246, nPorts = 2, nTopPorts = 1, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.011, height = 0.0001, zeta_out = 0, zeta_in = 1),Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.21, zeta_out = 0, zeta_in = 1)}, stiffCharacteristicForEmptyPort = false) annotation(
    Placement(visible = true, transformation(origin = {-89, 31}, extent = {{-11, -11}, {11, 11}}, rotation = 0)));
  Modelica.Fluid.Examples.AST_BatchPlant.BaseClasses.TankWithTopPorts tank_B202(redeclare package Medium = Medium, V0 = 0.0001, crossArea = 0.01431355, height = 0.22, level_start = 0.147512, nPorts = 1, nTopPorts = 1, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.011, height = 0.0001, zeta_out = 0, zeta_in = 1)}, stiffCharacteristicForEmptyPort = false) annotation(
    Placement(visible = true, transformation(origin = {-51, 31}, extent = {{-11, -11}, {11, 11}}, rotation = 0)));
  Modelica.Fluid.Examples.AST_BatchPlant.BaseClasses.TankWithTopPorts tank_B203(redeclare package Medium = Medium, V0 = 0.0001, crossArea = 0.01431355, height = 0.22, level_start = 0.148613, nPorts = 1, nTopPorts = 1, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.011, height = 0.0001, zeta_out = 0, zeta_in = 1)}, stiffCharacteristicForEmptyPort = false) annotation(
    Placement(visible = true, transformation(origin = {-13, 31}, extent = {{-11, -11}, {11, 11}}, rotation = 0)));
  Modelica.Fluid.Examples.AST_BatchPlant.BaseClasses.TankWithTopPorts tank_B204(redeclare package Medium = Medium, V0 = 0.0001, crossArea = 0.0324, height = 0.35, level_start = 0.0012844, nPorts = 1, nTopPorts = 1, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.011, height = 0.0001, zeta_out = 0, zeta_in = 1)}, stiffCharacteristicForEmptyPort = false) annotation(
    Placement(visible = true, transformation(origin = {47, 25}, extent = {{-11, -11}, {11, 11}}, rotation = 0)));
  /*                       
                  Modelica.Fluid.Vessels.OpenTank tank_B201(redeclare package Medium = Medium, T_start = Modelica.Units.Conversions.from_degC(20), crossArea = 0.01431355, height = 0.22, level_start = 0.2, nPorts = 0, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.22, zeta_out = 0, zeta_in = 1), Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.000001, zeta_out = 0, zeta_in = 1)}, use_portsData = true) annotation(
                    Placement(visible = true, transformation(origin = {-88, 28}, extent = {{-12, -12}, {12, 12}}, rotation = 0)));
                   
                  Modelica.Fluid.Vessels.OpenTank tank_B202(redeclare package Medium = Medium, T_start = Modelica.Units.Conversions.from_degC(20), crossArea = 0.01431355, height = 0.22, level_start = 0.2, nPorts = 0, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.22, zeta_out = 0, zeta_in = 1), Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.000001, zeta_out = 0, zeta_in = 1)}, use_portsData = true) annotation(
                    Placement(visible = true, transformation(origin = {-50, 28}, extent = {{-12, -12}, {12, 12}}, rotation = 0)));
                  Modelica.Fluid.Vessels.OpenTank tank_B203(redeclare package Medium = Medium, T_start = Modelica.Units.Conversions.from_degC(20), crossArea = 0.01431355, height = 0.22, level_start = 0.2, nPorts = 0, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.22, zeta_out = 0, zeta_in = 1), Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.000001, zeta_out = 0, zeta_in = 1)}, use_portsData = true) annotation(
                    Placement(visible = true, transformation(origin = {-14, 28}, extent = {{-12, -12}, {12, 12}}, rotation = 0)));
                  Modelica.Fluid.Vessels.OpenTank tank_B204(redeclare package Medium = Medium, T_start = Modelica.Units.Conversions.from_degC(20), crossArea = 0.0324, height = 0.35, level_start = 0.01, nPorts = 0, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.34, zeta_out = 0, zeta_in = 1), Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 0.000001, zeta_out = 0, zeta_in = 1)}, use_portsData = true) annotation(
                    Placement(visible = true, transformation(origin = {46, 26}, extent = {{-14, -14}, {14, 14}}, rotation = 0)));
                */
  //Actuators
  //Valves
  Modelica.Fluid.Valves.ValveLinear V201(redeclare package Medium = Medium, dp_nominal = 10, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-88, -12}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V202(redeclare package Medium = Medium, dp_nominal = 10, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-48, -12}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V203(redeclare package Medium = Medium, dp_nominal = 10, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-14, -12}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V204(redeclare package Medium = Medium, dp_nominal = 1041.4693877551022, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-88, 70}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V205(redeclare package Medium = Medium, dp_nominal = 1347.4897959183675, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-50, 68}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V206(redeclare package Medium = Medium, dp_nominal = 10, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {-14, 68}, extent = {{6, -6}, {-6, 6}}, rotation = 90)));
  Modelica.Fluid.Valves.ValveLinear V209(redeclare package Medium = Medium, dp_nominal = 20, dp_start = 10, m_flow_nominal = 0.1, m_flow_small = 0.000001, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {120, -10}, extent = {{-6, 6}, {6, -6}}, rotation = -0)));
  //Pumps
  Modelica.Fluid.Machines.PrescribedPump P201(redeclare package Medium = Medium, N_nominal = 166.43, m_flow_start = 0.000001, T_start = system.T_start, V(displayUnit = "m3") = 0.00004398128, checkValve = true, checkValveHomotopy = Modelica.Fluid.Types.CheckValveHomotopyType.Closed, energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, redeclare function flowCharacteristic =Modelica.Fluid.Machines.BaseClasses.PumpCharacteristics.quadraticFlow(V_flow_nominal = {P202_V_flow_at_max_head, P202_V_flow_at_middle_head, P202_V_flow_at_min_head}, head_nominal = {P202_head_max, P202_head_middle, P202_head_min}), massDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, nParallel = 1, p_a_start = 100000, p_b_start = 100000, use_N_in = true, N(start = 0)) annotation(
    Placement(transformation(origin = {-9, -57}, extent = {{-7, -7}, {7, 7}})));
  Modelica.Fluid.Machines.PrescribedPump P202(redeclare package Medium = Medium, N_nominal = 166.43, m_flow_start = 0.000001, T_start = system.T_start, V(displayUnit = "m3") = 0.00004398128, checkValve = true, checkValveHomotopy = Modelica.Fluid.Types.CheckValveHomotopyType.Closed, energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, redeclare function flowCharacteristic = Modelica.Fluid.Machines.BaseClasses.PumpCharacteristics.quadraticFlow(V_flow_nominal = {P202_V_flow_at_max_head, P202_V_flow_at_middle_head, P202_V_flow_at_min_head}, head_nominal = {P202_head_max, P202_head_middle, P202_head_min}), massDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial, nParallel = 1, p_a_start = 100000, p_b_start = 100000, use_N_in = true, N(start = 0)) annotation(
    Placement(transformation(origin = {65, -45}, extent = {{-7, -7}, {7, 7}})));
  //Sensors
  //Pipes
  Modelica.Fluid.Pipes.StaticPipe pipe_V206_B201(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.05, length = 0.15) annotation(
    Placement(transformation(origin = {-88, 51}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_V205_B202(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.05, length = 0.15) annotation(
    Placement(transformation(origin = {-50, 51}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_V204_B203(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.05, length = 0.15) annotation(
    Placement(transformation(origin = {-14, 51}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_B201_V201(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.04, length = 0.27) annotation(
    Placement(visible = true, transformation(origin = {-88, 5}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_B202_V202(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.04, length = 0.27) annotation(
    Placement(visible = true, transformation(origin = {-50, 5}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_B203_V203(redeclare package Medium = Medium, diameter = 0.01, height_ab = -0.04, length = 0.27) annotation(
    Placement(transformation(origin = {-14, 5}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_V201_Tee1(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.19) annotation(
    Placement(transformation(origin = {-82, -44}, extent = {{-6, -6}, {6, 6}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_V202_Tee2(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.11) annotation(
    Placement(transformation(origin = {-43, -21}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_V203_Tee2(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.31) annotation(
    Placement(transformation(origin = {-19, -21}, extent = {{5, -5}, {-5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee2_Tee1(redeclare package Medium = Medium, diameter = 0.009877551020408163, height_ab = 0, length = 0.11) annotation(
    Placement(transformation(origin = {-45, -33}, extent = {{5, -5}, {-5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee1_P201(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.16) annotation(
    Placement(transformation(origin = {-37, -51}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_P202_Tee6(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0.1, length = 0.1) annotation(
    Placement(transformation(origin = {83, -45}, extent = {{-5, 5}, {5, -5}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee6_V207(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0.09, length = 0.09) annotation(
    Placement(transformation(origin = {102, -10}, extent = {{-6, 6}, {6, -6}})));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee6_FI272(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0.20, length = 0.50, m_flow_start = 0) annotation(
    Placement(transformation(origin = {89, 49}, extent = {{-5, 5}, {5, -5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee8_V206(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.26) annotation(
    Placement(transformation(origin = {-15, 85}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee8_V205(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.06) annotation(
    Placement(transformation(origin = {-49, 85}, extent = {{5, 5}, {-5, -5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_Tee7_V206(redeclare package Medium = Medium, diameter = 0.01, height_ab = 0, length = 0.15) annotation(
    Placement(transformation(origin = {-89, 87}, extent = {{5, 5}, {-5, -5}}, rotation = 90)));
  // Fittings
  //Tees
  Modelica.Fluid.Fittings.TeeJunctionVolume Tee1(redeclare package Medium = Medium, V = 0.0000003, p_start = 99999.99999999999) annotation(
    Placement(transformation(origin = {-59, -43}, extent = {{5, -5}, {-5, 5}}, rotation = 90)));
  Modelica.Fluid.Fittings.TeeJunctionVolume Tee6(redeclare package Medium = Medium, V = 0.0000003, p_start = 99999.99999999999) annotation(
    Placement(transformation(origin = {89, -9}, extent = {{-5, 5}, {5, -5}}, rotation = 90)));
  Modelica.Fluid.Fittings.TeeJunctionVolume Tee2(redeclare package Medium = Medium, V = 0.0000003, p_start = 99999.99999999999) annotation(
    Placement(transformation(origin = {-31, -25}, extent = {{-5, -5}, {5, 5}}, rotation = -90)));
  Modelica.Fluid.Fittings.TeeJunctionVolume Tee8(redeclare package Medium = Medium, V = 0.0000003, p_start = 99999.99999999999) annotation(
    Placement(transformation(origin = {-49, 99}, extent = {{5, 5}, {-5, -5}})));
  //Boundaries
  Modelica.Fluid.Sources.FixedBoundary boundary(redeclare package Medium = Medium, nPorts = 1, p(displayUnit = "Pa") = 101325) annotation(
    Placement(visible = true, transformation(origin = {142, -18}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  //Signals
  //Pump Characteristics
  //Modelica.Blocks.Sources.RealExpression P201_V_flow_at_max_head(y = 0.000122);
  parameter Real P201_V_flow_at_max_head = 0.000122;
  //[0.0001, 0.00015]
  //Modelica.Blocks.Sources.RealExpression P201_V_flow_at_middle_head(y = 0.0002);
  parameter Real P201_V_flow_at_middle_head = 0.0002;
  //[0.00018, 0.00021]
  //Modelica.Blocks.Sources.RealExpression P201_V_flow_at_min_head(y = 0.00025);
  parameter Real P201_V_flow_at_min_head = 0.00025;
  //[0.00022, 0.00028]
  //Modelica.Blocks.Sources.RealExpression P201_head_max(y = 2.045);
  parameter Real P201_head_max = 2.045;
  //[1.85, 2.20]     (Viel Förderhöhe sorgt für wenig Durchfluss)
  //Modelica.Blocks.Sources.RealExpression P201_head_middle(y = 1.534);
  parameter Real P201_head_middle = 1.534;
  //[1.35, 1.649]
  //Modelica.Blocks.Sources.RealExpression P201_head_min(y = 1.022);
  parameter Real P201_head_min = 1.022;
  //[0.85, 1.149]
  //Modelica.Blocks.Sources.RealExpression P202_V_flow_at_max_head(y = 0.000122);
  parameter Real P202_V_flow_at_max_head = 0.000122;
  //[0.0001, 0.00015]
  //Modelica.Blocks.Sources.RealExpression P202_V_flow_at_middle_head(y = 0.0002);
  parameter Real P202_V_flow_at_middle_head = 0.0002;
  //[0.00018, 0.00021]
  //Modelica.Blocks.Sources.RealExpression P202_V_flow_at_min_head(y = 0.00025);
  parameter Real P202_V_flow_at_min_head = 0.00025;
  //[0.00022, 0.00028]
  //Modelica.Blocks.Sources.RealExpression P202_head_max(y = 2.045);
  parameter Real P202_head_max = 2.045;
  //[1.85, 2.20]     (Viel Förderhöhe sorgt für wenig Durchfluss)
  parameter Real P202_head_middle = 1.534;
  //Modelica.Blocks.Sources.RealExpression P202_head_middle(y = 1.534);
  //[1.35, 1.649]
  //Modelica.Blocks.Sources.RealExpression P202_head_min(y = 1.022);
  parameter Real P202_head_min = 1.022;
 //[0.85, 1.149]
  //Control
  //State Graph
  // Cut to reduce compilation time
  /*
                                                    Modelica.Blocks.Sources.RealExpression B201_level(y = tank_B201.level) annotation(
                                                      Placement(visible = true, transformation(origin = {-376, 34}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.RealExpression B202_level(y = tank_B202.level) annotation(
                                                      Placement(visible = true, transformation(origin = {-378, -2}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.RealExpression B203_level(y = tank_B203.level) annotation(
                                                      Placement(visible = true, transformation(origin = {-378, -48}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.RealExpression B204_level(y = tank_B204.level) annotation(
                                                      Placement(visible = true, transformation(origin = {-378, -96}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LA210(y = if tank_B201.level > 0.219 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, 42}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LS202(y = if tank_B201.level < 0.01 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, 28}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LA211(y = if tank_B202.level > 0.219 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, 6}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LS203(y = if tank_B202.level < 0.01 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -10}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LA212(y = if tank_B203.level > 0.219 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -42}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LS204(y = if tank_B203.level < 0.01 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -56}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LA213(y = if tank_B204.level > 0.349 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LS205(y = if tank_B204.level > 0.175 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -96}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                    Modelica.Blocks.Sources.BooleanExpression LS206(y = if tank_B204.level < 0.01 then true else false) annotation(
                                                      Placement(visible = true, transformation(origin = {-350, -110}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
                                                   */
  Modelica.Blocks.Sources.CombiTimeTable ActuatorControl(table = [0.628625, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 21.601068, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 46.84808, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 71.726626, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0; 73.335518, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0; 126.723401, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0; 178.501439, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0; 180.140964, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0; 230.06377, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 231.783974, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 258.245052, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 283.105067, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 308.182818, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0; 361.415688, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0; 414.637898, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0; 464.461751, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0; 466.108099, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 492.778021, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 517.933282, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0; 542.832951, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0; 595.81635, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], timeEvents = Modelica.Blocks.Types.TimeEvents.NoTimeEvents, smoothness = Modelica.Blocks.Types.Smoothness.ConstantSegments, startTime = 0, extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint) annotation(
    Placement(transformation(origin = {-140, -6}, extent = {{-10, -10}, {10, 10}})));
  //Testing Values for Pipe_B204_P202.diameter 0.009 mehr 0.007 mehr 0.005 weniger 0.006 mehr 0.0065 doch weniger 0.0055 ein bisschen mehr 0.00575 ein bisschen mehr 0.0058 weniger 0.0578
  Modelica.Fluid.Pipes.StaticPipe Pipe_B204_P202(redeclare package Medium = Medium, diameter = 0.00578, height_ab = -0.006, length = 0.44) annotation(
    Placement(transformation(origin = {47, 3}, extent = {{5, 5}, {-5, -5}}, rotation = 90)));
  Modelica.Fluid.Sensors.VolumeFlowRate FI272(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {51, 109}, extent = {{-5, -5}, {5, 5}}, rotation = 180)));
  Modelica.Fluid.Fittings.TeeJunctionVolume Tee7(V = 0.0000003, redeclare package Medium = Medium, p_start = 99999.99999999999) annotation(
    Placement(transformation(origin = {-81, 99}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe Pipe_Tee7_Tee8(length = 0.12, diameter = 0.01, redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {-65, 99}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Pipes.StaticPipe Pipe_FI272_Tee7(length = 0.36, diameter = 0.01, height_ab = 0.13, redeclare package Medium = Medium, m_flow_start = 0) annotation(
    Placement(transformation(origin = {-11, 107}, extent = {{-5, -5}, {5, 5}}, rotation = 180)));
  Modelica.Fluid.Sensors.Pressure PI252(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {-63, 5}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Sensors.Pressure PI251(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {-103, 5}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Sensors.Pressure PI253(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {-27, 5}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Fluid.Sensors.Temperature TI262(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {-18, -38}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Fluid.Sensors.Pressure PI254(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {69, 5}, extent = {{-5, -5}, {5, 5}})));
  Modelica.Blocks.Sources.RealExpression LI211(y = tank_B201.level) annotation(
    Placement(transformation(origin = {-104, 40}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Sources.RealExpression LI212(y = tank_B202.level) annotation(
    Placement(transformation(origin = {-66, 40}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Sources.RealExpression LI213(y = tank_B203.level) annotation(
    Placement(transformation(origin = {-28, 40}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Sources.RealExpression LI214(y = tank_B204.level) annotation(
    Placement(transformation(origin = {62, 36}, extent = {{-4, -4}, {4, 4}})));
  //Modelica.Blocks.Sources.RealExpression TI261(y = tank_B204.temperature)  annotation(
  //Placement(transformation(origin = {62, 18}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Math.RealToBoolean LA205_RB(threshold = 0.175) annotation(
    Placement(transformation(origin = {104, 26}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Math.RealToBoolean LA204_RB(threshold = 0.05) annotation(
    Placement(transformation(origin = {104, 16}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Interaction.Show.BooleanValue LA205 annotation(
    Placement(transformation(origin = {118, 26}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Interaction.Show.BooleanValue LA204 annotation(
    Placement(transformation(origin = {118, 16}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Math.RealToBoolean LA240_RB(threshold = 0.3) annotation(
    Placement(transformation(origin = {104, 36}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Interaction.Show.BooleanValue LA240 annotation(
    Placement(transformation(origin = {118, 36}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Blocks.Math.RealToBoolean LA210_RB(threshold = 0.2) annotation(
    Placement(transformation(origin = {-103, 33}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA210 annotation(
    Placement(transformation(origin = {-108, 32}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Blocks.Math.RealToBoolean LA201_RB(threshold = 0.001) annotation(
    Placement(transformation(origin = {-103, 25}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA201 annotation(
    Placement(transformation(origin = {-108, 24}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Blocks.Math.RealToBoolean LA220_RB(threshold = 0.2) annotation(
    Placement(transformation(origin = {-65, 33}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Math.RealToBoolean LA202_RB(threshold = 0.001) annotation(
    Placement(transformation(origin = {-65, 25}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Math.RealToBoolean LA230_RB(threshold = 0.2) annotation(
    Placement(transformation(origin = {-27, 33}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Math.RealToBoolean LA203_RB(threshold = 0.001) annotation(
    Placement(transformation(origin = {-27, 25}, extent = {{3, -3}, {-3, 3}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA220 annotation(
    Placement(transformation(origin = {-70, 32}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA202 annotation(
    Placement(transformation(origin = {-70, 24}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA230 annotation(
    Placement(transformation(origin = {-34, 32}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Blocks.Interaction.Show.BooleanValue LA203 annotation(
    Placement(transformation(origin = {-34, 24}, extent = {{2, -2}, {-2, 2}}, rotation = -0)));
  Modelica.Fluid.Sensors.Temperature TI261(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {70, 18}, extent = {{-4, -4}, {4, 4}})));
  Modelica.Fluid.Sensors.VolumeFlowRate FI271(redeclare package Medium = Medium) annotation(
    Placement(transformation(origin = {15, -27}, extent = {{-7, -7}, {7, 7}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_P201_FI271(redeclare package Medium = Medium, length = 0.05, diameter = 0.01, height_ab = 0.05, m_flow_start = 1e-6) annotation(
    Placement(transformation(origin = {13, -47}, extent = {{-5, -5}, {5, 5}}, rotation = 90)));
  Modelica.Fluid.Pipes.StaticPipe pipe_FI271_B204(length = 0.57, diameter = 0.01, height_ab = 0.405, redeclare package Medium = Medium, m_flow_start = 0) annotation(
    Placement(transformation(origin = {14, 0}, extent = {{-6, -6}, {6, 6}}, rotation = 90)));
    //k = 95.58163265306122 to k = 55.58163265306122
 Modelica.Blocks.Math.Gain P202_Characteristic(k = 95.58163265306122)  annotation(
    Placement(transformation(origin = {65, -29}, extent = {{-3, -3}, {3, 3}}, rotation = -90)));
 Modelica.Blocks.Math.Gain P201_Characteristic(k = 99.17959183673469)  annotation(
    Placement(transformation(origin = {-7, -43}, extent = {{-3, -3}, {3, 3}}, rotation = -90)));
 Modelica.Fluid.Vessels.OpenTank Overflow(redeclare package Medium = Medium, nPorts = 1, height = 5, crossArea = 0.5, level_start = 0.001, portsData = {Modelica.Fluid.Vessels.BaseClasses.VesselPortsData(diameter = 0.01, height = 4, zeta_out = 0, zeta_in = 1)})  annotation(
    Placement(transformation(origin = {32, 86}, extent = {{-8, -8}, {8, 8}})));
 Modelica.Fluid.Pipes.StaticPipe Overflow_pipe(length = 5.1, diameter = 0.5, height_ab = -5, redeclare package Medium = Medium)  annotation(
    Placement(transformation(origin = {32, 63}, extent = {{-8, -5}, {8, 5}}, rotation = 90)));
equation
//Control_V201.y = if time < 5 then true else false;
// V207.opening = 1;
// mflow_small_original = 0.000001;
//V209.opening = 0.00000001;
/*
  B204_empty.condition = if tank_B201.level > 0.219 or tank_B202.level > 0.219 or tank_B203.level > 0.219 or tank_B204.level < 0.01 then true else false;
  V201.opening = if Empty_B201.active then 1 else 0;
  V202.opening = if Empty_B202.active then 1 else 0;
  V203.opening = if Empty_B203.active then 1 else 0;
  V204.opening = if Empty_B204.active then 1 else 0;
  V205.opening = if Empty_B204.active then 1 else 0;
  V206.opening = if Empty_B204.active then 1 else 0;
  V207.opening = if Empty_B204.active then 1 else 0;
  V209.opening = 0;
  P201.N_in = if Empty_B201.active or Empty_B202.active or Empty_B203.active then 166.43 else 0.0000001;
  P202.N_in = if Empty_B204.active then 166.43 else 0.0000001;
  */
//Deal with overflow
  connect(pipe_P202_Tee6.port_a, P202.port_b) annotation(
    Line(points = {{78, -45}, {72, -45}}, color = {0, 127, 255}));
  connect(pipe_V202_Tee2.port_b, Tee2.port_1) annotation(
    Line(points = {{-38, -21}, {-34, -21}, {-34, -20}, {-31, -20}}, color = {0, 127, 255}));
  connect(pipe_V203_Tee2.port_b, Tee2.port_3) annotation(
    Line(points = {{-24, -21}, {-24, -22}, {-26, -22}, {-26, -25}}, color = {0, 127, 255}));
  connect(Tee2.port_2, pipe_Tee2_Tee1.port_a) annotation(
    Line(points = {{-31, -30}, {-36, -30}, {-36, -33}, {-40, -33}}, color = {0, 127, 255}));
  connect(pipe_V201_Tee1.port_b, Tee1.port_3) annotation(
    Line(points = {{-76, -44}, {-76, -43}, {-64, -43}}, color = {0, 127, 255}));
  connect(Tee1.port_1, pipe_Tee2_Tee1.port_b) annotation(
    Line(points = {{-59, -38}, {-59, -36.5}, {-50, -36.5}, {-50, -33}}, color = {0, 127, 255}));
  connect(Tee1.port_2, pipe_Tee1_P201.port_a) annotation(
    Line(points = {{-59, -48}, {-60, -48}, {-60, -51}, {-42, -51}}, color = {0, 127, 255}));
  connect(pipe_Tee1_P201.port_b, P201.port_a) annotation(
    Line(points = {{-32, -51}, {-24, -51}, {-24, -57}, {-16, -57}}, color = {0, 127, 255}));
  connect(pipe_P202_Tee6.port_b, Tee6.port_1) annotation(
    Line(points = {{88, -45}, {88, -29.5}, {89, -29.5}, {89, -14}}, color = {0, 127, 255}));
  connect(Tee6.port_3, pipe_Tee6_V207.port_a) annotation(
    Line(points = {{94, -9}, {93, -9}, {93, -10}, {96, -10}}, color = {0, 127, 255}));
  connect(Tee8.port_3, pipe_Tee8_V205.port_a) annotation(
    Line(points = {{-49, 94}, {-49, 90}}));
  connect(pipe_V206_B201.port_b, tank_B201.topPorts[1]) annotation(
    Line(points = {{-88, 46}, {-88, 42}}, color = {0, 127, 255}));
  connect(tank_B201.ports[1], pipe_B201_V201.port_a) annotation(
    Line(points = {{-88, 20}, {-88, 10}}, color = {0, 127, 255}));
  connect(pipe_V205_B202.port_b, tank_B202.topPorts[1]) annotation(
    Line(points = {{-50, 46}, {-50, 42}}, color = {0, 127, 255}));
  connect(tank_B202.ports[1], pipe_B202_V202.port_a) annotation(
    Line(points = {{-50, 20}, {-50, 10}}, color = {0, 127, 255}));
  connect(tank_B203.topPorts[1], pipe_V204_B203.port_b) annotation(
    Line(points = {{-12, 42}, {-14, 42}, {-14, 46}}, color = {0, 127, 255}));
  connect(tank_B203.ports[1], pipe_B203_V203.port_a) annotation(
    Line(points = {{-12, 20}, {-14, 20}, {-14, 10}}, color = {0, 127, 255}));
  connect(V209.port_a, pipe_Tee6_V207.port_b) annotation(
    Line(points = {{114, -10}, {108, -10}}));
  connect(V209.port_b, boundary.ports[1]) annotation(
    Line(points = {{126, -10}, {132, -10}, {132, -18}}, color = {0, 127, 255}));
  connect(V201.port_a, pipe_B201_V201.port_b) annotation(
    Line(points = {{-88, -6}, {-88, 0}}, color = {0, 127, 255}));
  connect(V201.port_b, pipe_V201_Tee1.port_a) annotation(
    Line(points = {{-88, -18}, {-88, -44}}, color = {0, 127, 255}));
  connect(V202.port_a, pipe_B202_V202.port_b) annotation(
    Line(points = {{-48, -6}, {-48, -3}, {-50, -3}, {-50, 0}}, color = {0, 127, 255}));
  connect(V202.port_b, pipe_V202_Tee2.port_a) annotation(
    Line(points = {{-48, -18}, {-48, -21}}, color = {0, 127, 255}));
  connect(V203.port_a, pipe_B203_V203.port_b) annotation(
    Line(points = {{-14, -6}, {-14, 0}}, color = {0, 127, 255}));
  connect(V203.port_b, pipe_V203_Tee2.port_a) annotation(
    Line(points = {{-14, -18}, {-14, -21}}, color = {0, 127, 255}));
  connect(V205.port_a, pipe_Tee8_V205.port_b) annotation(
    Line(points = {{-50, 74}, {-50, 78}, {-49, 78}, {-49, 80}}, color = {0, 127, 255}));
  connect(V205.port_b, pipe_V205_B202.port_a) annotation(
    Line(points = {{-50, 62}, {-50, 56}}, color = {0, 127, 255}));
  connect(pipe_Tee8_V206.port_b, V206.port_a) annotation(
    Line(points = {{-15, 80}, {-15, 76}, {-14, 76}, {-14, 74}}, color = {0, 127, 255}));
  connect(V206.port_b, pipe_V204_B203.port_a) annotation(
    Line(points = {{-14, 62}, {-14, 56}}, color = {0, 127, 255}));
  connect(V204.port_b, pipe_V206_B201.port_a) annotation(
    Line(points = {{-88, 64}, {-88, 56}}, color = {0, 127, 255}));
  connect(tank_B204.ports[1], Pipe_B204_P202.port_a) annotation(
    Line(points = {{48, 14}, {48, 8}}, color = {0, 127, 255}));
  connect(Tee6.port_2, pipe_Tee6_FI272.port_a) annotation(
    Line(points = {{89, -4}, {89, 44}}, color = {0, 127, 255}));
  connect(pipe_Tee6_FI272.port_b, FI272.port_a) annotation(
    Line(points = {{89, 54}, {84, 54}, {84, 109}, {56, 109}}, color = {0, 127, 255}));
  connect(FI272.port_b, Pipe_FI272_Tee7.port_a) annotation(
    Line(points = {{46, 109}, {20, 109}, {20, 107}, {-6, 107}}, color = {0, 127, 255}));
  connect(Pipe_FI272_Tee7.port_b, Tee7.port_3) annotation(
    Line(points = {{-16, 107}, {-16, 108}, {-81, 108}, {-81, 104}}, color = {0, 127, 255}));
  connect(Tee7.port_1, pipe_Tee7_V206.port_a) annotation(
    Line(points = {{-86, 99}, {-86, 95.5}, {-89, 95.5}, {-89, 92}}, color = {0, 127, 255}));
  connect(pipe_Tee7_V206.port_b, V204.port_a) annotation(
    Line(points = {{-89, 82}, {-89, 79}, {-88, 79}, {-88, 76}}, color = {0, 127, 255}));
  connect(Tee7.port_2, Pipe_Tee7_Tee8.port_a) annotation(
    Line(points = {{-76, 99}, {-70, 99}}, color = {0, 127, 255}));
  connect(Pipe_Tee7_Tee8.port_b, Tee8.port_2) annotation(
    Line(points = {{-60, 99}, {-54, 99}}, color = {0, 127, 255}));
  connect(Tee8.port_1, pipe_Tee8_V206.port_a) annotation(
    Line(points = {{-44, 99}, {-44, 100}, {-15, 100}, {-15, 90}}, color = {0, 127, 255}));
  connect(PI253.port, pipe_B203_V203.port_b) annotation(
    Line(points = {{-26, 0}, {-14, 0}}, color = {0, 127, 255}));
  connect(PI252.port, pipe_B202_V202.port_b) annotation(
    Line(points = {{-62, 0}, {-50, 0}}, color = {0, 127, 255}));
  connect(PI251.port, pipe_B201_V201.port_b) annotation(
    Line(points = {{-102, 0}, {-88, 0}}, color = {0, 127, 255}));
  connect(TI262.port, pipe_V203_Tee2.port_b) annotation(
    Line(points = {{-18, -42}, {-18, -43}, {-24, -43}, {-24, -21}}, color = {0, 127, 255}));
  connect(PI254.port, Pipe_B204_P202.port_b) annotation(
    Line(points = {{70, 0}, {60, 0}, {60, -2}, {48, -2}}, color = {0, 127, 255}));
  connect(LA205_RB.u, LI214.y) annotation(
    Line(points = {{99, 26}, {91.5, 26}, {91.5, 36}, {66, 36}}, color = {0, 0, 127}));
  connect(LA204_RB.u, LI214.y) annotation(
    Line(points = {{100, 16}, {92, 16}, {92, 36}, {66, 36}}, color = {0, 0, 127}));
  connect(LA205_RB.y, LA205.activePort) annotation(
    Line(points = {{108, 26}, {113, 26}}, color = {255, 0, 255}));
  connect(LA204_RB.y, LA204.activePort) annotation(
    Line(points = {{108, 16}, {114, 16}}, color = {255, 0, 255}));
  connect(LA240_RB.y, LA240.activePort) annotation(
    Line(points = {{108, 36}, {114, 36}}, color = {255, 0, 255}));
  connect(LA240_RB.u, LI214.y) annotation(
    Line(points = {{100, 36}, {66, 36}}, color = {0, 0, 127}));
  connect(LA210_RB.u, LI211.y) annotation(
    Line(points = {{-99, 33}, {-99, 40}, {-100, 40}}, color = {0, 0, 127}));
  connect(LA210.activePort, LA210_RB.y) annotation(
    Line(points = {{-106, 32}, {-106, 33}}, color = {255, 0, 255}));
  connect(LA201_RB.u, LI211.y) annotation(
    Line(points = {{-99, 25}, {-99, 40}, {-100, 40}}, color = {0, 0, 127}));
  connect(LA201.activePort, LA201_RB.y) annotation(
    Line(points = {{-106, 24}, {-106.3, 24}, {-106.3, 25}, {-106, 25}}, color = {255, 0, 255}));
  connect(LA220.activePort, LA220_RB.y) annotation(
    Line(points = {{-68, 32}, {-68, 33}}, color = {255, 0, 255}));
  connect(LA202.activePort, LA202_RB.y) annotation(
    Line(points = {{-68, 24}, {-68, 25}}, color = {255, 0, 255}));
  connect(LA230.activePort, LA230_RB.y) annotation(
    Line(points = {{-32, 32}, {-31, 32}, {-31, 33}, {-30, 33}}, color = {255, 0, 255}));
  connect(LA203.activePort, LA203_RB.y) annotation(
    Line(points = {{-32, 24}, {-31, 24}, {-31, 25}, {-30, 25}}, color = {255, 0, 255}));
  connect(LA230_RB.u, LI213.y) annotation(
    Line(points = {{-23, 33}, {-23, 40}, {-24, 40}}, color = {0, 0, 127}));
  connect(LA203_RB.u, LI213.y) annotation(
    Line(points = {{-23, 25}, {-23, 40}, {-24, 40}}, color = {0, 0, 127}));
  connect(LA220_RB.u, LI212.y) annotation(
    Line(points = {{-61, 33}, {-61, 40}, {-62, 40}}, color = {0, 0, 127}));
  connect(LA202_RB.u, LI212.y) annotation(
    Line(points = {{-61, 25}, {-61, 40}, {-62, 40}}, color = {0, 0, 127}));
  connect(TI261.port, Pipe_B204_P202.port_a) annotation(
    Line(points = {{70, 14}, {62, 14}, {62, 8}, {48, 8}}, color = {0, 127, 255}));
  connect(pipe_P201_FI271.port_b, FI271.port_a) annotation(
    Line(points = {{13, -42}, {13, -37}, {15, -37}, {15, -34}}, color = {0, 127, 255}));
  connect(pipe_P201_FI271.port_a, P201.port_b) annotation(
    Line(points = {{13, -52}, {13, -57}, {-2, -57}}, color = {0, 127, 255}));
  connect(FI271.port_b, pipe_FI271_B204.port_a) annotation(
    Line(points = {{15, -20}, {15, -13}, {14, -13}, {14, -6}}, color = {0, 127, 255}));
  connect(pipe_FI271_B204.port_b, tank_B204.topPorts[1]) annotation(
    Line(points = {{14, 6}, {14, 42}, {48, 42}, {48, 36}}, color = {0, 127, 255}));
  connect(ActuatorControl.y[1], V201.opening) annotation(
    Line(points = {{-129, -6}, {-92, -6}, {-92, -12}, {-93, -12}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[2], V202.opening) annotation(
    Line(points = {{-129, -6}, {-54.5, -6}, {-54.5, -12}, {-53, -12}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[3], V203.opening) annotation(
    Line(points = {{-129, -6}, {-19.5, -6}, {-19.5, -12}, {-19, -12}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[6], V206.opening) annotation(
    Line(points = {{-129, -6}, {-122, -6}, {-122, 60}, {-20.5, 60}, {-20.5, 68}, {-19, 68}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[5], V205.opening) annotation(
    Line(points = {{-129, -6}, {-122, -6}, {-122, 60}, {-54, 60}, {-54, 68}, {-55, 68}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[4], V204.opening) annotation(
    Line(points = {{-129, -6}, {-122, -6}, {-122, 60}, {-92, 60}, {-92, 70}, {-93, 70}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[7], V209.opening) annotation(
    Line(points = {{-129, -6}, {-129, -5.5}, {-121, -5.5}, {-121, -70}, {120, -70}, {120, -15}}, color = {0, 0, 127}));
  connect(P202_Characteristic.y, P202.N_in) annotation(
    Line(points = {{65, -32}, {65, -35}, {66, -35}, {66, -38}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[9], P202_Characteristic.u) annotation(
    Line(points = {{-128, -6}, {-122, -6}, {-122, -70}, {56, -70}, {56, -25}, {65, -25}}, color = {0, 0, 127}));
  connect(P201_Characteristic.y, P201.N_in) annotation(
    Line(points = {{-7, -46}, {-6, -46}, {-6, -50}, {-8, -50}}, color = {0, 0, 127}));
  connect(ActuatorControl.y[8], P201_Characteristic.u) annotation(
    Line(points = {{-128, -6}, {-122, -6}, {-122, -70}, {4, -70}, {4, -39}, {-7, -39}}, color = {0, 0, 127}));
 connect(Pipe_B204_P202.port_b, P202.port_a) annotation(
    Line(points = {{48, -2}, {48, -44}, {58, -44}}, color = {0, 127, 255}));
 connect(Overflow_pipe.port_b, Overflow.ports[1]) annotation(
    Line(points = {{32, 72}, {32, 78}}, color = {0, 127, 255}));
 connect(Overflow_pipe.port_a, tank_B201.ports[2]) annotation(
    Line(points = {{32, 56}, {32, 46}, {4, 46}, {4, 20}, {-88, 20}}, color = {0, 127, 255}));

  annotation(
    uses(Modelica(version = "4.0.0")),
 //good results with IDA, max 1 Integration and 1 Processor. Still need to figure out optimal solver setup
 // cvode produces veery fast results
    Diagram(coordinateSystem(extent = {{-160, 120}, {160, -100}})),
    version = "",
    experiment(StartTime = 0, StopTime = 600, Tolerance = 1e-05, Interval = 1),
    __OpenModelica_commandLineOptions = "--matchingAlgorithm=PFPlusExt --indexReductionMethod=dynamicStateSelection -d=initialization,NLSanalyticJacobian",
    __OpenModelica_simulationFlags(lv = "LOG_STATS", s = "cvode", outputFormat=csv, variableFilter = ".*level|.*flow|.*opening|.*p|.*N.*y"));
end ModVA_online_stable;
