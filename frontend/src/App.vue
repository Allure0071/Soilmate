<template>
  <div class="app-shell">
    <div ref="siteContentRef" class="site-content" :class="{ 'site-content-home': siteView==='home', 'site-content-map': siteView==='explore'||siteView==='gold', 'site-content-research': siteView==='analysis'||siteView==='trace' }">
    <HomeLanding v-if="siteView==='home'" :account="account" @navigate="navigateFromLanding" />
    <header v-if="siteView!=='home'" class="topbar" :class="{ 'topbar-research': siteView==='analysis'||siteView==='trace', 'topbar-map': siteView==='explore'||siteView==='gold' }" :inert="soiledgeOpen || scientificOpen">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><path d="M4 20c4-9 10-14 17-14 8 0 14 6 15 14-1 8-7 14-15 14C14 34 8 29 4 20Z"/><path d="M10 20c3-6 7-9 12-9 5 0 9 4 10 9-1 5-5 9-10 9-5 0-9-3-12-9Z"/><path d="M16 20c2-2 4-4 7-4s5 2 6 4c-1 3-3 5-6 5s-5-2-7-5Z"/></svg></div>
        <div class="brand-copy"><strong>壤脉天玑</strong><span>SOILMATE</span></div>
      </div>
      <nav class="primary-nav" aria-label="主站导航">
        <button type="button" :class="{active:siteView==='home'}" @click="openMainView('home')">首页</button>
        <button type="button" :class="{active:siteView==='explore'}" @click="openMainView('explore')">探索数据</button>
        <button type="button" :class="{active:siteView==='gold'}" @click="openMainView('gold')">数据资源</button>
        <button type="button" :class="{active:siteView==='analysis'}" @click="openResearch('analysis')">分析中心</button>
        <button type="button" :class="{active:siteView==='trace'}" @click="openResearch('trace')">证据追溯</button>
      </nav>
      <div class="topbar-right">
        <div class="resolution-switch" role="group" aria-label="数据分辨率"><button v-for="value in [5, 1]" :key="value" type="button" :class="{ active: resolution === value }" :aria-pressed="resolution === value" @click="changeResolution(value)">{{ value }} km</button></div>

        <span class="connection" :class="apiState"><i></i>{{ apiState === 'ready' ? '已连接' : apiState === 'loading' ? '正在连接' : '连接中断' }}</span>
        <button class="mobile-catalog-toggle" type="button" @click="catalogOpen = !catalogOpen" :aria-expanded="catalogOpen" aria-label="切换图层目录"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
      </div>
      <div class="account-nav">
        <a v-if="!account" href="/account/index.html?next=/analysis">登录 / 注册</a>
        <template v-else><span :title="account.email">{{ account.email }}</span><button type="button" @click="logout">退出</button></template>
      </div>
    </header>

    <main v-show="siteView==='explore'||siteView==='gold'" class="workspace" :inert="soiledgeOpen || scientificOpen" :class="{ 'has-point': !!clicked }">
      <nav class="navigation-rail" aria-label="工作区工具">
        <button ref="layerTrigger" type="button" :class="{ active: catalogOpen }" :aria-expanded="catalogOpen" aria-controls="layer-drawer" title="探索图层" aria-label="探索图层" @click="catalogOpen = !catalogOpen"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h7v7H4zM13 5h7v7h-7zM4 14h7v6H4zM13 14h7v6h-7z"/></svg></button>
        <button type="button" title="搜索指标" aria-label="搜索指标" @click="openLayerSearch"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.3"/><path d="m16 16 4.2 4.2"/></svg></button>
        <button type="button" title="重置地图范围" aria-label="重置地图范围" @click="resetMapView"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2.3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg></button>
        <span class="rail-spacer"></span><span class="rail-resolution">{{ resolution }} km</span>
      </nav>
      <div v-if="catalogOpen" class="drawer-scrim" aria-hidden="true" @click="catalogOpen = false"></div>
      <aside id="layer-drawer" ref="catalogRef" class="catalog" :class="{ 'catalog-open': catalogOpen }" role="dialog" aria-modal="true" aria-label="图层目录" tabindex="-1" :inert="!catalogOpen" @keydown="handleDrawerKeydown" @touchstart.passive="onDrawerTouchStart" @touchend.passive="onDrawerTouchEnd">
        <button class="drawer-close" type="button" aria-label="关闭图层目录" @click="catalogOpen = false">×</button>
        <div class="catalog-intro"><h1>探索图层</h1></div>
        <div class="catalog-search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.3"/><path d="m16 16 4.2 4.2"/></svg><input v-model="search" type="search" placeholder="搜索指标或代码" aria-label="搜索指标或代码" /></div>
        <div class="category-tabs" role="tablist" aria-label="图层分类"><button v-for="category in categories" :key="category.id" type="button" role="tab" :aria-selected="activeCategory === category.id" :class="{ active: activeCategory === category.id }" @click="activeCategory = category.id">{{ category.label }}</button></div>
        <div class="list-meta"><span>{{ activeCategory === 'all' ? '全部图层' : categories.find(c => c.id === activeCategory)?.label }}</span><span>{{ filteredIndicators.length }} 已登记 · {{ filteredPreviewLayers.length }} 预览</span></div>
        <div class="indicator-list">
          <div v-if="filteredPreviewLayers.length" class="preview-list">
            <span class="section-kicker">研究预览 · 不参与评分</span>
            <button v-for="layer in previewPrimaryLayers" :key="layer.id" type="button" class="indicator-item preview-item" :class="{ active: selectedPreviewId === layer.id }" @click="choosePreview(layer.id)"><span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ layer.name }}</strong><small>{{ layer.unit }} · 5 km 对齐</small></span></button>
            <button v-if="previewAdditionalLayers.length" type="button" class="preview-more" :aria-expanded="showMorePreviews || !!search.trim()" @click="showMorePreviews = !showMorePreviews">{{ showMorePreviews || search.trim() ? '收起' : '查看' }}更多年份与土层（{{ previewAdditionalLayers.length }}）</button>
            <template v-if="showMorePreviews || search.trim()"><button v-for="layer in previewAdditionalLayers" :key="layer.id" type="button" class="indicator-item preview-item" :class="{ active: selectedPreviewId === layer.id }" @click="choosePreview(layer.id)"><span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ layer.name }}</strong><small>{{ layer.unit }} · 5 km 对齐</small></span></button></template>
          </div>
          <div v-if="apiState === 'loading'" class="catalog-state"><span class="state-spinner"></span><strong>正在读取图层</strong><small>请稍候，正在连接数据服务</small></div>
          <div v-else-if="apiState === 'error'" class="catalog-state"><span class="state-icon">!</span><strong>数据服务暂不可用</strong><small>{{ indicatorError }}</small><button type="button" @click="loadIndicators">重新连接</button></div>
          <div v-else-if="!filteredIndicators.length" class="catalog-state"><span class="state-icon">∅</span><strong>没有找到匹配图层</strong><small>试试其他关键词或分类</small></div>
          <button v-for="ind in filteredIndicators" :key="ind.col_name" type="button" class="indicator-item" :class="{ active: selectedKey === ind.col_name }" @click="chooseIndicator(ind.col_name)">
            <span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ displayName(ind.col_name, ind.cname || ind.name) }}</strong></span>
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m7 4 6 6-6 6"/></svg>
          </button>
        </div>
        <div class="catalog-foot"><span class="foot-orbit" aria-hidden="true"></span><span>{{ resolution }} km 网格数据 · 全国范围</span></div>
      </aside>

      <section class="map-stage" aria-label="土壤指标地图">
        <div id="map"></div>
        <div class="map-tools"><span class="map-tools-title">{{ selectedPreview?.name || (selected ? displayName(selected.col_name, selected.cname || selected.name) : '中国土壤空间分布') }}</span><button type="button" @click="catalogOpen = true">切换图层 <span aria-hidden="true">↗</span></button><button type="button" :aria-pressed="zonesVisible" :disabled="zonesLoading" @click="toggleReferenceZones">{{ zonesLoading ? '加载分区…' : zonesVisible ? '隐藏参考分区' : '参考分区' }}</button></div>
        <div v-if="zoneError" class="map-tile-note map-zone-error" role="status">{{ zoneError }}</div>
        <div v-if="tileAvailability === false && !selectedPreviewId" class="map-tile-note" role="status">专题图层暂未提供 · 可点选查询数据</div>
        <div class="map-coordinate">{{ cursorCoords || '移动鼠标查看坐标' }}</div>
        <div v-if="selected && legend && tileAvailability !== false" class="map-legend">
          <div class="legend-title"><span>{{ displayName(selected.col_name, selected.cname || selected.name) }}</span><strong>{{ displayUnit(selected.col_name, selected.unit) || (/(^|_)soil_ph$/.test(selected.col_name) ? '无量纲' : '单位待核实') }}</strong></div>
          <div class="legend-gradient" :style="{ background: isCategorical ? categoryLegendCss : legendCss }"></div>
          <div class="legend-range"><span>{{ fmt(displayValue(selected.col_name, legend.min)) }}</span><span>{{ fmt(displayValue(selected.col_name, legend.max)) }}</span></div>
          <div class="legend-opacity"><label for="opacity">图层透明度</label><input id="opacity" v-model.number="layerOpacity" type="range" min="20" max="100" @input="updateOpacity"/><span>{{ layerOpacity }}%</span></div>
        </div>
        <div v-if="selectedPreview" class="map-legend preview-legend"><div class="legend-title"><span>{{ selectedPreview.name }}</span><strong>{{ selectedPreview.unit }}</strong></div><div class="legend-gradient" :style="{ background: previewLegendCss }"></div><div class="legend-range"><span>{{ selectedPreview.range[0] }}</span><span>{{ selectedPreview.range[1] }}</span></div><p>研究预览 · 不参与评分</p></div>
        <div class="map-attribution">数据视图 · WGS84 坐标</div>
      </section>

      <aside class="inspector" :class="`sheet-${sheetState}`" aria-label="点位分析结果">
        <div class="inspector-head"><div><span class="section-kicker">{{ siteView==='home' && !clicked ? 'SOILMATE / OVERVIEW' : '点位数据' }}</span><h2>{{ siteView==='home' && !clicked ? '研究总览' : '位置剖面' }}</h2></div><button class="sheet-toggle" type="button" :aria-label="sheetState === 'full' ? '收起分析面板' : '展开分析面板'" @click="cycleSheet">{{ sheetState === 'full' ? '收起' : '展开' }} <span aria-hidden="true">{{ sheetState === 'full' ? '⌄' : '⌃' }}</span></button></div>
        <section v-if="!clicked && siteView==='home'" class="home-overview" aria-labelledby="home-title">
          <div class="home-intro">
            <span class="section-kicker">研究方向 / NITROGEN CYCLE</span>
            <h3 id="home-title">农田土壤氮循环功能研究</h3>
            <p>从土壤指标到微生物功能线索，沿着可追溯的证据路径开展分析。</p>
          </div>
          <div class="home-research-path" aria-label="研究路径">
            <span><b>01</b>筛选土壤指标</span>
            <span><b>02</b>核验样本来源</span>
            <span><b>03</b>联合验证线索</span>
          </div>
          <button type="button" class="home-analysis-link" @click="openResearch('analysis')">进入分析中心 <span aria-hidden="true">→</span></button>
          <section class="home-task-list" aria-labelledby="home-tasks-title">
            <div class="home-task-heading"><h4 id="home-tasks-title">最近研究任务</h4><button type="button" @click="openResearch('trace')">全部记录 <span aria-hidden="true">→</span></button></div>
            <p v-if="!account" class="home-task-state">登录后查看你的研究任务。<a href="/account/index.html?next=/analysis">登录 / 注册</a></p>
            <p v-else-if="homeResearch.loading" class="home-task-state" role="status">正在读取已保存任务…</p>
            <p v-else-if="homeResearch.error" class="home-task-state home-task-error" role="status">任务记录暂不可用：{{ homeResearch.error }}</p>
            <p v-else-if="!homeResearch.runs.length" class="home-task-state">尚无已保存分析任务。运行分析后，任务状态会显示在这里。</p>
            <ul v-else><li v-for="run in homeResearch.runs" :key="run.id"><span><b>{{ run.kind==='nshi'?'土壤指标筛选':'KO 通路结构分析' }}</b><small>{{ run.project_name }} · {{ run.dataset_id }}</small></span><em :class="`task-${run.status}`">{{ researchStatusLabel(run.status) }}</em></li></ul>
          </section>
        </section>
        <div v-else-if="!clicked" class="inspector-empty"><div class="empty-target" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M16 27s9-7.6 9-15a9 9 0 1 0-18 0c0 7.4 9 15 9 15Z" stroke="currentColor" stroke-width="1.7"/><circle cx="16" cy="12" r="3.2" stroke="currentColor" stroke-width="1.7"/></svg></div><strong>选取地图位置</strong><p>点击地图，查看该位置的土壤指标。</p></div>
        <template v-else>
          <div class="point-summary"><div class="point-label"><span class="point-signal"></span>{{ loading ? '正在解析位置' : pointError ? '查询暂不可用' : clicked.found ? '已定位数据点' : '该位置暂无数据' }}</div><div class="point-coords"><strong>{{ clicked.lat.toFixed(4) }}° N</strong><strong>{{ clicked.lon.toFixed(4) }}° E</strong></div><div v-if="clicked.gridId" class="point-grid-id">栅格 ID · {{ clicked.gridId }}</div><div class="point-separator"></div><div class="point-stats"><div><b>{{ loading ? '···' : validEntries.length }}</b><span>有效指标</span></div><div><b>{{ loading ? '···' : nullCount }}</b><span>无数据</span></div></div></div>
          <div v-if="pointError" class="result-error"><span>{{ pointError }}</span><button type="button" @click="retryPoint">重试</button></div>
          <div v-if="loading" class="result-loading"><span class="state-spinner"></span>正在读取此位置的数据…</div>
          <template v-else-if="clicked.found">
            <div v-if="selected && selectedPointValue != null" class="featured-value"><span>当前图层 · {{ displayName(selected.col_name, selected.cname || selected.name) }}</span><div><strong>{{ fmt(selectedPointValue) }}</strong><small>{{ displayUnit(selected.col_name, selected.unit) }}</small></div></div>
            <section class="assessment-section"><span class="section-kicker">核心指标</span><h3>土壤指标</h3><div class="core-grid"><button v-for="item in coreIndicators" :key="item.id" type="button" class="core-metric" :aria-expanded="expandedMetric === item.id" @click="expandedMetric = expandedMetric === item.id ? '' : item.id"><span>{{ item.label }}</span><strong>{{ item.value == null ? '—' : fmt(item.value) }} <small>{{ item.unit }}</small></strong><em>{{ item.status }} · {{ expandedMetric === item.id ? '收起' : '详情' }}</em><span v-if="expandedMetric === item.id" class="metric-detail">来源：{{ item.source || '待确认' }}<br>年份：{{ item.year || '待确认' }}<br>土层：{{ item.depth || '待确认' }}</span></button></div></section>
            <details :key="`${clicked.lat}:${clicked.lon}:${resolution}`" class="other-indicators"><summary><span><b>其他指标</b></span><span class="other-count">{{ otherEntries.length + otherNullEntries.length }} 项 <i aria-hidden="true">⌄</i></span></summary><div class="other-content"><div class="result-tabs" role="tablist" aria-label="其他指标分类"><button v-for="category in categories" :key="category.id" type="button" role="tab" :aria-selected="activeResultCategory === category.id" :class="{ active: activeResultCategory === category.id }" @click="activeResultCategory = category.id">{{ category.label }}</button></div><div class="result-list"><div v-for="[key, item] in filteredEntries" :key="key" class="result-row"><span>{{ displayName(key, item.cname || item.name) }}</span><strong>{{ fmt(displayValue(key, item.value)) }}<small>{{ displayUnit(key, item.unit) }}</small></strong></div><p v-if="!filteredEntries.length" class="results-empty">此分类在该位置没有有效值。</p><button v-if="otherNullEntries.length" type="button" class="missing-toggle" :aria-expanded="showNulls" @click="showNulls = !showNulls">{{ showNulls ? '收起' : '查看' }} {{ otherNullEntries.length }} 项无数据指标 <span>{{ showNulls ? '↑' : '↓' }}</span></button><template v-if="showNulls"><div v-for="[key, item] in otherNullEntries" :key="key" class="result-row missing"><span>{{ displayName(key, item.cname || item.name) }}</span><strong>—</strong></div></template></div></div></details>
            <section class="assessment-section"><span class="section-kicker">区域背景</span><h3>区域指标</h3><p v-if="clicked.z01" class="region-name">Z01 参考区划 · {{ clicked.z01.source_name }}<small> · {{ clicked.z01.code }}</small></p><p v-if="clicked.z01" class="regional-caveat">来源区划按 1 km 网格定位，边界附近可能有偏差；与模型九大区的映射尚未核验，不参与 N + X 评分。</p><p v-if="clicked.regionName" class="region-name">模型农业区 · {{ clicked.regionName }}<small v-if="clicked.regionId"> · {{ clicked.regionId }}</small></p><p v-if="!clicked.regionName" class="assessment-note">当前尚无可核验的模型农业区映射；区域扩展指标待接入。</p><p v-else-if="!regionalIndicators.length" class="assessment-note">该农业区尚无已核对的 X 指标配置。</p><div v-else class="regional-list"><div v-for="item in regionalIndicators" :key="item.label" class="regional-row"><span>{{ item.label }}</span><strong>{{ item.value == null ? '待接入' : `${fmt(item.value)} ${item.unit}` }}</strong></div></div><p v-if="regionalIndicators.length" class="regional-caveat">区域归属来自点位接口；X 清单来自项目指标审计。仅展示对应字段的返回值，其余不参与评分。</p></section>
            <section class="assessment-section"><span class="section-kicker">SOIL HEALTH ASSESSMENT</span><h3>土壤健康评价</h3><div class="assessment-modes" role="group" aria-label="评价模式"><button type="button" :class="{ active: assessmentMode === 'base' }" @click="assessmentMode = 'base'">Base-SHI</button><button type="button" :class="{ active: assessmentMode === 'regional' }" @click="assessmentMode = 'regional'">N + X</button></div><div class="score-pending"><strong>—</strong><div><b>评分规则待核验</b><p>{{ assessmentMode === 'base' ? '尚未接入经过核验的基础评分规则与结果。' : '区域映射与扩展指标未完整接入，暂不能计算 N + X。' }}</p></div></div></section>
          </template>
          <div v-else class="unavailable-analysis"><span class="section-kicker">核心指标</span><h3>数据尚未返回</h3><p>位置已经在地图上标记。服务恢复后，可在此查看土壤指标与区域评价。</p><div class="pending-metrics"><span v-for="item in coreDefinitions" :key="item.id">{{ item.label }}<b>—</b></span></div><div class="pending-score"><span class="section-kicker">SOIL HEALTH ASSESSMENT</span><strong>评分待评估</strong><small>没有真实指标和核验规则时，不生成分数。</small></div></div>
        </template>
      </aside>
    </main>
    <ResearchWorkspace v-if="account && (siteView==='analysis'||siteView==='trace')" :key="siteView" :trace-only="siteView==='trace'" :map-point="clicked" :csrf-token="csrfToken" @back="openMainView('explore')" />
    <div v-if="soiledgeOpen" class="edge-backdrop"><SoiledgeWorkbench @close="soiledgeOpen = false" /></div>
    <ScientificWorkbench v-if="scientificOpen" :key="scientificTab" :initial-tab="scientificTab" :point="clicked" :resolution="resolution" :preview-values="previewValues" @close="scientificOpen=false;siteView='explore'" />
    <div v-if="dataBrowserOpen" class="browser-backdrop">
      <section ref="browserRef" class="data-browser" role="dialog" aria-modal="true" aria-labelledby="browser-title" tabindex="-1" @keydown="handleBrowserKeydown">
        <header class="browser-head"><div><h2 id="browser-title">数据资源</h2></div><button type="button" class="browser-close" aria-label="返回地图" @click="closeDataBrowser">返回地图 ×</button></header>
        <div class="browser-tabs" role="tablist" aria-label="数据资源内容"><button type="button" role="tab" :aria-selected="browserTab === 'layers'" :class="{ active: browserTab === 'layers' }" @click="browserTab = 'layers'">指标目录 <span>{{ indicators.length }}</span></button><button type="button" role="tab" :aria-selected="browserTab === 'database'" :class="{ active: browserTab === 'database' }" @click="browserTab = 'database'">原始表浏览</button></div>
        <template v-if="browserTab === 'layers'">
          <div class="browser-layer-tools"><label>查找指标<input v-model="browserSearch" type="search" placeholder="名称、字段代码或来源文件" /></label><div class="catalog-filters" role="group" aria-label="指标类别"><button v-for="category in categories" :key="category.id" type="button" :class="{ active: catalogCategory === category.id }" :aria-pressed="catalogCategory === category.id" @click="catalogCategory = category.id">{{ category.label }}</button></div><span>{{ filteredBrowserIndicators.length }} / {{ indicators.length }} 项</span></div>
          <div class="product-catalog">
            <div class="product-list" aria-label="指标产品列表"><button v-for="item in filteredBrowserIndicators" :key="item.col_name" type="button" :class="{ active: catalogSelected?.col_name === item.col_name }" :aria-pressed="catalogSelected?.col_name === item.col_name" @click="selectedCatalogKey = item.col_name"><span class="product-list-title">{{ displayName(item.col_name, item.cname || item.name) }}</span><span class="product-list-meta">{{ item.col_name }} · {{ catalogUnit(item) }}</span></button><div v-if="apiState === 'loading'" class="product-list-state">正在读取指标目录…</div><div v-else-if="apiState === 'error'" class="product-list-state">{{ indicatorError }} <button type="button" @click="loadIndicators">重试</button></div><div v-else-if="!filteredBrowserIndicators.length" class="product-list-state">没有匹配的指标，请调整关键词或类别。</div></div>
            <article v-if="catalogSelected" class="product-detail"><div class="product-detail-head"><div><span class="section-kicker">指标产品 / {{ groupLabel(catalogSelected.col_name) }}</span><h3>{{ displayName(catalogSelected.col_name, catalogSelected.cname || catalogSelected.name) }}</h3><p>{{ catalogSelected.col_name }} · {{ resolution }} km 网格</p></div><button type="button" class="product-map-action" @click="showCatalogLayer(catalogSelected.col_name)">在地图查看 ↗</button></div><div class="product-evidence"><strong>数据状态</strong><span>年份、土层与实测／预测属性未登记。</span></div><dl class="product-facts"><div><dt>单位</dt><dd>{{ catalogUnit(catalogSelected) }}</dd></div><div><dt>空间分辨率</dt><dd>{{ resolution }} km</dd></div><div><dt>来源文件</dt><dd>{{ catalogSelected.source_file || '待登记' }}</dd></div><div><dt>波段</dt><dd>{{ catalogSelected.band ?? '待登记' }}</dd></div><div><dt>有效像元</dt><dd>{{ catalogSelected.valid_count == null ? '未统计' : Number(catalogSelected.valid_count).toLocaleString() }}</dd></div><div><dt>数值范围</dt><dd>{{ catalogSelected.min == null || catalogSelected.max == null ? '未统计' : `${fmt(displayValue(catalogSelected.col_name, catalogSelected.min))} – ${fmt(displayValue(catalogSelected.col_name, catalogSelected.max))}` }}</dd></div><div><dt>数据年份</dt><dd>未登记</dd></div><div><dt>土层深度</dt><dd>未登记</dd></div><div><dt>属性类型</dt><dd>待核对</dd></div></dl><details class="product-detail-foot"><summary>数据说明</summary><p>有效像元数不等于独立采样点数；数值范围不代表健康阈值。目录只展示已登记信息。</p></details></article>
            <div v-else class="product-empty">选择指标查看详情</div>
          </div>
          <footer class="browser-pagination"><span>{{ resolution }} km 指标目录</span></footer>
        </template>
        <template v-else>
          <div class="db-switch" role="group" aria-label="选择数据库"><button v-for="value in [5, 1]" :key="value" type="button" :class="{ active: dbResolution === value }" :aria-pressed="dbResolution === value" @click="selectDatabase(value)">{{ value }} km 数据库</button><span>只读 · 50 行 / 页</span></div>
          <div class="db-workspace">
            <aside class="db-sidebar" aria-label="数据表"><label>查找数据表<input v-model="tableSearch" type="search" placeholder="输入表名" /></label><div class="db-table-list"><button v-for="table in filteredDbTables" :key="table.name" type="button" :class="{ active: selectedTable === table.name }" @click="selectDbTable(table.name)"><strong>{{ table.name }}</strong></button><p v-if="!filteredDbTables.length">没有匹配的数据表。</p></div></aside>
            <div class="db-main"><div class="browser-meta"><strong>{{ selectedTable || '选择左侧数据表' }}</strong><span>{{ selectedTable ? `${Number(dataResult.total || 0).toLocaleString()} 行 · ${dataResult.columns.length} 列 · 第 ${dataPage} / ${totalPages} 页` : '选择数据表后查看所有字段' }}</span></div><div v-if="dataError" class="browser-error">{{ dataError }} <button type="button" @click="loadData">重试</button></div><div class="data-table-scroll" :aria-busy="dataLoading"><table v-if="selectedTable && dataResult.columns.length"><thead><tr><th v-for="column in dataResult.columns" :key="column.col" scope="col">{{ column.cname || column.col }}<small v-if="column.cname && column.cname !== column.col">{{ column.col }}</small></th></tr></thead><tbody><tr v-for="(row, index) in dataResult.rows" :key="`${dataPage}-${index}`"><td v-for="(value, colIndex) in row" :key="colIndex">{{ formatDbCell(value) }}</td></tr></tbody></table><div v-if="dataLoading" class="table-state"><span class="state-spinner"></span>正在读取数据…</div><div v-else-if="dataError" class="table-state">当前数据表暂无法读取。</div><div v-else-if="!selectedTable" class="table-state">选择左侧数据表，查看完整字段和分页记录。</div><div v-else-if="!dataResult.rows.length" class="table-state">此表没有记录。</div></div><footer class="browser-pagination"><button type="button" :disabled="!selectedTable || dataPage <= 1 || dataLoading" @click="goToPage(dataPage - 1)">上一页</button><span>{{ dataPage }} / {{ totalPages }}</span><button type="button" :disabled="!selectedTable || dataPage >= totalPages || dataLoading" @click="goToPage(dataPage + 1)">下一页</button></footer></div>
          </div>
        </template>
      </section>
    </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, computed, nextTick, watch } from 'vue'
