# 设计文档

## 概述

本设计文档详细描述了如何将研发效能管理平台的配色方案完全升级为苹果官网的现代化配色风格。设计将采用苹果官网的配色理念，包括纯净的白色背景、精致的灰色层次、标志性的蓝色强调色以及优雅的渐变效果，以提供更加专业和现代的用户界面体验。

## 架构

### 配色系统架构

配色系统将采用分层架构，包含以下层次：

1. **基础色彩层** - 定义主要的背景色和文字色
2. **语义色彩层** - 定义功能性颜色（成功、警告、错误等）
3. **交互色彩层** - 定义悬停、激活等交互状态颜色
4. **主题色彩层** - 支持明暗两种主题模式

### CSS变量系统

使用CSS自定义属性（CSS Variables）来管理所有颜色值，确保一致性和可维护性：

```css
:root {
  /* 苹果官网主色调 */
  --apple-white: #ffffff;
  --apple-gray-50: #f5f5f7;
  --apple-gray-100: #f2f2f7;
  --apple-gray-200: #e8e8ed;
  --apple-gray-300: #d2d2d7;
  --apple-gray-400: #a1a1a6;
  --apple-gray-500: #86868b;
  --apple-gray-600: #6d6d70;
  --apple-gray-700: #515154;
  --apple-gray-800: #424245;
  --apple-gray-900: #1d1d1f;
  --apple-black: #000000;
  
  /* 苹果蓝色系统 */
  --apple-blue: #007aff;
  --apple-blue-dark: #0056cc;
  --apple-blue-light: #4da6ff;
  
  /* 暗色模式颜色 */
  --apple-dark-bg: #000000;
  --apple-dark-surface: #1c1c1e;
  --apple-dark-blue: #0a84ff;
}
```

## 组件和接口

### 1. 导航栏组件

**设计规范：**
- 背景：半透明白色 `rgba(255, 255, 255, 0.8)` 配合毛玻璃效果
- 文字：主标题使用 `--apple-gray-900`，导航链接使用 `--apple-gray-600`
- 激活状态：使用 `--apple-blue` 作为强调色
- 悬停效果：背景变为 `rgba(0, 122, 255, 0.1)`

**实现接口：**
```css
.navbar {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--apple-gray-200);
}

.nav-logo h2 {
  color: var(--apple-gray-900);
}

.nav-link {
  color: var(--apple-gray-600);
}

.nav-link:hover {
  color: var(--apple-blue);
  background: rgba(0, 122, 255, 0.1);
}

.nav-link.active {
  color: var(--apple-blue);
}
```

### 2. 数据指标卡片组件

**设计规范：**
- 背景：纯白色 `--apple-white` 配合微妙阴影
- 标题：使用 `--apple-gray-600`
- 数值：使用 `--apple-blue` 作为强调
- 阴影：苹果风格的多层阴影效果

**实现接口：**
```css
.metric-card {
  background: var(--apple-white);
  border-radius: 12px;
  box-shadow: 
    0 1px 3px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--apple-gray-200);
}

.metric-card h3 {
  color: var(--apple-gray-600);
}

.metric-value {
  color: var(--apple-blue);
}
```

### 3. 按钮组件

**设计规范：**
- 主要按钮：`--apple-blue` 背景，白色文字
- 次要按钮：透明背景，`--apple-blue` 边框和文字
- 悬停效果：使用 `--apple-blue-dark`

### 4. 表格组件

**设计规范：**
- 表头：`--apple-gray-50` 背景，`--apple-gray-700` 文字
- 表格行：交替使用白色和 `--apple-gray-50`
- 边框：使用 `--apple-gray-200`

## 数据模型

### 颜色配置模型

```typescript
interface ColorScheme {
  name: string;
  colors: {
    primary: ColorPalette;
    secondary: ColorPalette;
    neutral: ColorPalette;
    semantic: SemanticColors;
  };
  darkMode: boolean;
}

interface ColorPalette {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
}

interface SemanticColors {
  success: string;
  warning: string;
  error: string;
  info: string;
}
```

### 主题切换模型

```typescript
interface ThemeConfig {
  currentTheme: 'light' | 'dark';
  autoSwitch: boolean;
  systemPreference: boolean;
}
```

## 错误处理

### 颜色对比度检查

实现颜色对比度检查机制，确保所有文字和背景的对比度符合WCAG 2.1 AA标准：

```typescript
function checkColorContrast(foreground: string, background: string): boolean {
  const contrast = calculateContrast(foreground, background);
  return contrast >= 4.5; // AA标准
}
```

### 颜色回退机制

为不支持CSS变量的浏览器提供回退颜色：

```css
.metric-card {
  background: #ffffff; /* 回退颜色 */
  background: var(--apple-white);
}
```

## 测试策略

### 1. 视觉回归测试

使用自动化工具对比配色更新前后的视觉差异：

- 截图对比测试
- 颜色值验证测试
- 对比度合规性测试

### 2. 跨浏览器兼容性测试

测试在不同浏览器中的颜色显示效果：

- Chrome、Firefox、Safari、Edge
- 移动端浏览器兼容性
- 高DPI屏幕显示效果

### 3. 可访问性测试

确保新配色方案符合可访问性标准：

- 颜色对比度测试
- 色盲友好性测试
- 键盘导航可见性测试

### 4. 性能测试

评估配色更新对页面性能的影响：

- CSS文件大小变化
- 渲染性能影响
- 动画流畅度测试

## 实现细节

### 渐变效果实现

苹果官网风格的微妙渐变效果：

```css
.apple-gradient-bg {
  background: linear-gradient(135deg, 
    var(--apple-white) 0%, 
    var(--apple-gray-50) 100%);
}

.apple-button-gradient {
  background: linear-gradient(135deg, 
    var(--apple-blue) 0%, 
    var(--apple-blue-dark) 100%);
}
```

### 毛玻璃效果实现

现代化的毛玻璃背景效果：

```css
.glass-effect {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}
```

### 暗色模式实现

基于CSS媒体查询和数据属性的暗色模式：

```css
@media (prefers-color-scheme: dark) {
  :root {
    --apple-white: var(--apple-dark-bg);
    --apple-gray-50: var(--apple-dark-surface);
    --apple-blue: var(--apple-dark-blue);
  }
}

[data-theme="dark"] {
  --apple-white: var(--apple-dark-bg);
  --apple-gray-50: var(--apple-dark-surface);
  --apple-blue: var(--apple-dark-blue);
}
```

### 动画过渡效果

平滑的颜色过渡动画：

```css
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
}
```

## 迁移策略

### 阶段性实施

1. **第一阶段**：更新CSS变量系统和基础颜色
2. **第二阶段**：更新主要组件（导航栏、卡片、按钮）
3. **第三阶段**：更新数据可视化组件
4. **第四阶段**：实现暗色模式支持
5. **第五阶段**：优化和测试

### 兼容性保证

在迁移过程中保持向后兼容性，确保现有功能不受影响。