# Flow 路线：WiFi 结构体 + 数组怎么落地

> **⚠ 本目录（no-flow 变体）永远走不了本文这条路**：`flowSupport=false` ⇒ EEZ 不发射
> `eez-flow.cpp/h`，`EEZ_FOR_LVGL` 不成立，于是本文依赖的 `Value` / `ArrayValue` /
> `makeArrayRef` / `getGlobalVariable` / `setGlobalVariable` / `StructValue` **一个都不存在**，
> `aps[i].ssid` 这类绑定写法也无从谈起。要按本文实施，前提是先回退成母工程形态
> （`build_example.py` 里 `flowSupport`、`generateSourceCodeForEezFramework` 改回 `true`）。
> 实测对照见 `README.md` 的账单表与 `ARCHITECTURE.md` §8。
>
> **★ 已被 v4 取代（2026-10-21）**：数组变量已移出 EEZ（`ap_info`/`aps[]`/`ap_len` 删除，
> `ap_store` 桥删除），列表数据由 native 直读 io 接口（`wifi_ap_at`/`wifi_ap_count`）。
> 本文保留作 **v3 历史方案** 与技术调研记录（`makeArrayRef` 三坑等仍在 P-0167 有效）。
> 现行架构见 `ARCHITECTURE.md`（v4）与 `design/mockups/mockup_17_flow_arch.svg`（v4）。

> 前提：**走 EEZ Flow 运行时**（`EEZ_FOR_LVGL`）。这条路能用 `aps[i].ssid` 这种写法，
> 变量数从 37 降到 3，但换执行模型。本文只写"要建什么、怎么填、卡在哪"。

---

## 1. "这个变量是不是 C++ 容器？" —— 分三层看

| 视角 | 实际类型 | 说明 |
|---|---|---|
| **EEZ Studio 里（画布预览 / Run）** | JS 值（`ArrayValue` / `StructValue` 类） | Studio 自带一套 JS 版 Flow 解释器做预览；数组就是 JS Array，可任意 push/裁剪 |
| **设备侧（生成的 C++ 固件）** | `eez::flow::Value` / `ArrayValue` / `StructValue` | eez-flow 的 C++ 运行时：`ArrayValue` 是 `{ arraySize, arrayType, Value values[1] }` **定长柔性数组**（`makeArrayRef` 创建，引用计数），结构体是「字段值数组 + 类型 id」→ **是 C++ 容器，但不可变长、不能 push** |
| **你的 C 代码里** | 不是容器，是 **Value 句柄** | 只能通过 eez-flow 的 API 读写（`getGlobalVariable` / `Value` / `ArrayValue`），**不能**当 `ap_t[]` 直接 memcpy |

> 已在本机核实：Studio 的 asar 里确实有 `ArrayValue` / `StructValue` /
> `getGlobalVariable` 这套 JS 实现（预览用）。C++ 侧（`eez/flow/flow.h`）
> 本机没有源码，**API 具体名字需要拉 eez-flow 源码确认后再写**——我不猜。

---

## 2. 前提三件事（缺一个，`structs.h` 就是空的）

`structs.h` 生成模板整段被 `#if defined(EEZ_FOR_LVGL)` 包着，所以：

| # | 条件 | 现状 |
|---|---|---|
| 1 | 编译宏 `EEZ_FOR_LVGL` | ✅ 已满足：`eez-flow.h` 第 17 行自带 `#define EEZ_FOR_LVGL 1` |
| 2 | 链接 **eez-flow 库**（`eez/flow` + `eez/core`） | 当前只链 lvgl + 源码，**没有** |
| 3 | `ui_init()` 走 `eez_flow_init(assets,…)` | ✅ 已满足：`ui.c:48` 已调用，`assets[444]` 已生成并编入 |

> 也就是说："用 Flow" 不是勾一个开关，而是**换 UI 执行模型**。`flowSupport: true`
> 只是允许 Studio 编辑 Flow，不代表固件已经在跑 Flow。

---

## 3. EEZ 里要建的东西（Flow 路线）

### 3.1 Struct 定义（Variables 面板 → Structures）

| 字段 | 类型 | 说明 |
|---|---|---|
| `ssid` | String | 网络名 |
| `auth` | Integer | 0 open / 1 WPA2 / 2 WPA3（枚举更好：`AuthType`） |
| `rssi` | Integer | dBm（负值） |
| `band` | Integer | 0 = 2.4G / 1 = 5G |
| `lock` | Boolean | 需要密码 |
| `saved` | Boolean | 已保存密码 |
| `conn` | Boolean | 当前已连接 |

### 3.2 变量（全局）

| 名称 | 类型 | 作用 |
|---|---|---|
| `aps` | `ap_info[]`（数组） | **扫描结果本体**，运行时可变长（C 侧 push） |
| `ap_len` | Integer | 长度/总数。**必须单独有**——EEZ 表达式没有 null 判断，"列表为空"要靠它 |
| `scan_state` | Integer | 0 空闲 / 1 扫描中 / 2 完成 |
| `wifi_state` | Integer | 0 未连 / 1 连接中 / 2 已连 / 3 失败 |
| `pick_index` | Integer | 当前选中项的下标（替代 `pick_ssid`） |

**对比**：扁平方案要 37 个输入变量，这边 **3 个**（`aps` + `ap_len` + `scan_state`）。

