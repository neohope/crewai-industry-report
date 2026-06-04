# Kill和超时配置指南

本指南说明如何配置项目的超时、kill和质量控制参数。

---

## 📋 配置文件

所有配置在 `.env` 文件中设置。

首先复制模板：
```bash
cp .env.example .env
```

---

## ⏱️ 超时配置详解

### 1. 项目级超时

```env
# 整个项目的最大运行时间（秒）
# 超过此时间会强制终止
PROJECT_TIMEOUT=7200
```

**说明**:
- 默认: 7200 秒 = 2小时
- 建议范围: 1800-14400 秒（30分钟-4小时）
- **用途**: 防止程序无限运行

**示例**:
```env
# 快速测试：30分钟
PROJECT_TIMEOUT=1800

# 完整研究：4小时
PROJECT_TIMEOUT=14400
```

---

### 2. 阶段级超时

```env
# 单个阶段的最大运行时间（秒）
STAGE_TIMEOUT=3600
```

**说明**:
- 默认: 3600 秒 = 1小时
- 用于各个阶段的默认超时

---

### 3. 各阶段具体超时

```env
# 数据采集阶段超时（秒）
# 3个采集员并行运行
COLLECTION_TIMEOUT=2400

# 数据分析阶段超时（秒）
ANALYSIS_TIMEOUT=600

# 报告撰写阶段超时（秒）
WRITE_TIMEOUT=1200

# 报告评价阶段超时（秒）
REVIEW_TIMEOUT=600

# 报告发布阶段超时（秒）
PUBLISH_TIMEOUT=300
```

**各阶段说明**:

| 阶段 | 默认 | 说明 | 建议范围 |
|------|------|------|---------|
| COLLECTION_TIMEOUT | 2400秒（40分）| 3个采集员搜索网络 | 1200-3600 |
| ANALYSIS_TIMEOUT | 600秒（10分）| 数据验证和清洗 | 300-1200 |
| WRITE_TIMEOUT | 1200秒（20分）| 撰写报告 | 600-2400 |
| REVIEW_TIMEOUT | 600秒（10分）| 评价和评分 | 300-900 |
| PUBLISH_TIMEOUT | 300秒（5分）| 发布文档和消息 | 120-600 |

---

## 🎯 质量控制配置

### 1. 迭代次数

```env
# 最大审核迭代次数
MAX_REVIEW_ITERATIONS=2
```

**说明**:
- 默认: 2次
- 每次迭代: 撰写 → 评价
- 建议范围: 1-3次

**示例**:
```env
# 快速模式：1次迭代（不修改）
MAX_REVIEW_ITERATIONS=1

# 标准模式：2次迭代
MAX_REVIEW_ITERATIONS=2

# 高质量模式：3次迭代
MAX_REVIEW_ITERATIONS=3
```

### 2. 通过分数

```env
# 通过评分阈值（0-100）
# 达到或超过此分数视为通过
PASSING_SCORE=95
```

**说明**:
- 默认: 95分
- 范围: 0-100分
- 影响: 决定是否需要继续迭代

**评分维度**:
```
内容详实性：30分
逻辑性：30分
可靠性：25分
可读性：15分
────────────────
总计：100分
```

**示例**:
```env
# 宽松模式：85分通过
PASSING_SCORE=85

# 标准模式：95分通过
PASSING_SCORE=95

# 严格模式：98分通过
PASSING_SCORE=98
```

---

## 📝 日志和调试配置

```env
# 是否启用详细日志
VERBOSE=true

# 是否保存中间结果
SAVE_INTERMEDIATE_RESULTS=true
```

**说明**:
- VERBOSE=true: 显示详细的代理工作过程
- SAVE_INTERMEDIATE_RESULTS=true: 保存每一步的结果

---

## 🔒 安全配置

```env
# 是否启用API调用限流
ENABLE_RATE_LIMIT=true

# API调用最小间隔（秒）
API_CALL_INTERVAL=0.1
```

**说明**:
- 防止API调用过快导致限制
- 0.1秒 = 100毫秒间隔

---

## 🎛️ 推荐配置方案

### 方案1: 快速测试

```env
# 适合快速验证
PROJECT_TIMEOUT=1800          # 30分钟
COLLECTION_TIMEOUT=600        # 10分钟
ANALYSIS_TIMEOUT=300          # 5分钟
WRITE_TIMEOUT=600             # 10分钟
REVIEW_TIMEOUT=300            # 5分钟
PUBLISH_TIMEOUT=120           # 2分钟
MAX_REVIEW_ITERATIONS=1       # 1次迭代
PASSING_SCORE=80              # 80分通过
```

