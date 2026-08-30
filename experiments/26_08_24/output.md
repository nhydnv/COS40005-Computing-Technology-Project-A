## FUNCTIONAL DESCRIPTION

## 1. Air Conditioning

## 1.1. FCU/VRV System (Variable Refrigerant Volume Units)

## 1.1.1. System Overview

The  BMS  monitors  and  controls  20-off  Variable  Refrigerant  Volume  (VRV)  units  which  serve  Swinburne Universities UN building's 'late lab' via Daikin BACnet gateway (provided by others), communicating with each individual VRV unit through high-level interface (HLI). Each VRV will have an associated outdoor unit to provide the appropriate heating and cooling to the specified zones. These VRV units will operate in conjunction with energy  recovery  ventilators  to  provide  air  comfort  and  fresh  air  control  in  addition  to  heating  and  cooling requirements. VRVs will be grouped in their respective zones (floors) and be controlled as zones as opposed to individual VRVs.

## 1.1.2. Gateway Devices

| DESCRIPTION    |   DEVICE INSTANCE | IP ADDRESS   | SUBNET MASK   | LOCATION                                    |
|----------------|-------------------|--------------|---------------|---------------------------------------------|
| Daikin Gateway |              7200 | 172.22.33.13 | 255.255.255.0 | MSSB-L4 (Level 4 Mechanical Services Riser) |
| Abakus Server  |             10101 | 172.22.33.16 | 255.255.255.0 | Level 3 DDC Panel Location                  |

## 1.1.3. Controlled Equipment

| UNIT           | ASSOCI ATED OUTDOOR UNIT   | MODE L/ SE RIES   | LOCATION         | CO MMENT   |
|----------------|----------------------------|-------------------|------------------|------------|
| Level 1        | Level 1                    | Level 1           | Level 1          | Level 1    |
| H-LL-FCU-L1.W1 | H-LL-CU-1.1                | FXMQ/REY          | Student Lounge   |            |
| H-LL-FCU-L1.N1 | H-LL-CU-1.1                | FXMQ/REY          | Student Lounge   |            |
| H-LL-FCU-L1.N2 | H-LL-CU-1.1                | FXMQ/REY          | Student Lounge   |            |
| H-LL-FCU-L1.I1 | H-LL-CU-1.1                | FXMQ/REY          | Student Lounge   |            |
| H-LL-FCU-L1.I2 | H-LL-CU-1.1                | FXMQ/REY          | Informal Seating |            |
| Level 2        | Level 2                    | Level 2           | Level 2          | Level 2    |

| UNIT           | ASSOCI ATED OUTDOOR UNIT   | MODE L/ SE RIES   | LOCATION          | CO MMENT   |
|----------------|----------------------------|-------------------|-------------------|------------|
| H-LL-FCU-L2.W1 |                            | FXMQ/REY          | Student Work Zone |            |
| H-LL-FCU-L2.N1 |                            | FXMQ/REY          | Student Work Zone |            |
| H-LL-FCU-L2.N3 |                            | FXMQ/REY          | Project Booth     |            |
| H-LL-FCU-L2.I1 | H-LL-CU-2.1                | FXMQ/REY          | Student Work Zone |            |
| H-LL-FCU-L2.I2 |                            | FXMQ/REY          | Student Work Zone |            |
| H-LL-FCU-L2.P1 |                            | FXMQ/REY          | Project Room      |            |
| H-LL-FCU-L2.P2 |                            | FXMQ/REY          | Project Room      |            |
| Level 3        | Level 3                    | Level 3           | Level 3           | Level 3    |
| H-LL-FCU-L3.W1 | H-LL-CU-3.1                | FXMQ/REY          | Student Kitchen   |            |
| H-LL-FCU-L3.N1 | H-LL-CU-3.1                | FXMQ/REY          | Student Kitchen   |            |
| H-LL-FCU-L3.E1 | H-LL-CU-3.1                | FXMQ/REY          | Student Kitchen   |            |
| H-LL-FCU-L3.I1 | H-LL-CU-3.1                | FXMQ/REY          | Student Kitchen   |            |
| LEVEL 4        | LEVEL 4                    | LEVEL 4           | LEVEL 4           | LEVEL 4    |
| H-LL-FCU-L4.N1 | H-LL-CU-4.1                | FXMQ/REY          | Event Space       |            |
| H-LL-FCU-L4.I1 | H-LL-CU-4.1                | FXMQ/REY          | Event Space       |            |
| H-LL-FCU-L4.W1 | H-LL-CU-4.1                | FXMQ/REY          | Event Space       |            |
| H-LL-FCU-L4.E1 | H-LL-CU-4.1                | FXMQ/REY          | Event Space       |            |