import SoiledgeWorkbench from './SoiledgeWorkbench.vue'
import HomeLanding from './HomeLanding.vue'
import ScientificWorkbench from './ScientificWorkbench.vue'
import ResearchWorkspace from './ResearchWorkspace.vue'
import L from 'leaflet'
import { fetchIndicators, fetchMeta, fetchPoint, fetchData, fetchPreviewLayers, fetchPreviewPoint, fetchZ01Boundaries, fetchZ01Point, previewTileUrl, tileUrl } from './api.js'
import { displayName, displayUnit, displayValue } from './dataDisplay.js'
import { regionalConfigFor } from './regionIndicatorConfig.js'
const indicators = ref([])
const siteContentRef = ref(null)
const selectedKey = ref('')
const selected = computed(() => indicators.value.find(ind => ind.col_name === selectedKey.value) || null)
const previewLayers = ref([])
const selectedPreviewId = ref('')
const selectedPreview = computed(() => previewLayers.value.find(layer => layer.id === selectedPreviewId.value) || null)
const previewValues = ref({})
const showMorePreviews = ref(false)
const clicked = ref(null)
const loading = ref(false)
const indicatorError = ref('')
const pointError = ref('')
const apiState = ref('loading')
const showNulls = ref(false)
const search = ref('')
const activeCategory = ref('all')
const activeResultCategory = ref('all')
const catalogOpen = ref(false)
const layerTrigger = ref(null)
const catalogRef = ref(null)
const assessmentMode = ref('base')
const expandedMetric = ref('')
const sheetState = ref('half')
const cursorCoords = ref('')
const layerOpacity = ref(78)
const resolution = ref(5)
const tileAvailability = ref(null)
const zonesVisible = ref(false)
const zonesLoading = ref(false)
const zoneError = ref('')
const dataBrowserOpen = ref(false)
const soiledgeOpen = ref(false)
const scientificOpen = ref(false)
const scientificTab = ref('health')
const siteView = ref(window.location.pathname === '/analysis' ? 'analysis' : window.location.pathname === '/evidence' ? 'trace' : 'home')
const homeResearch = ref({ loading: true, error: '', runs: [] })
const account = ref(null)
const csrfToken = ref('')
function accountUrl(path = '/analysis') { return '/account/index.html?next=' + encodeURIComponent(path) }
async function checkAccount() {
  try {
    const response = await fetch('/api/auth/me', { credentials: 'same-origin' })
    if (!response.ok) throw new Error('not signed in')
    const data = await response.json()
    account.value = data.user
    csrfToken.value = data.csrf_token
    loadHomeResearch()
  } catch {
    account.value = null
    csrfToken.value = ''
    homeResearch.value = { loading: false, error: '', runs: [] }
    if (['/analysis', '/evidence'].includes(window.location.pathname)) window.location.replace(accountUrl(window.location.pathname))
  }
}
async function logout() {
  try { await fetch('/api/auth/logout', { method: 'POST', headers: { 'X-CSRF-Token': csrfToken.value }, credentials: 'same-origin' }) }
  finally { account.value = null; csrfToken.value = ''; openMainView('home'); homeResearch.value = { loading: false, error: '', runs: [] } }
}
let rememberedMapView = null
function restoreMapAfterAnalysis() {
  nextTick(() => {
    if (!map) return
    map.invalidateSize({ pan: false })
    const view = rememberedMapView || { center: [35, 105], zoom: 4 }
    map.setView(view.center, view.zoom, { animate: false })
  })
}
function openMainView(view) {
  const previousView = siteView.value
  const leavingAnalysis = previousView === 'analysis' || previousView === 'trace'
  if (view === 'home' && previousView !== 'home' && map) rememberedMapView = { center: map.getCenter(), zoom: map.getZoom() }
  if (window.location.pathname !== '/') history.pushState({}, '', '/')
  siteView.value = view
  scientificOpen.value = false
  if (view === 'gold') openDataBrowser()
  else dataBrowserOpen.value = false
  if (view === 'home' && account.value) loadHomeResearch()
  if (view === 'home') nextTick(() => siteContentRef.value?.scrollTo(0, 0))
  if (leavingAnalysis) restoreMapAfterAnalysis()
  else if (view !== 'home') nextTick(() => {
    map?.invalidateSize({ pan: false })
    if (previousView === 'home') {
      const target = rememberedMapView || { center: [35, 105], zoom: 4 }
      map?.setView(target.center, target.zoom, { animate: false })
    }
  })
}
function navigateFromLanding(destination) {
  if (destination === 'assessment') {
    openMainView('explore')
    soiledgeOpen.value = true
    return
  }
  openMainView(destination)
}
function openResearch(view = 'analysis') {
  if (!account.value) { window.location.assign(accountUrl(view === 'trace' ? '/evidence' : '/analysis')); return }
  if (map) rememberedMapView = { center: map.getCenter(), zoom: map.getZoom() }
  const path = view === 'trace' ? '/evidence' : '/analysis'
  if (window.location.pathname !== path) history.pushState({}, '', path)
  siteView.value = view
  scientificOpen.value = false
  dataBrowserOpen.value = false
  catalogOpen.value = false
}
function researchStatusLabel(status) { return ({raw_data:'仅原始数据',exploratory_assessment:'探索性评价',validated_assessment:'经验证评价',insufficient_data:'数据不足，无法判断'})[status] || status || '状态未知' }
async function loadHomeResearch() {
  if (!account.value) return
  homeResearch.value = { loading: true, error: '', runs: [] }
  try {
    const bootstrapResponse = await fetch('/api/research/bootstrap')
    if (!bootstrapResponse.ok) throw new Error(`HTTP ${bootstrapResponse.status}`)
    const bootstrap = await bootstrapResponse.json()
    const results = await Promise.all(bootstrap.projects.map(async project => {
      const response = await fetch(`/api/research/runs?project_id=${encodeURIComponent(project.id)}&limit=5`)
      if (!response.ok) throw new Error(`读取 ${project.name} 任务失败：HTTP ${response.status}`)
      return (await response.json()).map(run => ({ ...run, project_name: project.name }))
    }))
    const runs = results.flat().sort((a,b) => String(b.created_at).localeCompare(String(a.created_at))).slice(0,2)
    homeResearch.value = { loading: false, error: '', runs }
  } catch (error) {
    homeResearch.value = { loading: false, error: error.message || '读取失败', runs: [] }
  }
}
function onRouteChange() {
  const leavingAnalysis = (siteView.value === 'analysis' || siteView.value === 'trace') && !['/analysis', '/evidence'].includes(window.location.pathname)
  siteView.value = window.location.pathname === '/analysis' ? 'analysis' : window.location.pathname === '/evidence' ? 'trace' : 'home'
  scientificOpen.value = false
  dataBrowserOpen.value = false
  if (siteView.value === 'home' && account.value) loadHomeResearch()
  if ((siteView.value === 'analysis' || siteView.value === 'trace') && !account.value) window.location.replace(accountUrl(window.location.pathname))
  if (leavingAnalysis) restoreMapAfterAnalysis()
}
const browserTab = ref('layers')
const browserSearch = ref('')
const catalogCategory = ref('all')
const selectedCatalogKey = ref('soil_ph')
const dbResolution = ref(5)
const dbTables = [{ name: 'points' }, { name: 'indicators' }, { name: 'meta' }]
const tableSearch = ref('')
const selectedTable = ref('')
const browserRef = ref(null)
let browserReturnFocus = null
const dataLoading = ref(false)
const dataError = ref('')
const dataResult = ref({ columns: [], rows: [], total: 0 })
const dataPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil((dataResult.value.total || 0) / 50)))
const categories = [{ id: 'all', label: '全部' }, { id: 'soil', label: '土壤' }, { id: 'env', label: '环境' }, { id: 'crop', label: '农业' }, { id: 'water', label: '水域' }]
const featuredCatalogKeys = ['soil_ph', 'soil_an', 'soil_cec', 'soil_bd', 'soil_btsnd', 'ece']
const filteredBrowserIndicators = computed(() => { const query = browserSearch.value.trim().toLowerCase(); return indicators.value.filter(item => (catalogCategory.value === 'all' || groupOf(item.col_name) === catalogCategory.value) && (!query || `${item.col_name} ${item.cname || item.name || ''} ${item.source_file || ''}`.toLowerCase().includes(query))).sort((a, b) => { const ai = featuredCatalogKeys.indexOf(a.col_name); const bi = featuredCatalogKeys.indexOf(b.col_name); return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi) }) })
const catalogSelected = computed(() => filteredBrowserIndicators.value.find(item => item.col_name === selectedCatalogKey.value) || filteredBrowserIndicators.value[0] || null)
const filteredDbTables = computed(() => dbTables.filter(table => table.name.toLowerCase().includes(tableSearch.value.trim().toLowerCase())))