### 3.3 绑定写法（5 行固定，下标写死）

| 控件 | 绑定 |
|---|---|
| 行 N 显隐 | `ap_len <= N` → hidden（N = 0..4） |
| `lbl_ssid_N` | `aps[N].ssid` |
| `lbl_meta_N` | `aps[N].auth == 0 ? "开放网络" : aps[N].auth == 2 ? "WPA3" : "WPA2"` + `" · " + aps[N].rssi + "dBm"` |
| `bar_N_k` | `aps[N].rssi < TH[k]` → hidden（TH = -85/-75/-65/-55） |
| `img_lock_N` | `!aps[N].lock` → hidden |
| `pill_conn_N` | `!aps[N].conn` → hidden |
| `pill_saved_N` | `!aps[N].saved` → hidden |
| 空态 | `!(scan_state == 2 && ap_len == 0)` → hidden |
| 标题计数 | `"已发现 " + ap_len + " 个网络"` |

> ★ 关键认知：**数组能存 16 个，UI 仍只显示 5 行**。Flow 的 LVGL 项目里没有
> "列表 repeater/动态建行"，行还是要手动摆 5 个、下标写死。所以"用数组"换来的是
> 变量数少、数据成组，**不是**无限列表。

---

## 4. C 侧怎么填充（API 名字待核实，先给形状）

```cpp
#include <eez/flow/flow.h>
using namespace eez::flow;

void publish(const ap_t *list, int n)
{
    Value v = getGlobalVariable("aps");        // ← 名称/签名待核实
    ArrayValue &arr = v.getArray();            // ← 方法名待核实
    // 注：数组定长（makeArrayRef 创建），没有 clear/push；
    //     正确做法是一次建好 N 条，之后只改每个元素的字段
    for (int i = 0; i < n; i++) {
        Value item = makeValue();              // 按 StructType 逐字段 set
        setStructField(item, "ssid",  makeStringValue(list[i].ssid));
        setStructField(item, "rssi",  makeIntValue(list[i].rssi));
        /* auth / band / lock / saved / conn 略 */
        arr.values.push_back(item);
    }
    setGlobalVariable("ap_len", makeIntValue(n));
    setGlobalVariable("scan_state", makeIntValue(2));
}
```

**必须核实的 4 个点**（拉 eez-flow 源码后逐一确认，别照抄我上面写的名字）：
1. 全局变量怎么按名字取：`getGlobalVariable(name)` 还是 `g_globalVariables[enum]`；
2. `Value` 的构造/装箱函数名（`makeIntValue` / `Value(int32_t)`）；
3. `ArrayValue` 的成员名（`values` / `array`）与是否提供 `push`；
4. 结构体字段写入方式（按字段名还是按 index）。

---

## 5. 迁移清单（从当前"生成 C 代码"切到 Flow）

| # | 改动 | 影响 |
|---|---|---|
| 1 | `PC_SIM` CMake 加 `EEZ_FOR_LVGL` 定义 + 引入 eez-flow/eez-core 源 | 首次编译量变大 |
| 2 | 生成 assets 并嵌入（`eez_flow_init` 需要） | 构建流程多一步 |
| 3 | `src/native/app_model` 的 `get_var_* / set_var_*` 桥 → Flow 变量 API | io 层全部改写（**v4 收口已逆转**：EEZ 不再持有变量，此桥删除） |
| 4 | `native_vars.cpp` **已删除**（v4 收口：EEZ 不持有任何变量，无 Flow 变量桥） | 少一层 |
| 5 | `cli_build` 的 flow 守卫、`audit_chars`、`measure_ui`、check_project | 这些围绕"生成 C 代码"写，需重新验证 |
| 6 | 半页/键盘行为接线（`ui_behavior.cpp` 里直接操作 `objects.*`） | Flow 模式下 `objects` 仍可用，但要确认初始化顺序 |

---

## 6. 建议的验证顺序（别一步到位）

1. **最小实验（半天）**：新建空工程 → 开 `flowSupport` → 建 `ap_info` + `aps[]` + `ap_len`
   → 1 个 label 绑 `aps[0].ssid` → 在 Studio 的 Run 里先看到（JS 侧）；
2. **上 PC_SIM**：加 `EEZ_FOR_LVGL` + eez-flow，只跑一个静态数组（C 侧写死 2 条），
   看 label 能否显示 → 这一步能暴露 assets/初始化/API 三件事是否对；
3. **接 io**：把 `publish()` 接上扫描结果，验空列表/5 行/超 5 个截断；
4. 上述都过了，再迁本工程（此时才知道工具链要补什么）。

---

## 7. 我的判断（把话说清）

- **技术上可行**，且变量数从 37 降到 3，写法更自然（`aps[i].ssid`）；
- **但它是"换运行时"级别的改动**，不是加两个变量：3 个前提条件 + 6 项迁移 + 工具链重建；
- **它不会带来无限列表**：UI 仍是 5 个固定行；
- 如果目标是"数据成组、变量少"→ 值得切；如果目标是"尽快跑通、复用已验证工具链"
  → 扁平槽位更快（`IMPLEMENTATION.md` §7.4）。

**下一步我能做的**：拉 `eez-flow` 的 `flow.h`（GitHub）确认 §4 那 4 个 API 名字，
先给出一个**能编译的 `publish()` 实现 + 最小两变量实验工程**，再决定是否整体迁移。
