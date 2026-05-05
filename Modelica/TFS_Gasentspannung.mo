model TFS_Gasentspannung
  replaceable package Medium = ThermofluidStream.Media.myMedia.IdealGases.MixtureGases.SimpleNaturalGas;
  replaceable package Medium_Water = ThermofluidStream.Media.myMedia.Water.StandardWaterOnePhase;
  ThermofluidStream.Boundaries.Source source(redeclare package Medium = Medium, temperatureFromInput = true, T0_par = 293.15, p0_par = 5000000, pressureFromInput = true) annotation(
    Placement(transformation(origin = {-102, 18}, extent = {{-110, -10}, {-90, 10}})));
  ThermofluidStream.Boundaries.Sink sink(redeclare package Medium = Medium, p0_par = 100000) annotation(
    Placement(transformation(origin = {56, 18}, extent = {{90, -10}, {110, 10}})));
  ThermofluidStream.Processes.FlowResistance Pipe_Input_Filter(redeclare package Medium = Medium, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, r = 0.0052, l = 0.1, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss(k = 1e4)) annotation(
    Placement(transformation(origin = {-102, 18}, extent = {{-84, -10}, {-64, 10}})));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_Output(redeclare package Medium = Medium, digits = 3, temperatureUnit = "degC", outputMassFlowRate = true) annotation(
    Placement(transformation(origin = {56, 18}, extent = {{54, 0}, {74, 20}})));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_Input(redeclare package Medium = Medium, digits = 3, temperatureUnit = "degC") annotation(
    Placement(transformation(origin = {-104, 18}, extent = {{-58, 0}, {-38, 20}})));
  inner ThermofluidStream.DropOfCommons dropOfCommons annotation(
    Placement(transformation(origin = {-208, 194}, extent = {{78, -96}, {98, -76}})));
  /*
                                                                                                                                                                Utilities.showRealValue showRealValue(
                                                                                                                                                                  use_numberPort=false,
                                                                                                                                                                  description="Re",
                                                                                                                                                                  number=thermalConvection.Re_D,
                                                                                                                                                                  significantDigits=1)
                                                                                                                                                                  annotation (Placement(transformation(extent={{-28,-8},{-8,-28}})));
                                                                                                                                                                Utilities.showRealValue showRealValue1(
                                                                                                                                                                  use_numberPort=false,
                                                                                                                                                                  description="v_m",
                                                                                                                                                                  number=thermalConvection.v_m)
                                                                                                                                                                  annotation (Placement(transformation(extent={{10,-8},{30,-28}})));
                                                                                                                                                                  */
  ThermofluidStream.Processes.ThermalConvectionPipe Pipe_Choke_Valve_Output_Thermal(redeclare package Medium = Medium, r = 0.005, l = 100, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.none) annotation(
    Placement(transformation(origin = {58, 18}, extent = {{26, -10}, {46, 10}})));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_Pre_Heat_Exchanger(redeclare package Medium = Medium, digits = 3, temperatureUnit = "degC") annotation(
    Placement(transformation(origin = {-112, 18}, extent = {{0, 0}, {26, 20}})));
  ThermofluidStream.FlowControl.BasicControlValve Choke_Valve(redeclare package Medium = Medium, k_min = 0.0001, Kvs = 50) annotation(
    Placement(transformation(origin = {44, 18}, extent = {{-10, -10}, {10, 10}})));
  ThermofluidStream.FlowControl.BasicControlValve Filter(Kvs = 1000, redeclare package Medium = Medium, k_min = 0.0001) annotation(
    Placement(transformation(origin = {-126, 18}, extent = {{-10, -10}, {10, 10}})));
  ThermofluidStream.Processes.FlowResistance Pipe_Choke_Valve_Output(redeclare package Medium = Medium, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, l = 1.673, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss, r = 0.05) annotation(
    Placement(transformation(origin = {142, 18}, extent = {{-84, -10}, {-64, 10}})));
  ThermofluidStream.Processes.FlowResistance Pipe_Heat_Exchanger_Choke_Valve(redeclare package Medium = Medium, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, l = 2.048, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss, r = 0.0052) annotation(
    Placement(transformation(origin = {92, 18}, extent = {{-84, -10}, {-64, 10}})));
  ThermofluidStream.HeatExchangers.CounterFlowNTU Heat_Exchanger(redeclare package MediumA = Medium, redeclare package MediumB = Medium_Water, A = 10, k_NTU = 120) annotation(
    Placement(transformation(origin = {-36, 24}, extent = {{-10, -10}, {10, 10}})));
  ThermofluidStream.Boundaries.Source Source_Water(p0_par = 200000, redeclare package Medium = Medium_Water, T0_par = 333.15, temperatureFromInput = true) annotation(
    Placement(transformation(origin = {-22, 144}, extent = {{10, -10}, {-10, 10}}, rotation = 90)));
  ThermofluidStream.Boundaries.Sink Sink_Water(p0_par = 499999.9999999999, redeclare package Medium = Medium_Water) annotation(
    Placement(transformation(origin = {-56, 144}, extent = {{10, -10}, {-10, 10}}, rotation = -90)));
  ThermofluidStream.Processes.Pump pump(redeclare package Medium = Medium_Water, redeclare function dp_tau_pump = ThermofluidStream.Processes.Internal.TurboComponent.dp_tau_centrifugal, omega_from_input = true) annotation(
    Placement(transformation(origin = {-22, 120}, extent = {{10, -10}, {-10, 10}}, rotation = 90)));
  ThermofluidStream.FlowControl.Switch ThreeWayValve(redeclare package Medium = Medium_Water) annotation(
    Placement(transformation(origin = {-22, 96}, extent = {{10, -10}, {-10, 10}}, rotation = 90)));
  ThermofluidStream.Topology.JunctionT2 junctionT2(redeclare package Medium = Medium_Water) annotation(
    Placement(transformation(origin = {-56, 96}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_post_Heat_Exchanger(redeclare package Medium = Medium, digits = 3, temperatureUnit = "degC") annotation(
    Placement(transformation(origin = {-18, 18}, extent = {{0, 0}, {26, 20}})));
  Modelica.Blocks.Sources.CombiTimeTable ThreeWayValve_Input(extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint, smoothness = Modelica.Blocks.Types.Smoothness.LinearSegments, table = [0.0, 0.37; 111.1, 0.21; 222.2, 0.44; 333.3, 0.12; 444.4, 0.28; 555.6, 0.33; 666.7, 0.49; 777.8, 0.17; 888.9, 0.41; 1000.0, 0.24], tableOnFile = false, tableName = "ThreeWayValve_Input", fileName = "D:/WMA/06 Implementierungen/git_Projekte/AVEDAS/Modelica/Timetables/ThreeWayValve_Input.txt") annotation(
    Placement(transformation(origin = {32, 96}, extent = {{10, -10}, {-10, 10}})));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_Water_Pre_Heat_Exchanger(redeclare package Medium = Medium_Water, digits = 3, temperatureUnit = "degC") annotation(
    Placement(transformation(origin = {-22, 60}, extent = {{0, 0}, {-26, -20}}, rotation = -270)));
  ThermofluidStream.Sensors.MultiSensor_Tpm Multisensor_Water_Post_Heat_Exchanger(redeclare package Medium = Medium_Water, digits = 3, temperatureUnit = "degC") annotation(
    Placement(transformation(origin = {-56, 32}, extent = {{0, 0}, {-26, -20}}, rotation = 270)));
  ThermofluidStream.Processes.FlowResistance Pipe_Filter_Heat_Exchanger(redeclare package Medium = Medium, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, l = 1.27, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss, r = 0.0052) annotation(
    Placement(transformation(origin = {6, 18}, extent = {{-84, -10}, {-64, 10}})));
  ThermofluidStream.Processes.FlowResistance Pipe_Water_pre_Heat_Exchanger(redeclare package Medium = Medium_Water, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, l = 1.37, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss, r = 0.052) annotation(
    Placement(transformation(origin = {-22, -4}, extent = {{-84, -10}, {-64, 10}}, rotation = -90)));
  ThermofluidStream.Processes.FlowResistance Pipe_Water_pre_Heat_Exchanger1(redeclare package Medium = Medium_Water, initM_flow = ThermofluidStream.Utilities.Types.InitializationMethods.state, l = 1.37, redeclare function pLoss = ThermofluidStream.Processes.Internal.FlowResistance.linearQuadraticPressureLoss, r = 0.0052) annotation(
    Placement(transformation(origin = {-56, 144}, extent = {{-84, -10}, {-64, 10}}, rotation = 90)));
  Modelica.Blocks.Sources.CombiTimeTable Choke_Valve_Input(extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint, smoothness = Modelica.Blocks.Types.Smoothness.LinearSegments, table = [0.0, 0.003; 52.6, 0.012; 105.3, 0.025; 157.9, 0.03; 210.5, 0.022; 263.2, 0.009; 315.8, 0.035; 368.4, 0.048; 421.1, 0.02; 473.7, 0.045; 526.3, 0.018; 578.9, 0.04; 631.6, 0.015; 684.2, 0.033; 736.8, 0.049; 789.5, 0.027; 842.1, 0.05; 894.7, 0.019; 947.4, 0.042; 1000.0, 0.031], tableOnFile = false, tableName = "Choke_Valve_Input", fileName = "D:/WMA/06 Implementierungen/git_Projekte/AVEDAS/Modelica/Timetables/Choke_Valve_Input.txt") annotation(
    Placement(transformation(origin = {24, 38}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Blocks.Sources.CombiTimeTable Water_Input_Conditions(extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint, smoothness = Modelica.Blocks.Types.Smoothness.LinearSegments, table = [0.0, 338.2, 997.4; 29.4, 335.5, 1006.3; 58.8, 332.6, 991.1; 88.2, 337.7, 998.9; 117.6, 334.3, 1003.7; 147.1, 330.4, 990.9; 176.5, 331.2, 995.8; 205.9, 329.1, 1001.5; 235.3, 338.6, 1000.3; 264.7, 333.4, 1007.6; 294.1, 328.2, 992.5; 323.5, 331.9, 1009.1; 352.9, 330.8, 996.4; 382.4, 327.7, 1003.9; 411.8, 339.3, 994.7; 441.2, 326.5, 1006.1; 470.6, 332.9, 993.8; 500.0, 336.1, 1005.2; 529.4, 328.6, 999.6; 558.8, 327.1, 1007.4; 588.2, 336.8, 996.8; 617.6, 334.7, 1002.5; 647.1, 333.2, 991.7; 676.5, 339.8, 1008.9; 705.9, 330.1, 993.1; 735.3, 329.4, 1004.6; 764.7, 338.7, 995.3; 794.1, 331.5, 1009.8; 823.5, 333.9, 990.2; 852.9, 335.2, 998.5; 882.4, 328.9, 1007.1; 911.8, 327.4, 994.1; 941.2, 326.7, 1002.2; 970.6, 337.4, 996.2; 1000.0, 330.0, 1005.9], tableOnFile = false, tableName = "Water_Input_Conditions", fileName = "D:/WMA/06 Implementierungen/git_Projekte/AVEDAS/Modelica/Timetables/Water_Input_Conditions.txt") annotation(
    Placement(transformation(origin = {32, 126}, extent = {{10, -10}, {-10, 10}})));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow Heat_Loss_Choke_Valve(T_ref = 293.15, alpha = 120) annotation(
    Placement(transformation(origin = {104, 48}, extent = {{10, -10}, {-10, 10}})));
  Modelica.Blocks.Math.Gain corrective_factor(k = -25) annotation(
    Placement(transformation(origin = {127, 49}, extent = {{-5, -5}, {5, 5}}, rotation = 180)));
  Modelica.Blocks.Sources.CombiTimeTable Input_Conditions(extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint, smoothness = Modelica.Blocks.Types.Smoothness.LinearSegments, table = [0.0, 293.15, 6000000.0; 34.5, 294.37, 5920000.0; 69.0, 296.22, 5830000.0; 103.4, 297.95, 5750000.0; 137.9, 295.88, 5670000.0; 172.4, 298.76, 5600000.0; 206.9, 300.54, 5520000.0; 241.4, 301.87, 5440000.0; 275.9, 299.15, 5360000.0; 310.3, 296.77, 5280000.0; 344.8, 295.22, 5200000.0; 379.3, 294.0, 5120000.0; 413.8, 296.9, 5050000.0; 448.3, 298.2, 4970000.0; 482.8, 299.4, 4890000.0; 517.2, 300.85, 4810000.0; 551.7, 302.1, 4730000.0; 586.2, 301.0, 4660000.0; 620.7, 298.75, 4580000.0; 655.2, 297.1, 4500000.0; 689.7, 295.3, 4550000.0; 724.1, 294.15, 4600000.0; 758.6, 296.6, 4700000.0; 793.1, 297.95, 4800000.0; 827.6, 299.1, 4900000.0; 862.1, 301.2, 5000000.0; 896.6, 302.9, 5100000.0; 931.0, 301.5, 5200000.0; 965.5, 299.4, 5300000.0; 1000.0, 297.25, 5400000.0], tableOnFile = false, tableName = "Input_Conditions", fileName = "D:/WMA/06 Implementierungen/git_Projekte/AVEDAS/Modelica/Timetables/Input_Conditions.txt") annotation(
    Placement(transformation(origin = {-222, 18}, extent = {{-10, -10}, {10, 10}})));
  Modelica.Blocks.Sources.Ramp filter_clogging(height = 0.00, duration = 500, offset = 0.025, startTime = 0)  annotation(
    Placement(transformation(origin = {-152, 54}, extent = {{-10, -10}, {10, 10}})));
equation
  connect(sink.inlet, Multisensor_Output.outlet) annotation(
    Line(points = {{146, 18}, {130, 18}}, color = {28, 108, 200}, thickness = 0.5));
  connect(Pipe_Input_Filter.outlet, Multisensor_Input.inlet) annotation(
    Line(points = {{-166, 18}, {-162, 18}}, color = {28, 108, 200}, thickness = 0.5));
  connect(Multisensor_Output.inlet, Pipe_Choke_Valve_Output_Thermal.outlet) annotation(
    Line(points = {{110, 18}, {104, 18}}, color = {28, 108, 200}, thickness = 0.5));
  connect(Filter.outlet, Multisensor_Pre_Heat_Exchanger.inlet) annotation(
    Line(points = {{-116, 18}, {-112, 18}}, color = {28, 108, 200}));
  connect(Pipe_Choke_Valve_Output.outlet, Pipe_Choke_Valve_Output_Thermal.inlet) annotation(
    Line(points = {{78, 18}, {84, 18}}, color = {28, 108, 200}));
  connect(Pipe_Choke_Valve_Output.inlet, Choke_Valve.outlet) annotation(
    Line(points = {{58, 18}, {54, 18}}, color = {28, 108, 200}));
  connect(Pipe_Heat_Exchanger_Choke_Valve.outlet, Choke_Valve.inlet) annotation(
    Line(points = {{28, 18}, {34, 18}}, color = {28, 108, 200}));
  connect(Filter.inlet, Multisensor_Input.outlet) annotation(
    Line(points = {{-136, 18}, {-142, 18}}, color = {28, 108, 200}));
  connect(Source_Water.outlet, pump.inlet) annotation(
    Line(points = {{-22, 134}, {-22, 130}}, color = {28, 108, 200}));
  connect(junctionT2.outlet, Sink_Water.inlet) annotation(
    Line(points = {{-56, 106}, {-56, 134}}, color = {28, 108, 200}));
  connect(pump.outlet, ThreeWayValve.inlet) annotation(
    Line(points = {{-22, 110}, {-22, 106}}, color = {28, 108, 200}));
  connect(ThreeWayValve.outletB, junctionT2.inletA) annotation(
    Line(points = {{-32, 96}, {-46, 96}}, color = {28, 108, 200}));
  connect(Heat_Exchanger.outletA, Multisensor_post_Heat_Exchanger.inlet) annotation(
    Line(points = {{-26, 18}, {-18, 18}}, color = {28, 108, 200}));
  connect(Multisensor_post_Heat_Exchanger.outlet, Pipe_Heat_Exchanger_Choke_Valve.inlet) annotation(
    Line(points = {{8, 18}, {8, 18}}, color = {28, 108, 200}));
  connect(Multisensor_Water_Pre_Heat_Exchanger.outlet, Heat_Exchanger.inletB) annotation(
    Line(points = {{-22, 34}, {-26, 34}, {-26, 30}}, color = {28, 108, 200}));
  connect(Multisensor_Water_Post_Heat_Exchanger.inlet, Heat_Exchanger.outletB) annotation(
    Line(points = {{-56, 32}, {-46, 32}, {-46, 30}}, color = {28, 108, 200}));
  connect(source.outlet, Pipe_Input_Filter.inlet) annotation(
    Line(points = {{-192, 18}, {-186, 18}}, color = {28, 108, 200}));
  connect(Multisensor_Pre_Heat_Exchanger.outlet, Pipe_Filter_Heat_Exchanger.inlet) annotation(
    Line(points = {{-86, 18}, {-78, 18}}, color = {28, 108, 200}));
  connect(Pipe_Filter_Heat_Exchanger.outlet, Heat_Exchanger.inletA) annotation(
    Line(points = {{-58, 18}, {-46, 18}}, color = {28, 108, 200}));
  connect(ThreeWayValve.outletA, Pipe_Water_pre_Heat_Exchanger.inlet) annotation(
    Line(points = {{-22, 86}, {-22, 80}}, color = {28, 108, 200}));
  connect(Pipe_Water_pre_Heat_Exchanger.outlet, Multisensor_Water_Pre_Heat_Exchanger.inlet) annotation(
    Line(points = {{-22, 60}, {-22, 60}}, color = {28, 108, 200}));
  connect(Multisensor_Water_Post_Heat_Exchanger.outlet, Pipe_Water_pre_Heat_Exchanger1.inlet) annotation(
    Line(points = {{-56, 58}, {-56, 60}}, color = {28, 108, 200}));
  connect(Pipe_Water_pre_Heat_Exchanger1.outlet, junctionT2.inletB) annotation(
    Line(points = {{-56, 80}, {-56, 86}}, color = {28, 108, 200}));
  connect(Choke_Valve_Input.y[1], Choke_Valve.u_in) annotation(
    Line(points = {{35, 38}, {45, 38}, {45, 26}, {43, 26}}, color = {0, 0, 127}));
  connect(Heat_Loss_Choke_Valve.port, Pipe_Choke_Valve_Output_Thermal.heatPort) annotation(
    Line(points = {{94, 48}, {94, 28}}, color = {191, 0, 0}));
  connect(Multisensor_Output.m_flow_out, corrective_factor.u) annotation(
    Line(points = {{130, 22}, {140, 22}, {140, 49}, {133, 49}}, color = {0, 0, 127}));
  connect(corrective_factor.y, Heat_Loss_Choke_Valve.Q_flow) annotation(
    Line(points = {{121.5, 49}, {118, 49}, {118, 48}, {114, 48}}, color = {0, 0, 127}));
  connect(Input_Conditions.y[1], source.T0_var) annotation(
    Line(points = {{-210, 18}, {-204, 18}}, color = {0, 0, 127}));
  connect(Input_Conditions.y[2], source.p0_var) annotation(
    Line(points = {{-210, 18}, {-208, 18}, {-208, 24}, {-204, 24}}, color = {0, 0, 127}));
  connect(Water_Input_Conditions.y[1], Source_Water.T0_var) annotation(
    Line(points = {{21, 126}, {-8, 126}, {-8, 146}, {-22, 146}}, color = {0, 0, 127}));
  connect(Water_Input_Conditions.y[2], pump.omega_input) annotation(
    Line(points = {{21, 126}, {4.5, 126}, {4.5, 120}, {-12, 120}}, color = {0, 0, 127}));
  connect(ThreeWayValve_Input.y[1], ThreeWayValve.u) annotation(
    Line(points = {{22, 96}, {-14, 96}}, color = {0, 0, 127}));
  connect(filter_clogging.y, Filter.u_in) annotation(
    Line(points = {{-140, 54}, {-126, 54}, {-126, 26}}, color = {0, 0, 127}));
  annotation(
    Icon(coordinateSystem(preserveAspectRatio = false)),
    Diagram(coordinateSystem(preserveAspectRatio = false, extent = {{-240, 160}, {180, -60}}), graphics = {Text(origin = {-125, 15}, rotation = 90, extent = {{-8, 6}, {8, -6}}, textString = "Filter", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-175, 25}, rotation = 90, extent = {{-17, 3}, {17, -3}}, textString = "Pipe_Input_Filter", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-152, 26}, rotation = 90, extent = {{-18, 4}, {18, -4}}, textString = "Multisensor_Input", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-36, 46}, rotation = 90, extent = {{-39, 1}, {39, -1}}, textString = "Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-5, 51}, rotation = 90, extent = {{-44, 2}, {44, -2}}, textString = "Multisensor_post_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {18, 43}, rotation = 90, extent = {{-36, 3}, {36, -3}}, textString = "Pipe_Heat_Exchanger_Choke_Valve", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {44, 29}, rotation = 90, extent = {{-22, 3}, {22, -3}}, textString = "Choke_Valve", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {70, 37}, rotation = 90, extent = {{-29, 4}, {29, -4}}, textString = "Pipe_Choke_Valve_Output", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {95, 47}, rotation = 90, extent = {{-39, 3}, {39, -3}}, textString = "Pipe_Choke_Valve_Output_Thermal", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {122, -20}, rotation = -90, extent = {{-27, -3}, {27, 3}}, textString = "Multisensor_Output", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {8, 90}, extent = {{-26, 2}, {26, -2}}, textString = "ThreeWayValve", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-89, 60}, rotation = 180, extent = {{42, 3}, {-42, -3}}, textString = "Multisensor_Water_post_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {31, 61}, extent = {{-47, 3}, {47, -3}}, textString = "Multisensor_Water_pre_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-67, 50}, rotation = 90, extent = {{-43, 2}, {43, -2}}, textString = "Pipe_Filter_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {25, 75}, extent = {{-41, 3}, {41, -3}}, textString = "Pipe_Water_pre_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-85, 75}, extent = {{-35, 3}, {35, -3}}, textString = "Pipe_Water_post_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left), Text(origin = {-99, 47}, rotation = 90, extent = {{-39, 3}, {39, -3}}, textString = "Multisensor_Pre_Heat_Exchanger", fontSize = 12, horizontalAlignment = TextAlignment.Left)}),
    experiment(StopTime = 1000, Tolerance = 1e-06, Interval = 1, StartTime = 0),
    Documentation(info = "<html>
        <p>Owner: <a >Malte Ramonat</a></p>
</html>"),
    uses(ThermofluidStream(version = "1.1.0"), Modelica(version = "4.0.0")),
    version = "");
end TFS_Gasentspannung;