function groupOf(key) {
  if (key.startsWith('soil_') || key === 'ece') return 'soil'
  if (key.startsWith('water_') || key === 'waterdist') return 'water'
  if (/^(corn|rice|soybean|wheat)(_|$)/.test(key)) return 'crop'
  return 'env'
}
function groupLabel(key) { return categories.find(item => item.id === groupOf(key))?.label || '环境' }
function catalogUnit(item) { return displayUnit(item.col_name, item.unit) || (item.col_name === 'soil_ph' ? '无量纲' : '单位待核对') }
const filteredIndicators = computed(() => {
  const query = search.value.trim().toLowerCase()
  return indicators.value.filter(ind => (activeCategory.value === 'all' || groupOf(ind.col_name) === activeCategory.value) && (!query || `${ind.col_name} ${displayName(ind.col_name, ind.cname || ind.name)}`.toLowerCase().includes(query)))
})
const filteredPreviewLayers = computed(() => resolution.value !== 5 ? [] : previewLayers.value.filter(layer => {
  const query = search.value.trim().toLowerCase()
  const category = layer.category || 'soil'
  return (activeCategory.value === 'all' || activeCategory.value === category) && (!query || `${layer.name} ${layer.id}`.toLowerCase().includes(query))
}))
const previewPrimaryLayers = computed(() => filteredPreviewLayers.value.filter(layer => ['n01_an', 'n02_som', 'x07_slope'].includes(layer.id)))
const previewAdditionalLayers = computed(() => filteredPreviewLayers.value.filter(layer => !['n01_an', 'n02_som', 'x07_slope'].includes(layer.id)))
const validEntries = computed(() => Object.entries(clicked.value?.values || {}).filter(([key, item]) => displayValue(key, item.value) != null))
const nullEntries = computed(() => Object.entries(clicked.value?.values || {}).filter(([key, item]) => displayValue(key, item.value) == null))
const nullCount = computed(() => nullEntries.value.length)
const selectedPointValue = computed(() => selected.value && clicked.value ? displayValue(selected.value.col_name, clicked.value.values?.[selected.value.col_name]?.value) : null)
const coreDefinitions = [
  { id: 'ece', label: '土壤电导率 EC' }, { id: 'soil_an', label: '碱解氮 AN' },
  { id: 'soil_bd', label: '容重 BD' }, { id: 'soil_btsnd', label: '砂粒 Sand' },
  { id: 'soil_cec', label: '阳离子交换量 CEC' }, { id: 'soil_ph', label: '酸碱度 pH' },
]
const coreIds = new Set(coreDefinitions.map(item => item.id))
const otherEntries = computed(() => validEntries.value.filter(([key]) => !coreIds.has(key)))
const otherNullEntries = computed(() => nullEntries.value.filter(([key]) => !coreIds.has(key)))
const filteredEntries = computed(() => otherEntries.value.filter(([key]) => activeResultCategory.value === 'all' || groupOf(key) === activeResultCategory.value))
const coreIndicators = computed(() => coreDefinitions.map(def => {
  const entry = clicked.value?.values?.[def.id]
  const officialValue = entry ? displayValue(def.id, entry.value) : null
  const isAnPreview = def.id === 'soil_an' && officialValue == null && resolution.value === 5 && previewValues.value.n01_an != null
  const value = isAnPreview ? previewValues.value.n01_an : officialValue
  return { ...def, value, unit: isAnPreview ? '原始值（待核）' : displayUnit(def.id, entry?.unit), source: isAnPreview ? 'CSDLv2 研究预览' : entry?.source, year: entry?.sourceYear || entry?.year, depth: isAnPreview ? '0–5 cm' : entry?.depth, status: isAnPreview ? '研究预览 · 不参与评分' : value == null ? '数据缺失 / 未接入' : '点位栅格值' }
}))
const regionalIndicators = computed(() => {
  const configured = regionalConfigFor(clicked.value?.regionName)
  return configured?.map(item => {
    const data = item.id ? clicked.value?.values?.[item.id] : null
    return { ...item, value: data ? displayValue(item.id, data.value) : null, unit: item.id ? displayUnit(item.id, data?.unit) : '' }
  }) || []
})
const legend = computed(() => selected.value ? { min: selected.value.legend_min ?? selected.value.min, max: selected.value.legend_max ?? selected.value.max } : null)
const legendCss = 'linear-gradient(90deg, #440154 0%, #414487 22%, #2a788e 45%, #22a884 68%, #7ad151 85%, #fde725 100%)'
const previewLegendCss = 'linear-gradient(90deg, #efe5c2 0%, #accc97 35%, #398f80 70%, #14495e 100%)'
const categoryLegendCss = 'linear-gradient(90deg, #440154 0% 16%, #3b528b 16% 33%, #21918c 33% 50%, #5ec962 50% 67%, #fde725 67% 84%, #b5de2b 84% 100%)'
const isCategorical = computed(() => selectedKey.value === 'soil_texcls')
const transparentTile = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='
let map = null, tileLayer = null, marker = null, highlightLayer = null, zoneLayer = null, queryId = 0, lastPoint = null, indicatorId = 0, dataId = 0
let mapResizeObserver = null
let drawerTouchStart = null
watch(() => !!clicked.value, () => nextTick(() => map?.invalidateSize({ pan: false })))
watch(catalogOpen, async open => {
  await nextTick()
  if (open) requestAnimationFrame(() => catalogRef.value?.focus())
  else if (!dataBrowserOpen.value) layerTrigger.value?.focus()
})
watch(dataBrowserOpen, async open => {
  await nextTick()
  if (open) browserRef.value?.focus()
  else if (browserReturnFocus?.isConnected) browserReturnFocus.focus()
})
watch(soiledgeOpen, async open => {
  await nextTick()
  if (open) document.querySelector('.edge-back')?.focus()
  else document.querySelector('.primary-nav button.active')?.focus()
})

