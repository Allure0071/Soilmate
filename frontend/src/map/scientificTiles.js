import { tileWarpGrid } from './coordinates.js'

function drawTriangle(context, image, points, originX, originY) {
  const [p, q, r] = points
  const sx = p.sourceX - originX, sy = p.sourceY - originY
  const ux = q.sourceX - p.sourceX, uy = q.sourceY - p.sourceY
  const vx = r.sourceX - p.sourceX, vy = r.sourceY - p.sourceY
  const determinant = ux * vy - vx * uy
  const a = ((q.x - p.x) * vy - (r.x - p.x) * uy) / determinant
  const c = ((r.x - p.x) * ux - (q.x - p.x) * vx) / determinant
  const b = ((q.y - p.y) * vy - (r.y - p.y) * uy) / determinant
  const d = ((r.y - p.y) * ux - (q.y - p.y) * vx) / determinant
  context.save()
  context.beginPath()
  context.moveTo(p.x, p.y); context.lineTo(q.x, q.y); context.lineTo(r.x, r.y)
  context.closePath(); context.clip()
  context.setTransform(a, b, c, d, p.x - a * sx - c * sy, p.y - b * sx - d * sy)
  context.drawImage(image, 0, 0)
  context.restore()
}

export function createScientificTileLayer(L, url, options) {
  const tasks = new WeakMap()
  const WarpedLayer = L.GridLayer.extend({
    createTile(coords, done) {
      const tile = document.createElement('canvas')
      tile.width = tile.height = 256
      const grid = tileWarpGrid(coords)
      const points = grid.flat()
      const left = Math.floor(Math.min(...points.map(p => p.sourceX)) / 256)
      const top = Math.floor(Math.min(...points.map(p => p.sourceY)) / 256)
      const right = Math.floor(Math.max(...points.map(p => p.sourceX)) / 256)
      const bottom = Math.floor(Math.max(...points.map(p => p.sourceY)) / 256)
      const atlas = document.createElement('canvas')
      atlas.width = (right - left + 1) * 256
      atlas.height = (bottom - top + 1) * 256
      const atlasContext = atlas.getContext('2d')
      const images = [], pending = []
      let cancelled = false
      tasks.set(tile, () => { cancelled = true; for (const image of images) if (!image.complete) image.src = '' })
      for (let y = top; y <= bottom; y++) for (let x = left; x <= right; x++) {
        const image = new Image()
        image.crossOrigin = 'anonymous'
        images.push(image)
        pending.push(new Promise((resolve, reject) => {
          image.onload = () => { if (!cancelled) atlasContext.drawImage(image, (x - left) * 256, (y - top) * 256, 256, 256); resolve() }
          image.onerror = () => reject(new Error('Scientific tile unavailable'))
          const count = 2 ** coords.z
          image.src = L.Util.template(url, { z: coords.z, x: ((x % count) + count) % count, y })
        }))
      }
      Promise.all(pending).then(() => {
        if (cancelled) return
        const context = tile.getContext('2d')
        context.imageSmoothingEnabled = false
        // Adjacent clipped triangles share anti-aliased edge coverage. Adding
        // their premultiplied pixels avoids transparent seams in the mesh.
        context.globalCompositeOperation = 'lighter'
        for (let y = 0; y < grid.length - 1; y++) for (let x = 0; x < grid[y].length - 1; x++) {
          const p = grid[y][x], q = grid[y][x + 1], r = grid[y + 1][x], s = grid[y + 1][x + 1]
          drawTriangle(context, atlas, [p, q, r], left * 256, top * 256)
          drawTriangle(context, atlas, [q, s, r], left * 256, top * 256)
        }
        tasks.delete(tile)
        done(null, tile)
      }, error => { tasks.delete(tile); if (!cancelled) done(error, tile) })
      return tile
    },
  })
  const layer = new WarpedLayer(options)
  layer.on('tileunload', ({ tile }) => { tasks.get(tile)?.(); tasks.delete(tile) })
  return layer
}