## 1.1.4. Points List (for each VRV unit)

| POINTS                 | BI   | AI   | BO   | AO   | MO   |   HLI | CO MMENTS          |
|------------------------|------|------|------|------|------|-------|--------------------|
| Unit Enable            |      |      |      |      |      |     1 | Via Daikin Gateway |
| Unit Status            |      |      |      |      |      |     1 | Via Daikin Gateway |
| Unit Fault             |      |      |      |      |      |     1 | Via Daikin Gateway |
| Operation Mode Setting |      |      |      |      |      |     1 | Via Daikin Gateway |
| Operation Mode Status  |      |      |      |      |      |     1 | Via Daikin Gateway |

| POINTS                        | BI      | AI      | BO      | AO      | MO      | HLI     | CO MMENTS                                                                                      |
|-------------------------------|---------|---------|---------|---------|---------|---------|------------------------------------------------------------------------------------------------|
| Zone Temperature              |         | 1       |         |         |         |         | 0-10V Active Output Signal (Belimo 22-RTM-19-1)                                                |
| Airflow Command               |         |         |         |         |         | 1       | Via Daikin Gateway                                                                             |
| Airflow Rate                  |         |         |         |         |         | 1       | Via Daikin Gateway                                                                             |
| Supply Air Temperature Sensor |         | 1       |         |         |         |         | 10K Type II Duct Mounted Temperature Sensor (Belimo 01DT-1LL)                                  |
| Return Air Temperature Sensor |         | 1       |         |         |         |         | 10K Type II Duct Mounted Temperature Sensor (Belimo 01DT-1LL)                                  |
| CO2 Sensor                    |         | 1       |         |         |         |         | 0-10V Active Output Signal (Belimo 22-RTM-19-1)                                                |
| Outside Air Damper Actuator   |         |         |         | 1       |         |         | 0-10V Modulating Damper Actuator                                                               |
| Level 1                       | Level 1 | Level 1 | Level 1 | Level 1 | Level 1 | Level 1 | Level 1                                                                                        |
| Window Open Status            |         | 1       |         |         |         |         | Via window reed switches on Level 1 Café windows                                               |
| Roof                          | Roof    | Roof    | Roof    | Roof    | Roof    | Roof    | Roof                                                                                           |
| Outside Air Temperature       |         | 1       |         |         |         |         | 10 Type II Wall Mounted Outdoor Temperature Sensor (Belimo 01UT-1L) (Mounted on H-LL-ERV-LR.1) |

## 1.1.5. Points List [People Counting System]

| POINTS                    |   BI |   AI | BO   | AO   | MO   | HLI   | CO MMENTS          |
|---------------------------|------|------|------|------|------|-------|--------------------|
| Sensor In                 |      |    1 |      |      |      |       | Via Abakus Gateway |
| Sensor Out                |      |    1 |      |      |      |       | Via Abakus Gateway |
| Sensor Status             |    1 |      |      |      |      |       | Via Abakus Gateway |
| Floor Occupancy           |      |    1 |      |      |      |       | Via Abakus Gateway |
| Building Occupancy        |      |    1 |      |      |      |       | Via Abakus Gateway |
| Floor Occupancy Status    |    1 |      |      |      |      |       | Via Abakus Gateway |
| Building Occupancy Status |    1 |      |      |      |      |       | Via Abakus Gateway |

## 1.1.6. Start/Stop Control

