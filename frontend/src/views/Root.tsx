import { useEffect, useState } from "react";
import Graph from "graphology";
import { SigmaContainer, useLoadGraph, useSigma } from "@react-sigma/core";
import { useWorkerLayoutForce } from "@react-sigma/layout-force";
import { createNodeImageProgram } from "@sigma/node-image";
import "@react-sigma/core/lib/react-sigma.min.css";
import { easings } from "sigma/utils";
import IJS from "image-js";

import ShipOverview from "./ShipOverview";
import Search from "./Search";
import { ShipsContext, type ShipsData } from "../context/ShipsContext";
import { drawHover } from "../utils/rendering";

import type { Dispatch, SetStateAction } from "react";

const imageProgram = createNodeImageProgram({
  keepWithinCircle: false,
  objectFit: "contain",
});

// Component that load the graph
const LoadGraph = (props: {
  setShips: Dispatch<SetStateAction<ShipsData | null>>;
}) => {
  const loadGraph = useLoadGraph();
  const sigma = useSigma();

  useEffect(() => {
    const graph = new Graph();

    const nodesReq = fetch("/data/nodes.json").then((r) => r.json());
    const shipsReq = fetch("/data/filtered_ships.json").then((r) => r.json());

    Promise.all([nodesReq, shipsReq])
      .then(async ([nodes, ships]) => {
        let minX = 0;
        let maxX = 0;
        let minY = 0;
        let maxY = 0;

        // const variants = ["ship1.png", "ship2.png"];
        const variants = ["ship2.png"];
        const angles = [];
        for (let i = 0; i < 360; i += 360 / 8) {
          angles.push(i);
        }

        const promises = [];
        for (const variant of variants) {
          const image = await IJS.load(variant);

          for (const angle of angles) {
            const rotated = image.rotate(angle);

            promises.push(rotated.toDataURL());
          }
        }

        const shipImgs = await Promise.all(promises);

        for (const node in nodes) {
          if (node === "HIGH_SEAS_ISLAND") {
            graph.addNode(node, {
              label: "",
              x: nodes[node][0],
              y: nodes[node][1],
              size: 75,
              color: "#00000000",
              image: "island.png",
            });
            continue;
          }

          if (nodes[node][0] < minX) minX = nodes[node][0];
          if (nodes[node][0] > maxX) maxX = nodes[node][0];
          if (nodes[node][1] < minY) minY = nodes[node][1];
          if (nodes[node][1] > maxY) maxY = nodes[node][1];

          const name = ships[node].fields.title;
          const img = shipImgs[Math.floor(Math.random() * shipImgs.length)];
          graph.addNode(node, {
            label: name,
            x: nodes[node][0],
            y: nodes[node][1],
            size: 15,
            color: "#00000000",
            image: img,
          });
        }

        props.setShips(ships);
      })
      .then(() => {
        loadGraph(graph);

        const displayData = sigma.getNodeDisplayData("HIGH_SEAS_ISLAND");
        if (!displayData) return;
        const camera = sigma.getCamera();
        camera.setState({
          x: displayData.x,
          y: displayData.y,
          ratio: 0.4,
        });
      });
  }, [loadGraph]);

  if (sigma.getGraph().nodes().length === 0) {
    return (
      <div className="h-screen w-screen fixed top-0 left-0 flex justify-center items-center">
        <p className="text-2xl font-bold text-center text-white">
          Loading map...
        </p>
      </div>
    );
  }
  return null;
};

const KeyboardControl = (props: { typing: boolean }) => {
  const sigma = useSigma();

  useEffect(() => {
    let keymap: { [key: string]: boolean } = {};

    const listener = (e: KeyboardEvent) => {
      keymap[e.key] = e.type == "keydown";

      if (props.typing) return;

      const camera = sigma.getCamera();
      const state = camera.getState();
      const translateIncrement = 1 / 7 / sigma.getGraphToViewportRatio();
      const zoomIncrement = 0.15;
      let dx = 0;
      let dy = 0;
      let dz = 0;

      const pressedKeys = Object.entries(keymap)
        .filter((k) => k[1])
        .map((k) => k[0]);

      if (pressedKeys.includes("ArrowUp") || pressedKeys.includes("w")) {
        dy = translateIncrement;
      }
      if (pressedKeys.includes("ArrowLeft") || pressedKeys.includes("a")) {
        dx = -translateIncrement;
      }
      if (pressedKeys.includes("ArrowDown") || pressedKeys.includes("s")) {
        dy = -translateIncrement;
      }
      if (pressedKeys.includes("ArrowRight") || pressedKeys.includes("d")) {
        dx = translateIncrement;
      }
      if (pressedKeys.includes("-") || pressedKeys.includes("_")) {
        dz = zoomIncrement;
      }
      if (pressedKeys.includes("+") || pressedKeys.includes("=")) {
        dz = -zoomIncrement;
      }

      camera.animate(
        {
          x: state.x + dx,
          y: state.y + dy,
          ratio: state.ratio + dz,
        },
        {
          easing: easings.linear,
        },
      );
    };

    document.addEventListener("keydown", listener);
    document.addEventListener("keyup", listener);

    return () => {
      document.removeEventListener("keydown", listener);
      document.removeEventListener("keyup", listener);
    };
  }, [props.typing]);

  return null;
};

const ForceLayout = () => {
  const { start, kill } = useWorkerLayoutForce({
    isNodeFixed: () => true,
    settings: {
      attraction: 10,
    },
  });

  useEffect(() => {
    start();

    return () => {
      kill();
    };
  }, [start, kill]);

  return null;
};

export default function Root() {
  const [ships, setShips] = useState<ShipsData | null>(null);
  const [selectedShip, setSelectedShip] = useState<string>();
  const [typing, setTyping] = useState(false);

  return (
    <main>
      <ShipsContext.Provider value={ships}>
        <SigmaContainer
          style={{
            height: "100vh",
            width: "100vw",
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
            labelSize: 11,
            defaultDrawNodeHover: drawHover,
            minCameraRatio: 0.01,
            maxCameraRatio: 0.4,
          }}
        >
          <ForceLayout />
          <LoadGraph setShips={setShips} />
          <KeyboardControl typing={typing} />
          <ShipOverview selectedShip={selectedShip} />
          <Search setSelectedShip={setSelectedShip} setTyping={setTyping} />
        </SigmaContainer>
      </ShipsContext.Provider>
    </main>
  );
}
