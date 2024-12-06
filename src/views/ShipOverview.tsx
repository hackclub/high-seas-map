import { useSigma } from "@react-sigma/core";
import { useState, useEffect, useContext, useCallback } from "react";
import Markdown from "react-markdown";
import { FaLink, FaCode } from "react-icons/fa";
import remarkGfm from "remark-gfm";
import remarkEmoji from "remark-emoji";
// @ts-expect-error
import remarkStripHtml from "remark-strip-html";

import { ShipsContext, type ShipData } from "../context/ShipsContext";

import type { SigmaNodeEventPayload } from "sigma/types";

export default function ShipOverview({
  selectedShip,
}: {
  selectedShip?: string;
}) {
  const sigma = useSigma();
  const [ship, setShip] = useState<ShipData | null>(null);
  const [readme, setReadme] = useState<string | null>(null);
  const ships = useContext(ShipsContext);

  const updateShip = useCallback(
    (shipId: string) => {
      if (!ships) return;
      const shipData = ships[shipId];

      setShip(shipData);

      fetch(shipData.readme_url)
        .then((r) => r.text())
        .then((text) => {
          setReadme(text);
        })
        .catch(() => {
          setReadme("No README available for this ship");
        });
    },
    [ships],
  );

  useEffect(() => {
    if (!selectedShip) return;
    updateShip(selectedShip);
  }, [selectedShip]);

  useEffect(() => {
    const clickNodeListener = (payload: SigmaNodeEventPayload) => {
      const shipId = payload.node;

      if (shipId !== "HIGH_SEAS_ISLAND") {
        updateShip(shipId);
      }
    };

    const clickOffListener = () => {
      setShip(null);
    };

    sigma.on("clickNode", clickNodeListener);
    sigma.on("clickEdge", clickOffListener);
    sigma.on("clickStage", clickOffListener);

    return () => {
      sigma.removeListener("clickNode", clickNodeListener);
      sigma.removeListener("clickEdge", clickOffListener);
      sigma.removeListener("clickStage", clickOffListener);
    };
  }, [ships]);

  if (!ship) return null;

  return (
    <div className="fixed bottom-3 shadow-sm shadow-yellow-600 right-3 rounded-sm w-2/5 max-h-[50vh] overflow-y-scroll border-2 bg-hwidget border-yellow-600 text-white">
      <div className="flex flex-col justify-start items-start px-10 pt-10 pb-2 w-full bg-hwidget">
        <div className="flex flex-row justify-between items-center w-full">
          <p className="text-white sm:text-lg text-xl font-bold">
            {ship.title}
          </p>
          <div className="flex justify-start items-center gap-3">
            {ship.deploy_url && (
              <a
                title="Ship deploy link"
                href={ship.deploy_url}
                target="_blank"
              >
                <FaLink className="text-xl" />
              </a>
            )}
            {ship.repo_url && (
              <a title="Ship repo link" href={ship.repo_url} target="_blank">
                <FaCode className="text-xl" />
              </a>
            )}
          </div>
        </div>
        <p className="text-lg italic">
          Made in {ship.hours.toFixed(1)} hour{ship.hours === 1 ? "" : "s"}{" "}
          by&nbsp;
          <a
            href={`https://hackclub.slack.com/team/${ship.slack_id}`}
            target="_blank"
            className="underline"
          >
            @{ship.slack_username}
          </a>
        </p>
        <hr className="border-[1px] border-gray-400 my-2 w-full" />
      </div>
      <Markdown
        remarkPlugins={[remarkGfm, remarkEmoji, remarkStripHtml]}
        className="p-10 pt-0 prose sm:prose-sm prose-invert"
      >
        {readme ?? "Loading..."}
      </Markdown>
    </div>
  );
}
