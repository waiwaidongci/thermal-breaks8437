# 焰谷热程变点研究档案

焰谷工业烘焙研究组的 16 位工艺分析员把独立批次温度序列整理为可复查的离线巡查假设。上游提供采集文件 `yg-thermal-1-202611.csv`，本系统替代人工在表格中按固定分钟切段、目测波动和反复调罚项的工作，下游由负责人审阅后供现场巡查员下载 CSV。人工固定分钟切分忽略真实位置、对罚项不敏感、把波动直接解释成工艺变更，是要解决的三个具体问题。

四个固定 seed 合成批次各 300 点：均值阶跃、平滑漂移、纯噪声、恒定对照，共 1200 点。A 批 min_size12 / max_segments8 / β80 的实际结果是 3 段、断点 90 和 200、RSS 356.09341455693374、总目标 516.0934145569337。这里没有在线告警或原因识别。

## 启动和账号

```sh
cp .env.example .env
docker compose up --build -d --wait
docker compose exec -T backend python -m scripts.seed_demo
```

|入口|地址|
|---|---|
|浏览器|http://localhost:18228|
|API / Swagger|http://localhost:19228/docs|
|PostgreSQL|127.0.0.1:17728|

|账号|密码|页面和权限|典型动作|
|---|---|---|---|
|admin@yangu.demo|Yangu2026!|全部页面、写入与审阅|确认或退回巡查说明|
|analyst@yangu.demo|Yangu2026!|全部页面、底稿和研究写入|导入、修订观测、排队分段、写说明；审批403|
|viewer@yangu.demo|Yangu2026!|读取底稿、结果、说明和审计|下载已确认 CSV；所有写入403|

首次后端启动自动 seed。脚本按自然键幂等，重复运行不新增、不覆盖已有底稿和人工说明。`.env.example` 列出端口、数据库、JWT_SECRET、SEED_DEMO；部署须设置自己的密码和 JWT secret。源码无外部平台令牌。

恰好五个服务 frontend / backend / worker / db / redis，各有健康检查。Nginx `/api/` 代理移除前缀，与后端路由一致；前端探针访问 127.0.0.1。backend 等待数据库和 Redis，worker 再等待 backend；Celery 通过 Redis 真正排队计算。共享 artifacts 卷保存运行 JSON。停止清除本题数据：`docker compose down -v --remove-orphans`。

## 一天的工作剧本

1. 09:00，分析员陈禾打开“热程首页”，先读离线模型的解释边界。
2. 到“温度底稿”选择 `YG-2411-A 阶跃焙程`，核对 `yg-thermal-1-202611.csv`。每 30 秒一点；A 批原记录从 2026-11-10 09:00:00 UTC 开始，页面按浏览器时区显示。
3. 核对温度、连续序号和带时区时间。页面允许导入带 points 数组的 JSON，也可修订单点；已有运行仍保留当时序列。
4. 在“分段配置”预先设 min_size=12、max_segments=8、当前罚项 β=80，路径 `[0,20,80,320,1280]`，建立研究。采样间隔不齐的批次可切换“按持续时间”，指定研究结束时刻与最短持续时长（秒），其余罚项参数复用同一界面。
5. 真实队列执行精确 DP。结果显示段区间 1–90、91–200、201–300；断点 90 表示第 90 个点仍在左段，第 91 点开始右段。
6. 展开各预设罚项的段数、断点和目标，并对照相邻段均值差。路径反映参数选择敏感性，不能当断点置信区间。
7. 到“巡查审阅”选择成功运行，提交包含全部分段快照的巡查假设和现场核对行动，不认定波动原因。
8. 负责人赵砚登录确认或退回；巡查观察员吴川只能下载已确认 CSV。导出含指纹、均温、RSS、区间与人工意见。
9. 在“研究留痕”核对导入、点修订、任务、审阅和导出记录；HTTP 响应含 X-Request-ID。

## 算法、坐标和失败态

给定温度 y、最小段长 m 和段数上界 Kmax，段成本 `C(a,b)=sum(y[a:b]^2)-sum(y[a:b])^2/(b-a)`，数组采用左闭右开 `[a,b)`。精确 DP 为 `D[k,b]=min_a(D[k-1,a]+C(a,b))`，只访问满足最小段长的前切点。可行 K 上界为 `min(Kmax,floor(N/m))`；Kmax 只是上界，即使 Kmax>N 仍可求解。只有 m>N 才没有任何合法段。N≤600、Kmax≤12。

选择目标 `D[K,N]+β*(K-1)`；首段不受罚，β 的单位与 RSS 一样是温度平方。给定多个预先输入的 β（以及当前 β），复用同一个 DP 的最优 RSS frontier，不为每个 β 重建 DP。结果保存 dp_builds=1、每个 K 的最优 RSS 和所有路径分段。时间复杂度 O(Kmax N²)，状态 O(Kmax N)。

累计成本先减去首个观测，再除以最大中心化绝对偏差，在 NumPy longdouble 中累计一、二阶矩；均值、RSS 和罚项目标换回原单位。零方差的 scale 取1，恒温合法，β=0 也选择一段。中心化/缩放防止大偏移小方差的直接相减消去，但不能恢复输入 double 已经丢失的精度。

平局使用相对 64×longdouble eps 的舍入容差。总目标相同优先更少段；固定 K 在相同数值成本时取更早的最后前切点，递归沿用这一规则。没有随机切点。longdouble 精度依平台变化，本次容器为33位精度。精确指动态规划遍历全部可行状态，而非声称无限精度算术。

