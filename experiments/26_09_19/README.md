# Zone CO2 → Outside Air Damper Compliance Example
### Brick + CTRLont + SHACL/SPARQL walkthrough

**Scenario (formal rule):**
> The outside air damper will be at its minimum outside air damper position until the zone CO2 reaches its minimum setpoint of 600 ppm, and will open proportionally to a maximum outside air damper position when the zone CO2 is equal to or greater than 800 ppm. The minimum position is 40% and the maximum position is 80%.

## 1. Brick — physical entities

### Full source
**entities.ttl**
```python
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix ex: <http://example.org/building#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# H-LL-FCU-L2.I1 is an FCU which feeds into the Student Work Zone
# and has a CO2 Sensor point named H-LL-FCU-L2.I1_CO2.
ex:H-LL-FCU-L2.I1 a brick:Fan_Coil_Unit ;
    brick:feeds ex:Student_Work_Zone ;
    brick:hasPoint ex:H-LL-FCU-L2.I1_CO2 ;
    brick:hasPart ex:H-LL-FCU-L2.I1_Damper .

# H-LL-FCU-L2.I1_CO2 is a CO2 Sensor, which controls the damper H-LL-FCU-L2.I1_Damper
ex:H-LL-FCU-L2.I1_CO2 a brick:CO2_Level_Sensor ;
    brick:isPointOf ex:H-LL-FCU-L2.I1 .

# Damper H-LL-FCU-L2.I1_Damper is an outside air damper
ex:H-LL-FCU-L2.I1_Damper a brick:Outside_Air_Damper ;
    brick:isPartOf ex:H-LL-FCU-L2.I1 ;
    brick:hasPoint ex:H-LL-FCU-L2.I1_Damper_PositionCommand .

# Damper's position command
ex:H-LL-FCU-L2.I1_Damper_PositionCommand a brick:Outside_Air_Damper_Position_Command ;
    brick:isPointOf ex:H-LL-FCU-L2.I1_Damper .

# The Student Work Zone is an HVAC Zone
ex:Student_Work_Zone a brick:HVAC_Zone .
```

### Defining the prefixes
```python
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix ex: <http://example.org/building#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
```

### Defining the Fan Coil Unit
`H-LL-FCU-L2.I1` is an FCU which feeds into the Student Work Zone. It has a CO2 Sensor point named `H-LL-FCU-L2.I1_CO2` and a damper named `H-LL-FCU-L2.I1_Damper`.
```python
ex:H-LL-FCU-L2.I1 a brick:Fan_Coil_Unit ;
    brick:feeds ex:Student_Work_Zone ;
    brick:hasPoint ex:H-LL-FCU-L2.I1_CO2 ;
    brick:hasPart ex:H-LL-FCU-L2.I1_Damper .
```

### Defining the CO2 sensor
`H-LL-FCU-L2.I1_CO2` is a CO2 Sensor, which is a point of `H-LL-FCU-L2.I1` (the FCU defined above).
```python
ex:H-LL-FCU-L2.I1_CO2 a brick:CO2_Level_Sensor ;
    brick:isPointOf ex:H-LL-FCU-L2.I1 .
```

### Defining the damper
Damper `H-LL-FCU-L2.I1_Damper` is an outside air damper.
```python
ex:H-LL-FCU-L2.I1_Damper a brick:Outside_Air_Damper ;
    brick:isPartOf ex:H-LL-FCU-L2.I1 ;
    brick:hasPoint ex:H-LL-FCU-L2.I1_Damper_PositionCommand .
```

### Defining the damper's position
```python
ex:H-LL-FCU-L2.I1_Damper_PositionCommand a brick:Outside_Air_Damper_Position_Command ;
    brick:isPointOf ex:H-LL-FCU-L2.I1_Damper .
```

### Defining the HVAC Zone
The Student Work Zone is an HVAC Zone.
```python
ex:Student_Work_Zone a brick:HVAC_Zone .
```

## 2. CTRLont + our extensions — control logic

We have to extend CTRLont with our own ontology to model the control rules. The design of this ontology is one of the tasks we must do to ensure the all rule definitions are covered.

