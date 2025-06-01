import socket
import keyboard
import threading
import json
import time
import pandas as pd
from datetime import datetime
import csv
import struct
import numpy as np
import math

class LiDARDataAnalyzer:
    def __init__(self, distance_scale=1.0, angle_offset=0.0):
        # 數據幀格式定義
        self.FRAME_IDENTIFIER = 0xAA55
        self.ECHO_TYPES = {
            0b1010: "Intensity",
            0b1101: "First-half of scanning line", 
            0b1110: "Second-half of scanning line"
        }
        
        # LiDAR參數配置
        self.distance_scale = distance_scale
        self.angle_offset = angle_offset
        self.horizontal_fov = 60.0
        self.points_per_line = 300
        self.angle_resolution = self.horizontal_fov / self.points_per_line
        
        # 數據存儲
        self.parsed_frames = []
        self.point_cloud_data = []
        self.is_analyzing = False
        self.frame_count = 0
        self.valid_frame_count = 0
        
    def parse_frame(self, data):
        """解析單個數據幀"""
        if len(data) < 6:  # 先檢查最小長度
            if len(data) > 0:
                print(f"[調試] 數據包太短: {len(data)} 字節")
            return None
            
        try:
            # 檢查幀標識符
            frame_id = struct.unpack('>H', data[0:2])[0]
            
            # 調試信息：顯示幀標識符
            if hasattr(self, '_debug_count'):
                self._debug_count += 1
            else:
                self._debug_count = 1
                
            if self._debug_count <= 10:  # 只顯示前10個幀的調試信息
                print(f"[調試] 幀 #{self._debug_count}: 標識符=0x{frame_id:04X}, 預期=0x{self.FRAME_IDENTIFIER:04X}")
            
            if frame_id != self.FRAME_IDENTIFIER:
                if self._debug_count <= 10:
                    print(f"[調試] 幀標識符不匹配，跳過此幀")
                return None
            
            # 檢查完整幀長度
            if len(data) < 1206:
                print(f"[調試] 完整幀長度不足: {len(data)}/1206 字節")
                return None
                
            # 解析Echo信息
            echo_byte = data[2]
            echo_id = (echo_byte >> 4) & 0x0F
            echo_depth = echo_byte & 0x0F
            echo_line = data[3]
            
            if self._debug_count <= 5:
                print(f"[調試] Echo ID={echo_id}, Depth={echo_depth}, Line={echo_line}")
            
            # 解析Echo數據
            echo_data_raw = data[4:1204]
            echo_points = []
            xyz_points = []
            
            for i in range(0, len(echo_data_raw), 2):
                if i + 1 < len(echo_data_raw):
                    point_value = struct.unpack('>H', echo_data_raw[i:i+2])[0]
                    echo_points.append(point_value)
                    
                    point_index = i // 2
                    x, y, z, distance_mm, h_angle, v_angle = self.convert_to_xyz(
                        point_value, point_index, echo_line
                    )
                    
                    xyz_points.append({
                        'point_index': point_index,
                        'raw_distance': point_value,
                        'distance_mm': distance_mm,
                        'x': x, 'y': y, 'z': z,
                        'horizontal_angle': h_angle,
                        'vertical_angle': v_angle,
                        'valid': x is not None
                    })
            
            # 解析幀計數
            frame_count = struct.unpack('>H', data[1204:1206])[0]
            
            echo_type_key = (echo_id << 1) | (1 if echo_depth > 0 else 0)
            echo_type = self.ECHO_TYPES.get(echo_type_key, f"Unknown ({echo_id:04b})")
            
            if self._debug_count <= 5:
                print(f"[調試] 解析成功! 幀計數={frame_count}, 點數={len(echo_points)}")
            
            parsed_frame = {
                'timestamp': datetime.now(),
                'frame_identifier': frame_id,
                'echo_id': echo_id,
                'echo_depth': echo_depth,
                'echo_line': echo_line,
                'echo_type': echo_type,
                'echo_points': echo_points,
                'xyz_points': xyz_points,
                'frame_count': frame_count,
                'points_count': len(echo_points)
            }
            
            return parsed_frame
            
        except Exception as e:
            print(f"解析錯誤: {e}")
            if hasattr(self, '_debug_count') and self._debug_count <= 5:
                print(f"[調試] 錯誤數據長度: {len(data)}")
            return None

    def convert_to_xyz(self, distance_raw, point_index, echo_line):
        """將極坐標數據轉換為XYZ笛卡爾坐標"""
        distance_mm = distance_raw * self.distance_scale
        
        if distance_mm <= 0:
            return None, None, None, 0, 0, 0
        
        horizontal_angle_deg = (point_index * self.angle_resolution) - (self.horizontal_fov / 2.0) + self.angle_offset
        horizontal_angle_rad = math.radians(horizontal_angle_deg)
        vertical_angle_deg = 0.0
        vertical_angle_rad = math.radians(vertical_angle_deg)
        
        x = distance_mm * math.cos(vertical_angle_rad) * math.cos(horizontal_angle_rad)
        y = distance_mm * math.cos(vertical_angle_rad) * math.sin(horizontal_angle_rad)
        z = distance_mm * math.sin(vertical_angle_rad)
        
        return x, y, z, distance_mm, horizontal_angle_deg, vertical_angle_deg
    
    def start_analysis(self):
        """開始數據分析"""
        self.is_analyzing = True
        self.frame_count = 0
        self.valid_frame_count = 0
        self.parsed_frames = []
        print("開始LiDAR數據分析...")
    
    def stop_analysis(self):
        """停止數據分析"""
        self.is_analyzing = False
        print(f"停止數據分析 - 總幀數: {self.frame_count}, 有效幀數: {self.valid_frame_count}")
    
    def process_frame(self, data):
        """處理單個數據幀"""
        if not self.is_analyzing:
            return
            
        self.frame_count += 1
        parsed_frame = self.parse_frame(data)
        
        if parsed_frame:
            self.valid_frame_count += 1
            self.parsed_frames.append(parsed_frame)
            
            # 每100幀顯示一次狀態
            if self.valid_frame_count % 100 == 0:
                valid_points = len([p for p in parsed_frame['xyz_points'] if p['valid']])
                print(f"已接收 {self.valid_frame_count} 有效幀, 當前幀有效點數: {valid_points}/300")
    
    def export_data(self, filename=None):
        """導出數據"""
        if not self.parsed_frames:
            print("沒有數據可導出")
            return
            
        if filename is None:
            filename = f"lidar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 導出CSV
        csv_data = []
        for frame in self.parsed_frames:
            for xyz_point in frame.get('xyz_points', []):
                if xyz_point['valid']:
                    csv_data.append({
                        'timestamp': frame['timestamp'],
                        'frame_count': frame['frame_count'],
                        'echo_type': frame['echo_type'],
                        'point_index': xyz_point['point_index'],
                        'distance_mm': xyz_point['distance_mm'],
                        'x_mm': xyz_point['x'],
                        'y_mm': xyz_point['y'],
                        'z_mm': xyz_point['z'],
                        'horizontal_angle_deg': xyz_point['horizontal_angle']
                    })
        
        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_filename = f"{filename}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"數據已導出至: {csv_filename} ({len(csv_data)} 個有效點)")

