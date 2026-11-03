<template>
  <div class="app-shell">
    <div ref="siteContentRef" class="site-content" :class="{ 'site-content-home': siteView==='home', 'site-content-workspace': siteView!=='home', 'site-content-resources': siteView==='gold', 'site-content-tools': siteView==='tools', 'site-content-map': siteView==='explore', 'site-content-research': siteView==='research'||siteView==='assistant', 'site-content-health': siteView==='research', 'site-content-assessment': siteView==='research' && researchStage==='input' }">
    <HomeLanding v-if="siteView==='home'" :account="account" @navigate="destination => transitionTo(navigateFromLanding, destination)" @logout="logout" />
    <SiteHeader v-if="siteView!=='home'" :active="siteView === 'research' ? 'research' : siteView" :account="account" :preview="assessmentPreview && siteView==='research'" :login-href="accountUrl(locationPath())" @navigate="destination => transitionTo(navigateFromHeader, destination)" @logout="logout" />

    <div v-if="toolOrigin && siteView !== 'tools'" class="tools-return-bar"><a :href="toolDirectoryPath" @click.prevent="transitionTo(returnToTools)"><WorkspaceIcon name="back" />返回工具目录</a><span>{{ activeToolName }}</span></div>
    <ToolsCenter ref="toolsCenterRef" v-show="siteView === 'tools'" :active="siteView === 'tools'" :account="account" @open-tool="tool => transitionTo(openTool, tool)" @import-research="payload => transitionTo(openResearchImport, payload)" />

    <section v-show="siteView==='explore'" class="explorer-workspace" :inert="soiledgeOpen || scientificOpen">
      <div class="map-workspace-toolbar">
        <h1 tabindex="-1">探索数据</h1>
        <div class="map-data-controls">
          <div class="map-basemap-control" role="group" aria-label="地图底图"><span>底图</span><HoverSwitch><button v-for="option in basemapOptions" :key="option.id" type="button" :class="{ active: basemapMode === option.id }" :aria-pressed="basemapMode === option.id" :disabled="!basemapEnabled" :title="!basemapEnabled ? `${basemapProviderLabel}底图待启用` : option.label" @click="changeBasemap(option.id)">{{ option.label }}</button></HoverSwitch></div>
          <div class="module-resolution" role="group" aria-label="地图数据分辨率"><span>数据分辨率</span><HoverSwitch><button v-for="value in [5, 1]" :key="value" type="button" :class="{ active: resolution === value }" :aria-pressed="resolution === value" @click="changeResolution(value)">{{ value }} km</button></HoverSwitch></div>
          <span class="map-dataset-count">{{ indicators.length ? `${indicators.length} 项已登记指标` : '正在读取目录' }}</span>
          <span class="map-data-connection" :class="apiState"><i aria-hidden="true"></i>{{ apiState === 'ready' ? '数据已连接' : apiState === 'loading' ? '正在连接' : '连接中断' }}</span>
        </div>
      </div>
    <main class="workspace" :class="{ 'has-point': !!clicked }">
      <nav class="navigation-rail" aria-label="工作区工具">
        <button ref="layerTrigger" type="button" :class="{ active: catalogOpen }" :aria-expanded="catalogOpen" aria-controls="layer-drawer" title="探索图层" aria-label="探索图层" @click="catalogOpen = !catalogOpen"><WorkspaceIcon name="layers" /></button>
        <button type="button" title="搜索指标" aria-label="搜索指标" @click="openLayerSearch"><WorkspaceIcon name="search" /></button>
        <button type="button" title="重置地图范围" aria-label="重置地图范围" @click="resetMapView"><WorkspaceIcon name="locate" /></button>
        <span class="rail-spacer"></span><span class="rail-resolution">{{ resolution }} km</span>
      </nav>
      <div v-if="catalogOpen" class="drawer-scrim" aria-hidden="true" @click="catalogOpen = false"></div>
      <aside id="layer-drawer" ref="catalogRef" class="catalog" :class="{ 'catalog-open': catalogOpen }" role="dialog" aria-modal="true" aria-label="图层目录" tabindex="-1" :inert="!catalogOpen" @keydown="handleDrawerKeydown" @touchstart.passive="onDrawerTouchStart" @touchend.passive="onDrawerTouchEnd">
        <button class="drawer-close" type="button" aria-label="关闭图层目录" @click="catalogOpen = false">×</button>
        <div class="catalog-intro"><h1>探索图层</h1></div>
        <div class="catalog-search"><WorkspaceIcon name="search" /><input v-model="search" type="search" placeholder="搜索指标或代码" aria-label="搜索指标或代码" /></div>
        <HoverSwitch class="category-tabs" role="tablist" aria-label="图层分类"><button v-for="category in categories" :key="category.id" type="button" role="tab" :aria-selected="activeCategory === category.id" :class="{ active: activeCategory === category.id }" @click="activeCategory = category.id">{{ category.label }}</button></HoverSwitch>
        <div class="list-meta"><span>{{ activeCategory === 'all' ? '全部图层' : categories.find(c => c.id === activeCategory)?.label }}</span><span>{{ filteredIndicators.length }} 已登记 · {{ filteredPreviewLayers.length }} 预览</span></div>
        <div class="indicator-list">
          <div v-if="filteredPreviewLayers.length" class="preview-list">
            <span class="section-kicker">研究预览 · 不参与评分</span>
            <button v-for="layer in previewPrimaryLayers" :key="layer.id" type="button" class="indicator-item preview-item" :class="{ active: selectedPreviewId === layer.id }" @click="choosePreview(layer.id)"><span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ layer.name }}</strong><small>{{ layer.unit }} · 5 km 对齐</small></span></button>
            <button v-if="previewAdditionalLayers.length" type="button" class="preview-more" :aria-expanded="showMorePreviews || !!search.trim()" @click="showMorePreviews = !showMorePreviews">{{ showMorePreviews || search.trim() ? '收起' : '查看' }}更多年份与土层（{{ previewAdditionalLayers.length }}）</button>
            <template v-if="showMorePreviews || search.trim()"><button v-for="layer in previewAdditionalLayers" :key="layer.id" type="button" class="indicator-item preview-item" :class="{ active: selectedPreviewId === layer.id }" @click="choosePreview(layer.id)"><span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ layer.name }}</strong><small>{{ layer.unit }} · 5 km 对齐</small></span></button></template>
          </div>
          <div v-if="apiState === 'loading'" class="catalog-state"><span class="state-spinner"></span><strong>正在读取图层</strong></div>
          <div v-else-if="apiState === 'error'" class="catalog-state"><span class="state-icon">!</span><strong>数据服务暂不可用</strong><small>{{ indicatorError }}</small><button type="button" @click="loadIndicators">重新连接</button></div>
          <div v-else-if="!filteredIndicators.length" class="catalog-state"><span class="state-icon">∅</span><strong>没有找到匹配图层</strong><small>试试其他关键词或分类</small></div>
          <button v-for="ind in filteredIndicators" :key="ind.col_name" type="button" class="indicator-item" :class="{ active: selectedKey === ind.col_name }" @click="chooseIndicator(ind.col_name)">
            <span class="item-symbol" aria-hidden="true"><span></span></span><span class="item-copy"><strong>{{ displayName(ind.col_name, ind.cname || ind.name) }}</strong></span>
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m7 4 6 6-6 6"/></svg>
          </button>
        </div>
        <div class="catalog-foot"><span class="foot-orbit" aria-hidden="true"></span><span>{{ resolution }} km 网格数据 · 全国范围</span></div>
      </aside>

      <section class="map-stage" :class="{ 'map-stage-amap': usingAmap }" aria-label="土壤指标地图">
        <div v-if="usingAmap" id="amap-basemap" ref="amapContainerRef" class="amap-basemap" aria-hidden="true"></div>
        <div id="map"></div>
        <div v-if="basemapState !== 'ready'" class="basemap-status" :class="{ 'basemap-status-loading': basemapState === 'loading' }" role="status"><span>{{ basemapState === 'unconfigured' ? `${basemapProviderLabel}底图待启用` : basemapState === 'loading' ? `正在加载${basemapProviderLabel}` : `${basemapProviderLabel}底图暂不可用` }}</span><button v-if="basemapState === 'error'" type="button" @click="changeBasemap(basemapMode)">重试</button></div>
        <div class="map-tools"><span class="map-tools-title">{{ selectedPreview?.name || (selected ? displayName(selected.col_name, selected.cname || selected.name) : '中国土壤空间分布') }}</span><button type="button" @click="catalogOpen = true">切换图层 <span aria-hidden="true">↗</span></button><button type="button" :aria-pressed="zonesVisible" :disabled="zonesLoading" @click="toggleReferenceZones">{{ zonesLoading ? '加载分区…' : zonesVisible ? '隐藏参考分区' : '参考分区' }}</button></div>
        <div v-if="dataNavigationError" class="map-data-link-error" role="status">{{ dataNavigationError }}</div>
        <div v-if="zoneError" class="map-tile-note map-zone-error" role="status">{{ zoneError }}</div>
        <div v-if="tileAvailability === false && !selectedPreviewId" class="map-tile-note" role="status">专题图层暂未提供 · 可点选查询</div>
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
        <div class="inspector-head"><div><span class="section-kicker">{{ siteView==='home' && !clicked ? '沃壤知行 / 研究总览' : '点位数据' }}</span><h2>{{ siteView==='home' && !clicked ? '研究总览' : '位置剖面' }}</h2></div><button class="sheet-toggle" type="button" :aria-label="sheetState === 'full' ? '收起分析面板' : '展开分析面板'" @click="cycleSheet">{{ sheetState === 'full' ? '收起' : '展开' }} <span aria-hidden="true">{{ sheetState === 'full' ? '⌄' : '⌃' }}</span></button></div>
        <section v-if="selected && !selectedPreviewId" class="map-layer-source" aria-label="当前图层资料"><h3>{{ displayName(selected.col_name, selected.cname || selected.name) }}</h3><dl><div><dt>单位</dt><dd>{{ displayUnit(selected.col_name, selected.unit) || (selected.col_name === 'soil_ph' ? '无量纲' : '待核对') }}</dd></div><div><dt>分辨率</dt><dd>{{ resolution }} km</dd></div><div><dt>来源文件</dt><dd>{{ selected.source_file || '未登记' }}</dd></div></dl><p>{{ selected.source_file === 'SYNTHETIC_TEST_DATA' ? '合成测试数据，仅供界面演示。' : '年份、土层与覆盖范围请到资源详情核对。' }}</p><button type="button" @click="transitionTo(openIndicatorResource)">查看数据来源与覆盖信息</button><button v-if="resourceReturn" type="button" @click="transitionTo(returnToResource)">返回数据资源</button></section>
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
          <button type="button" class="home-analysis-link" @click="openResearch('analysis')">进入健康研究 <span aria-hidden="true">→</span></button>
          <section class="home-task-list" aria-labelledby="home-tasks-title">
            <div class="home-task-heading"><h4 id="home-tasks-title">最近研究任务</h4><button type="button" @click="openResearch('report')">全部记录 <span aria-hidden="true">→</span></button></div>
            <p v-if="!account" class="home-task-state">登录后查看你的研究任务。<a href="/account/index.html?next=/analysis">登录 / 注册</a></p>
            <p v-else-if="homeResearch.loading" class="home-task-state" role="status">正在读取已保存任务…</p>
            <p v-else-if="homeResearch.error" class="home-task-state home-task-error" role="status">任务记录暂不可用：{{ homeResearch.error }}</p>
            <p v-else-if="!homeResearch.runs.length" class="home-task-state">尚无已保存分析任务。运行分析后，任务状态会显示在这里。</p>
            <ul v-else><li v-for="run in homeResearch.runs" :key="run.id"><span><b>{{ run.kind==='nshi'?'土壤指标筛选':'KO 通路结构分析' }}</b><small>{{ run.project_name }} · {{ run.dataset_id }}</small></span><em :class="`task-${run.status}`">{{ researchStatusLabel(run.status) }}</em></li></ul>
          </section>
        </section>
        <div v-else-if="!clicked" class="inspector-empty"><div class="empty-target" aria-hidden="true"><WorkspaceIcon name="location" /></div><strong>选取地图位置</strong><p>点击地图，查看该位置的土壤指标。</p></div>
        <template v-else>
          <div class="point-summary"><div class="point-label"><span class="point-signal"></span>{{ loading ? '正在解析位置' : pointError ? '查询暂不可用' : clicked.found ? '已定位数据点' : '该位置暂无数据' }}</div><div class="point-coords"><strong>{{ clicked.lat.toFixed(4) }}° N</strong><strong>{{ clicked.lon.toFixed(4) }}° E</strong></div><div v-if="clicked.gridId" class="point-grid-id">栅格 ID · {{ clicked.gridId }}</div><div class="point-separator"></div><div class="point-stats"><div><b>{{ loading ? '···' : validEntries.length }}</b><span>有效指标</span></div><div><b>{{ loading ? '···' : nullCount }}</b><span>无数据</span></div></div></div>
          <div v-if="pointError" class="result-error"><span>{{ pointError }}</span><button type="button" @click="retryPoint">重试</button></div>
          <div v-if="loading" class="result-loading" role="status"><span class="state-spinner"></span>{{ clicked.found ? '正在读取新位置的数据，下方暂保留上次查询结果…' : '正在读取此位置的数据…' }}</div>
          <template v-if="clicked.found">
            <div v-if="selected && selectedPointValue != null" class="featured-value"><span>当前图层 · {{ displayName(selected.col_name, selected.cname || selected.name) }}</span><div><strong>{{ fmt(selectedPointValue) }}</strong><small>{{ displayUnit(selected.col_name, selected.unit) }}</small></div></div>
            <section class="assessment-section"><span class="section-kicker">SOIL PROFILE / 核心指标</span><h3>六项核心土壤指标</h3><div class="core-grid"><button v-for="item in coreIndicators" :key="item.id" type="button" class="core-metric" :aria-expanded="expandedMetric === item.id" @click="expandedMetric = expandedMetric === item.id ? '' : item.id"><span>{{ item.label }}</span><strong>{{ item.value == null ? '—' : fmt(item.value) }} <small>{{ item.unit }}</small></strong><em>{{ item.status }} · {{ expandedMetric === item.id ? '收起' : '详情' }}</em><span v-if="expandedMetric === item.id" class="metric-detail">来源：{{ item.source || '待确认' }}<br>年份：{{ item.year || '待确认' }}<br>土层：{{ item.depth || '待确认' }}</span></button></div></section>
            <details :key="`${clicked.lat}:${clicked.lon}:${resolution}`" class="other-indicators"><summary><span><b>其他指标</b><small>保留当前点位的全部非核心指标</small></span><span class="other-count">{{ otherEntries.length + otherNullEntries.length }} 项 <i aria-hidden="true">⌄</i></span></summary><div class="other-content"><HoverSwitch class="result-tabs" role="tablist" aria-label="其他指标分类"><button v-for="category in categories" :key="category.id" type="button" role="tab" :aria-selected="activeResultCategory === category.id" :class="{ active: activeResultCategory === category.id }" @click="activeResultCategory = category.id">{{ category.label }}</button></HoverSwitch><div class="result-list"><div v-for="[key, item] in filteredEntries" :key="key" class="result-row"><span>{{ displayName(key, item.cname || item.name) }}</span><strong>{{ fmt(displayValue(key, item.value)) }}<small>{{ displayUnit(key, item.unit) }}</small></strong></div><p v-if="!filteredEntries.length" class="results-empty">此分类在该位置没有有效值。</p><button v-if="otherNullEntries.length" type="button" class="missing-toggle" :aria-expanded="showNulls" @click="showNulls = !showNulls">{{ showNulls ? '收起' : '查看' }} {{ otherNullEntries.length }} 项无数据指标 <span>{{ showNulls ? '↑' : '↓' }}</span></button><template v-if="showNulls"><div v-for="[key, item] in otherNullEntries" :key="key" class="result-row missing"><span>{{ displayName(key, item.cname || item.name) }}</span><strong>—</strong></div></template></div></div></details>
            <section class="assessment-section"><span class="section-kicker">REGIONAL CONTEXT</span><h3>区域指标</h3><p v-if="clicked.z01" class="region-name">Z01 参考区划 · {{ clicked.z01.source_name }}<small> · {{ clicked.z01.code }}</small></p><p v-if="clicked.z01" class="regional-caveat">来源区划按 1 km 网格定位，边界附近可能有偏差；与模型九大区的映射尚未核验，不参与 N + X 评分。</p><p v-if="clicked.regionName" class="region-name">模型农业区 · {{ clicked.regionName }}<small v-if="clicked.regionId"> · {{ clicked.regionId }}</small></p><p v-if="!clicked.regionName" class="assessment-note">当前尚无可核验的模型农业区映射；区域扩展指标待接入。</p><p v-else-if="!regionalIndicators.length" class="assessment-note">该农业区尚无已核对的 X 指标配置。</p><div v-else class="regional-list"><div v-for="item in regionalIndicators" :key="item.label" class="regional-row"><span>{{ item.label }}</span><strong>{{ item.value == null ? '待接入' : `${fmt(item.value)} ${item.unit}` }}</strong></div></div><p v-if="regionalIndicators.length" class="regional-caveat">区域归属来自点位接口；X 清单来自项目指标审计。仅展示对应字段的返回值，其余不参与评分。</p></section>
            <section class="assessment-section"><span class="section-kicker">SOIL HEALTH ASSESSMENT</span><h3>土壤健康评价</h3><HoverSwitch class="assessment-modes" role="group" aria-label="评价模式"><button type="button" :class="{ active: assessmentMode === 'base' }" @click="assessmentMode = 'base'">Base-SHI</button><button type="button" :class="{ active: assessmentMode === 'regional' }" @click="assessmentMode = 'regional'">N + X</button></HoverSwitch><div class="score-pending"><strong>—</strong><div><b>评分规则待核验</b><p>{{ assessmentMode === 'base' ? '尚未接入经过核验的基础评分规则与结果。' : '区域映射与扩展指标未完整接入，暂不能计算 N + X。' }}</p></div></div></section>
          </template>
          <div v-else-if="!loading" class="unavailable-analysis"><span class="section-kicker">SOIL PROFILE / 核心指标</span><h3>数据尚未返回</h3><p>位置已经在地图上标记。服务恢复后，可在此查看六项核心土壤指标与区域评价。</p><div class="pending-metrics"><span v-for="item in coreDefinitions" :key="item.id">{{ item.label }}<b>—</b></span></div><div class="pending-score"><span class="section-kicker">SOIL HEALTH ASSESSMENT</span><strong>评分待评估</strong><small>没有真实指标和核验规则时，不生成分数。</small></div></div>
        </template>
      </aside>
    </main>
    </section>
    <HealthResearchHub v-if="siteView==='research' && (account || assessmentPreview)" :account="account" :preview="assessmentPreview" :map-point="assessmentMapPoint || clicked" :csrf-token="csrfToken" :stage="researchStage" :context="assistantContext" :draft="assistantDraft" @update:stage="stage => transitionTo(setResearchStage, stage)" @context-change="assistantContext = $event" @update:draft="assistantDraft = $event" @navigate="destination => transitionTo(openMainView, destination)" @open-assistant="transitionTo(openAssistant)" />
    <AssistantWorkspace v-if="siteView==='assistant' && account" :account-id="String(account.id || 'local')" :context="assistantContext" :draft="assistantDraft" :csrf-token="csrfToken" @update:context="assistantContext = $event" @update:draft="assistantDraft = $event" @navigate-research="transitionTo(openResearch, assistantContext?.sample && researchStage === 'input' ? 'analysis' : researchStage)" />
    <div v-if="soiledgeOpen" class="edge-backdrop"><SoiledgeWorkbench @close="soiledgeOpen = false" /></div>
    <ScientificWorkbench v-if="scientificOpen" :key="scientificTab" :initial-tab="scientificTab" :point="clicked" :resolution="resolution" :preview-values="previewValues" @close="scientificOpen=false;siteView='explore'" />
    <main v-show="siteView==='gold'" class="data-browser resource-workspace" aria-labelledby="browser-title">

        <RepositoryWorkspace v-if="browserTab === 'layers'" :active="siteView === 'gold'" :indicators="indicators" :resolution="resolution" :api-state="apiState" :error="indicatorError" :tiles-available="tileAvailability" @resolution-change="changeResolution" @map-preview="payload => transitionTo(showCatalogLayer, payload)" @return-map="path => transitionTo(returnToDataMap, path)" @open-database="openRawDatabase" @retry="loadIndicators" />
        <template v-else>
          <header class="browser-head"><div class="browser-head-copy"><h1 id="browser-title" tabindex="-1">原始数据表</h1><p>按数据库与数据表分页检查字段和记录。</p></div><button type="button" class="browser-close" @click="openResourceCatalog">返回数据目录</button></header>

          <HoverSwitch class="db-switch" role="group" aria-label="选择数据库"><button v-for="value in [5, 1]" :key="value" type="button" :class="{ active: dbResolution === value }" :aria-pressed="dbResolution === value" @click="selectDatabase(value)">{{ value }} km 数据库</button><span>只读浏览 · 每页 50 行</span></HoverSwitch>
          <div class="db-workspace">
            <aside class="db-sidebar" aria-label="数据表"><label>查找数据表<input v-model="tableSearch" type="search" placeholder="输入表名" /></label><HoverSwitch class="db-table-list"><button v-for="table in filteredDbTables" :key="table.name" type="button" :class="{ active: selectedTable === table.name }" @click="selectDbTable(table.name)"><strong>{{ table.name }}</strong></button><p v-if="!filteredDbTables.length">没有匹配的数据表。</p></HoverSwitch></aside>
            <div class="db-main"><div class="browser-meta"><strong>{{ selectedTable || '选择左侧数据表' }}</strong><span>{{ selectedTable ? `${Number(dataResult.total || 0).toLocaleString()} 行 · ${dataResult.columns.length} 列 · 第 ${dataPage} / ${totalPages} 页` : '选择数据表后查看所有字段' }}</span></div><div v-if="dataError" class="browser-error">{{ dataError }} <button type="button" @click="loadData">重试</button></div><div ref="dataTableRef" class="data-table-scroll" :aria-busy="dataLoading" :style="dataLoading && dataTableLoadingHeight ? { minHeight: dataTableLoadingHeight + 'px' } : undefined"><table v-if="selectedTable && dataResult.columns.length"><thead><tr><th v-for="column in dataResult.columns" :key="column.col" scope="col">{{ column.cname || column.col }}<small v-if="column.cname && column.cname !== column.col">{{ column.col }}</small></th></tr></thead><tbody><tr v-for="(row, index) in dataResult.rows" :key="`${dataPage}-${index}`"><td v-for="(value, colIndex) in row" :key="colIndex">{{ formatDbCell(value) }}</td></tr></tbody></table><div v-if="dataLoading" class="table-state"><span class="state-spinner"></span>正在读取数据…</div><div v-else-if="dataError" class="table-state">当前数据表暂无法读取。</div><div v-else-if="!selectedTable" class="table-state">选择左侧数据表，查看完整字段和分页记录。</div><div v-else-if="!dataResult.rows.length" class="table-state">此表没有记录。</div></div><footer class="browser-pagination"><button type="button" :disabled="!selectedTable || dataPage <= 1 || dataLoading" @click="goToPage(dataPage - 1)">上一页</button><span>{{ dataPage }} / {{ totalPages }}</span><button type="button" :disabled="!selectedTable || dataPage >= totalPages || dataLoading" @click="goToPage(dataPage + 1)">下一页</button></footer></div>
          </div>
        </template>
    </main>
    </div>
  </div>