An VRV zone will be enabled when any of the following conditions are met:

- The time of the day is equal or past the units scheduled start time (initially set to 00:00-23:59 ~ 24 hours)

## AND

- The floor's occupancy status is active (determined via occupancy status from the lighting interface gateway)

OR

- Overridden ON via BMS front-end.

An VRV zone will be disabled when any of the following conditions are met:

- The time of the day is equal to or past the units scheduled stop time (initially set to 00:00-23:59 ~ 24 hours)

AND

- 25  mins  (adj.)  after  the floor's occupancy  has  been  deactivated  (determined  via  occupancy  status from the lighting interface gateway)

OR

- Overridden OFF via BMS front-end.

Notes:

- Although the 'late lab' will operate 24/7, the schedule is be programmed such that if there are any planned shut downs, the university could lockout the VRV operation via the BMS.

## 1.1.7. Temperature Control (Via People Counting System)

The FCU zone temperature control will operate in two modes: fixed setpoint control and floating temperature control, based on occupancy and window status conditions. The system will monitor the Abakus People Counter, Café window status, and floor occupancy status (as provided by the lighting control system).

When the floor occupancy status is ON, and either the Abakus People Count exceeds the adjustable setpoint of 5 people OR the Café window status is open, the FCU zone temperature will be controlled to a fixed setpoint of 22.5°C. This ensures consistent comfort conditions during periods of higher occupancy or when external air is introduced into the space.

In all other conditions, the FCU zone temperature will revert to a floating control strategy, maintaining the zone temperature within the defined limits of 20°C (heating threshold) and 24°C (cooling threshold). Within this range, no  active  heating  or  cooling  will  be  applied,  allowing  the  space  temperature  to  drift  for  improved  energy efficiency.

## 1.1.8. Warm Up Cycle

As  part  of  an  optimised  start  control,  each  VRV  unit  shall  utilise  the  control  of  their  respective  outside  air motorised damper to provide a warm up cycle based on the average indoor space temperature (on the respective floor) and ambient temperatures.

The following conditions needs to be satisfied before warm-up cycle is allowed to run:

- Ambient temperature is below 20°C (adjustable)
- When the average indoor space temperature is greater than 2°C (adj.) above the ambient temperature
- The zone/floor is calling for heating

Once all the above conditions are satisfied, the motorised outside air damper of the VRV unit will fully open. When each respective zone reaches 22°C (adj.), then that VRV unit will revert to its minimum outside air damper position and controls will revert to normal operation based on CO2 control (see section 1.1.9 CO2 Control)

## 1.1.9. Cool Down Cycle

Like the 'Warm Up Cycle,' each VRV unit shall utilise the control of their respective outside air motorised damper to provide a cool down cycle based on the average indoor space temperature and ambient temperatures.

Swinburne University UN Building -Revision: H

- Ambient temperature is above 16°C (adjustable)
- When the average indoor space temperature is less than 2°C (adj.) below the ambient temperature
- The zone/floor is calling for cooling

Once all the above conditions are satisfied, the motorised outside air damper of the VRV unit will fully open. When each respective zone reaches 22°C (adj.), then that VRV unit will revert to its minimum outside air damper position and controls will revert to normal operation based on CO2 control (see section 1.1.9 CO2 Control)

## 1.1.10. CO2 Control

In 'normal operation' the  BMS  will  modulate  each  VRV  zone  outside  air  damper  to  control  zone  CO2.  The outside air damper will be a its minimum outside air damper position until the zone CO2 reaches its minimum setpoint of 600 ppm (adj.) and will open proportionally to a maximum outside air damper position when the zone CO2 is equal to or greater than 800 ppm (adj.).

Fig. 1.1.9 Sample CO2 Damper Control. In this example, the minimum outside air damper position is commissioned at 40% open and the maximum outside air damper position at 80% open. Both parameters are adjustable on the BMS as required

<!-- image -->

## 1.1.11. Temperature Control

