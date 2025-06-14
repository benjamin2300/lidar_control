# LiDAR系統指令集參考文件

## 文件版本：1.0
## 日期：2025-05-17

本文件列出LiDAR掃描系統支援的指令集，用於系統控制與配置。

---

## 1. 通訊協議基本資訊

### 1.1 通訊格式
- **訊息開頭標記**：0xAA55
- **指令格式**：[指令碼(1 Byte)] [參數長度(1 Byte)] [參數(n Bytes)] [校驗和(1 Byte)]
- **回應格式**：[回應碼(1 Byte)] [資料長度(1 Byte)] [資料(n Bytes)] [校驗和(1 Byte)]
- **校驗和計算**：從指令碼到最後一個參數的所有位元組總和取補數

### 1.2 回應碼
- **0x00**：命令執行成功
- **0x01**：參數錯誤
- **0x02**：系統忙
- **0x03**：硬體錯誤
- **0x04**：指令不支援
- **0xFF**：未知錯誤

---

## 2. 系統控制指令

### 2.1 系統初始化與重置
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x01 | 系統重置 | 無 | 執行系統完全重置 |
| 0x02 | 軟體重置 | 無 | 重置軟體，保留校準參數 |
| 0x03 | 設備資訊請求 | 無 | 返回設備ID、韌體版本等 |

### 2.2 系統狀態控制
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x10 | 取得系統狀態 | 無 | 返回系統當前狀態 |
| 0x11 | 設定系統模式 | 1 Byte:<br>0x00=待機<br>0x01=掃描<br>0x02=校準 | 設定系統運行模式 |
| 0x12 | 進入低功耗模式 | 無 | 使系統進入節能狀態 |
| 0x13 | 恢復正常模式 | 無 | 從低功耗模式恢復 |

---

## 3. 馬達控制指令

### 3.1 基本馬達控制
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x20 | 開始馬達運行 | 無 | 啟動BLDC和步進馬達 |
| 0x21 | 停止馬達運行 | 無 | 停止所有馬達運行 |
| 0x22 | 設定BLDC馬達轉速 | 2 Bytes (RPM) | 設定BLDC馬達轉速 |
| 0x23 | 設定步進馬達速度 | 1 Byte (0-7) | 設定步進馬達速度級別 |

### 3.2 校準與原點控制
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x30 | 啟動Go Top Home模式 | 無 | 讓反射鏡移至上方極限位置 |
| 0x31 | 啟動Go Home模式 | 無 | 讓反射鏡移至歸零位置 |
| 0x32 | 移至掃描起點 | 無 | 移動至掃描起始位置 |
| 0x33 | 重新校準編碼器 | 無 | 重置編碼器記數 |

---

## 4. 掃描參數設定指令

### 4.1 掃描範圍設定
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x40 | 設定水平掃描範圍 | 4 Bytes:<br>[起始角度(2)][結束角度(2)] | 設定水平掃描角度範圍，單位0.1度 |
| 0x41 | 設定垂直掃描範圍 | 4 Bytes:<br>[起始角度(2)][結束角度(2)] | 設定垂直掃描角度範圍，單位0.1度 |
| 0x42 | 設定水平解析度 | 2 Bytes (單位0.01度) | 設定水平角解析度 |
| 0x43 | 設定垂直解析度 | 2 Bytes (單位0.01度) | 設定垂直角解析度 |

### 4.2 雷射控制參數
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x50 | 設定雷射重複率 | 4 Bytes (Hz) | 設定雷射發射重複率 |
| 0x51 | 設定雷射功率 | 1 Byte (0-100%) | 設定雷射輸出功率百分比 |
| 0x52 | 設定雷射啟用位置1 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定第一雷射啟用位置 |
| 0x53 | 設定雷射禁用位置1 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定第一雷射禁用位置 |
| 0x54 | 設定雷射啟用位置2 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定第二雷射啟用位置 |
| 0x55 | 設定雷射禁用位置2 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定第二雷射禁用位置 |

