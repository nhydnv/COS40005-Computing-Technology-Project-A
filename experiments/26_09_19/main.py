from pathlib import Path

from rdflib import Graph, Namespace, RDF
from pyshacl import validate

DATA_FILES = ["data.ttl", "entities.ttl", "rules.ttl"]
SH = Namespace("http://www.w3.org/ns/shacl#")
TRACE_QUERY = """
PREFIX ctrl: <https://w3id.org/ibp/CTRLont#>
PREFIX projctrl: <http://example.org/projctrl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>

SELECT ?inputName ?outputName ?inputTime ?outputTime ?x ?actual WHERE {
    ?logic ctrl:logicInput ?inputEl ;
           ctrl:logicOutput ?outputEl .

    ?inputEl sosa:hasSimpleResult ?x ;
             sosa:observedProperty ?inputPoint ;
             sosa:resultTime ?inputTime .

    ?outputEl sosa:hasSimpleResult ?actual ;
              sosa:observedProperty ?outputPoint ;
              sosa:resultTime ?outputTime .

    BIND(STRAFTER(STR(?inputPoint), "#") AS ?inputName)
    BIND(STRAFTER(STR(?outputPoint), "#") AS ?outputName)
}
"""

def report_violations(data_graph, results_graph):
    report = []
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        focus_node = results_graph.value(result, SH.focusNode)
        message = results_graph.value(result, SH.resultMessage)
        rows = list(data_graph.query(TRACE_QUERY, initBindings={"logic": focus_node}))
        report.append({
            "rule": focus_node,
            "message": str(message),
            "trace": dict(rows[0].asdict()) if rows else None,
        })
    return report


def print_report(entries):
    for i, entry in enumerate(entries, 1):
        print(f"{'='*60}")
        print(f"VIOLATION #{i}")
        print(f"{'='*60}")
        print(f"  Rule:     {entry['rule']}")
        print(f"  Message:  {entry['message']}")
        if entry["trace"]:
            t = entry["trace"]
            print(f"  Time:     {t['inputTime']}")
            print(f"  Input:    {t['inputName']} = {t['x']}")
            print(f"  Output:   {t['outputName']} = {t['actual']}")
        else:
            print("  (no trace data found)")
        print()


# Brick + CTRLont instance data, plus the trend-data snapshot
data_graph = Graph()
for f in DATA_FILES:
    data_graph.parse(Path(__file__).parent / f, format="turtle")

# Shape library
shapes_graph = Graph()
shapes_graph.parse(Path(__file__).parent / "shapes.ttl", format="turtle")

# Debugging
query = """
PREFIX ctrl: <https://w3id.org/ibp/CTRLont#>
PREFIX ex: <http://example.org/building#>
PREFIX projctrl: <http://example.org/projctrl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>

SELECT
    ?logic ?inputEl ?outputEl ?inMin ?inMax ?outMin ?outMax ?tol ?x ?actual
WHERE {
    ?logic a projctrl:LinearLogic ;
        ctrl:logicInput ?inputEl ;
        ctrl:logicOutput ?outputEl .

    ?inputEl sosa:hasSimpleResult ?x .

    ?outputEl sosa:hasSimpleResult ?actual .

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
}
"""

for row in data_graph.query(query):
    print("Logic:", row.logic)
    print("Input:", row.inputEl)
    print("Output:", row.outputEl)
    print("Input min:", row.inMin)
    print("Input max:", row.inMax)
    print("Output min:", row.outMin)
    print("Output max:", row.outMax)
    print("Tolerance:", row.tol)
    print("Measured input:", row.x)
    print("Actual output:", row.actual)

print(f"Data graph has {len(data_graph)} triples")
print(f"Shapes graph has {len(shapes_graph)} triples")

conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    advanced=True,  # required for sh:sparql constraints
    abort_on_first=False,
)

print(conforms)

# Print traceability report
print_report(report_violations(data_graph, results_graph))