</template>

<script setup>
import HoverSwitch from './design-system/HoverSwitch.vue'
import { defineAsyncComponent, onMounted, onBeforeUnmount, ref, computed, nextTick, watch } from 'vue'
import SoiledgeWorkbench from './SoiledgeWorkbench.vue'
import HomeLanding from './HomeLanding.vue'
import SiteHeader from './SiteHeader.vue'
import { transitionPage } from './design-system/motion.js'
import { createTiandituBasemap } from './map/tianditu.js'
import { createAmapBasemap } from './map/amap.js'
import { createGcj02Crs } from './map/coordinates.js'
import { createScientificTileLayer } from './map/scientificTiles.js'
import mapConfig from './map/config.json'
import ToolsCenter from './tools/ToolsCenter.vue'
const RepositoryWorkspace = defineAsyncComponent(() => import('./RepositoryWorkspace.vue'))
import { getTool, toolTarget } from './tools/catalog.js'
import { siteLinks, viewFromPath } from './siteNavigation.js'
import ScientificWorkbench from './ScientificWorkbench.vue'
import HealthResearchHub from './HealthResearchHub.vue'
import AssistantWorkspace from './AssistantWorkspace.vue'
import WorkspaceIcon from './WorkspaceIcon.vue'
import L from 'leaflet'
import { fetchIndicators, fetchMeta, fetchPoint, fetchData, fetchPreviewLayers, fetchPreviewPoint, fetchZ01Boundaries, fetchZ01Point, previewTileUrl, tileUrl } from './api.js'
import { localDataPath, mapDataPath, readDataLocation, resourceDataPath } from './dataNavigation.js'
import { displayName, displayUnit, displayValue } from './dataDisplay.js'
import { regionalConfigFor } from './regionIndicatorConfig.js'
const indicators = ref([])
const siteContentRef = ref(null)
const initialDataLocation = readDataLocation(location.search)
const selectedKey = ref(location.pathname === '/explore' ? initialDataLocation.key : '')
const resourceReturn = ref(location.pathname === '/explore' ? initialDataLocation.resourceReturn : '')
const dataNavigationError = ref('')
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
const resolution = ref(['/explore', '/resources'].includes(location.pathname) ? initialDataLocation.res : 5)
const tileAvailability = ref(null)
const zonesVisible = ref(false)
const zonesLoading = ref(false)
const zoneError = ref('')
const soiledgeOpen = ref(false)
const scientificOpen = ref(false)
const scientificTab = ref('health')
function viewFromLocation() { return viewFromPath(window.location.pathname) }
function stageFromLocation() {
  const legacy = ({ '/analysis': 'analysis', '/evidence': 'evidence' })[window.location.pathname]
  const stage = new URLSearchParams(window.location.search).get('stage')
  return legacy || (['input', 'analysis', 'evidence', 'report'].includes(stage) ? stage : 'input')
}
function isAssessmentPreview() { return import.meta.env.DEV && window.location.pathname === '/assessment/preview' }
const siteView = ref(viewFromLocation())
const researchStage = ref(stageFromLocation())
const toolOrigin = ref(new URLSearchParams(location.search).get('from') === 'tools')
const toolsCenterRef = ref(null)
const toolDirectoryPath = ref(readToolDirectory())
const activeToolId = ref(new URLSearchParams(location.search).get('tool') || '')
const activeToolName = computed(() => getTool(activeToolId.value)?.name || '从工具中心打开')
function readToolDirectory() {
  try {
    const url = new URL(new URLSearchParams(location.search).get('returnTo') || '/tools', location.origin)
    return url.origin === location.origin && url.pathname === '/tools' ? url.pathname + url.search : '/tools'
  } catch { return '/tools' }
}
function withToolsOrigin(path) {
  if (!toolOrigin.value) return path
  const url = new URL(path, location.origin)
  url.searchParams.set('from', 'tools')
  if (activeToolId.value) url.searchParams.set('tool', activeToolId.value)
  if (toolDirectoryPath.value !== '/tools') url.searchParams.set('returnTo', toolDirectoryPath.value)
  return url.pathname + url.search
}
function openTool(payload) {
  const id = typeof payload === 'string' ? payload : payload.id
  const path = toolTarget(id, typeof payload === 'object' ? payload.directory : '/tools')
  if (!path) return
  if (getTool(id)?.login && !account.value) { window.location.assign(accountUrl(path)); return }
  history.pushState({}, '', path)
  onRouteChange()
}
function openResearchImport({ token, directory }) {
  const params = new URLSearchParams({ stage: 'input', mode: 'quick', step: 'input', import: token, from: 'tools', tool: 'data-audit', returnTo: directory })
  const path = '/research?' + params.toString()
  if (!account.value) { window.location.assign(accountUrl(path)); return }
  history.pushState({}, '', path)
  onRouteChange()
  window.dispatchEvent(new Event('soilmate:history-commit'))
}
function returnToTools() {
  history.pushState({}, '', toolDirectoryPath.value)
  onRouteChange()
}

