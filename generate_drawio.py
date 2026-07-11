import xml.etree.ElementTree as ET
import xml.dom.minidom

def create_drawio(filename, nodes, edges):
    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", name="Page-1", id="diag-1")
    mxGraphModel = ET.SubElement(diagram, "mxGraphModel", dx="1000", dy="1000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="850", pageHeight="1100", math="0", shadow="0")
    root = ET.SubElement(mxGraphModel, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    
    for n in nodes:
        node = ET.SubElement(root, "mxCell", id=n['id'], value=n['value'], parent="1", vertex="1")
        if n['type'] == 'sum':
            node.set("style", "shape=sumEllipse;perimeter=ellipsePerimeter;whiteSpace=wrap;html=1;backgroundOutline=1;")
            ET.SubElement(node, "mxGeometry", x=str(n['x']), y=str(n['y']), width="40", height="40", **{"as": "geometry"})
        elif n['type'] == 'text':
            node.set("style", "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;")
            ET.SubElement(node, "mxGeometry", x=str(n['x']), y=str(n['y']), width=str(n.get('w', 60)), height=str(n.get('h', 30)), **{"as": "geometry"})
        else:
            node.set("style", "rounded=0;whiteSpace=wrap;html=1;")
            ET.SubElement(node, "mxGeometry", x=str(n['x']), y=str(n['y']), width=str(n.get('w', 120)), height=str(n.get('h', 60)), **{"as": "geometry"})
            
    for e in edges:
        edge = ET.SubElement(root, "mxCell", id=e['id'], value=e.get('value', ''), parent="1", edge="1", source=e['source'], target=e['target'])
        edge.set("style", e.get('style', "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"))
        geo = ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})
        if 'points' in e:
            arr = ET.SubElement(geo, "Array", **{"as": "points"})
            for p in e['points']:
                ET.SubElement(arr, "mxPoint", x=str(p[0]), y=str(p[1]))

    xmlstr = xml.dom.minidom.parseString(ET.tostring(mxfile)).toprettyxml(indent="  ")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xmlstr)