function fmt(v) {
  if (v == null || !Number.isFinite(v)) return '—'
  if (v === 0) return '0'
  const a = Math.abs(v)
  if (a >= 1000) return v.toFixed(0)
  if (a >= 1) return v.toFixed(2)
  if (a >= 0.01) return v.toFixed(3)
  return v.toExponential(1)
}
function chooseIndicator(key) {
  selectedPreviewId.value = ''
  selectedKey.value = key
  catalogOpen.value = false
  if (!map) return
  if (tileLayer) map.removeLayer(tileLayer)
  if (!key) { tileLayer = null; return }
  if (tileAvailability.value === false) { tileLayer = null; return }
  tileLayer = L.tileLayer(tileUrl(key, resolution.value), { opacity: layerOpacity.value / 100, maxZoom: 12, maxNativeZoom: resolution.value === 1 ? 8 : 7, minZoom: 3, errorTileUrl: transparentTile }).addTo(map)
  tileLayer.on('tileload', event => { if (selectedKey.value === key && !event.tile.src.startsWith('data:')) tileAvailability.value = true })
  tileLayer.setZIndex(50)
}
function choosePreview(id) {
  selectedPreviewId.value = id
  selectedKey.value = ''
  catalogOpen.value = false
  if (!map) return
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = L.tileLayer(previewTileUrl(id), { opacity: layerOpacity.value / 100, maxZoom: 12, maxNativeZoom: 8, minZoom: 3, errorTileUrl: transparentTile }).addTo(map)
  tileLayer.setZIndex(50)
}
function openLayerSearch() { catalogOpen.value = true; requestAnimationFrame(() => requestAnimationFrame(() => document.querySelector('.catalog-search input')?.focus())) }
function resetMapView() { map?.setView([35, 105], 4) }
async function toggleReferenceZones() {
  if (zonesVisible.value) {
    zoneLayer?.remove()
    zonesVisible.value = false
    return
  }
  zoneError.value = ''
  zonesLoading.value = true
  try {
    if (!zoneLayer) {
      const boundaries = await fetchZ01Boundaries()
      zoneLayer = L.geoJSON(boundaries, {
        interactive: false,
        style: { color: '#111111', weight: 1.7, opacity: 0.9, fillColor: '#7cae83', fillOpacity: 0.07 },
      })
    }
    zoneLayer.addTo(map)
    zonesVisible.value = true
  } catch {
    zoneError.value = '参考分区暂不可用，请检查本地数据服务。'
  } finally {
    zonesLoading.value = false
  }
}
function handleDrawerKeydown(event) {
  if (event.key !== 'Tab') return
  const elements = [...catalogRef.value.querySelectorAll('button:not([disabled]), input:not([disabled])')].filter(element => element.offsetParent !== null)
  if (!elements.length) return
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && (document.activeElement === first || document.activeElement === catalogRef.value)) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}
function handleBrowserKeydown(event) {
  if (event.key !== 'Tab') return
  const elements = [...browserRef.value.querySelectorAll('button:not([disabled]), input:not([disabled])')].filter(element => element.offsetParent !== null)
  if (!elements.length) return
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && (document.activeElement === first || document.activeElement === browserRef.value)) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}
function onDrawerTouchStart(event) { drawerTouchStart = { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY } }
function onDrawerTouchEnd(event) {
  if (!drawerTouchStart) return
  const dx = event.changedTouches[0].clientX - drawerTouchStart.x
  const dy = event.changedTouches[0].clientY - drawerTouchStart.y
  if (dx < -70 && Math.abs(dx) > Math.abs(dy) * 1.5) catalogOpen.value = false
  drawerTouchStart = null
}
function cycleSheet() { sheetState.value = sheetState.value === 'half' ? 'full' : sheetState.value === 'full' ? 'closed' : 'half'; nextTick(() => map?.invalidateSize({ pan: false })) }
function handleKeydown(event) { if (event.key === 'Escape') { if (dataBrowserOpen.value) closeDataBrowser(); else if (soiledgeOpen.value) soiledgeOpen.value = false; else catalogOpen.value = false } }
function updateOpacity() { if (tileLayer) tileLayer.setOpacity(layerOpacity.value / 100) }
async function loadIndicators() {
  const currentLoad = ++indicatorId
  apiState.value = 'loading'
  indicatorError.value = ''
  try {
    const data = await fetchIndicators(resolution.value)
    if (currentLoad !== indicatorId) return
    if ((data.res == null && resolution.value === 1) || (data.res != null && Number(data.res) !== resolution.value)) throw new Error(`当前服务未提供 ${resolution.value} km 数据，请启动 phase2 后端`)
    if (resolution.value === 1 && (data.count !== 19 || !Array.isArray(data.indicators) || data.indicators.length !== 19)) throw new Error('1 km 指标清单不符合 phase2 数据，当前服务可能仍是旧版后端')
    indicators.value = Array.isArray(data.indicators) ? data.indicators : []
    apiState.value = 'ready'
    if (!indicators.value.some(ind => ind.col_name === selectedKey.value)) selectedKey.value = ''
    if (!selectedKey.value) chooseIndicator(indicators.value.find(ind => ind.col_name === 'soil_ph')?.col_name || indicators.value[0]?.col_name || '')
    else chooseIndicator(selectedKey.value)
  } catch (e) {
    if (currentLoad !== indicatorId) return
    apiState.value = 'error'
    indicatorError.value = `指标加载失败：${e.message}${e.message.includes('500') ? '；请检查本地数据服务' : ''}`
  }
}
async function loadTileAvailability() {
  const requestedResolution = resolution.value
  tileAvailability.value = null
  try {
    const meta = await fetchMeta(requestedResolution)
    if (resolution.value === requestedResolution && tileAvailability.value !== true) tileAvailability.value = typeof meta.tiles_available === 'boolean' ? meta.tiles_available : null
  } catch { if (resolution.value === requestedResolution) tileAvailability.value = null }
}
watch(tileAvailability, available => {
  if (!map || selectedPreviewId.value) return
  if (available === false && tileLayer) { map.removeLayer(tileLayer); tileLayer = null }
  if (available === true && selectedKey.value && !tileLayer) chooseIndicator(selectedKey.value)
})
async function loadPreviewLayers() {
  try { previewLayers.value = (await fetchPreviewLayers()).layers || [] }
  catch { previewLayers.value = [] }
}
async function queryPoint(lng, lat) {
  lastPoint = { lng, lat }
  sheetState.value = 'half'
  const currentQuery = ++queryId
  loading.value = apiState.value === 'ready'
  pointError.value = ''
  previewValues.value = {}
  showNulls.value = false
  expandedMetric.value = ''
  clicked.value = { lon: lng, lat, values: {}, found: false }
  if (highlightLayer) { map.removeLayer(highlightLayer); highlightLayer = null }
  if (marker) marker.setLatLng([lat, lng])
  else marker = L.marker([lat, lng], { icon: L.divIcon({ className: 'probe-marker', html: '<span></span>', iconSize: [30, 30], iconAnchor: [15, 15] }) }).addTo(map)
  if (apiState.value !== 'ready') {
    pointError.value = '地图已定位；数据服务未连接。请检查本地后端，然后重试。'
    return
  }
  try {
    const [res, preview, zone] = await Promise.all([
      fetchPoint(lng, lat, resolution.value),
      resolution.value === 5 && previewLayers.value.length ? fetchPreviewPoint(lng, lat).catch(() => null) : Promise.resolve(null),
      fetchZ01Point(lng, lat).catch(() => null),
    ])
    if (currentQuery !== queryId) return
    previewValues.value = preview?.values || {}
    clicked.value = res ? {
      lon: res.lon ?? lng, lat: res.lat ?? lat, values: res.values || {}, found: !!res.found,
      gridId: res.gridId ?? res.grid_id ?? null,
      regionId: res.regionId ?? res.region_id ?? null,
      regionName: res.regionName ?? res.region_name ?? null,
      z01: zone?.zone ?? null,
      geometry: res.geometry ?? null,
    } : { lon: lng, lat, values: {}, found: false, z01: zone?.zone ?? null }
    if (res?.geometry && typeof res.geometry === 'object') {
      try {
        highlightLayer = L.geoJSON(res.geometry, { style: { color: '#2e8057', weight: 2, fillColor: '#8ac49c', fillOpacity: 0.18 } }).addTo(map)
      } catch { /* Keep the coordinate marker if server geometry is invalid. */ }
    }
    activeResultCategory.value = 'all'
  } catch (e) {
    if (currentQuery !== queryId) return
    pointError.value = /Failed to fetch|NetworkError|fetch failed/i.test(e.message)
      ? '地图已定位；无法连接数据服务。请检查本地后端。'
      : `点位查询失败：${e.message}`
  } finally {
    if (currentQuery === queryId) loading.value = false
  }
}
function retryPoint() { if (lastPoint) queryPoint(lastPoint.lng, lastPoint.lat) }
function changeResolution(value) {
  if (resolution.value === value) return
  resolution.value = value
  loadTileAvailability()
  const pendingQuery = ++queryId
  const point = lastPoint
  clicked.value = null
  if (tileLayer) { map.removeLayer(tileLayer); tileLayer = null }
  indicators.value = []
  selectedKey.value = ''
  selectedPreviewId.value = ''
  if (value === 1) activeCategory.value = 'all'
  loadIndicators().then(() => { if (point && queryId === pendingQuery) queryPoint(point.lng, point.lat) })
}
function openDataBrowser(event) { browserReturnFocus = event?.currentTarget || document.activeElement; browserTab.value = 'layers'; dataBrowserOpen.value = true; catalogOpen.value = false }
function closeDataBrowser() { dataBrowserOpen.value = false; if (siteView.value === 'gold') siteView.value = 'explore' }
function showCatalogLayer(key) { chooseIndicator(key); closeDataBrowser(); nextTick(() => map?.invalidateSize({ pan: false })) }
function selectDatabase(value) { if (dbResolution.value === value) return; ++dataId; dbResolution.value = value; selectedTable.value = ''; dataResult.value = { columns: [], rows: [], total: 0 }; dataPage.value = 1; dataLoading.value = false; dataError.value = '' }
function selectDbTable(name) { selectedTable.value = name; dataPage.value = 1; loadData() }
async function loadData() {
  if (!selectedTable.value) return
  const currentLoad = ++dataId
  dataLoading.value = true
  dataError.value = ''
  dataResult.value = { columns: [], rows: [], total: 0 }
  try {
    const result = await fetchData({ res: dbResolution.value, table: selectedTable.value, page: dataPage.value, pageSize: 50 })
    if (currentLoad === dataId) {
      const columns = (result.columns || []).map(column => typeof column === 'string' ? { col: column } : { col: column.col ?? column.name, cname: column.cname })
      dataResult.value = { columns, rows: (result.rows || []).map(row => Array.isArray(row) ? row : columns.map(column => row[column.col])), total: result.total || 0 }
    }
  } catch (e) {
    if (currentLoad === dataId) dataError.value = `数据读取失败：${e.message}`
  } finally { if (currentLoad === dataId) dataLoading.value = false }
}
function goToPage(page) { dataPage.value = page; loadData() }
function formatDbCell(value) { if (value == null) return 'NULL'; if (typeof value === 'object') return JSON.stringify(value); return String(value) }
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('popstate', onRouteChange)
  map = L.map('map', { center: [35, 105], zoom: 4, minZoom: 3, maxZoom: 12, zoomControl: false })
  mapResizeObserver = new ResizeObserver(() => map?.invalidateSize({ pan: false }))
  mapResizeObserver.observe(document.getElementById('map'))
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors', maxZoom: 19, className: 'soil-basemap-tiles' }).addTo(map)
  L.control.zoom({ position: 'bottomright' }).addTo(map)
  map.on('mousemove', e => { cursorCoords.value = `${e.latlng.lat.toFixed(3)}° N  /  ${e.latlng.lng.toFixed(3)}° E` })
  map.on('mouseout', () => { cursorCoords.value = '' })
  map.on('click', e => queryPoint(e.latlng.lng, e.latlng.lat))
  loadIndicators()
  loadTileAvailability()
  loadPreviewLayers()
  checkAccount()
})
onBeforeUnmount(() => { window.removeEventListener('keydown', handleKeydown); window.removeEventListener('popstate', onRouteChange); mapResizeObserver?.disconnect(); if (map) { map.remove(); map = null } })
</script>