# 全局變量
s = None
analyzer = LiDARDataAnalyzer()
rxRunState = 0
txRunState = 0
remoteAddr = None

def RxMessage():
    """接收控制命令回應和點雲數據"""
    global s, rxRunState, analyzer
    timeCount = 0
    while rxRunState == 1:
        s.settimeout(1)
        timeCount = timeCount + 1
        try:
            indata, addr = s.recvfrom(2048)  # 增加緩衝區大小以接收點雲數據
            
            # 嘗試解碼為文字命令回應
            try:
                response = indata.decode()
                print(response, end='', flush=True)
                if response == 'stopfire':
                    print('cmd>')
            except UnicodeDecodeError:
                # 無法解碼的是二進制點雲數據
                if analyzer.is_analyzing:
                    print(f"\n[調試] 收到點雲數據: {len(indata)} 字節, 來源: {addr}")
                    analyzer.process_frame(indata)
                    
        except socket.timeout:
            continue
        except Exception as e:
            if rxRunState == 1:
                print(f"接收錯誤: {e}")

def TxMessage():
    """發送控制命令"""
    global s, remoteAddr, txRunState, analyzer
    
    while txRunState == 1:
        outdata = input('cmd>')
        if outdata == '':
            pass
        elif outdata == 'exit':
            txRunState = 0
        elif outdata.startswith('scanxy'):
            # 處理掃描命令
            s.sendto(outdata.encode(), remoteAddr)
            parts = outdata.split()
            if len(parts) > 1:
                if parts[1] == '1':
                    analyzer.start_analysis()
                elif parts[1] == '0':
                    analyzer.stop_analysis()
        elif outdata == 'startlidar':
            # 完整的LiDAR啟動序列
            print("執行完整LiDAR啟動序列...")
            commands = ['stephomeup', 'startbldc 0 1000', 'scanxy 1']
            for cmd in commands:
                print(f"發送: {cmd}")
                s.sendto(cmd.encode(), remoteAddr)
                time.sleep(2)  # 等待每個命令完成
            analyzer.start_analysis()
        elif outdata == 'stoplidar':
            # 完整的LiDAR停止序列
            print("執行完整LiDAR停止序列...")
            commands = ['scanxy 0', 'stopbldc', 'stopfire']
            for cmd in commands:
                print(f"發送: {cmd}")
                s.sendto(cmd.encode(), remoteAddr)
                time.sleep(1)
            analyzer.stop_analysis()
        elif outdata == 'stopfire':
            # 停火命令
            s.sendto(outdata.encode(), remoteAddr)
            analyzer.stop_analysis()
        elif outdata == 'exportdata':
            # 導出數據命令
            analyzer.export_data()
        elif outdata == 'showstatus':
            # 顯示狀態命令
            print(f"分析狀態: {'運行中' if analyzer.is_analyzing else '停止'}")
            print(f"總幀數: {analyzer.frame_count}, 有效幀數: {analyzer.valid_frame_count}")
        elif outdata == 'help':
            # 顯示幫助
            print("\n=== 整合版 LiDAR 控制命令 ===")
            print("標準命令: fire, apddc, apdhv, tmp, getid 等 (參考command_list.txt)")
            print("掃描控制:")
            print("  startlidar     - 完整啟動序列 (stephomeup + startbldc + scanxy)")
            print("  stoplidar      - 完整停止序列 (scanxy 0 + stopbldc + stopfire)")
            print("  scanxy 1       - 開始掃描並啟動數據分析")
            print("  scanxy 0       - 停止掃描")
            print("  stopfire       - 停止激光和數據分析")
            print("馬達控制:")
            print("  stephomeup     - 步進馬達回原點")
            print("  startbldc 0 1000 - 啟動無刷馬達 (方向0, 速度1000)")
            print("  stopbldc       - 停止無刷馬達")
            print("數據分析:")
            print("  showstatus     - 顯示當前分析狀態")
            print("  exportdata     - 導出當前數據到CSV")
            print("  exit           - 退出程式")
            print("================================")
        else:
            # 其他命令直接發送
            s.sendto(outdata.encode(), remoteAddr)