**rules.ttl**
### Full source
```python
@prefix ctrl: <https://w3id.org/ibp/CTRLont#> .
@prefix ex: <http://example.org/building#> .
@prefix projctrl: <http://example.org/projctrl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# The slope/intercept of the line through (600ppm, 40%) and (800ppm, 80%):
# - slope = (80 − 40) / (800 − 600) = 0.2
# - intercept: 40 = 0.2 × 600 + b -> b = −80
# - expected position = 0.2 × CO2 − 80, clamped to [40, 80] outside the 600–800ppm range

# --- Project extensions (not part of base CTRLont) ---

projctrl:LinearLogic rdfs:subClassOf ctrl:ApplicationLogic ;
    rdfs:comment "Custom extension: A proportional reset curve between an input and an output, bounded by parameters." .

projctrl:MinParameter rdfs:subClassOf ctrl:Parameter .
projctrl:MaxParameter rdfs:subClassOf ctrl:Parameter .
projctrl:ToleranceParameter rdfs:subClassOf ctrl:Parameter .

projctrl:constrains a rdf:Property ;
    rdfs:comment "Project extension: links a Parameter to the Input or Output it bounds." .

projctrl:correspondsToBrickPoint a rdf:Property ;
    rdfs:comment "Project extension: bridges a ctrl:Input/Output to its corresponding Brick point." .

# --- Control rules --- #

# Define function input: CO2 point
ex:CO2Input a ctrl:Input ;
    ctrl:hasUnit ex:PPM ;
    projctrl:correspondsToBrickPoint ex:H-LL-FCU-L2.I1_CO2 .  # bridge to Brick - not part of CTRLont, our own link

# Define function output: Damper % position
ex:DamperOutput a ctrl:Output ;
    ctrl:hasUnit ex:Percent ;
    projctrl:correspondsToBrickPoint ex:H-LL-FCU-L2.I1_Damper_PositionCommand .

# Clamp
ex:MinSetpoint a projctrl:MinParameter ; 
    projctrl:constrains ex:CO2Input ;
    rdf:value "600"^^xsd:float .
ex:MaxSetpoint a projctrl:MaxParameter ; 
    projctrl:constrains ex:CO2Input ;
    rdf:value "800"^^xsd:float .
ex:MinPosition a projctrl:MinParameter ; 
    projctrl:constrains ex:DamperOutput ;
    rdf:value "40"^^xsd:float .
ex:MaxPosition a projctrl:MaxParameter ; 
    projctrl:constrains ex:DamperOutput ;
    rdf:value "80"^^xsd:float .
ex:Tolerance a projctrl:ToleranceParameter,
    ctrl:Parameter ; ctrl:hasUnit ex:Percent ;
    rdf:value "5"^^xsd:float .

# Define the rule itself
ex:DamperResetLogic a projctrl:LinearLogic ;
    ctrl:logicInput ex:CO2Input ;
    ctrl:logicOutput ex:DamperOutput ;
    ctrl:logicParameter ex:MinSetpoint, ex:MaxSetpoint, ex:MinPosition, ex:MaxPosition, ex:Tolerance .

# Bind the rule to the damper controller
ex:DamperController a ctrl:ControlActor ;
    ctrl:hasApplicationLogic ex:DamperResetLogic .
```

### Our custom extensions

- `projctrl:LinearLogic`: Model a linear function.
- `projctrl:MinParameter`, `projctrl:MaxParameter`, `projctrl:ToleranceParameter`: Parameters of this function.
- `projctrl:constrains`: Link a parameter to the Input or Output it bounds.
- `projctrl:correspondsToBrickPoint`: Link a `ctrl:Input/Output` to its corresponding Brick point.

```python
@prefix projctrl: <http://example.org/projctrl#> .

projctrl:LinearLogic rdfs:subClassOf ctrl:ApplicationLogic ;
    rdfs:comment "Custom extension: A proportional reset curve between an input and an output, bounded by parameters." .

projctrl:MinParameter rdfs:subClassOf ctrl:Parameter .
projctrl:MaxParameter rdfs:subClassOf ctrl:Parameter .
projctrl:ToleranceParameter rdfs:subClassOf ctrl:Parameter .

projctrl:constrains a rdf:Property ;
    rdfs:comment "Project extension: links a Parameter to the Input or Output it bounds." .

projctrl:correspondsToBrickPoint a rdf:Property ;
    rdfs:comment "Project extension: bridges a ctrl:Input/Output to its corresponding Brick point." .
```

