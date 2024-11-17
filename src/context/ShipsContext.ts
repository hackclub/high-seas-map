import { createContext } from "react";

export type ShipData = {
  fields: {
    title: string;
    readme_url: string;
    repo_url: string;
    deploy_url: string;
  };
};

export type ShipsData = {
  [ship: string]: ShipData;
};

export const ShipsContext = createContext<ShipsData | null>(null);