### 4.3 步進馬達控制參數
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x60 | 設定脈波數 | 2 Bytes | 設定反射鏡來回掃描所需脈波數 |
| 0x61 | 設定方向改變位置 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定方向改變位置的編碼器數值 |
| 0x62 | 設定起始位置 | 4 Bytes:<br>[高字節(2)][低字節(2)] | 設定掃描起始位置 |

---

## 5. 數據獲取與傳輸控制

### 5.1 數據傳輸控制
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x70 | 開始數據傳輸 | 無 | 開始傳送掃描數據 |
| 0x71 | 停止數據傳輸 | 無 | 停止傳送掃描數據 |
| 0x72 | 設定數據格式 | 1 Byte:<br>0=2字節距離<br>1=4字節距離 | 設定距離數據格式 |
| 0x73 | 設定傳輸速率 | 2 Bytes (Hz) | 設定數據傳輸速率 |

### 5.2 數據獲取控制
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x80 | 請求當前幀 | 無 | 請求當前正在掃描的一幀數據 |
| 0x81 | 請求特定幀 | 2 Bytes (Frame ID) | 請求特定ID的掃描幀 |
| 0x82 | 設定最大回波數 | 1 Byte (1-5) | 設定每個掃描點記錄的最大回波數 |
| 0x83 | 設定回波閾值 | 2 Bytes | 設定回波訊號強度閾值 |

---

## 6. 診斷與維護指令

### 6.1 系統診斷
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0x90 | 執行自檢 | 無 | 執行系統自我診斷 |
| 0x91 | 讀取溫度 | 無 | 讀取系統各部件溫度 |
| 0x92 | 讀取電壓 | 無 | 讀取系統電源電壓 |
| 0x93 | 讀取錯誤記錄 | 無 | 讀取系統錯誤日誌 |

### 6.2 韌體與校準維護
| 指令碼 | 名稱 | 參數 | 說明 |
|--------|------|------|------|
| 0xA0 | 進入韌體更新模式 | 無 | 使系統進入韌體更新狀態 |
| 0xA1 | 保存參數 | 無 | 將當前參數保存到非揮發性記憶體 |
| 0xA2 | 載入預設參數 | 無 | 重置所有參數為出廠設定 |
| 0xA3 | 讀取運行時間 | 無 | 讀取系統總運行時間 |

---

## 7. UDP資料封包格式

### 7.1 標準掃描數據封包
- **Header**: 0xAA55 (2 Bytes)
- **Echo訊息**: 2 Bytes
  - 掃描線號碼(bit0-bit8): 0-299
  - Echo ID(bit9-bit12): 強度、掃描線前半部、後半部、整條掃描線
  - Echo位置(bit13-bit15): 0-4 (1st-5th Echo)
- **額外訊息**: Frame ID (2 Bytes)
- **資料部分**: 距離數據 (水平600點 × 每點2或4 Bytes)

### 7.2 狀態回報封包
- **Header**: 0xAA55 (2 Bytes)
- **類型碼**: 0xFF (1 Byte) 表示這是狀態封包
- **狀態碼**: 1 Byte
- **錯誤碼**: 1 Byte
- **運行模式**: 1 Byte
- **溫度**: 1 Byte
- **其他系統資訊**: n Bytes

---

## 8. 附錄：狀態碼定義

### 系統狀態碼
- 0x00: 系統待機
- 0x01: 系統初始化中
- 0x02: 校準中
- 0x03: 掃描中
- 0x04: 數據處理中
- 0x05: 錯誤狀態
- 0x06: 低功耗模式

### 錯誤碼
- 0x00: 無錯誤
- 0x01: 馬達錯誤
- 0x02: 雷射錯誤
- 0x03: 溫度過高
- 0x04: 電壓異常
- 0x05: 通訊錯誤
- 0x06: 記憶體錯誤
- 0xFF: 未知錯誤

---

**注意**: 本文件僅供參考，實際系統可能有所不同。使用前請確認您的系統版本與指令集相容性。
