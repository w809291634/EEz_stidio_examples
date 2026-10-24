# native/ —— 手写代码的目录边界

`src/ui/` 由 EEZ 覆盖式生成；`src/native/` 才是手写 C/C++ 的唯一落点。
业务状态集中在 `app/watch_model.*`，页面去向不进入业务文件，平台代码不引用 EEZ 对象。

## 当前布局

```text
src/native/
├── app/                         # [项目可变] 业务保持扁平文件，不再建功能子目录
│   ├── watch_model.*             # 业务状态真值；无 LVGL / 无驱动
│   ├── watch_view.*              # model / 平台快照 → 全部已有 objects.*
│   ├── watch_events.*            # 按钮回调、透明点击区、事件绑定
│   └── watch_logic.*             # 初始化与 100ms 持续状态调度
├── platform/                    # [硬件可变] PC 仿真 / 真机板级适配边界
│   ├── watch_platform.h          # app 唯一可包含的平台接口
│   ├── pc/watch_platform_pc.c    # 宿主时间、模拟数据与日志
│   └── device/watch_platform_device.c # 真机实现入口；启用前必须接板
├── navigation/                  # [框架稳定] 页面进入、返回、Tab 切换
│   └── watch_nav.*
├── widgets/applist/             # [项目可变] AppList 手势、吸附、几何与参数
│   ├── watch_list_native.*
│   └── watch_list_config.h
├── third_party/rxroller/        # [冻结] 上游原文、补丁产物、LICENSE、说明
└── generated/app_rows.*         # [生成] 由 design/build_watch_ui.py 生成，禁止手改
```

## 每层文件与函数做什么

| 文件 | 函数职责 | 可以依赖 | 禁止做什么 |
| --- | --- | --- | --- |
| `app/watch_model.*` | 保存步数、闹钟、计时器、设置等**业务真值**；例如 `watch_model.sport_steps` | C 标准类型 | 引用 `lv_obj_t`、写 UI、调用 BLE/PWM |
| `app/watch_view.*` | 读取 model/平台快照，把主表盘与功能页刷新到 `objects.*` | `watch_model`、`watch_platform_get_local_time()`、`objects.*` | 保存业务状态、决定导航、绑定事件 |
| `app/watch_events.*` | 接收按钮输入、更新 model、发出平台命令、请求局部刷新；入口 `watch_events_bind()` | `watch_model`、view、platform、已有 `objects.*` | 自行推进时间、承担页面跳转 |
| `app/watch_logic.*` | 初始化 events/view；100ms 推进计时、测量、进度等持续状态 | `watch_model`、view、platform | 绑定单击业务、直接访问 `objects.*`、承担页面跳转 |
| `platform/watch_platform.h` | 提供时间、BLE、传感器、背光、声音等窄接口 | C 标准类型 | 引用 `objects.*`、改变页面样式 |
| `platform/pc/` / `platform/device/` | 同一接口的 PC 模拟或真机驱动实现 | C 标准库或板级 SDK | 同时定义同一套 `watch_platform_*` 符号 |
| `navigation/watch_nav.*` | 返回、进入 APP、切换 Tab；入口 `watch_nav_init()` | `objects.*`、列表公开接口 | 保存业务数据、解析硬件数据 |
| `widgets/applist/*` | AppList 滚轮的吸附、行创建、横滑协作、边界约束 | Rxroller、列表配置、`objects.*` | 实现闹钟/媒体等页面业务 |
| `third_party/rxroller/` | 第三方滚轮能力；`Rxroller.c` 由 `design/port_rxroller.py` 重建 | LVGL | 手工修改生成物 |
| `generated/app_rows.*` | 应用顺序、图标和 screen 指针的数据表 | `design_source.APPS` 的生成结果 | 手改内容或加入业务逻辑 |

### 一次点击的调用链

```text
EEZ 生成按钮
  → app/watch_events 的事件回调
  → app/watch_model 更新真值
  → app/watch_view 投影到 objects.*
  → 必要时调用 platform/watch_platform 接口
  → PC 模拟实现 或 真机驱动实现
```

例如“血氧测量”：`on_spo2()` 写入 `spo2_measuring`，调用
`watch_platform_start_spo2()`，再刷新血氧页面；PC 版在定时器后给出模拟结果，
真机版将由传感器回调写入同一个模型字段。

## 新文件放置规则

| 内容 | 目录 | 规则 |
| --- | --- | --- |
| 数据快照 | `app/watch_model.*` | 无 LVGL / 无平台调用 |
| UI 数值、开关、进度、表盘刷新 | `app/watch_view.*` | 只读取 model/平台快照并写 `objects.*` |
| 控件回调与事件绑定 | `app/watch_events.*` | 只做输入→model→平台命令→刷新 |
| 定时推进与装配 | `app/watch_logic.*` | 只做初始化和持续状态推进 |
| PC 时间/模拟数据 | `platform/pc/` | 默认 PC 构建；不得接入板级 SDK |
| RTC、BLE、PWM、传感器、NVS | `platform/device/` | 真机构建定义 `WATCH_PLATFORM_DEVICE` 后实现 |
| 页面跳转、Tab 落点 | `navigation/watch_nav.cpp` | 不保存业务状态，不混入设备协议 |
| 专用动态控件 | `widgets/applist/` | 父对象必须来自 EEZ；控件几何不要在 C 侧另写真值 |
| 上游/第三方件 | `third_party/rxroller/` | 原文、补丁脚本、许可证、台账必须同行 |

## 三条防腐化规则

1. 模型、view、events、logic 四者分离：模型可用无头测试验证，view 不决定业务规则，events 不推进时间，logic 不读 UI 对象。
2. 动态点击区的矩形不手填；要么由 EEZ 生成点击对象，要么从 `design/` 生成 C 常量。
3. 每个新外设接口都先有 PC 模拟实现和断言，再补真机实现；禁止在 `app/` 直接包含 SDK/BLE 驱动头。

## 平台选择规则

PC 构建不定义 `WATCH_PLATFORM_DEVICE`，因此只由 `platform/pc/watch_platform_pc.c`
提供 `watch_platform_*`。真机构建必须定义该宏；PC 文件变为空翻译单元，
`platform/device/watch_platform_device.c` 必须替换为实际板级实现。两者绝不能同时提供接口符号。

## 手写文件的分块注释约定

一个 `.c/.cpp` 文件不按“功能目录”再切碎，而用稳定的区块标题组织。推荐顺序：

```c
/* ===== 1. 模块私有状态与常量 ===== */
/* ===== 2. 小工具 / 坐标换算 ===== */
/* ===== 3. 状态投影或事件回调 ===== */
/* ===== 4. 定时任务 / 算法 ===== */
/* ===== 5. 对外初始化与公开接口 ===== */
```

注释解释“为什么有这个边界或顺序”，不重复函数名。生成物 `generated/` 和上游件
`third_party/` 不手加注释，避免下一次生成或升级时制造无意义 diff。