const assistantContext = ref(null)
const assistantDraft = ref('')
const assessmentPreview = ref(isAssessmentPreview())
const assessmentMapPoint = ref(readAssessmentMapPoint())
function readAssessmentMapPoint() {
  try {
    const point = JSON.parse(sessionStorage.getItem('soilmate.assessment.map-context') || 'null')
    return point && Number.isFinite(point.lon) && Number.isFinite(point.lat) ? { lon: point.lon, lat: point.lat } : null
  } catch { return null }
}
const homeResearch = ref({ loading: true, error: '', runs: [] })
const account = ref(null)
const csrfToken = ref('')
function locationPath() { return window.location.pathname + window.location.search }
function accountUrl(path = '/research') { return '/account/index.html?next=' + encodeURIComponent(path) }
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
    if ((siteView.value === 'research' && !assessmentPreview.value) || siteView.value === 'assistant') window.location.replace(accountUrl(window.location.pathname + window.location.search))
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
  const leavingAnalysis = previousView === 'research' || previousView === 'assistant'
  if (view === 'home' && previousView !== 'home' && map) rememberedMapView = { center: map.getCenter(), zoom: map.getZoom() }
  if (view === 'tools' || view === 'home') toolOrigin.value = false
  const path = withToolsOrigin(siteLinks.find(link => link.id === view)?.href || '/')
  if (window.location.pathname + window.location.search !== path) history.pushState({}, '', path)
  siteView.value = view
  if (view === 'gold') window.dispatchEvent(new Event('soilmate:history-commit'))
  if (view === 'tools' && previousView === 'tools') toolsCenterRef.value?.readLocation()
  assessmentPreview.value = false
  scientificOpen.value = false
  soiledgeOpen.value = false
  catalogOpen.value = false
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
let navigationFade = null
let navigationFadeVersion = 0
function transitionTo(action, ...args) {
  const version = ++navigationFadeVersion
  navigationFade?.cancel()
  return transitionPage(() => action(...args), async () => {
    await nextTick()
    if (version !== navigationFadeVersion || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const selector = { home: '.landing-hero', explore: '.explorer-workspace', gold: '.resource-workspace', research: '.health-hub', assistant: '.assistant-workspace', tools: '.tools-workspace' }[siteView.value]
    const content = selector && siteContentRef.value?.querySelector(selector)
    if (content) navigationFade = content.animate([{ opacity: .8 }, { opacity: 1 }], { duration: 150, easing: 'cubic-bezier(.22,1,.36,1)' })
  }, { snapshot: false })
}
function onHistoryNavigation() {
  transitionTo(() => {
    onRouteChange()
    window.dispatchEvent(new Event('soilmate:history-commit'))
  })
}
function navigateFromHeader(destination) {
  soiledgeOpen.value = false
  scientificOpen.value = false
  toolOrigin.value = false
  if (destination === 'research') {
    if (researchStage.value === 'input') openAssessment()
    else openResearch(researchStage.value)
  } else if (destination === 'assistant') openAssistant()
  else openMainView(destination)
}
function navigateFromLanding(destination) {
  if (destination === 'assessment' || destination === 'research') {
    openAssessment()
    return
  }
  if (destination === 'assistant') { openAssistant(); return }
  openMainView(destination)
}
function openAssessment() {
  if (siteView.value === 'research' && assessmentPreview.value) return
  if (clicked.value && Number.isFinite(clicked.value.lon) && Number.isFinite(clicked.value.lat)) {
    assessmentMapPoint.value = { lon: clicked.value.lon, lat: clicked.value.lat }
    try { sessionStorage.setItem('soilmate.assessment.map-context', JSON.stringify(assessmentMapPoint.value)) } catch { /* Keep position in memory if browser storage is unavailable. */ }
  }
  openResearch('input')
}
function openResearch(view = 'analysis') {
  if (!account.value) { window.location.assign(accountUrl(withToolsOrigin(`/research?stage=${view === 'trace' ? 'evidence' : view}`))); return }
  if (map) rememberedMapView = { center: map.getCenter(), zoom: map.getZoom() }
  researchStage.value = view === 'trace' ? 'evidence' : view
  const path = withToolsOrigin(`/research?stage=${researchStage.value}`)
  if (window.location.pathname + window.location.search !== path) history.pushState({}, '', path)
  assessmentPreview.value = false
  siteView.value = 'research'
  scientificOpen.value = false
  soiledgeOpen.value = false
  catalogOpen.value = false
}
function setResearchStage(stage) {
  const changed = researchStage.value !== stage
  researchStage.value = stage
  const stageUrl = new URL(location.href); stageUrl.searchParams.set('stage', stage)
  const path = stageUrl.pathname + stageUrl.search
  if (window.location.pathname + window.location.search !== path) history.pushState({}, '', path)
  if (changed) nextTick(() => {
    siteContentRef.value?.scrollTo({ top: 0 })
    const title = siteContentRef.value?.querySelector('.research-embedded .records-heading h2, .research-embedded .finding-column h2')
    if (stage !== 'input' && title) { title.tabIndex = -1; title.focus({ preventScroll: true }) }
  })
}
function openAssistant() {
  if (!account.value) { window.location.assign(accountUrl(withToolsOrigin('/assistant'))); return }
  if (siteView.value === 'research' && researchStage.value === 'input') assistantContext.value = null
  const path = withToolsOrigin('/assistant')
  if (locationPath() !== path) history.pushState({}, '', path)
  siteView.value = 'assistant'
  assessmentPreview.value = false
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
  const leavingAnalysis = ['research', 'assistant'].includes(siteView.value) && !['/analysis', '/evidence', '/assessment', '/assessment/preview', '/research', '/assistant'].includes(window.location.pathname)
  siteView.value = viewFromLocation()
  const params = new URLSearchParams(location.search)
  toolOrigin.value = params.get('from') === 'tools'
  toolDirectoryPath.value = readToolDirectory()
  activeToolId.value = params.get('tool') || ''
  if (siteView.value === 'gold') browserTab.value = params.get('tab') === 'database' ? 'database' : 'layers'
  if (siteView.value === 'research') researchStage.value = stageFromLocation()
  assessmentPreview.value = isAssessmentPreview()
  scientificOpen.value = false
  if (siteView.value === 'home' && account.value) loadHomeResearch()
  if ((siteView.value === 'assistant' || (siteView.value === 'research' && !assessmentPreview.value)) && !account.value) window.location.replace(accountUrl(window.location.pathname + window.location.search))
  if (leavingAnalysis || siteView.value === 'explore') restoreMapAfterAnalysis()
  catalogOpen.value = false
  if (siteView.value === 'explore') nextTick(applyDataLocation)
}
watch(siteView, async view => {
  await nextTick()
  const heading = { home: '.landing-content h1', explore: '.map-workspace-toolbar h1', gold: '#browser-title', research: '#health-hub-title', assistant: '.assistant-main h1', tools: '#tools-title' }[view]
  const target = heading && document.querySelector(heading)
  if (target) { target.setAttribute('tabindex', '-1'); target.focus({ preventScroll: true }) }
})
const browserTab = ref(new URLSearchParams(location.search).get('tab') === 'database' ? 'database' : 'layers')
const dbResolution = ref(5)
const dbTables = [{ name: 'points' }, { name: 'indicators' }, { name: 'meta' }]
const tableSearch = ref('')
const selectedTable = ref('')
const dataLoading = ref(false)
const dataTableRef = ref(null)
const dataTableLoadingHeight = ref(0)
const dataError = ref('')
const dataResult = ref({ columns: [], rows: [], total: 0 })
const dataPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil((dataResult.value.total || 0) / 50)))
const categories = [{ id: 'all', label: '全部' }, { id: 'soil', label: '土壤' }, { id: 'env', label: '环境' }, { id: 'crop', label: '农业' }, { id: 'water', label: '水域' }]
const filteredDbTables = computed(() => dbTables.filter(table => table.name.toLowerCase().includes(tableSearch.value.trim().toLowerCase())))

