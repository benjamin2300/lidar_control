# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 項目概述

這是一個基於 Python 的 LiDAR 控制系統，用於控制和可視化 LiDAR 掃描設備。系統提供實時 3D 點雲顯示、數據保存、距離顏色映射等功能。

## 開發環境設置

### 虛擬環境
```bash
# 激活虛擬環境
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate     # Windows
```

### 依賴安裝
```bash
pip install -r requirements.txt
```

### 運行應用程式
```bash
python main.py
```

## 程式碼架構

### 主要模組結構
```
src/
├── controller/
│   └── lidar_controller.py    # LiDAR 設備控制器
├── data/
│   ├── data_processor.py      # 數據處理器
│   └── color_mapper.py        # 距離顏色映射
├── gui/
│   └── main_window.py         # 主要 GUI 介面
├── monitor/
│   └── system_monitor.py      # 系統監控
└── test/
    └── test_open3d.py         # 測試檔案
```

### 核心組件

1. **LidarController** (`src/controller/lidar_controller.py`)
   - 負責 UDP 通信（控制端口 8880，數據端口 8881）
   - 處理掃描指令和數據接收
   - 使用 `etherInform.json` 配置網路參數

2. **LidarDataProcessor** (`src/data/data_processor.py`)
   - 解析 LiDAR 封包數據
   - 組裝點雲數據
   - 處理數據保存和載入

3. **MainWindow** (`src/gui/main_window.py`)
   - 主要使用者介面
   - 3D 點雲可視化（使用 matplotlib）
   - 距離顏色映射顯示

4. **DistanceColorMapper** (`src/data/color_mapper.py`)
   - 根據距離映射顏色
   - 動態調整顏色比例尺

## 開發常用指令

### 測試
```bash
# 目前沒有標準測試框架，建議使用以下方式測試
python main.py  # 測試主程式
python src/test/test_open3d.py  # 測試 Open3D 功能
```

### 程式碼風格
項目使用以下工具：
```bash
# 格式化程式碼
black .

# 檢查程式碼風格
flake8 .
```

### 打包發布
```bash
# 使用 PyInstaller 打包
pyinstaller --onefile --add-data "etherInform.json;." --name "Lidar控制系統_v0.5.0" main.py
```

## 重要配置檔案

### `etherInform.json`
網路配置檔案，包含：
- `localIP`: 本機 IP
- `remoteIP`: LiDAR 設備 IP
- `port`: 控制端口（預設 8880）
- `dataPort`: 數據端口（預設 8881）

### `requirements.txt`
所有 Python 依賴包清單

## 數據格式

### 點雲數據格式
- 使用 NumPy 陣列存儲
- 每個點包含：[X, Y, Z, 距離, 強度]
- 坐標系：右手坐標系，Z 軸向上

### 封包格式
LiDAR 使用 UDP 協議，兩種封包類型：
- "d" 封包：前 300 個 X 軸點（0-299）
- "e" 封包：後 300 個 X 軸點（300-599）

## 開發注意事項

1. **網路配置**：確保 `etherInform.json` 中的 IP 地址正確
2. **端口占用**：程式需要綁定 8880 和 8881 端口
3. **數據存儲**：掃描數據保存在 `data/saved_clouds/` 目錄
4. **座標轉換**：系統使用笛卡爾坐標系，需要進行極坐標轉換
5. **繁體中文**：所有使用者介面和文檔都使用繁體中文

## 故障排除

### 常見問題
1. **連接失敗**：檢查網路配置和端口占用
2. **數據顯示異常**：確認 LiDAR 設備是否正確發送數據
3. **打包失敗**：確認所有依賴包已正確安裝

### 日誌系統
系統提供日誌功能，可通過 GUI 的「顯示日誌」按鈕查看運行狀態。

## 版本控制

項目使用 Git 進行版本控制，主要分支為 `main`。開發時請：
1. 創建功能分支
2. 進行充分測試
3. 提交清晰的 commit 訊息
4. 合併前進行代碼審查