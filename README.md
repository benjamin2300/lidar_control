# LiDAR 控制系統

## 系統說明
這是一個用於控制和可視化 LiDAR 數據的系統。系統提供了基本的 LiDAR 控制功能以及進階的 3D 點雲可視化功能。

## 開發環境
- Python 3.x
- PyQt5
- NumPy

## 打包說明
使用 PyInstaller 打包應用程式，生成可執行文件。

### 打包指令
```bash
# 基本打包指令（生成可執行文件）
pyinstaller --onefile --add-data "etherInform.json;." --name "Lidar控制系統_v0.5.0" main.py
```

### 指令參數說明
- `--onefile`: 生成單一可執行文件
- `--add-data "etherInform.json;."`: 添加配置文件
- `--name "Lidar控制系統_v0.5.0"`: 指定輸出文件名稱

### 打包後文件位置
打包完成後，可執行文件將位於 `dist/` 目錄下。

## 注意事項
1. 確保所有依賴包都已正確安裝
2. 打包前請確保 `etherInform.json` 文件存在於專案根目錄
3. 如果遇到模組導入問題，可以嘗試使用 `--hidden-import` 參數添加缺失的模組

## 常見問題
1. 如果遇到 "ModuleNotFoundError"，請檢查是否所有依賴都已正確安裝
2. 如果配置文件無法讀取，請檢查 `etherInform.json` 是否正確打包

## 版本歷史
- v0.5.0: 當前版本
  - 基本 LiDAR 控制功能
  - 優化系統性能
  - 改進用戶界面
- v0.0.1: 初始版本
  - 基本 LiDAR 控制功能
  - 3D 點雲可視化
  - 進階可視化功能（點大小調整、顏色映射等） 