// Draws text in loaded web fonts onto a <canvas> and saves it as a PNG, for
// "保存为图片" (the pairing page and the compare page). Each picture carries
// the site's address in the corner, so shared images lead people back.

export interface TextBlock {
  /** Font name shown above the text, in the interface font */
  label?: string;
  text: string;
  family: string; // a loaded font-family name (from loadFont)
  weight: number;
  size: number; // px, at the image's scale
  lineHeight: number; // multiple of size
  letterSpacing?: number; // em
  color?: string;
}

const UI_FONT = '-apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';

/** Break text into lines that fit `maxWidth`, one character at a time (CJK has no spaces). */
function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number, spacing: number): string[] {
  const lines: string[] = [];
  for (const para of text.split("\n")) {
    let line = "";
    for (const ch of para) {
      const next = line + ch;
      if (line && ctx.measureText(next).width + spacing * next.length > maxWidth) {
        lines.push(line);
        line = ch;
      } else line = next;
    }
    lines.push(line);
  }
  return lines;
}

function drawText(ctx: CanvasRenderingContext2D, b: TextBlock, x: number, y: number, width: number): number {
  if (b.label) {
    ctx.font = `600 22px ${UI_FONT}`;
    ctx.fillStyle = b.color ?? "#1a1a1a";
    ctx.globalAlpha = 0.6;
    ctx.fillText(b.label, x, y + 22);
    ctx.globalAlpha = 1;
    y += 46;
  }
  ctx.font = `${b.weight} ${b.size}px "${b.family}", ${UI_FONT}`;
  ctx.fillStyle = b.color ?? "#1a1a1a";
  const spacing = (b.letterSpacing ?? 0) * b.size;
  if ("letterSpacing" in ctx) (ctx as unknown as { letterSpacing: string }).letterSpacing = `${spacing}px`;
  const lineH = b.size * b.lineHeight;
  for (const line of wrap(ctx, b.text, width, spacing)) {
    ctx.fillText(line, x, y + b.size);
    y += lineH;
  }
  if ("letterSpacing" in ctx) (ctx as unknown as { letterSpacing: string }).letterSpacing = "0px";
  return y;
}

/**
 * Lay out columns of text blocks and return a canvas.
 * columns: each column is a list of blocks drawn top to bottom.
 * perRow: how many columns sit side by side before wrapping to a new row.
 */
export function renderImage(
  columns: TextBlock[][],
  { width = 1600, perRow = columns.length, background = "#FAFAF8", ink = "#1a1a1a" } = {},
): HTMLCanvasElement {
  const pad = 80;
  const gap = 64;
  const colW = (width - pad * 2 - gap * (perRow - 1)) / perRow;
  // First pass on a scratch canvas to measure each column's height
  const scratch = document.createElement("canvas").getContext("2d")!;
  const heights = columns.map((col) => {
    let y = 0;
    for (const b of col) y = drawText(scratch, b, 0, y, colW) + 32;
    return y;
  });
  const rows: number[] = [];
  for (let i = 0; i < columns.length; i += perRow) rows.push(Math.max(...heights.slice(i, i + perRow)));
  const height = pad * 2 + rows.reduce((a, b) => a + b, 0) + gap * (rows.length - 1) + 60;

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = Math.ceil(height);
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = background;
  ctx.fillRect(0, 0, width, canvas.height);
  ctx.fillStyle = "#C23B22";
  ctx.fillRect(0, 0, 10, canvas.height); // the site's accent stripe

  let rowTop = pad;
  rows.forEach((rowH, r) => {
    for (let c = 0; c < perRow; c++) {
      const col = columns[r * perRow + c];
      if (!col) break;
      let y = rowTop;
      for (const b of col) y = drawText(ctx, { ...b, color: b.color ?? ink }, pad + c * (colW + gap), y, colW) + 32;
    }
    rowTop += rowH + gap;
  });

  ctx.font = `22px ${UI_FONT}`;
  ctx.fillStyle = ink;
  ctx.globalAlpha = 0.5;
  ctx.textAlign = "right";
  ctx.fillText("字相 · zixiangfont.com", width - pad, canvas.height - 40);
  ctx.globalAlpha = 1;
  return canvas;
}