### Defining the input (CO2 level) and output (damper position)
Define function input: CO2 point
```python
ex:CO2Input a ctrl:Input ;
    ctrl:hasUnit ex:PPM ;
    projctrl:correspondsToBrickPoint ex:H-LL-FCU-L2.I1_CO2 .  # bridge to Brick - not part of CTRLont, our own link
```
Define function output: Damper % position

```python
ex:DamperOutput a ctrl:Output ;
    ctrl:hasUnit ex:Percent ;
    projctrl:correspondsToBrickPoint ex:H-LL-FCU-L2.I1_Damper_PositionCommand .
```

### Defining the actual minimum, maximum, and tolerance values (derived from the rule)

- `ex:MinSetpoint` = 600 ("minimum" CO2 setpoint)
- `ex:MaxSetpoint` = 800 ("maximum" CO2 setpoint)
- `ex:MinPosition` = 40% (minimum damper position)
- `ex:MaxPosition` = 80% (maximum damper position)

```python
ex:MinSetpoint a projctrl:MinParameter ; 
    projctrl:constrains ex:CO2Input ;
    rdf:value "600"^^xsd:float .

ex:MaxSetpoint a projctrl:MaxParameter ; 
    projctrl:constrains ex:CO2Input ;
    rdf:value "800"^^xsd:float .

ex:MinPosition a projctrl:MinParameter ; 
    projctrl:constrains ex:DamperOutput ;
    rdf:value "40"^^xsd:float .

ex:MaxPosition a projctrl:MaxParameter ; 
    projctrl:constrains ex:DamperOutput ;
    rdf:value "80"^^xsd:float .

ex:Tolerance a projctrl:ToleranceParameter,
    ctrl:Parameter ; ctrl:hasUnit ex:Percent ;
    rdf:value "5"^^xsd:float .
```

### Defining the rule itself
The rule is named DamperResetLogic. It is a type of LinearLogic as the rule defines a linear relationship between the CO2 level and the damper's position.

Here we bind the input, output, and actual minimum and maximum values that were just defined above to the rule.

```python
ex:DamperResetLogic a projctrl:LinearLogic ;
    ctrl:logicInput ex:CO2Input ;
    ctrl:logicOutput ex:DamperOutput ;
    ctrl:logicParameter ex:MinSetpoint, ex:MaxSetpoint, ex:MinPosition, ex:MaxPosition, ex:Tolerance .
```

## 3. Mapping trend data into the graph
Mapping the actual data values from the Excel sheet. Ideally we want to automate this, but just for demo reasons mapped the piece of data below manually. 

Here we makes use of an additional ontology: Sensor, Observation, Sample, and Actuator (`sosa`).

### Full source
**data.ttl**
```python
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix ex: <http://example.org/building#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix sosa: <http://www.w3.org/ns/sosa/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:CO2Input a sosa:Observation ;
    sosa:observedProperty ex:H-LL-FCU-L2.I1_CO2 ;
    sosa:hasSimpleResult "911.99"^^xsd:float ;
    sosa:resultTime "2026-12-05T13:05:00Z"^^xsd:dateTime .

ex:DamperOutput a sosa:Observation ;
    sosa:observedProperty ex:H-LL-FCU-L2.I1_Damper_PositionCommand ;
    sosa:hasSimpleResult "40"^^xsd:float ;
    sosa:resultTime "2026-12-05T13:05:00Z"^^xsd:dateTime .
```

### Reading the CO2 level
CO2 level = 911.99 (made up)
```python
ex:CO2Input a sosa:Observation ;
    sosa:observedProperty ex:H-LL-FCU-L2.I1_CO2 ;
    sosa:hasSimpleResult "911.99"^^xsd:float ;
    sosa:resultTime "2026-12-05T13:05:00Z"^^xsd:dateTime .
```

### Reading the damper's position
Damper position = 40%
```python
ex:DamperOutput a sosa:Observation ;
    sosa:observedProperty ex:H-LL-FCU-L2.I1_Damper_PositionCommand ;
    sosa:hasSimpleResult "40"^^xsd:float ;
    sosa:resultTime "2026-12-05T13:05:00Z"^^xsd:dateTime .
```

## 4. SHACL — the compliance check (generic across every LinearLogic rule)