断点 b 定义为左侧累计样本数。图中线在序号 b 与 b+1 之间；结果表显示起始序号 a+1、结束序号 b（均含），CSV 一致。相邻均值差为右段均值减左段均值，不附带显著性或因果解释。

## 按持续时间的分段研究

采样间隔不齐时，按点数切段会被密集采样段左右结果。配置页可把研究口径切到“按持续时间”（请求字段 `study_mode:"duration"`），此时点 i 的温度按零阶保持持续到点 i+1 的时刻，末点持续到用户指定的带时区结束时刻 `end_time`；每点权重 wᵢ 即其持续秒数。段成本按时长加权：`C(a,b)=Σwᵢyᵢ²-(Σwᵢyᵢ)²/Σwᵢ`，均温为时长加权均值，RSS 单位为 °C²·秒，选择目标仍为 `D[K,N]+β(K-1)`，因此该口径下 β 与 RSS 同量纲（°C²·秒），不能与按点数研究的 β 数值直接互换。分段约束改为每段持续时长不短于 `min_duration` 秒（正数），不再使用 `min_size`。

加权一、二阶矩沿用同一套中心化/缩放与 longdouble 累计；精确 DP 只访问时长不短于约束的前切点，平局规则与按点数完全一致。可行段数上界先取 `min(Kmax, floor(窗口总时长/min_duration))`，再收敛到实际可达的最大 K——离散切点可能使上界内的某些 K 无法构造，结果只暴露可达 K。只有连一个合法段都凑不出（窗口总时长小于最短段长）才拒绝。

同温区间内插入同温测点只把原区间的持续时长切成两段，区间加权均温、RSS 与断点时刻完全不变（零阶保持的可加矩性质）。因此“同温区间加密测点后结果不变”是可复算的性质，测试用例直接核对边界时刻、均温、RSS 与持续时长。结束时刻必须严格晚于最后观测且为有效带时区时间，否则在提交处返回 422；历史坏任务在 worker 重验时落 failed，不生成伪分段。

时长研究结果额外给出 `end_time`、`min_duration`、`total_duration_seconds`、每段 `start_time`/`end_time`/`duration_seconds`。结果页可核对首尾区间时刻、段间首尾相接以及各段时长合计等于窗口总时长；分段表和巡查导出 CSV 追加“区间起(时刻)/区间止(时刻)/段持续时长(秒)”三列，原十一列保持不变，历史按点数导出照常可读，历史行的新列为空。该口径使用独立的指纹版本 `centered-scaled-duration-weighted-exact-dp-v1`；按点数研究的配置形状与指纹 `centered-scaled-exact-dp-v1` 保持原样，旧运行（无 `study_mode`）一律按按点数处理。

输入每批1–600点，序号从1连续唯一，带时区时间按序号严格递增，温度有限且绝对值≤1e12；重复时间、跳号、倒序、无时区、非有限值、负罚项、重复单一罚项路径和非法参数均拒绝。worker 独立重验，历史坏任务会落 failed，不生成伪分段。指纹包含批次元数据、按序号排序的全部点字段、配置和算法版本，对行序稳定、字段修改敏感。

独立同方差的片段误差是工作近似。平滑漂移也可能切成阶跃；β 路径不是置信区间，分段不是在线警报，均值差不是因果归因。观察过程、测量误差和现场条件必须另行核对。

## 工程结构与开发

|层|技术与职责|
|---|---|
|前端|React18 / TypeScript / Vite6.4.6，SVG按真实序列画图，Work Sans+Noto Serif SC|
|后端|Python3.11 / FastAPI / SQLAlchemy，JWT三角色、审计、错误边界|
|计算|NumPy longdouble，精确DP和单frontier罚项路径，按点数等权与按时长零阶保持加权两套成本共用同一 DP/选择逻辑，Celery5.4/Kombu5.4.2|
|存储|PostgreSQL16 / Redis7，五实体、User和AuditLog|

87 个有职责的 Python/TS/TSX/CSS 文件，不含空包、依赖或构建产物。五个业务实体为 ThermalBatch → TemperaturePoint → SegmentationRun → Segment → InspectionNote，贯穿 ORM、schema、服务、路由、前端API/store和六个业务页面。后端 `src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}`；前端 `src/{api,stores,types,components/common,hooks,pages,router,utils,constants}`。

共享枚举 Role、RunStatus、NoteStatus 位于后端 `src/constants/enums.py` 与前端 `src/constants/enums.ts`。RequestID/Error 两个中间件负责追踪与统一错误；ThermalChart、RunSummary、RunTable 在多页复用，另有 PenaltyPath、SegmentTable 和 common 组件。useAsync/useHash 与 format 工具处理交互和格式。说明冻结 segment_snapshot，底稿修订不能改写已批准导出。

本地前端开发 `cd frontend && npm ci && npm run dev`；`npm run build` 执行 tsc 和 Vite。后端安装 requirements.txt，设置 DATABASE_URL/REDIS_URL/JWT_SECRET 后运行 uvicorn；数据库须先就绪。迁移目录提供初始表结构说明，当前使用 ORM metadata 创建表，没有生产版本迁移链。许可证见 LICENSE（MIT）。

测试脚本、关键 JSON、CSV、截图、日志和完整验收记录位于批次 `test-artifacts/gb-0024/`，其中 TESTING.md 是实际证据索引。测试的 12 点 UI 导入与 4 点手算批次是额外测试输入，不能冒充原始1200点 fixture。未验证生产并发、外部真实设备或超600点。按点数研究按样本个数约束段长、每点等权；按持续时间研究按零阶保持秒数加权并以 `min_duration` 约束段长，两种口径并存、指纹版本不同。字体断网会回退本地衬线/无衬线字体。
