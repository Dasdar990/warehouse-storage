/**
 * Walls are stored (and rendered on the real map, see WarehouseMap/FreeformMap)
 * as a rotated rectangle: { x, y, width, height, rotation }, where width is
 * the wall's length, height is its thickness, and (x, y) is the corner of
 * the un-rotated rectangle.
 *
 * The room/zone/shelf editors, on the other hand, want to let someone drag
 * a wall by its two endpoints -- a much more natural editing UX for a
 * straight wall segment. These helpers convert between the two shapes so
 * every editor can work in endpoint coordinates while still reading/writing
 * the exact same rect format the rest of the app (and the backend) expects.
 */

export interface WallRect {
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
}

export interface WallEndpoints {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Default thickness (px) used when a wall is created purely from two
 *  endpoints and no thickness has been picked yet. */
export const DEFAULT_WALL_THICKNESS = 14;

/** Rect -> the two endpoints of its centerline, in world coordinates. */
export function wallToEndpoints(wall: WallRect): WallEndpoints {
  const rad = (wall.rotation * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const halfThickness = wall.height / 2;
  return {
    x1: wall.x - halfThickness * sin,
    y1: wall.y + halfThickness * cos,
    x2: wall.x + wall.width * cos - halfThickness * sin,
    y2: wall.y + wall.width * sin + halfThickness * cos,
  };
}

/** The exact inverse of `wallToEndpoints`, given a thickness to use. */
export function endpointsToWall(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  thickness: number = DEFAULT_WALL_THICKNESS,
): WallRect {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const width = Math.max(1, Math.hypot(dx, dy));
  const rotation = (Math.atan2(dy, dx) * 180) / Math.PI;
  const rad = (rotation * Math.PI) / 180;
  const halfThickness = thickness / 2;
  return {
    x: x1 + halfThickness * Math.sin(rad),
    y: y1 - halfThickness * Math.cos(rad),
    width,
    height: thickness,
    rotation,
  };
}
