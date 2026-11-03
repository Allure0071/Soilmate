import test from 'node:test'
import assert from 'node:assert/strict'
import { localDataPath, mapDataPath, readDataLocation, resourceDataPath } from './dataNavigation.js'
test('map/resource links preserve exact layer, resolution, view and catalog filters without recursive return URLs',()=>{
 const catalog='/resources?category=soil&q=pH&page=3&sort=name&res=1'
 const map=mapDataPath('soil_ph',1,[31.123456,118.987654,7],catalog)
 const state=readDataLocation(map.split('?')[1])
 assert.equal(state.key,'soil_ph');assert.equal(state.res,1);assert.deepEqual(state.center,[31.12346,118.98765,7]);assert.equal(state.resourceReturn,catalog)
 const resource=resourceDataPath('soil_ph',1,map,catalog),url=new URL(resource,'https://soilmate.invalid')
 assert.equal(url.searchParams.get('q'),'pH');assert.equal(url.searchParams.get('page'),'3')
 assert.equal(new URL(url.searchParams.get('mapReturn'),'https://soilmate.invalid').searchParams.has('resourceReturn'),false)
})
test('navigation rejects foreign return destinations and impossible coordinates',()=>{
 for(const value of ['https://evil.test/resources','//evil.test/resources','/\\evil.test/resources','/research',null]) assert.equal(localDataPath(value,'/resources'),'')
 assert.equal(readDataLocation('?res=9&view=999,20,90').res,5);assert.equal(readDataLocation('?view=999,20,90').center,null)
 assert.equal(new URL(mapDataPath('soil_ph',5,null,'https://evil.test/resources'),'https://soilmate.invalid').searchParams.has('resourceReturn'),false)
})
