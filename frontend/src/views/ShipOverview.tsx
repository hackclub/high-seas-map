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

      fetch(shipData.fields.readme_url)
        .then((r) => r.text())
        .then((text) => {
          setReadme(text);
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

      updateShip(shipId);
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
      <div className="sticky top-0 px-10 pt-10 pb-2 w-full bg-hwidget">
        <div className="flex flex-row justify-between items-center">
          <p className="text-white text-xl font-bold">{ship.fields.title}</p>
          <div className="flex justify-start items-center gap-3">
            {ship.fields.deploy_url && (
              <a
                title="Ship deploy link"
                href={ship.fields.deploy_url}
                target="_blank"
              >
                <FaLink className="text-xl" />
              </a>
            )}
            {ship.fields.repo_url && (
              <a
                title="Ship repo link"
                href={ship.fields.repo_url}
                target="_blank"
              >
                <FaCode className="text-xl" />
              </a>
            )}
          </div>
        </div>
        <hr className="border-[1px] border-gray-400 my-2 w-full" />
      </div>
      {readme === null ? (
        <p>Loading...</p>
      ) : (
        <Markdown
          remarkPlugins={[remarkGfm, remarkEmoji, remarkStripHtml]}
          className="p-10 pt-0 prose prose-invert"
        >
          {readme}
        </Markdown>
      )}
    </div>
  );
}
