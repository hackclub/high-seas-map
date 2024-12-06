import { createContext } from "react";

export type ShipData = {
  identifier: string;
  title: string;
  readme_url: string;
  repo_url: string;
  deploy_url: string;
  screenshot_url: string;
  hours: number;
  slack_id: string;
  slack_username: string;
  x_pos: number;
  y_pos: number;
};

export type ShipsData = {
  [ship: string]: ShipData;
};

export const ShipsContext = createContext<ShipsData | null>(null);