The SHACL check, which is presumably manually written by ourselves. The generic SHACL shape below checks any rule that defines a linear relationship.

### Full source
**shapes.ttl**
```python
@prefix sh: <http://www.w3.org/ns/shacl#>
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ex: <http://example.org/building#> .
@prefix projctrl: <http://example.org/projctrl#> .

ex:LinearComplianceShape a sh:NodeShape ;
    sh:targetClass ctrl:ApplicationLogic ;
    sh:sparql [
        sh:message "Measured output deviates from the linear reset curve beyond tolerance." ;
        sh:select """
            PREFIX ctrl: <https://w3id.org/ibp/CTRLont#>
            PREFIX projctrl: <http://example.org/projctrl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX sosa: <http://www.w3.org/ns/sosa/>

            SELECT $this WHERE {
            
                $this a projctrl:LinearLogic ;
                    ctrl:logicInput ?inputEl ;
                    ctrl:logicOutput ?outputEl ;
                    ctrl:logicParameter ?minSp, ?maxSp, ?minPos, ?maxPos, ?tolP .

                ?minSp a projctrl:MinParameter ;
                    projctrl:constrains ?inputEl ;
                    rdf:value ?inMin .

                ?maxSp a projctrl:MaxParameter ;
                    projctrl:constrains ?inputEl ;
                    rdf:value ?inMax .

                ?minPos a projctrl:MinParameter ;
                    projctrl:constrains ?outputEl ;
                    rdf:value ?outMin .

                ?maxPos a projctrl:MaxParameter ;
                    projctrl:constrains ?outputEl ;
                    rdf:value ?outMax .

                ?tolP a projctrl:ToleranceParameter ;
                    rdf:value ?tol .

                ?inputEl sosa:hasSimpleResult ?x .
                ?outputEl sosa:hasSimpleResult ?actual .

                BIND(
                    IF(
                        ?x < ?inMin,
                        ?inMin,
                        IF(?x > ?inMax, ?inMax, ?x)
                    )
                    AS ?xClamped
                )

                BIND(
                    (?outMax - ?outMin) / (?inMax - ?inMin)
                    AS ?slope
                )

                BIND(
                    ?outMin + ?slope * (?xClamped - ?inMin)
                    AS ?expected
                )

                FILTER(
                    ABS(?actual - ?expected) > ?tol
                )
            }
        """ ;
    ] .
```

### Defining the shape ("rule checker")
The `LinearComplianceShape` shape checks all `LinearLogic` instances. `DamperResetLogic` (defined above in `rules.ttl`) is one of them. The line below essentially tells SHACL to apply itself to every resource in the data graph that is an instance of `projctrl:LinearLogic`.

```python
ex:LinearComplianceShape a sh:NodeShape ;
    sh:targetClass projctrl:LinearLogic ;
```

### The SPARQL query - the main check
Built-in SHACL validation is not sophisticated enough; therefore, we need to make us of SPARQL queries. SPARQL is basically SQL but for graph data.

```python
sh:select """
    PREFIX ctrl: <https://w3id.org/ibp/CTRLont#>
    PREFIX projctrl: <http://example.org/projctrl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sosa: <http://www.w3.org/ns/sosa/>

    SELECT $this WHERE {
    
        $this ctrl:logicInput ?inputEl ;
            ctrl:logicOutput ?outputEl ;
            ctrl:logicParameter ?minSp, ?maxSp, ?minPos, ?maxPos, ?tolP .

        ?minSp a projctrl:MinParameter ;
            projctrl:constrains ?inputEl ;
            rdf:value ?inMin .

        ?maxSp a projctrl:MaxParameter ;
            projctrl:constrains ?inputEl ;
            rdf:value ?inMax .

        ?minPos a projctrl:MinParameter ;
            projctrl:constrains ?outputEl ;
            rdf:value ?outMin .

        ?maxPos a projctrl:MaxParameter ;
            projctrl:constrains ?outputEl ;
            rdf:value ?outMax .

        ?tolP a projctrl:ToleranceParameter ;
            rdf:value ?tol .

        ?inputEl sosa:hasSimpleResult ?x .
        ?outputEl sosa:hasSimpleResult ?actual .

        BIND(
            IF(
                ?x < ?inMin,
                ?inMin,
                IF(?x > ?inMax, ?inMax, ?x)
            )
            AS ?xClamped
        )

        BIND(
            (?outMax - ?outMin) / (?inMax - ?inMin)
            AS ?slope
        )

        BIND(
            ?outMin + ?slope * (?xClamped - ?inMin)
            AS ?expected
        )

        FILTER(
            ABS(?actual - ?expected) > ?tol
        )
    }
""" ;
] .
```

