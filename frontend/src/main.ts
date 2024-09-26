import "./style.css";
import Graph from "graphology";
import Sigma from "sigma";

const graph = new Graph();

const nodesReq = fetch("/data/nodes.json").then((r) => r.json());
const shipsReq = fetch("/data/filtered_ships.json").then((r) => r.json());

Promise.all([nodesReq, shipsReq]).then(
  ([nodes, ships]) => {
    for (const node in nodes) {
      const name = ships[node].fields.title;
      graph.addNode(node, {
        label: name,
        x: nodes[node][0],
        y: nodes[node][1],
        size: 5,
      });
    }

    // for (const edge of edges) {
    //   graph.addEdge(edge.split("-")[0], edge.split("-")[1], { size: 0.5 });
    // }

    const sigmaInstance = new Sigma(graph, document.getElementById("app")!);
  },
);
