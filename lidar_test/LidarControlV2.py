import socket
import keyboard
import threading
import json
import struct
from datetime import datetime
import time

class LiDARController:
    def __init__(self):
        self.load_config()
        self.setup_sockets()
        self.running = True
        self.monitoring_8881 = False
        
    def load_config(self):
        """載入網路配置"""
        self.etherInfom = {
            "localIP": "192.168.2.194",
            "remoteIP": "192.168.2.10", 
            "port": 8880
        }
        
        try:
            with open('etherInform.json', 'r') as openfile:
                self.etherInfom = json.load(openfile)
        except:
            pass
        
        # 允許用戶更新配置
        localIP_Data = input('輸入電腦 IP 位址 (Enter=使用現有): ')
        remoteIP_Data = input('輸入光達 IP 位址 (Enter=使用現有): ')
        PORT_Data = input('輸入控制埠號 (Enter=使用現有): ')
        
        if localIP_Data != '':
            self.etherInfom['localIP'] = localIP_Data
        if remoteIP_Data != '':
            self.etherInfom['remoteIP'] = remoteIP_Data  
        if PORT_Data != '':
            self.etherInfom['port'] = int(PORT_Data)
        
        print(f"本機IP: {self.etherInfom['localIP']}")
        print(f"光達IP: {self.etherInfom['remoteIP']}")
        print(f"控制端口: {self.etherInfom['port']}")
        
        # 保存配置
        with open("etherInform.json", "w") as outfile:
            json.dump(self.etherInfom, outfile)
    
    def setup_sockets(self):
        """設置socket連線"""
        self.HOST = self.etherInfom['localIP']
        self.REMOTE = self.etherInfom['remoteIP']
        self.PORT = self.etherInfom['port']
        
        self.localAddr = (self.HOST, self.PORT)
        self.remoteAddr = (self.REMOTE, self.PORT)
        
        # 控制socket (原本的功能)
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 8881監聽socket (新增)
        self.monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.control_socket.bind(self.localAddr)
            print(f'控制端口啟動: {self.localAddr}')
            self.control_connected = True
        except Exception as e:
            print(f'控制端口綁定失敗: {self.localAddr}, 錯誤: {e}')
            self.control_connected = False
        
        try:
            self.monitor_socket.bind((self.HOST, 8881))
            print(f'數據監聽端口啟動: {self.HOST}:8881')
            self.monitor_connected = True
        except Exception as e:
            print(f'監聽端口綁定失敗: {self.HOST}:8881, 錯誤: {e}')
            self.monitor_connected = False
    
    def rx_control_messages(self):
        """接收控制回應 (原本的RxMessage功能)"""
        while self.running and self.control_connected:
            try:
                self.control_socket.settimeout(1)
                indata, addr = self.control_socket.recvfrom(1500)
                message = indata.decode()
                print(f"[控制回應] {message}", end='', flush=True)
                if message == 'stopfire':
                    print('cmd>')
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[控制接收錯誤] {e}")
                break
    
    def monitor_8881_data(self):
        """監聽8881端口數據"""
        frame_count = 0
        
        while self.running and self.monitor_connected and self.monitoring_8881:
            try:
                self.monitor_socket.settimeout(1)
                data, addr = self.monitor_socket.recvfrom(2048)
                frame_count += 1
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                if len(data) == 1206:  # LiDAR數據幀
                    self.analyze_lidar_frame(data, frame_count, timestamp)
                elif len(data) == 606:  # 狀態數據
                    print(f"\n[8881-狀態] 時間:{timestamp} 大小:{len(data)}字節 第{frame_count}包")
                else:
                    print(f"\n[8881-其他] 時間:{timestamp} 大小:{len(data)}字節 第{frame_count}包")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running and self.monitoring_8881:
                    print(f"[8881監聽錯誤] {e}")
                break
    
    def analyze_lidar_frame(self, data, frame_count, timestamp):
        """根據最新規格解析LiDAR數據幀"""
        try:
            # 幀標識符（0-1）：0xAA55，little-endian
            frame_flag = int.from_bytes(data[0:2], byteorder='little')
            if frame_flag != 0xAA55:
                print(f"\n[8881-數據] 非標準幀 時間:{timestamp} 幀頭:0x{frame_flag:04X}")
                return

            # 封包類型type: 13->'d', 14->'e', 10->'a'
            packet_type_val = (data[3] >> 4) & 0x0F
            packet_type = {13: 'd', 14: 'e', 10: 'a'}.get(packet_type_val, f'unk({packet_type_val})')
            y_scan = ((data[3] & 0x0F) << 8) | data[2]

            # 距離數據（4-1203）：300點，每點4字節little-endian，僅過濾0為None
            distances = []
            for i in range(4, 1204, 4):
                dist = int.from_bytes(data[i:i+4], byteorder='little')
                if dist != 0:
                    distances.append(dist)
                else:
                    distances.append(None)  # 無效點

            # Frame ID（1204-1205）：little-endian
            frame_id = int.from_bytes(data[1204:1206], byteorder='little')

            # 統計有效點
            valid_distances = [d for d in distances if d is not None]
            min_dist = min(valid_distances) if valid_distances else 0
            max_dist = max(valid_distances) if valid_distances else 0

            print(f"raw type val: {packet_type_val}")
            print(f"\n[LiDAR數據] 時間:{timestamp} 幀#{frame_id} 類型:{packet_type} Y順序:{y_scan}")
            print(f"           有效點:{len(valid_distances)}/300 範圍:{min_dist}-{max_dist}")

        except Exception as e:
            print(f"\n[數據解析錯誤] {e}")
    
    def send_command(self):
        """發送控制命令 (原本的TxMessage功能)"""
        while self.running and self.control_connected:
            try:
                outdata = input('cmd>')
                
                if outdata == '':
                    continue
                elif outdata == 'exit':
                    self.running = False
                    break
                elif outdata == 'monitor_start':
                    # 特殊命令：開始監聽8881
                    self.start_8881_monitoring()
                elif outdata == 'monitor_stop':
                    # 特殊命令：停止監聽8881
                    self.stop_8881_monitoring()
                elif outdata == 'help_extended':
                    # 顯示擴展命令幫助
                    self.show_extended_help()
                else:
                    # 發送正常的LiDAR命令
                    self.control_socket.sendto(outdata.encode(), self.remoteAddr)
                    print(f"[已發送] {outdata} -> {self.remoteAddr}")
                    
            except Exception as e:
                print(f"[命令發送錯誤] {e}")
                break
    
    def start_8881_monitoring(self):
        """開始8881端口監聽"""
        if not self.monitor_connected:
            print("[錯誤] 8881端口未連接")
            return
            
        if not self.monitoring_8881:
            self.monitoring_8881 = True
            monitor_thread = threading.Thread(target=self.monitor_8881_data)
            monitor_thread.daemon = True
            monitor_thread.start()
            print("[8881監聽] 已開始監聽數據流")
        else:
            print("[8881監聽] 已在監聽中")
    
    def stop_8881_monitoring(self):
        """停止8881端口監聽"""
        self.monitoring_8881 = False
        print("[8881監聽] 已停止監聽")
    
    def show_extended_help(self):
        """顯示擴展命令幫助"""
        print("\n=== 擴展控制命令 ===")
        print("monitor_start    - 開始監聽8881端口數據")
        print("monitor_stop     - 停止監聽8881端口數據") 
        print("help_extended    - 顯示此幫助")
        print("exit            - 退出程式")
        print("\n=== 標準LiDAR命令 ===")
        print("fire [cnt]      - 開始掃描")
        print("stopfire        - 停止掃描")
        print("help            - 顯示LiDAR命令幫助")
        print("getid           - 獲取設備ID")
        print("tmp             - 獲取溫度")
        print("(更多命令請參考 command_list.txt)")
    
    def run(self):
        """主運行函數"""
        if not self.control_connected:
            print("控制連接失敗，無法啟動")
            input('請按任意鍵結束...')
            return
        
        print(f"\n=== LiDAR 控制器啟動 ===")
        print(f"控制端口: {self.localAddr}")
        print(f"目標設備: {self.remoteAddr}")
        print(f"監聽端口: {self.HOST}:8881 {'[已連接]' if self.monitor_connected else '[連接失敗]'}")
        print("輸入 'help_extended' 查看所有命令")
        
        # 啟動接收線程
        rx_thread = threading.Thread(target=self.rx_control_messages)
        rx_thread.daemon = True
        rx_thread.start()
        
        # 主線程處理命令輸入
        try:
            self.send_command()
        except KeyboardInterrupt:
            print("\n用戶中斷")
        finally:
            self.running = False
            self.monitoring_8881 = False
            print("正在關閉連接...")
            self.control_socket.close()
            self.monitor_socket.close()
            print("程式已退出")

# 主程式
if __name__ == "__main__":
    print('LiDAR 控制器 version : 20240723 0.0.2 (含8881監聽)')
    
    controller = LiDARController()
    controller.run()