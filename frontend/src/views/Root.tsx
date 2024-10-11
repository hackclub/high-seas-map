import { useEffect, useState } from "react";
import Graph from "graphology";
import { SigmaContainer, useLoadGraph } from "@react-sigma/core";
import { createNodeImageProgram } from "@sigma/node-image";
import "@react-sigma/core/lib/react-sigma.min.css";

import ShipOverview from "./ShipOverview";
import { ShipsContext, type ShipsData } from "../context/ShipsContext";

import type { Dispatch, SetStateAction } from "react";

const imageProgram = createNodeImageProgram({
  keepWithinCircle: false,
  objectFit: "contain",
});

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
            size: 15,
            color: "#00000000",
            image: Math.random() > 0.5 ? "ship2.png" : "ship1.png",
          });
        }

        // for (const edge of edges) {
        //   graph.addEdge(edge.split("-")[0], edge.split("-")[1], { size: 0.1 });
        // }
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
        <SigmaContainer
          style={{
            height: "100vh",
            width: "100vw",
            // backgroundColor: "#10d5eb",
            backgroundImage: "url(/seabkgr.svg)",
            backgroundSize: "cover",
          }}
          settings={{
            defaultNodeType: "image",
            nodeProgramClasses: {
              image: imageProgram,
            },
            labelColor: {
              color: "white",
            },
            labelWeight: "800",
            labelDensity: 0.1,
            labelSize: 10,
          }}
        >
          <LoadGraph setShips={setShips} />
          <ShipOverview />
        </SigmaContainer>
      </ShipsContext.Provider>
    </main>
  );
}
