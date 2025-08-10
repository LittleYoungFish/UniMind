# 剩余流量查询功能使用指南

## 🚀 快速开始

现在您可以使用自然语言查询中国联通手机的剩余流量了！系统会自动启动联通APP、点击"剩余通用流量"按钮并智能识别页面上的流量数值。

## 📱 使用方式

### 1. 支持的查询指令

以下任何自然语言指令都会触发流量查询：

```text
查询剩余流量
我想看看还有多少流量
剩余通用流量是多少
查询流量使用情况
流量还有多少
数据流量余量
```

### 2. 通过Web界面使用

1. 访问 Web 界面
2. 在聊天框中输入上述任何一条指令
3. 系统会自动执行以下步骤：
   - 检查设备连接
   - 启动中国联通APP
   - 查找并点击"剩余通用流量"按钮
   - 智能识别页面流量数据
   - 返回结果

### 3. 通过API直接调用

```python
from agilemind.tool.app_automation_tools import AppAutomationTools

# 初始化工具
tools = AppAutomationTools()

# 查询剩余流量
result = tools.query_unicom_data_usage()

# 处理结果
if result['success']:
    print(f"剩余流量: {result['data_usage']}")
    print(f"数值: {result['raw_amount']} {result['unit']}")
    print(f"置信度: {result['confidence_score']}")
    print(f"查询时间: {result['duration_seconds']:.1f} 秒")
else:
    print(f"查询失败: {result['message']}")
```

### 4. 通过通用AI助手调用

```python
from agilemind.universal_ai_assistant import universal_ai_assistant

# 使用自然语言查询
result = universal_ai_assistant("查询剩余流量")

# 查看结果
if result['success']:
    print(result['user_response'])  # "流量查询成功！您的剩余流量为 156.08GB"
else:
    print(result['error'])
```

## 📊 结果展示

### Web界面展示特点

1. **彩色显示**：根据剩余流量自动选择颜色
   - 🟢 绿色：10GB以上（充足）
   - 🟠 橙色：1-10GB（适中）
   - 🔴 红色：1GB以下（偏少）

2. **智能建议**：
   - 流量不足时提醒及时充值
   - 流量适中时提示合理使用
   - 流量充足时显示可放心使用

3. **详细信息**：
   - 显示具体数值和单位
   - 显示智能识别置信度
   - 显示查询执行时间

### 典型查询结果

```json
{
  "success": true,
  "data_usage": "156.08GB",
  "raw_amount": 156.08,
  "unit": "GB",
  "confidence_score": 105,
  "query_time": "2024-08-10 13:29:25",
  "duration_seconds": 67.1,
  "message": "成功查询剩余流量: 156.08GB"
}
```

## 🔧 技术细节

### 支持的流量单位
- **GB** (Gigabyte)：最常见格式
- **MB** (Megabyte)：小流量显示
- **TB** (Terabyte)：大流量套餐

### 智能识别能力
- 自动识别"2.5GB"格式的完整流量信息
- 智能关联分离的数值和单位（如"2.5"+"GB"）
- 基于上下文关键词提升识别准确性
- 支持多种流量相关术语识别

### 执行流程
1. **设备检测**：检查Android设备连接状态
2. **APP启动**：自动启动中国联通APP
3. **按钮定位**：智能查找"剩余通用流量"按钮
4. **精确点击**：避免意外滑动的精确点击操作
5. **智能识别**：使用语义分析提取流量数据
6. **结果返回**：格式化返回查询结果

## ⚠️ 使用注意事项

### 前置条件
- Android设备通过USB连接
- 已安装中国联通手机营业厅APP
- 设备已开启USB调试模式
- ADB工具正常工作

### 常见问题

**Q: 查询失败怎么办？**
A: 请检查：
- 设备连接是否正常
- 联通APP是否已安装
- 网络连接是否稳定
- APP是否需要登录

**Q: 识别结果不准确怎么办？**
A: 系统会显示置信度分数，如果分数较低可能存在识别问题，建议手动确认。

**Q: 查询速度慢怎么办？**
A: 正常查询时间为60-80秒，包含APP启动和界面响应时间，属于正常范围。

## 🎯 使用建议

1. **定期查询**：建议每日查询一次了解流量使用情况
2. **流量管理**：根据剩余流量合理规划上网行为
3. **及时充值**：当剩余流量低于1GB时及时充值
4. **多种方式**：可以通过Web界面、API或命令行多种方式使用

## 📞 技术支持

如遇到任何问题，请：
1. 查看详细日志信息
2. 检查设备连接状态
3. 确认APP版本兼容性
4. 参考错误提示信息

---

*功能版本: 1.0*  
*更新时间: 2024年8月*  
*兼容系统: Android 7.0+*