# 1. Perturbation diagram
nodes_pert = [
    {"id": "d_in", "value": "D(s)", "type": "text", "x": 100, "y": 205},
    {"id": "sum", "value": "", "type": "sum", "x": 200, "y": 200},
    {"id": "minus", "value": "-", "type": "text", "x": 180, "y": 180, "w": 20, "h": 20},
    {"id": "plus", "value": "+", "type": "text", "x": 220, "y": 240, "w": 20, "h": 20},
    {"id": "plant", "value": "Planta<br>Gp(s)", "type": "block", "x": 300, "y": 190, "w": 120, "h": 60},
    {"id": "y_out", "value": "Temperatura Y(s)", "type": "text", "x": 480, "y": 205, "w": 120, "h": 30},
    {"id": "sensor", "value": "Sensor Pt100<br>H(s) = 0.2", "type": "block", "x": 300, "y": 320, "w": 120, "h": 60},
    {"id": "ctrl", "value": "Controlador<br>Gc(s)", "type": "block", "x": 160, "y": 320, "w": 120, "h": 60},
]
edges_pert = [
    {"id": "e1", "source": "d_in", "target": "sum", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e2", "source": "sum", "target": "plant", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e3", "source": "plant", "target": "y_out", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e4", "source": "plant", "target": "sensor", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;", "points": [(450, 220), (450, 350)]},
    {"id": "e5", "source": "sensor", "target": "ctrl", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=0;exitY=0.5;entryX=1;entryY=0.5;"},
    {"id": "e6", "source": "ctrl", "target": "sum", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=0.5;exitY=0;entryX=0.5;entryY=1;"},
]
create_drawio("diagrama_bloques_perturbacion.drawio", nodes_pert, edges_pert)

# 2. Simplified diagram
nodes_simp = [
    {"id": "vsp", "value": "Vsp(s)", "type": "text", "x": 100, "y": 205},
    {"id": "sum", "value": "", "type": "sum", "x": 200, "y": 200},
    {"id": "plus", "value": "+", "type": "text", "x": 180, "y": 180, "w": 20, "h": 20},
    {"id": "minus", "value": "-", "type": "text", "x": 200, "y": 240, "w": 20, "h": 20},
    {"id": "gc", "value": "-Gc(s)", "type": "block", "x": 300, "y": 190, "w": 100, "h": 60},
    {"id": "gp", "value": "Gp(s)", "type": "block", "x": 450, "y": 190, "w": 100, "h": 60},
    {"id": "yout", "value": "T(s)", "type": "text", "x": 600, "y": 205, "w": 60, "h": 30},
    {"id": "sensor", "value": "H(s) = 0.2", "type": "block", "x": 450, "y": 320, "w": 100, "h": 60},
    {"id": "e_s", "value": "E(s)", "type": "text", "x": 250, "y": 190, "w": 40, "h": 20},
    {"id": "u_s", "value": "U(s)", "type": "text", "x": 410, "y": 190, "w": 40, "h": 20},
]
edges_simp = [
    {"id": "e1", "source": "vsp", "target": "sum", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e2", "source": "sum", "target": "gc", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e3", "source": "gc", "target": "gp", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e4", "source": "gp", "target": "yout", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e5", "source": "gp", "target": "sensor", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;", "points": [(580, 220), (580, 350)]},
    {"id": "e6", "source": "sensor", "target": "sum", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=0;exitY=0.5;entryX=0.5;entryY=1;"},
]
create_drawio("diagrama_bloques_simplificado.drawio", nodes_simp, edges_simp)

# 3. Main block diagram (fig:bloques)
nodes_main = [
    {"id": "r", "value": "Consigna R(s)", "type": "text", "x": 20, "y": 205},
    {"id": "trans", "value": "Hr(s) = 0.2", "type": "block", "x": 120, "y": 190, "w": 100, "h": 60},
    {"id": "sum1", "value": "", "type": "sum", "x": 260, "y": 200},
    {"id": "p", "value": "P", "type": "block", "x": 360, "y": 100, "w": 80, "h": 60},
    {"id": "i", "value": "I", "type": "block", "x": 360, "y": 190, "w": 80, "h": 60},
    {"id": "d", "value": "D", "type": "block", "x": 360, "y": 280, "w": 80, "h": 60},
    {"id": "sumpid", "value": "", "type": "sum", "x": 480, "y": 200},
    {"id": "plant", "value": "Planta Gp(s)", "type": "block", "x": 600, "y": 190, "w": 100, "h": 60},
    {"id": "sumdist", "value": "", "type": "sum", "x": 840, "y": 200},
    {"id": "dist", "value": "Perturbación", "type": "text", "x": 820, "y": 140, "w": 80, "h": 30},
    {"id": "yout", "value": "Temp T(s)", "type": "text", "x": 920, "y": 205, "w": 80, "h": 30},
    {"id": "sensor", "value": "Sensor H(s)", "type": "block", "x": 340, "y": 400, "w": 120, "h": 60},
]
edges_main = [
    {"id": "e1", "source": "r", "target": "trans"},
    {"id": "e2", "source": "trans", "target": "sum1"},
    {"id": "e3", "source": "sum1", "target": "p", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e4", "source": "sum1", "target": "i"},
    {"id": "e5", "source": "sum1", "target": "d", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"},
    {"id": "e6", "source": "p", "target": "sumpid", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0.5;entryY=0;"},
    {"id": "e7", "source": "i", "target": "sumpid"},
    {"id": "e8", "source": "d", "target": "sumpid", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=0.5;entryY=1;"},
    {"id": "e9", "source": "sumpid", "target": "plant"},
    {"id": "e10", "source": "plant", "target": "sumdist"},
    {"id": "e12", "source": "dist", "target": "sumdist"},
    {"id": "e13", "source": "sumdist", "target": "yout"},
    {"id": "e14", "source": "sumdist", "target": "sensor", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=1;exitY=0.5;entryX=1;entryY=0.5;", "points": [(900, 220), (900, 430)]},
    {"id": "e15", "source": "sensor", "target": "sum1", "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;exitX=0;exitY=0.5;entryX=0.5;entryY=1;"},
]
create_drawio("diagrama_bloques_general.drawio", nodes_main, edges_main)

print("Drawio files generated successfully.")