/**
 * Draw an on-screen box (e.g. the 搭配预览 sample) as a picture with the SAME
 * proportions: each text child keeps its font, size, line height and colour,
 * all enlarged by one factor so the picture is sharp. The site's address
 * goes small in the bottom padding, so the shape doesn't change.
 */
export function renderBox(box: HTMLElement, targetWidth = 1200): HTMLCanvasElement {
  const k = Math.min(5, Math.max(2, targetWidth / box.offsetWidth));
  const bs = getComputedStyle(box);
  const pad = { top: parseFloat(bs.paddingTop), left: parseFloat(bs.paddingLeft), bottom: parseFloat(bs.paddingBottom) };
  const gap = parseFloat(bs.rowGap) || 0;
  const innerW = box.clientWidth - pad.left - parseFloat(bs.paddingRight);
  const blocks = [...box.children].filter((c): c is HTMLElement => c instanceof HTMLElement && !!c.textContent?.trim());

  // What the page background behind the box looks like (light or dark mode)
  let bg = "rgba(0, 0, 0, 0)";
  for (let n: HTMLElement | null = box; n && bg.endsWith(", 0)"); n = n.parentElement) bg = getComputedStyle(n).backgroundColor;
  if (bg.endsWith(", 0)")) bg = getComputedStyle(document.body).backgroundColor;

  const scratch = document.createElement("canvas").getContext("2d")!;
  const laid = blocks.map((el) => {
    const s = getComputedStyle(el);
    const size = parseFloat(s.fontSize);
    const lineH = s.lineHeight === "normal" ? size * 1.3 : parseFloat(s.lineHeight);
    const spacing = s.letterSpacing === "normal" ? 0 : parseFloat(s.letterSpacing);
    const font = `${s.fontWeight} ${size * k}px ${s.fontFamily}`;
    scratch.font = font;
    const lines = wrap(scratch, el.innerText.replace(/\n$/, ""), innerW * k, spacing * k);
    return { font, color: s.color, lineH: lineH * k, spacing: spacing * k, lines };
  });
  const contentH = laid.reduce((h, b) => h + b.lines.length * b.lineH, 0) + gap * k * Math.max(0, laid.length - 1);

  const canvas = document.createElement("canvas");
  canvas.width = Math.round(box.offsetWidth * k);
  canvas.height = Math.round((pad.top + pad.bottom) * k + contentH);
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.textBaseline = "middle";
  let y = pad.top * k;
  for (const b of laid) {
    ctx.font = b.font;
    ctx.fillStyle = b.color;
    if ("letterSpacing" in ctx) (ctx as unknown as { letterSpacing: string }).letterSpacing = `${b.spacing}px`;
    for (const line of b.lines) {
      ctx.fillText(line, pad.left * k, y + b.lineH / 2);
      y += b.lineH;
    }
    y += gap * k;
  }
  if ("letterSpacing" in ctx) (ctx as unknown as { letterSpacing: string }).letterSpacing = "0px";
  // The address, small, inside the bottom padding
  ctx.font = `${Math.min(pad.bottom * 0.55, 10) * k}px ${UI_FONT}`;
  ctx.fillStyle = laid[0]?.color ?? "#1a1a1a";
  ctx.globalAlpha = 0.45;
  ctx.textAlign = "right";
  ctx.fillText("字相 · zixiangfont.com", canvas.width - pad.left * k, canvas.height - (pad.bottom * k) / 2);
  ctx.globalAlpha = 1;
  return canvas;
}

/** Save a canvas as a PNG download. */
export function downloadCanvas(canvas: HTMLCanvasElement, filename: string) {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, "image/png");
}