The temperature control for the 'Late Lab' building will be done in VRV grouped zones (as opposed to individual VRV control ~ i.e., average zone temperature for the entire floor is controlled by all associated VRVs). Each zone will  have  a  desired  zone  temperature  setpoint  with  adjustable  deadband  (initially  set  to  1.5°C  (adj.)).  The operation mode will be determined by the zone temperature with respect to the zone temperature  setpoint. Each zone will have a desired temperature setpoint with an adjustable deadband; however, in line with client requirements, the control strategy will maintain the zone temperature within a defined range of 20°C to 24°C , allowing the temperature to float within this band under normal operating conditions.

Operation mode is set to heating when the zone temperature is below the zone temperature setpoint by more than the dead band. Likewise, operation mode is set to cooling when the zone temperature is above the zone temperature setpoint by more than the dead band.  The temperature setpoint will be either fixed or variable depending on the current thermal conditions called for (see Section 1.1.11 Occupied Mode Control)

Fig. 1.1.11 Variable Setpoint Control

<!-- image -->

Note -The zone temperature set point will scale linearly with building outside air temperature with both high and low temperature setpoint limits. The above shows an example of how zone temperature setpoint will vary.

## 1.1.12. VRV Outdoor Unit (CU) Integration

The VRV outdoor unit (condensing unit) serves all associated indoor units and is responsible for refrigerant flow, capacity control, and system mode operation. The CU is controlled by the manufacturer's proprietary controller (Daikin) and is not directly controlled by the BMS. The BMS provides control of indoor unit setpoints and operating conditions, which in turn generate load demand that the CU responds to accordingly.

## 1.1.13. Occupied Mode Control

There are 14 XOVIS people counting sensors placed at entry and exit points on each floor of the building and for each floor, the associated sensors' In Count and Out Count is aggregated.

The Occupancy is calculated as below:

## Total Floor In Count - Total Floor Out Count = Floor Occupancy

The 'total floor in count' will be used to adjust the thermal condition setpoints depending on the amount of people recorded to be in the floor. Specific details are as follows:

| Operation Mode (For Individual floors)                                                                          | Floor Occupancy from Lighting System   | HVAC Status   | Abakus People Count   | Thermal Conditions Type   | Thermal Conditions description                                                                                                      |
|-----------------------------------------------------------------------------------------------------------------|----------------------------------------|---------------|-----------------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| All hours                                                                                                       | ON                                     | ON            | >5                    | Narrow                    | Fixed setpoint of 22.5°C (adj.) with a deadband of 1.5°C (adj.)                                                                     |
| All hours                                                                                                       | ON                                     |               | ≤ 5                   | Wide                      | Variable setpoint of 19°C to 25°C (adj.) with a fixed deadband of 1.5°C (adj.) depending on ambient air temperatures.               |
| All hours                                                                                                       | OFF                                    | OFF           | NA                    | AC OFF                    | NA                                                                                                                                  |
| All hours (Café Window Open, Level 1 only). Note: café operator to open/close window/ as per licence agreement. | ON                                     | ON            | NA (any number)       | Wide                      | Level 1 only: Variable setpoint of 19°C to 25°C (adj.) with a fixed deadband of 1.5°C (adj.) depending on ambient air temperatures. |

## 1.1.14. Trend  and  Data  Logging

The BMS is monitoring and performing trend and data logging every 15 minutes. The following trend logs are visible and logged on the BMS:

- Unit Enable
- Unit Status
- Unit Fault
- Supply Air Temperature
- Return Air Temperature
- Zone Temperature Setpoint
- Zone Temperature
- Floor Occupancy

Swinburne University UN Building

-

- Building Occupancy
- Floor Occupancy Status
- Building Occupancy Status

Late Labs

## 1.1.15. Controller Failure / Alarms

In the event of power loss to the local controller, the VRV unit will stop operation; once power is reinstated,  the unit will commence operation in sequence (so long as the start/stop conditions are met) after a delayed time.

An alarm is generated when any of the following conditions are met after a delayed period:

- A fault signal is sent via Daikin gateway to the BMS.
- A BMS alarm will be raised when the café window is opened/kept open after the set hours

