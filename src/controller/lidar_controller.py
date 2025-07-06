import socket
import json
import threading
import time
from typing import Optional, Tuple, Dict, Any

class LidarController:
    def __init__(self, processor):
        self.processor = processor
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self.local_addr: Tuple[str, int] = ("", 0)
        self.remote_addr: Tuple[str, int] = ("", 0)
        self.data_port: int = 8881  # 新增：數據端口配置
        self.rx_thread: Optional[threading.Thread] = None
        self.tx_thread: Optional[threading.Thread] = None
        self.rx_running: bool = False
        self.tx_running: bool = False
        self.command_queue = []
        self.response_handlers = {}
        self.frame_packets = {}
        self.last_frame_id = None
        self.on_new_frame = None  # UI callback
        self.data_socket: Optional[socket.socket] = None
        self.data_rx_thread: Optional[threading.Thread] = None
        self.data_rx_running: bool = False
        self.frame_buffer = {}  # {frame_id: {y_scan: {'d': d_packet, 'e': e_packet}}}
        self.current_frame_id = None
        
        # 載入配置
        self.load_config()
    
    def load_config(self) -> None:
        """載入網路配置"""
        try:
            # 使用已存在的 etherInform.json 配置文件
            with open('etherInform.json', 'r') as f:
                config = json.load(f)
                self.local_addr = (config['localIP'], config['port'])
                self.remote_addr = (config['remoteIP'], config['port'])
                # 讀取數據端口配置，如果不存在則使用默認值8881
                self.data_port = config.get('dataPort', 8881)
        except FileNotFoundError:
            # 使用預設配置
            self.local_addr = ("192.168.2.194", 8880)
            self.remote_addr = ("192.168.2.10", 8880)
            self.data_port = 8881
    
    def save_config(self) -> None:
        """保存網路配置到 etherInform.json"""
        config = {
            'localIP': self.local_addr[0],
            'remoteIP': self.remote_addr[0],
            'port': self.local_addr[1],  # 控制端口
            'dataPort': self.data_port   # 數據端口
        }
        with open('etherInform.json', 'w') as f:
            json.dump(config, f, indent=4)
    
    def connect(self) -> bool:
        """建立UDP連接（同時監聽控制與數據）"""
        try:
            print(f"[DEBUG] 嘗試綁定控制端口: {self.local_addr}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(self.local_addr)
            print(f"[綁定成功] 控制端口: {self.local_addr}")
            self.connected = True
            self.start_rx_thread()
            # 新增數據socket
            print(f"[DEBUG] 嘗試綁定數據端口: ({self.local_addr[0]}, {self.data_port})")
            self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.data_socket.bind((self.local_addr[0], self.data_port))
            print(f"[綁定成功] 數據端口: ({self.local_addr[0]}, {self.data_port})")
            self.data_rx_running = True
            self.data_rx_thread = threading.Thread(target=self._data_rx_loop)
            self.data_rx_thread.daemon = True
            self.data_rx_thread.start()
            return True
        except Exception as e:
            print(f"連接錯誤: {e}")
            return False
    
    def disconnect(self) -> None:
        """斷開連接"""
        self.rx_running = False
        self.tx_running = False
        if self.socket:
            self.socket.close()
        if self.data_socket:
            self.data_rx_running = False
            self.data_socket.close()
        self.connected = False
    
    def start_rx_thread(self) -> None:
        """啟動接收線程"""
        self.rx_running = True
        self.rx_thread = threading.Thread(target=self._rx_loop)
        self.rx_thread.daemon = True
        self.rx_thread.start()
    
    def _rx_loop(self) -> None:
        """接收數據循環"""
        while self.rx_running:
            try:
                self.socket.settimeout(1)
                data, addr = self.socket.recvfrom(1500)
                self._handle_response(data)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收錯誤: {e}")
                break
    
    def _handle_response(self, data: bytes) -> None:
        """處理接收到的數據，根據新協議自動分辨封包型態"""
        if len(data) < 2:
            return
        # 檢查數據包頭
        if data[0:2] != b'\xAA\x55':
            return
        # 狀態封包: Header(2) + Type(1) + 狀態(1) + 錯誤(1) + 模式(1) + 溫度(1) + ...
        if len(data) >= 7 and data[2] == 0xFF:
            self._parse_status_packet(data)
            return
        # 掃描數據封包: Header(2) + Echo ID/Depth(1) + Echo Line(1) + Echo Data(1200) + Frame Count(2)
        if len(data) >= 1206:
            self._parse_scan_data_packet(data)
            return
        # 其他回應（如指令回應）
        response_code = data[2]
        if response_code in self.response_handlers:
            self.response_handlers[response_code](data[3:])

    def _parse_scan_data_packet(self, data: bytes) -> None:
        """解析新協議掃描數據封包"""
        # 0-1: Header, 2: Echo ID/Depth, 3: Echo Line, 4-1203: Echo Data, 1204-1205: Frame Count
        if len(data) < 1206:
            return
        frame_id = int.from_bytes(data[1204:1206], 'big')
        # 收集封包
        if frame_id not in self.frame_packets:
            self.frame_packets[frame_id] = []
        self.frame_packets[frame_id].append(data)
        # 檢查 frame_id 變化
        if self.last_frame_id is not None and frame_id != self.last_frame_id:
            packets = self.frame_packets.pop(self.last_frame_id, [])
            if packets:
                point_cloud = self.processor.assemble_frame_packets(packets)
                self.processor.current_frame = point_cloud
                if self.on_new_frame:
                    self.on_new_frame(point_cloud)
        self.last_frame_id = frame_id

    def _parse_status_packet(self, data: bytes) -> None:
        """解析狀態封包"""
        # Header(2) + Type(1) + 狀態(1) + 錯誤(1) + 模式(1) + 溫度(1) + ...
        status_code = data[3]
        error_code = data[4]
        mode = data[5]
        temp = data[6]
        print(f"[STATUS] 狀態={status_code}, 錯誤={error_code}, 模式={mode}, 溫度={temp}")
    
    def send_command(self, command_code: int, params: bytes = b'') -> None:
        """發送指令"""
        if not self.connected:
            return
            
        # 構建指令包
        packet = bytearray([0xAA, 0x55, command_code, len(params)])
        packet.extend(params)
        
        # 計算校驗和
        checksum = 0
        for b in packet[2:]:
            checksum += b
        checksum = (~checksum + 1) & 0xFF
        packet.append(checksum)
        
        try:
            self.socket.sendto(bytes(packet), self.remote_addr)
        except Exception as e:
            print(f"發送錯誤: {e}")
    
    def register_response_handler(self, response_code: int, handler: callable) -> None:
        """註冊回應處理函數"""
        self.response_handlers[response_code] = handler
    
    # 系統控制指令
    def system_reset(self) -> None:
        """系統重置 (0x01)"""
        self.send_command(0x01)
    
    def get_device_info(self) -> None:
        """獲取設備信息 (0x03)"""
        self.send_command(0x03)
    
    def set_system_mode(self, mode: int) -> None:
        """設定系統模式 (0x11)"""
        self.send_command(0x11, bytes([mode]))
    
    # 馬達控制指令
    def start_motors(self) -> None:
        """開始馬達運行 (0x20)"""
        self.send_command(0x20)
    
    def stop_motors(self) -> None:
        """停止馬達運行 (0x21)"""
        self.send_command(0x21)
    
    def set_motor_speed(self, speed: int) -> None:
        """設定BLDC馬達轉速 (0x22)"""
        speed_bytes = speed.to_bytes(2, 'big')
        self.send_command(0x22, speed_bytes)
    
    # 掃描控制指令
    def set_scan_range(self, start_angle: int, end_angle: int) -> None:
        """設定水平掃描範圍 (0x40)"""
        params = start_angle.to_bytes(2, 'big') + end_angle.to_bytes(2, 'big')
        self.send_command(0x40, params)
    
    def set_vertical_scan_range(self, start_angle: int, end_angle: int) -> None:
        """設定垂直掃描範圍 (0x41)"""
        params = start_angle.to_bytes(2, 'big') + end_angle.to_bytes(2, 'big')
        self.send_command(0x41, params)
    
    def set_laser_power(self, power: int) -> None:
        """設定雷射功率 (0x51)"""
        self.send_command(0x51, bytes([power]))
    
    # 數據獲取指令
    def start_data_transmission(self) -> None:
        """開始數據傳輸 (改為發送 scanxy 1)"""
        if not self.connected:
            return
        try:
            self.socket.sendto(b'scanxy 1', self.remote_addr)
        except Exception as e:
            print(f"發送錯誤: {e}")
    
    def stop_data_transmission(self) -> None:
        """停止數據傳輸 (改為發送 scanxy 0)"""
        if not self.connected:
            return
        try:
            self.socket.sendto(b'scanxy 0', self.remote_addr)
        except Exception as e:
            print(f"發送錯誤: {e}")
    
    def get_current_frame(self) -> None:
        """請求當前幀 (0x80)"""
        self.send_command(0x80)

    def set_data_format(self, fmt: int) -> None:
        """設定數據格式 (0x72)，0=距離資料, 1=強度資料, 2=距離+強度"""
        self.send_command(0x72, bytes([fmt]))

    def set_packet_split_mode(self, mode: int) -> None:
        """設定封包分割模式 (0x74)，0=完整幀傳輸, 1=分割傳輸"""
        self.send_command(0x74, bytes([mode]))

    def request_scan_line(self, line: int) -> None:
        """請求特定掃描線 (0x84)，line: 0-299"""
        self.send_command(0x84, bytes([line]))

    def request_intensity_data(self, line: int) -> None:
        """請求強度資料 (0x85)，line: 0-299"""
        self.send_command(0x85, bytes([line]))

    def set_on_new_frame_callback(self, callback):
        self.on_new_frame = callback

    def _data_rx_loop(self) -> None:
        """數據端口(8881)接收循環"""
        while getattr(self, 'data_rx_running', False):
            try:
                self.data_socket.settimeout(1)
                data, addr = self.data_socket.recvfrom(2048)
                pkt = self.processor.parse_lidar_packet(data)
                if pkt is None or pkt['packet_type'] not in ('d', 'e'):
                    continue
                frame_id = pkt['frame_id']
                y_scan = pkt['y_scan']
                ptype = pkt['packet_type']
                # 初始化frame_buffer
                if frame_id not in self.frame_buffer:
                    self.frame_buffer[frame_id] = {}
                if y_scan not in self.frame_buffer[frame_id]:
                    self.frame_buffer[frame_id][y_scan] = {}
                self.frame_buffer[frame_id][y_scan][ptype] = pkt
                # frame_id變化時組裝上一幀
                if self.current_frame_id is not None and frame_id != self.current_frame_id:
                    prev_packets = self.frame_buffer.pop(self.current_frame_id, {})
                    if prev_packets:
                        point_cloud = self.processor.assemble_point_cloud(prev_packets)
                        self.processor.current_frame = point_cloud
                        if self.on_new_frame:
                            self.on_new_frame(point_cloud)
                self.current_frame_id = frame_id
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[8881接收錯誤] {e}")
                break 