Step-by-step:
```
SELECT `$this` WHERE {...}, 
```
`$this` means the resource currently being validated by the SHACL shape, i.e. the `projctrl:LinearLogic` resource we targeted above. It effectively runs our query with: `$this = ex:DamperResetLogic`.

```
$this ;
    ctrl:logicInput ?inputEl ;
    ctrl:logicOutput ?outputEl ;
    ctrl:logicParameter ?minSp, ?maxSp, ?minPos, ?maxPos, ?tolP .
```
Triple pattern: every line is a subject - predicate - object triple. For instance, `ctrl:logicInput ?inputEl ;` means find whatever is the `ctrl:logicInput` of `$this` and store it in `?inputEl` (words prefixed by a ? is a variable).

Similarly, we extract the parameters of the control rule: min setpoint (`?minSp`), max setpoint (`?maxSp`), min position (`?minPos`), max position (`?maxPos`), and tolerance (`?tolP`) (these variables should be named more generically, but again, this is only for demo purposes). The actual values are stored in `?inMin`, `?inMax`, `?outMin`, `?outMax`, and `?tol`.

```
?minSp a projctrl:MinParameter ;
    projctrl:constrains ?inputEl ;
    rdf:value ?inMin .

?maxSp a projctrl:MaxParameter ;
    projctrl:constrains ?inputEl ;
    rdf:value ?inMax .

?minPos a projctrl:MinParameter ;
    projctrl:constrains ?outputEl ;
    rdf:value ?outMin .

?maxPos a projctrl:MaxParameter ;
    projctrl:constrains ?outputEl ;
    rdf:value ?outMax .

?tolP a projctrl:ToleranceParameter ;
    rdf:value ?tol .
```

This line below means extract all resources that is a type of `projctrl:MinParameter` and `projctrl:constrains` `?inputEl`. Store the resource in `?minSp`, and its `rdf:value` in `?inMin`.

```
?minSp a projctrl:MinParameter ;
    projctrl:constrains ?inputEl ;
    rdf:value ?inMin .
```

Then we extract the BMS trend data. The actual values are stored in `?x` and `?actual`.
```
?inputEl sosa:hasSimpleResult ?x .
?outputEl sosa:hasSimpleResult ?actual .
```

Filter for deviations by doing some arithmetic:

```
BIND(
    IF(
        ?x < ?inMin,
        ?inMin,
        IF(?x > ?inMax, ?inMax, ?x)
    )
    AS ?xClamped
)
BIND(
    (?outMax - ?outMin) / (?inMax - ?inMin)
    AS ?slope
)
BIND(
    ?outMin + ?slope * (?xClamped - ?inMin)
    AS ?expected
)
FILTER(
    ABS(?actual - ?expected) > ?tol
)
```

## 5. Python — Run the checks

**main.py**

### Reading the RDF graphs into memory
```python
from pathlib import Path

from rdflib import Graph
from pyshacl import validate

DATA_FILES = ["data.ttl", "entities.ttl", "rules.ttl"]

...

# Brick + CTRLont instance data, plus the trend-data snapshot
data_graph = Graph()
for f in DATA_FILES:
    data_graph.parse(Path(__file__).parent / f, format="turtle")

# Shape library
shapes_graph = Graph()
shapes_graph.parse(Path(__file__).parent / "shapes.ttl", format="turtle")
```

### Running the shapes against the knowledge graph
```python
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    advanced=True,  # required for sh:sparql constraints
    abort_on_first=False,
)

print(conforms)
```

### Results
```
False
============================================================
VIOLATION #1
============================================================
  Rule:     http://example.org/building#DamperResetLogic
  Message:  Measured output deviates from the linear reset curve beyond tolerance.
  Time:     2026-12-05T13:05:00+00:00
  Sensor:   H-LL-FCU-L2.I1_CO2 = 911.99
  Damper:   H-LL-FCU-L2.I1_Damper_PositionCommand = 40.0
```