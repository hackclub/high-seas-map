import { useEffect, useState } from "react";
import Graph from "graphology";
import { SigmaContainer, useLoadGraph, useSigma } from "@react-sigma/core";
import { useWorkerLayoutForce } from "@react-sigma/layout-force";
import { createNodeImageProgram } from "@sigma/node-image";
import "@react-sigma/core/lib/react-sigma.min.css";
import { easings } from "sigma/utils";

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

    const shipsReq = fetch(`/api/ships`).then((r) => r.json());

    shipsReq
      .then(async (ships) => {
        let minX = 0;
        let maxX = 0;
        let minY = 0;
        let maxY = 0;

        const variants = ["ship1", "ship2"];
        const angles = [];
        for (let i = 0; i < 360; i += 360 / 8) {
          angles.push(i);
        }

        const shipImgs = [];
        for (const variant of variants) {
          for (const angle of angles) {
            shipImgs.push(`ships/${variant}-${angle}.png`);
          }
        }

        for (const ship in ships) {
          if (ship === "HIGH_SEAS_ISLAND") {
            graph.addNode(ship, {
              label: "",
              x: ships[ship].x_pos,
              y: ships[ship].y_pos,
              size: 75,
              color: "#00000000",
              image: "harbor.svg",
            });
            continue;
          }

          if (ships[ship][0] < minX) minX = ships[ship].x_pos;
          if (ships[ship][0] > maxX) maxX = ships[ship].x_pos;
          if (ships[ship][1] < minY) minY = ships[ship].y_pos;
          if (ships[ship][1] > maxY) maxY = ships[ship].y_pos;

          const name = ships[ship].title;
          const img = shipImgs[Math.floor(Math.random() * shipImgs.length)];

          graph.addNode(ship, {
            label: name,
            x: ships[ship].x_pos,
            y: ships[ship].y_pos,
            size: 15,
            color: "#00000000",
            image: img,
            hours: ships[ship].hours,
            screenshotUrl: ships[ship].screenshot_url,
            username: ships[ship].slack_username,
            id: ship,
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
    settings: {
      attraction: 10,
      repulsion: 10.5,
      gravity: 0,
      maxMove: 0.001,
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
            labelDensity: 0,
            labelSize: 14,
            defaultDrawNodeHover: drawHover,
            minCameraRatio: 0.01,
            maxCameraRatio: 0.3,
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