def main():
    global s, rxRunState, txRunState, remoteAddr
    
    # 載入網路配置
    etherInfom = {
        "localIP": "192.168.2.194",
        "remoteIP": "192.168.2.10",
        "port": 8880
    }
    
    print('整合版 LiDAR 控制程式 v1.0')
    print('APP version : 20240723 0.0.1 + Data Analyzer')
    
    try:
        with open('etherInform.json', 'r') as openfile:
            etherInfom = json.load(openfile)
    except:
        pass

    # 輸入網路配置
    localIP_Data = input('輸入電腦 IP 位址 :')
    remoteIP_Data = input('輸入光達 IP 位址 :')
    PORT_Data = input('輸入控制埠號 :')

    if localIP_Data != '':
        etherInfom['localIP'] = localIP_Data
    if remoteIP_Data != '':
        etherInfom['remoteIP'] = remoteIP_Data
    if PORT_Data != '':
        etherInfom['port'] = int(PORT_Data)    
        
    # 確保port是整數類型
    if isinstance(etherInfom['port'], str):
        etherInfom['port'] = int(etherInfom['port'])
        
    print(f"控制IP: {etherInfom['localIP']}")
    print(f"LiDAR IP: {etherInfom['remoteIP']}")
    print(f"控制埠: {etherInfom['port']}")
    
    # 保存配置
    with open("etherInform.json", "w") as outfile:
        json.dump(etherInfom, outfile)
    
    HOST = etherInfom['localIP']
    REMOTE = etherInfom['remoteIP']
    PORT = int(etherInfom['port'])  # 確保是整數
    
    localAddr = (HOST, PORT)
    remoteAddr = (REMOTE, PORT)
    
    # 建立Socket (只需要一個)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IsConnectOK = 1
    
    try:
        s.bind(localAddr)
        print(f'LiDAR控制服務器啟動於: {localAddr}')
        print('等待連接...')
        print('輸入 help 查看可用命令')
    except Exception as e:
        print(f'服務器綁定失敗: {localAddr} - {e}')
        input('請按任意鍵結束...........')
        IsConnectOK = 0

    if IsConnectOK == 1:
        # 啟動雙線程 (原始架構)
        rxRunState = 1
        txRunState = 1
        
        rx = threading.Thread(target=RxMessage)
        tx = threading.Thread(target=TxMessage)
        
        rx.start()
        tx.start()
        
        # 等待線程結束
        tx.join()
        
        # 停止接收線程
        rxRunState = 0
        
        print("正在關閉LiDAR控制系統...")
        
        # 如果有數據，詢問是否導出
        if analyzer.valid_frame_count > 0:
            export_choice = input(f"共接收到 {analyzer.valid_frame_count} 有效幀數據，是否導出? (y/n): ")
            if export_choice.lower() == 'y':
                analyzer.export_data()
    
    else:
        txRunState = 0
        rxRunState = 0
    
    # 關閉Socket
    if s:
        s.close()
    
    print("系統已關閉")

if __name__ == "__main__":
    main()