function groupOf(key) {
  if (key.startsWith('soil_') || key === 'ece') return 'soil'
  if (key.startsWith('water_') || key === 'waterdist') return 'water'
  if (/^(corn|rice|soybean|wheat)(_|$)/.test(key)) return 'crop'
  return 'env'
}
function groupLabel(key) { return categories.find(item => item.id === groupOf(key))?.label || '环境' }
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
const usingAmap = (import.meta.env.VITE_MAP_PROVIDER || mapConfig.provider) === 'amap'
const amapKey = (import.meta.env.VITE_AMAP_KEY || mapConfig.amapKey || '').trim()
const tiandituKey = (import.meta.env.VITE_TIANDITU_KEY || '').trim()
const basemapEnabled = usingAmap ? Boolean(amapKey) : Boolean(tiandituKey)
const basemapProviderLabel = usingAmap ? '高德地图' : '天地图'
const amapContainerRef = ref(null)
const basemapOptions = [{ id: 'vector', label: '标准地图' }, { id: 'satellite', label: '卫星影像' }]
const basemapMode = ref('vector'), basemapState = ref('unconfigured')
let basemap = null
function changeBasemap(mode) { basemapMode.value = mode; basemap?.switchTo(mode) }
function scientificTileLayer(url, options) { return usingAmap ? createScientificTileLayer(L, url, options) : L.tileLayer(url, options) }
let mapResizeObserver = null, mapViewportObserver = null
let drawerTouchStart = null
function fitMapToViewport() {
  if (siteView.value !== 'explore') return
  const scroller = siteContentRef.value
  const surface = scroller?.querySelector('.explorer-workspace')
  const workspace = surface?.querySelector('.workspace')
  if (!workspace) return
  const padding = getComputedStyle(scroller)
  const top = workspace.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop
  const bottom = parseFloat(padding.paddingBottom) || 0
  const height = Math.max(360, Math.floor(scroller.clientHeight - top - bottom))
  if (surface.style.getPropertyValue('--explore-map-height') !== `${height}px`) surface.style.setProperty('--explore-map-height', `${height}px`)
}
watch(siteView, () => nextTick(fitMapToViewport))
watch(catalogOpen, async open => {
  await nextTick()
  if (open) requestAnimationFrame(() => catalogRef.value?.focus())
  else if (siteView.value === 'explore') layerTrigger.value?.focus()
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
function chooseIndicator(key, persist = true) {
  selectedPreviewId.value = ''
  selectedKey.value = key
  if (persist && key && location.pathname === '/explore') { const url = new URL(location.href); url.searchParams.set('indicator', key); url.searchParams.set('res', String(resolution.value)); history.replaceState(history.state, '', url.pathname + url.search) }
  catalogOpen.value = false
  if (!map) return
  if (tileLayer) map.removeLayer(tileLayer)
  if (!key) { tileLayer = null; return }
  if (tileAvailability.value === false) { tileLayer = null; return }
  tileLayer = scientificTileLayer(tileUrl(key, resolution.value), { opacity: layerOpacity.value / 100, maxZoom: 12, maxNativeZoom: resolution.value === 1 ? 8 : 7, minZoom: 3, errorTileUrl: transparentTile }).addTo(map)
  tileLayer.on('tileload', event => { if (selectedKey.value === key && !event.tile.src?.startsWith('data:')) tileAvailability.value = true })
  tileLayer.setZIndex(50)
}
function choosePreview(id) {
  selectedPreviewId.value = id
  selectedKey.value = ''
  catalogOpen.value = false
  if (!map) return
  if (tileLayer) map.removeLayer(tileLayer)
  tileLayer = scientificTileLayer(previewTileUrl(id), { opacity: layerOpacity.value / 100, maxZoom: 12, maxNativeZoom: 8, minZoom: 3, errorTileUrl: transparentTile }).addTo(map)
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
function onDrawerTouchStart(event) { drawerTouchStart = { x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY } }
function onDrawerTouchEnd(event) {
  if (!drawerTouchStart) return
  const dx = event.changedTouches[0].clientX - drawerTouchStart.x
  const dy = event.changedTouches[0].clientY - drawerTouchStart.y
  if (dx < -70 && Math.abs(dx) > Math.abs(dy) * 1.5) catalogOpen.value = false
  drawerTouchStart = null
}
function cycleSheet() { sheetState.value = sheetState.value === 'half' ? 'full' : sheetState.value === 'full' ? 'closed' : 'half'; nextTick(() => map?.invalidateSize({ pan: false })) }
function handleKeydown(event) { if (event.key === 'Escape') { if (soiledgeOpen.value) soiledgeOpen.value = false; else catalogOpen.value = false } }
function updateOpacity() { if (tileLayer) tileLayer.setOpacity(layerOpacity.value / 100) }
let pendingIndicatorLoad = null
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
    if (!selectedKey.value) chooseIndicator(indicators.value.find(ind => ind.col_name === 'soil_ph')?.col_name || indicators.value[0]?.col_name || '', false)
    else chooseIndicator(selectedKey.value, false)
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
  if (!clicked.value) {
    previewValues.value = {}
    clicked.value = { lon: lng, lat, values: {}, found: false }
  }
  if (highlightLayer) { map.removeLayer(highlightLayer); highlightLayer = null }
  if (marker) marker.setLatLng([lat, lng])
  else marker = L.marker([lat, lng], { icon: L.divIcon({ className: 'probe-marker', html: '<span></span>', iconSize: [30, 30], iconAnchor: [15, 15] }) }).addTo(map)
  if (apiState.value !== 'ready') {
    clicked.value = { lon: lng, lat, values: {}, found: false }
    previewValues.value = {}
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
    showNulls.value = false
    expandedMetric.value = ''
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
    clicked.value = { lon: lng, lat, values: {}, found: false }
    previewValues.value = {}
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
  if (location.pathname === '/explore') { const url = new URL(location.href); url.searchParams.set('res', String(value)); history.replaceState(history.state, '', url.pathname + url.search) }
  loadTileAvailability()
  const pendingQuery = ++queryId
  const point = lastPoint
  clicked.value = null
  if (tileLayer) { map.removeLayer(tileLayer); tileLayer = null }
  indicators.value = []
  selectedKey.value = ''
  selectedPreviewId.value = ''
  if (value === 1) activeCategory.value = 'all'
  pendingIndicatorLoad = loadIndicators().then(() => { if (point && queryId === pendingQuery) queryPoint(point.lng, point.lat) })
}
async function showCatalogLayer(payload) {
  const key = typeof payload === 'string' ? payload : payload.key
  const res = typeof payload === 'string' ? resolution.value : payload.res
  const center = map ? [map.getCenter().lat, map.getCenter().lng, map.getZoom()] : null
  const path = mapDataPath(key, res, center, payload.returnTo || '')
  history.pushState({}, '', path)
  onRouteChange()
  await applyDataLocation()
}
function openIndicatorResource() {
  if (!selected.value) return
  const center = map ? [map.getCenter().lat, map.getCenter().lng, map.getZoom()] : null
  const returnMap = mapDataPath(selectedKey.value, resolution.value, center)
  const path = resourceDataPath(selectedKey.value, resolution.value, returnMap, resourceReturn.value || '/resources')
  history.pushState({}, '', path); onRouteChange()
  window.dispatchEvent(new Event('soilmate:history-commit'))
}
function returnToDataMap(path) {
  const target = localDataPath(path, '/explore')
  if (!target) return
  history.pushState({}, '', target); onRouteChange(); applyDataLocation()
}
async function applyDataLocation() {
  if (location.pathname !== '/explore') return
  const state = readDataLocation(location.search)
  resourceReturn.value = state.resourceReturn
  if (state.res !== resolution.value) { changeResolution(state.res); await pendingIndicatorLoad }
  if (location.pathname !== '/explore') return
  if (state.key && apiState.value === 'ready') {
    if (indicators.value.some(item => item.col_name === state.key)) { chooseIndicator(state.key, false); dataNavigationError.value = '' }
    else { chooseIndicator('', false); dataNavigationError.value = '当前分辨率下未找到此指标，请重新选择图层。' }
  }
  if (state.center && map) map.setView(state.center.slice(0, 2), state.center[2], { animate: false })
}
function returnToResource() { if (resourceReturn.value) { history.pushState({}, '', resourceReturn.value); onRouteChange(); window.dispatchEvent(new Event('soilmate:history-commit')) } }

function openRawDatabase() { browserTab.value = 'database'; history.pushState({}, '', '/resources?tab=database') }
function openResourceCatalog() { browserTab.value = 'layers'; history.pushState({}, '', '/resources') }
function selectDatabase(value) { if (dbResolution.value === value) return; ++dataId; dbResolution.value = value; selectedTable.value = ''; dataResult.value = { columns: [], rows: [], total: 0 }; dataPage.value = 1; dataLoading.value = false; dataError.value = '' }
function selectDbTable(name) { selectedTable.value = name; dataPage.value = 1; loadData() }
async function loadData() {
  if (!selectedTable.value) return
  const currentLoad = ++dataId
  dataTableLoadingHeight.value = dataTableRef.value?.getBoundingClientRect().height || 0
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
  } finally { if (currentLoad === dataId) { dataLoading.value = false; dataTableLoadingHeight.value = 0 } }
}
function goToPage(page) { dataPage.value = page; loadData() }
function formatDbCell(value) { if (value == null) return 'NULL'; if (typeof value === 'object') return JSON.stringify(value); return String(value) }
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('popstate', onHistoryNavigation)
  fitMapToViewport()
  map = L.map('map', { crs: usingAmap ? createGcj02Crs(L) : L.CRS.EPSG3857, zoomAnimation: !usingAmap, center: initialDataLocation.center?.slice(0, 2) || [35, 105], zoom: initialDataLocation.center?.[2] || 4, minZoom: 3, maxZoom: 12, zoomControl: false, scrollWheelZoom: true })
  mapResizeObserver = new ResizeObserver(() => map?.invalidateSize({ pan: false, debounceMoveend: true }))
  mapResizeObserver.observe(document.getElementById('map'))
  mapViewportObserver = new ResizeObserver(fitMapToViewport)
  for (const element of [siteContentRef.value, siteContentRef.value?.querySelector('.site-header'), document.querySelector('.map-workspace-toolbar')]) {
    if (element) mapViewportObserver.observe(element)
  }
  const onBasemapState = state => { basemapState.value = state }
  basemap = usingAmap
    ? createAmapBasemap(map, amapContainerRef.value, amapKey, onBasemapState, import.meta.env.VITE_AMAP_SERVICE_HOST || '')
    : createTiandituBasemap(L, map, tiandituKey, onBasemapState)
  basemap.switchTo(basemapMode.value)
  L.control.zoom({ position: 'bottomright' }).addTo(map)
  map.on('mousemove', e => { cursorCoords.value = `${e.latlng.lat.toFixed(3)}° N  /  ${e.latlng.lng.toFixed(3)}° E` })
  map.on('mouseout', () => { cursorCoords.value = '' })
  map.on('click', e => queryPoint(e.latlng.lng, e.latlng.lat))
  pendingIndicatorLoad = loadIndicators().then(applyDataLocation)
  loadTileAvailability()
  loadPreviewLayers()
  checkAccount()
})
onBeforeUnmount(() => { navigationFade?.cancel(); window.removeEventListener('keydown', handleKeydown); window.removeEventListener('popstate', onHistoryNavigation); mapResizeObserver?.disconnect(); mapViewportObserver?.disconnect(); basemap?.destroy(); if (map) { map.remove(); map = null } })
</script>

