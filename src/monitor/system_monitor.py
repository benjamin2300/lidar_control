import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os

class LidarMonitor:
    def __init__(self):
        self.status_history: List[Dict] = []
        self.error_log: List[Dict] = []
        self.max_history_size = 1000
        self.max_error_log_size = 1000
        self.current_status = {
            'system_mode': 0,  # 0:待機, 1:掃描, 2:校準
            'error_code': 0,
            'temperature': 0,
            'voltage': 0,
            'motor_speed': 0,
            'laser_power': 0,
            'scan_progress': 0,
            'last_update': None
        }
        
        # 創建日誌目錄
        os.makedirs('logs', exist_ok=True)
    
    def update_status(self, status_data: Dict) -> None:
        """更新系統狀態"""
        self.current_status.update(status_data)
        self.current_status['last_update'] = datetime.now()
        
        # 添加到歷史記錄
        self.status_history.append(self.current_status.copy())
        
        # 限制歷史記錄大小
        if len(self.status_history) > self.max_history_size:
            self.status_history.pop(0)
    
    def log_error(self, error_code: int, error_msg: str) -> None:
        """記錄錯誤"""
        error_entry = {
            'timestamp': datetime.now(),
            'error_code': error_code,
            'error_msg': error_msg,
            'system_status': self.current_status.copy()
        }
        
        self.error_log.append(error_entry)
        
        # 限制錯誤日誌大小
        if len(self.error_log) > self.max_error_log_size:
            self.error_log.pop(0)
        
        # 保存到文件
        self._save_error_log()
    
    def get_status_history(self, duration_minutes: int = 60) -> List[Dict]:
        """獲取指定時間範圍內的狀態歷史"""
        if not self.status_history:
            return []
            
        cutoff_time = datetime.now().timestamp() - (duration_minutes * 60)
        return [s for s in self.status_history 
                if s['last_update'].timestamp() > cutoff_time]
    
    def get_error_log(self, duration_minutes: int = 60) -> List[Dict]:
        """獲取指定時間範圍內的錯誤日誌"""
        if not self.error_log:
            return []
            
        cutoff_time = datetime.now().timestamp() - (duration_minutes * 60)
        return [e for e in self.error_log 
                if e['timestamp'].timestamp() > cutoff_time]
    
    def _save_error_log(self) -> None:
        """保存錯誤日誌到文件"""
        if not self.error_log:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"logs/error_log_{timestamp}.json"
        
        # 轉換datetime對象為字符串
        log_data = []
        for entry in self.error_log:
            entry_copy = entry.copy()
            entry_copy['timestamp'] = entry_copy['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            if entry_copy['system_status']['last_update']:
                entry_copy['system_status']['last_update'] = \
                    entry_copy['system_status']['last_update'].strftime("%Y-%m-%d %H:%M:%S")
            log_data.append(entry_copy)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)
    
    def get_system_health(self) -> Dict:
        """獲取系統健康狀態"""
        if not self.status_history:
            return {'status': 'unknown', 'message': 'No status data available'}
        
        # 檢查最近的錯誤
        recent_errors = self.get_error_log(duration_minutes=5)
        if recent_errors:
            return {
                'status': 'error',
                'message': f'Recent errors: {len(recent_errors)}',
                'last_error': recent_errors[-1]
            }
        
        # 檢查溫度
        if self.current_status['temperature'] > 80:  # 假設80度為高溫警告
            return {
                'status': 'warning',
                'message': 'High temperature warning',
                'temperature': self.current_status['temperature']
            }
        
        # 檢查電壓
        if self.current_status['voltage'] < 10:  # 假設10V為低電壓警告
            return {
                'status': 'warning',
                'message': 'Low voltage warning',
                'voltage': self.current_status['voltage']
            }
        
        return {
            'status': 'healthy',
            'message': 'System is operating normally',
            'last_update': self.current_status['last_update'].strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def clear_history(self) -> None:
        """清空歷史記錄"""
        self.status_history.clear()
        self.error_log.clear()
    
    def export_status_report(self, duration_minutes: int = 60) -> str:
        """導出狀態報告"""
        if not self.status_history:
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/status_report_{timestamp}.json"
        
        report_data = {
            'report_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'duration_minutes': duration_minutes,
            'status_history': self.get_status_history(duration_minutes),
            'error_log': self.get_error_log(duration_minutes),
            'current_status': self.current_status,
            'system_health': self.get_system_health()
        }
        
        # 轉換datetime對象為字符串
        for entry in report_data['status_history']:
            if entry['last_update']:
                entry['last_update'] = entry['last_update'].strftime("%Y-%m-%d %H:%M:%S")
        
        for entry in report_data['error_log']:
            entry['timestamp'] = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            if entry['system_status']['last_update']:
                entry['system_status']['last_update'] = \
                    entry['system_status']['last_update'].strftime("%Y-%m-%d %H:%M:%S")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        
        return filename 