## 1.1.16. Fire  Mode

Typically, fire mode occurs when the MSSB receives a facility General Fire Alarm (GFA) directly from the facility. Fire  Indication  Panel  (FIP)  and  on  receipt  of  a  GFA,  the  VRV  units  should  be  disabled  directly  at  the corresponding MSSB. As this is hardwired to the unit, the BMS should have no control over this operation and will only monitor and mimic the fire mode operation to ensure that no false BMS alarms are raised.

## 1.2. Ceiling  Cassette  Units

## 1.2.1. System Overview

The BMS monitors and controls 2-off Ceiling Cassette Units (AC) which serve the level 1 and 4 comms rooms in the Swinburne Universities UN building's 'late lab'. These units are Daikin cassette units which will be controlled via high-level interface from the Daikin gateway at Level 4. These AC units operate as the second stage of cooling in the comms room when the temperature exceeds 28°C.

## 1.2.2. Controlled Equipment

| UNIT         | ASSOCI ATED OUTDOOR UNIT   | MODE L/ SE RIES   | LOCATION   | CO MMENT   |
|--------------|----------------------------|-------------------|------------|------------|
| Level 1      | Level 1                    | Level 1           | Level 1    | Level 1    |
| H-LL-AC-L1.2 | H-LL-CU-1.2                | FCA/RZA           | Comms Room |            |
| Level 4      | Level 4                    | Level 4           | Level 4    | Level 4    |
| H-LL-AC-L4.2 | H-LL-CU-4.2                | FCA/RZA           | Comms Room |            |

## 1.2.3. Points List (for each cassette unit)

| POINTS      | BI   | AI   | BO   | AO   |   HLI | CO MMENTS                 |
|-------------|------|------|------|------|-------|---------------------------|
| Unit Enable |      |      |      |      |     1 | Via Daikin BACnet gateway |
| Unit Status |      |      |      |      |     1 |                           |
| Unit Fault  |      |      |      |      |     1 |                           |

| POINTS                  | BI   |   AI | BO   | AO   | HLI   | CO MMENTS                                                |
|-------------------------|------|------|------|------|-------|----------------------------------------------------------|
| Zone Temperature Sensor |      |    1 |      |      |       | Wall mounted 10K type II Thermistor (Alerton TS-1050-BT) |

## 1.2.4. Start/Stop Control

An AC will be enabled when any of the following conditions are met:

- The zone temperature exceeds 28°C (adj.)

OR

- Overridden ON via BMS front-end.

An AC will be disabled when any of the following conditions are met:

- The zone temperature is below 28°C (adj.)

OR

- Overridden OFF via BMS front-end.

## 1.2.5. Temperature Control

The AC unit will be controlled via its proprietary Daikin controller utilising the wall mounted control panel within each comms room. The BMS will only enable the unit and monitor the rooms zone temperature, run status and unit fault.

## 1.2.6. Trend  and  Data  Logging

The BS is monitoring and performing trend and data logging every 15 minutes. The following trend logs are visible and logged on the BMS:

- Unit Enable
- Unit Status
- Unit Fault
- Zone Temperature

## 1.2.7. Controller Failure / Alarms

In the event of power loss to the local controller, the AC unit will stop operation; once power is reinstated, the unit will commence operation in sequence (so long as the start/stop conditions are met) after a delayed time.

An alarm is generated when any of the following conditions are met after a delayed period:

- There is a mismatch between the AC commanded value and actual value (determined from interface card).
- The BMS receives a fault signal directly from the interface card.
- The zone temperature exceeds 35°C (adj.) for a period of 5 minutes (adj.).

## 1.2.8. Fire  Mode

Typically, fire mode occurs when the MSSB receives a facility General Fire Alarm (GFA) directly from the facility. Fire Indication Panel (FIP) and on receipt of a GFA, the cassette units should be disabled directly at the corresponding MSSB. As this is hardwired to the unit, the BMS should have no control over this operation and will only monitor and mimic the fire mode operation to ensure that no false alarms are raised.