import { Settings } from "sigma/settings";
import { NodeDisplayData, PartialButFor, PlainObject } from "sigma/types";

const screenshotImages: {
  [id: string]: HTMLImageElement | string;
} = {};

export function drawRoundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
): void {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

/**
 * Custom hover renderer
 */
export function drawHover(
  context: CanvasRenderingContext2D,
  data: PlainObject,
  settings: PlainObject,
) {
  if (!data.label) return;

  const size = settings.labelSize;
  const font = settings.labelFont;
  const weight = settings.labelWeight;

  const hours = data.hours.toFixed(1);

  const label = data.label;
  const hoursText = `Made in ${hours} hour${hours === 1 ? "" : "s"} by @${data.username}`;

  // Then we draw the label background
  context.beginPath();
  context.fillStyle = "#fff";
  context.shadowOffsetX = 0;
  context.shadowOffsetY = 2;
  context.shadowBlur = 8;
  context.shadowColor = "#000";

  context.font = `${weight} ${size}px ${font}`;
  const labelWidth = context.measureText(label).width + size;
  const hoursWidth = context.measureText(hoursText).width + size;

  const imgError = screenshotImages[data.id] === "error";

  const maxWidth = Math.max(imgError ? 0 : 356, labelWidth, hoursWidth);

  const imgRatio = maxWidth / 356;

  const x = Math.round(data.x);
  const y = Math.round(data.y);
  const w = Math.round(maxWidth + 2);
  const hLabel = Math.round(size * 2 + 6);

  drawRoundRect(
    context,
    x + data.size + 1,
    y - 12,
    w,
    (imgError ? 0 : 267 * imgRatio) + hLabel,
    5,
  );
  context.closePath();
  context.fill();

  context.shadowOffsetX = 0;
  context.shadowOffsetY = 0;
  context.shadowBlur = 0;

  if (
    screenshotImages[data.id] &&
    typeof screenshotImages[data.id] !== "string"
  ) {
    context.drawImage(
      screenshotImages[data.id] as HTMLImageElement,
      data.x + data.size + 5,
      data.y - 5,
      350 * imgRatio,
      250 * imgRatio,
    );
  } else if (!screenshotImages[data.id]) {
    screenshotImages[data.id] = "loading";
    const screenshotImg = new Image(350 * imgRatio, 250 * imgRatio);
    screenshotImg.addEventListener("load", () => {
      screenshotImages[data.id] = screenshotImg;
    });
    screenshotImg.addEventListener("error", () => {
      screenshotImages[data.id] = "error";
    });
    screenshotImg.src = data.screenshotUrl;
  }

  context.fillStyle = "#000000";
  context.font = `${weight} ${size}px ${font}`;
  context.fillText(
    label,
    data.x + data.size + 5,
    (imgError ? 0 : 260 * imgRatio) + data.y + size / 3,
  );

  context.font = `${Number(weight) - 200} ${size - 1}px ${font}`;

  context.fillText(
    hoursText,
    data.x + data.size + 5,
    (imgError ? 0 : 260 * imgRatio) + data.y + size + 5,
  );
}

/**
 * Custom label renderer
 */
export function drawLabel(
  context: CanvasRenderingContext2D,
  data: PartialButFor<NodeDisplayData, "x" | "y" | "size" | "label" | "color">,
  settings: Settings,
): void {
  if (!data.label) return;

  const size = settings.labelSize,
    font = settings.labelFont,
    weight = settings.labelWeight;

  context.font = `${weight} ${size}px ${font}`;
  const width = context.measureText(data.label).width + 8;

  context.fillStyle = "#ffffffcc";
  context.fillRect(data.x + data.size, data.y + size / 3 - 15, width, 20);

  context.fillStyle = "#000";
  context.fillText(data.label, data.x + data.size + 3, data.y + size / 3);
}
