import { useSigma } from "@react-sigma/core";
import { useState, useContext, useEffect } from "react";
import { easings } from "sigma/utils";

import { ShipsContext, type ShipsData } from "../context/ShipsContext";
import type { Dispatch, SetStateAction } from "react";

export default function Search({
  setSelectedShip,
  setTyping,
}: {
  setSelectedShip: Dispatch<SetStateAction<string | undefined>>;
  setTyping: Dispatch<SetStateAction<boolean>>;
}) {
  const sigma = useSigma();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ShipsData>({});
  const ships = useContext(ShipsContext);

  useEffect(() => {
    if (query === "" || !ships) return;

    const entries = Object.entries(ships);
    const r = new RegExp(query, "ig");
    const res = entries.filter((t) => r.test(t[1].fields.title));
    setResults(Object.fromEntries(res));
  }, [query, ships]);

  return (
    <div className="fixed top-5 left-5 w-1/5">
      <div
        className={`w-full p-3 rounded-sm bg-widget border-2 border-black text-lg ${query !== "" ? "rounded-b-none" : "shadow-lg"}`}
      >
        <input
          type="text"
          className="outline-none w-full bg-widget placeholder:text-slate-200 text-white"
          placeholder="Search for a ship..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setTyping(true)}
          onBlur={() => setTyping(false)}
        />
      </div>
      {query !== "" && (
        <div className="flex flex-col justify-start items-start rounded-sm shadow-lg border-2 max-h-[50vh] overflow-y-scroll border-black border-t-0 rounded-t-none py-3 bg-widget text-white">
          {Object.entries(results).map((ship) => (
            <button
              key={ship[0]}
              className="p-3 hover:bg-hwidget w-full text-left"
              onClick={() => {
                const displayData = sigma.getNodeDisplayData(ship[0]);
                if (!displayData) return;
                const camera = sigma.getCamera();
                camera.animate(
                  {
                    x: displayData.x,
                    y: displayData.y,
                    ratio: 0.1,
                  },
                  {
                    duration: 1000,
                    easing: easings.quadraticInOut,
                  },
                );
                setSelectedShip(ship[0]);
                setQuery("");
              }}
            >
              {ship[1].fields.title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
