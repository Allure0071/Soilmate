import test from 'node:test'
import assert from 'node:assert/strict'
import { toGcj02, toWgs84, tileWarpGrid } from './coordinates.js'

test('China display coordinates round-trip to original scientific coordinates', () => {
  for (const point of [[116.397, 39.908], [113.2644, 23.1291], [121.4737, 31.2304], [87.6168, 43.8256], [91.1322, 29.6604]]) {
    const unchanged = point.slice()
    const gcj = toGcj02(point)
    assert.ok(Math.abs(gcj[0] - point[0]) > .001)
    const original = toWgs84(gcj)
    assert.ok(Math.abs(original[0] - point[0]) < 1e-6)
    assert.ok(Math.abs(original[1] - point[1]) < 1e-6)
    assert.deepEqual(point, unchanged, 'source coordinate arrays remain usable')
  }
  assert.deepEqual(toGcj02([-0.1276, 51.5072]), [-0.1276, 51.5072])
})

test('scientific tile meshes share exact edges and invert the GCJ display grid', () => {
  const coords = { x: 210, y: 97, z: 8 }
  const grid = tileWarpGrid(coords)
  const neighbour = tileWarpGrid({ ...coords, x: coords.x + 1 })
  const world = 256 * 2 ** coords.z
  for (let y = 0; y < grid.length; y++) {
    assert.equal(grid[y].at(-1).sourceX, neighbour[y][0].sourceX)
    assert.equal(grid[y].at(-1).sourceY, neighbour[y][0].sourceY)
    for (const sample of grid[y]) {
      const source = [sample.sourceX / world * 360 - 180, Math.atan(Math.sinh(Math.PI * (1 - 2 * sample.sourceY / world))) * 180 / Math.PI]
      const target = toGcj02(source)
      const targetX = (target[0] + 180) / 360 * world
      const targetY = (1 - Math.log(Math.tan(Math.PI / 4 + target[1] * Math.PI / 360)) / Math.PI) / 2 * world
      assert.ok(Math.abs(targetX - (coords.x * 256 + sample.x)) < .001)
      assert.ok(Math.abs(targetY - (coords.y * 256 + sample.y)) < .001)
    }
  }
})
