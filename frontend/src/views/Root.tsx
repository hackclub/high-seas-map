import { useEffect, useState } from "react";
import Graph from "graphology";
import { SigmaContainer, useLoadGraph } from "@react-sigma/core";
import "@react-sigma/core/lib/react-sigma.min.css";

import ShipOverview from "./ShipOverview";
import { ShipsContext, type ShipsData } from "../context/ShipsContext";

import type { Dispatch, SetStateAction } from "react";

// Component that load the graph
export const LoadGraph = (props: {
  setShips: Dispatch<SetStateAction<ShipsData | null>>;
}) => {
  const loadGraph = useLoadGraph();

  useEffect(() => {
    const graph = new Graph();

    const nodesReq = fetch("/data/nodes.json").then((r) => r.json());
    const edgesReq = fetch("/data/edges.json").then((r) => r.json());
    const shipsReq = fetch("/data/filtered_ships.json").then((r) => r.json());

    Promise.all([nodesReq, edgesReq, shipsReq])
      .then(([nodes, edges, ships]) => {
        for (const node in nodes) {
          const name = ships[node].fields.title;
          graph.addNode(node, {
            label: name,
            x: nodes[node][0],
            y: nodes[node][1],
            size: 5,
          });
        }

        for (const edge of edges) {
          graph.addEdge(edge.split("-")[0], edge.split("-")[1], { size: 0.1 });
        }
        props.setShips(ships);
      })
      .then(() => {
        loadGraph(graph);
      });
  }, [loadGraph]);

  return null;
};

export default function Root() {
  const [ships, setShips] = useState<ShipsData | null>(null);

  return (
    <main>
      <ShipsContext.Provider value={ships}>
        <SigmaContainer style={{ height: "100vh", width: "100vw" }}>
          <LoadGraph setShips={setShips} />
          <ShipOverview />
        </SigmaContainer>
      </ShipsContext.Provider>
    </main>
  );
}