### 方案2: 标准研究

```env
# 适合常规研究
PROJECT_TIMEOUT=7200          # 2小时
COLLECTION_TIMEOUT=2400       # 40分钟
ANALYSIS_TIMEOUT=600          # 10分钟
WRITE_TIMEOUT=1200            # 20分钟
REVIEW_TIMEOUT=600            # 10分钟
PUBLISH_TIMEOUT=300           # 5分钟
MAX_REVIEW_ITERATIONS=2       # 2次迭代
PASSING_SCORE=95              # 95分通过
```

### 方案3: 深度研究

```env
# 适合深入研究
PROJECT_TIMEOUT=14400         # 4小时
COLLECTION_TIMEOUT=3600       # 60分钟
ANALYSIS_TIMEOUT=1200         # 20分钟
WRITE_TIMEOUT=2400            # 40分钟
REVIEW_TIMEOUT=900            # 15分钟
PUBLISH_TIMEOUT=300           # 5分钟
MAX_REVIEW_ITERATIONS=3       # 3次迭代
PASSING_SCORE=98              # 98分通过
```

---

## 🚀 配置验证

### 1. 检查配置文件

```bash
# 查看配置
cat .env
```

### 2. 验证配置

在代码中：

```python
from src.config import Config

# 验证配置
errors = Config.validate()
if errors:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")
else:
    print("配置验证通过！")

# 打印配置
Config.print_config()
```

### 3. 获取阶段超时

```python
from src.config import Config

# 获取采集阶段超时
collection_timeout = Config.get_timeout_for_stage("collection")
print(f"采集阶段超时: {collection_timeout} 秒")

# 获取撰写阶段超时
write_timeout = Config.get_timeout_for_stage("write")
print(f"撰写阶段超时: {write_timeout} 秒")
```

---

## 🛠️ 使用超时工具

### 基本用法

```python
from src.tools.timeout_manager import (
    timeout,
    TimeoutException,
    safe_run,
    timeout_manager
)

# 使用装饰器
@timeout(300)  # 5分钟超时
def long_running_task():
    # 长时间运行的任务
    pass

# 使用安全运行
def my_task():
    # 任务代码
    pass

try:
    result = safe_run(my_task, 300, "任务超时")
    print("任务完成")
except TimeoutException:
    print("任务超时")
```

### 使用计时器

```python
from src.tools.timeout_manager import timeout_manager

# 启动计时器
timeout_manager.start_timer("数据采集", 2400)

# 检查超时
if timeout_manager.check_timeout("数据采集", 2400):
    print("超时了！")

# 获取已运行时间
elapsed = timeout_manager.get_elapsed("数据采集")
print(f"已运行: {elapsed:.1f} 秒")

# 停止计时器
timeout_manager.stop_timer("数据采集")
```

### 使用Kill开关

```python
from src.tools.timeout_manager import kill_switch

# 检查是否被kill
if kill_switch.is_killed():
    print("任务已被终止")

# 在任务中检查
def long_task():
    while not done:
        # 检查kill状态
        kill_switch.check_kill()
        # 继续任务...

# 触发kill
kill_switch.trigger("用户取消")
```

---

## ⚠️ 常见问题

### Q: 任务总是超时怎么办？

A: 增加对应阶段的超时时间：
```env
# 增加采集超时
COLLECTION_TIMEOUT=3600  # 60分钟

# 增加撰写超时
WRITE_TIMEOUT=1800       # 30分钟
```

### Q: 如何快速测试？

A: 使用"快速测试"配置方案（见上文）

### Q: 如何强制终止程序？

A: 使用 `Ctrl+C`，程序会捕获并优雅退出

### Q: 超时后会保存结果吗？

A: 会！程序会保存已有的中间结果

---

## 📊 配置监控

运行时会显示：
```
[⏱️] 计时器 '数据采集' 启动，超时: 2400 秒
[⏳] 运行中... 123.4 / 2400 秒
[✅] 计时器 '数据采集' 停止，运行: 1234.5 秒
```

---

## 🎉 配置检查清单

- [ ] `.env` 文件已创建
- [ ] `OPENAI_API_KEY` 已设置
- [ ] 超时时间已根据需要调整
- [ ] 迭代次数已设置
- [ ] 通过分数已设置
- [ ] 运行 `python check.py` 验证
- [ ] 运行 `python run_all_tests.py` 测试

---

**配置完成后，就可以运行项目了！**
