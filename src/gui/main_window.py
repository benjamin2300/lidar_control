import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Optional, Dict, Any
import socket
import threading
import matplotlib
import subprocess
import struct
import sys
import pyvista as pv
import time
from threading import Lock
import multiprocessing
import os
import gc
from datetime import datetime

matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

from src.controller.lidar_controller import LidarController
from src.data.data_processor import LidarDataProcessor
from src.monitor.system_monitor import LidarMonitor

class MainWindow:
    def __init__(self, root: ThemedTk, controller: LidarController, 
                 processor: LidarDataProcessor, monitor: LidarMonitor):
        self.root = root
        self.controller = controller
        self.processor = processor
        self.monitor = monitor
        
        # 設置主視窗
        self.root.title("LiDAR 控制系統")
        self.root.geometry("1200x900")
        
        # 3D圖表比例尺設定
        self.fixed_scale_enabled = True  # 是否啟用固定比例尺
        self.x_range = [-10, 10]  # X軸範圍 (米)
        self.y_range = [-10, 10]  # Y軸範圍 (米)
        self.z_range = [-5, 15]   # Z軸範圍 (米)
        self.auto_adjust_range = False  # 是否根據數據自動調整範圍一次
        
        # 創建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 創建各個面板
        self._create_menu()
        self._create_status_bar()
        self._create_control_panel()
        self._create_visualization_panel()
        self._create_log_panel()
        
        # 設置定時更新
        self._schedule_updates()
        
        # 設定點雲刷新 callback
        self.controller.set_on_new_frame_callback(self.on_new_frame)
        
        self.log_buffer = []  # 儲存所有log訊息
        self.log_window = None
        self.log_text_widget = None
        
        # 初始化3D視圖顯示
        self._update_visualization()
    
    def _create_menu(self) -> None:
        """創建菜單欄"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜單
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存數據", command=self._save_data)
        file_menu.add_command(label="導出報告", command=self._export_report)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 設置菜單
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設置", menu=settings_menu)
        settings_menu.add_command(label="網路設置", command=self._show_network_settings)
        settings_menu.add_command(label="掃描參數", command=self._show_scan_settings)
        settings_menu.add_command(label="數據格式", command=self._show_data_format_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="3D視圖設置", command=self._show_3d_view_settings)
        
        # 幫助菜單
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="幫助", menu=help_menu)
        help_menu.add_command(label="使用說明", command=self._show_help)
        help_menu.add_command(label="關於", command=self._show_about)
    
    def _create_status_bar(self) -> None:
        """創建狀態欄（合併連接與系統狀態）"""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=2)
        self.status_label = ttk.Label(
            self.status_frame,
            text="未連接",
            foreground="red"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def _create_control_panel(self) -> None:
        """創建控制面板"""
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        # 連接控制
        conn_frame = ttk.Frame(control_frame)
        conn_frame.pack(fill=tk.X, padx=5, pady=2)
        self.connect_btn = ttk.Button(
            conn_frame,
            text="連接",
            command=self._connect_device
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        self.disconnect_btn = ttk.Button(
            conn_frame,
            text="斷開",
            command=self._disconnect_device,
            state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        # 顯示日誌按鈕放在連接/斷開右側
        log_btn = ttk.Button(conn_frame, text="顯示日誌", command=self._show_log_window)
        log_btn.pack(side=tk.LEFT, padx=5)
        
        # 3D視圖控制按鈕
        view_control_btn = ttk.Button(conn_frame, text="固定比例尺", command=self._toggle_fixed_scale)
        view_control_btn.pack(side=tk.LEFT, padx=5)
        self.scale_status_label = ttk.Label(conn_frame, text="固定比例尺: 開啟", foreground="green")
        self.scale_status_label.pack(side=tk.LEFT, padx=5)
        
        # 掃描控制
        scan_frame = ttk.Frame(control_frame)
        scan_frame.pack(fill=tk.X, padx=5, pady=2)
        self.start_scan_btn = ttk.Button(
            scan_frame,
            text="開始掃描",
            command=self._start_scan
        )
        self.start_scan_btn.pack(side=tk.LEFT, padx=5)
        self.stop_scan_btn = ttk.Button(
            scan_frame,
            text="停止掃描",
            command=self._stop_scan
        )
        self.stop_scan_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_visualization_panel(self) -> None:
        """創建可視化面板"""
        vis_frame = ttk.LabelFrame(self.main_frame, text="數據可視化")
        vis_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 創建圖表
        self.fig = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 創建子圖
        self.ax1 = self.fig.add_subplot(121, projection='3d')
        self.ax2 = self.fig.add_subplot(122)
        
        self.fig.tight_layout()
    
    def _create_log_panel(self) -> None:
        pass  # 不再在主視窗顯示日誌
    
    def _schedule_updates(self) -> None:
        pass  # 不再自動定時更新
    
    def _update_status(self) -> None:
        pass  # 不再自動定時更新
    
    def _update_visualization(self) -> None:
        # 清除舊圖
        self.ax1.clear()
        self.ax2.clear()
        
        # 設定基本的軸標籤和標題
        self.ax1.set_title("3D點雲")
        self.ax1.set_xlabel('X (m)')
        self.ax1.set_ylabel('Y (m)')
        self.ax1.set_zlabel('Z (m)')
        self.ax2.set_title("2D投影")
        
        # 如果有數據，繪製點雲
        if self.processor.current_frame is not None:
            data = self.processor.current_frame
            
            if data.shape[1] >= 6:
                # 真實掃描數據，直接用XYZ
                self.ax1.scatter(data[:, 0], data[:, 1], data[:, 2], c=data[:, 3], cmap='viridis')
                self.ax2.scatter(data[:, 0], data[:, 1], c=data[:, 3], cmap='viridis')
            else:
                # 舊的測試數據，極座標轉換
                self.ax1.scatter(
                    data[:, 0] * np.cos(data[:, 1]),
                    data[:, 0] * np.sin(data[:, 1]),
                    data[:, 2], c=data[:, 3], cmap='viridis')
                self.ax2.scatter(
                    data[:, 0] * np.cos(data[:, 1]),
                    data[:, 0] * np.sin(data[:, 1]),
                    c=data[:, 3], cmap='viridis')
        else:
            # 沒有數據時，顯示提示信息
            if self.fixed_scale_enabled:
                # 在3D空間中央顯示提示文字
                mid_x = sum(self.x_range) / 2
                mid_y = sum(self.y_range) / 2  
                mid_z = sum(self.z_range) / 2
                self.ax1.text(mid_x, mid_y, mid_z, '等待數據...\n已設定固定比例尺', 
                             fontsize=12, ha='center', va='center',
                             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            else:
                self.ax1.text(0, 0, 0, '等待數據...', 
                             fontsize=12, ha='center', va='center',
                             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.7))
        
        # 應用固定比例尺設定（無論是否有數據都要設定）
        if self.fixed_scale_enabled:
            self._apply_fixed_scale()
            # 顯示範圍信息在圖表上
            range_info = f"範圍: X[{self.x_range[0]:.0f}~{self.x_range[1]:.0f}] Y[{self.y_range[0]:.0f}~{self.y_range[1]:.0f}] Z[{self.z_range[0]:.0f}~{self.z_range[1]:.0f}]m"
            self.ax1.text2D(0.02, 0.98, range_info, transform=self.ax1.transAxes, 
                           fontsize=8, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        
        # 添加座標箭頭（無論是否有數據都顯示）
        self._add_coordinate_arrows(self.ax1)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _apply_fixed_scale(self):
        """應用固定的比例尺設定到3D圖表"""
        # 設定固定的軸範圍
        self.ax1.set_xlim(self.x_range)
        self.ax1.set_ylim(self.y_range)
        self.ax1.set_zlim(self.z_range)
        
        # 確保比例相等 (可選)
        # self.ax1.set_aspect('equal')  # 注意：3D圖中可能不支持
        
        # 關閉自動縮放
        self.ax1.set_autoscale_on(False)
        self.ax1.autoscale(enable=False)
    
    def _toggle_fixed_scale(self):
        """切換固定比例尺功能"""
        self.fixed_scale_enabled = not self.fixed_scale_enabled
        if self.fixed_scale_enabled:
            self.scale_status_label.config(text="固定比例尺: 開啟", foreground="green")
            self._log_message("已啟用固定比例尺")
        else:
            self.scale_status_label.config(text="固定比例尺: 關閉", foreground="red")
            self.ax1.set_autoscale_on(True)
            self.ax1.autoscale(enable=True)
            self._log_message("已關閉固定比例尺")
        
        # 立即重新繪製
        if self.processor.current_frame is not None:
            self._update_visualization()
    
    def _show_3d_view_settings(self):
        """顯示3D視圖設置對話框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("3D視圖設置")
        settings_window.geometry("500x400")  # 增加視窗高度以容納更多按鈕
        settings_window.resizable(False, False)
        
        # 使視窗置中
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 固定比例尺開關
        scale_frame = ttk.LabelFrame(settings_window, text="比例尺設定")
        scale_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.scale_var = tk.BooleanVar(value=self.fixed_scale_enabled)
        scale_check = ttk.Checkbutton(scale_frame, text="啟用固定比例尺", variable=self.scale_var)
        scale_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 軸範圍設定
        range_frame = ttk.LabelFrame(settings_window, text="軸範圍設定 (米)")
        range_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # X軸範圍
        x_frame = ttk.Frame(range_frame)
        x_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(x_frame, text="X軸:").pack(side=tk.LEFT)
        self.x_min_var = tk.DoubleVar(value=self.x_range[0])
        self.x_max_var = tk.DoubleVar(value=self.x_range[1])
        ttk.Entry(x_frame, textvariable=self.x_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(x_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(x_frame, textvariable=self.x_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # Y軸範圍
        y_frame = ttk.Frame(range_frame)
        y_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(y_frame, text="Y軸:").pack(side=tk.LEFT)
        self.y_min_var = tk.DoubleVar(value=self.y_range[0])
        self.y_max_var = tk.DoubleVar(value=self.y_range[1])
        ttk.Entry(y_frame, textvariable=self.y_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(y_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(y_frame, textvariable=self.y_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # Z軸範圍
        z_frame = ttk.Frame(range_frame)
        z_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(z_frame, text="Z軸:").pack(side=tk.LEFT)
        self.z_min_var = tk.DoubleVar(value=self.z_range[0])
        self.z_max_var = tk.DoubleVar(value=self.z_range[1])
        ttk.Entry(z_frame, textvariable=self.z_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(z_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(z_frame, textvariable=self.z_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # 快速設定按鈕 - 重新設計為兩排
        quick_frame = ttk.LabelFrame(range_frame, text="快速設定")
        quick_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # 第一排：小到中等範圍
        quick_frame1 = ttk.Frame(quick_frame)
        quick_frame1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(quick_frame1, text="5m×5m×5m", 
                  command=lambda: self._set_quick_range(5, 5, 5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame1, text="20m×20m×10m", 
                  command=lambda: self._set_quick_range(20, 20, 10)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame1, text="50m×50m×20m", 
                  command=lambda: self._set_quick_range(50, 50, 20)).pack(side=tk.LEFT, padx=2)
        
        # 第二排：大範圍
        quick_frame2 = ttk.Frame(quick_frame)
        quick_frame2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(quick_frame2, text="100m×100m×30m", 
                  command=lambda: self._set_quick_range(100, 100, 30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame2, text="200m×200m×50m", 
                  command=lambda: self._set_quick_range(200, 200, 50)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame2, text="500m×500m×100m", 
                  command=lambda: self._set_quick_range(500, 500, 100)).pack(side=tk.LEFT, padx=2)
        
        # 第三排：超大範圍
        quick_frame3 = ttk.Frame(quick_frame)
        quick_frame3.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(quick_frame3, text="1km×1km×200m", 
                  command=lambda: self._set_quick_range(1000, 1000, 200)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame3, text="2km×2km×300m", 
                  command=lambda: self._set_quick_range(2000, 2000, 300)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame3, text="自定義...", 
                  command=self._show_custom_range_dialog).pack(side=tk.LEFT, padx=2)
        
        # 按鈕區域
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_settings():
            self.fixed_scale_enabled = self.scale_var.get()
            self.x_range = [self.x_min_var.get(), self.x_max_var.get()]
            self.y_range = [self.y_min_var.get(), self.y_max_var.get()]
            self.z_range = [self.z_min_var.get(), self.z_max_var.get()]
            
            # 更新狀態標籤
            if self.fixed_scale_enabled:
                self.scale_status_label.config(text="固定比例尺: 開啟", foreground="green")
            else:
                self.scale_status_label.config(text="固定比例尺: 關閉", foreground="red")
            
            # 立即重新繪製（無論是否有數據都要更新）
            self._update_visualization()
            
            self._log_message(f"3D視圖設置已更新: X={self.x_range}, Y={self.y_range}, Z={self.z_range}")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="應用", command=apply_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def _set_quick_range(self, x_range, y_range, z_range):
        """設定快速範圍"""
        self.x_min_var.set(-x_range/2)
        self.x_max_var.set(x_range/2)
        self.y_min_var.set(-y_range/2)
        self.y_max_var.set(y_range/2)
        self.z_min_var.set(0)
        self.z_max_var.set(z_range)
    
    def _log_message(self, message: str) -> None:
        self.log_buffer.append(message)
        if self.log_text_widget is not None:
            self.log_text_widget.insert(tk.END, message + "\n")
            self.log_text_widget.see(tk.END)
    
    # 事件處理函數
    def _connect_device(self) -> None:
        """連接設備"""
        ctrl_ok = False
        data_ok = False
        try:            
            # 嘗試綁定控制端口
            self.controller.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.controller.socket.bind(self.controller.local_addr)
            ctrl_ok = True
            # 嘗試綁定數據端口
            self.controller.data_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.controller.data_socket.bind((self.controller.local_addr[0], 8881))
            data_ok = True
            self.controller.connected = True
            self.controller.start_rx_thread()
            self.controller.data_rx_running = True
            self.controller.data_rx_thread = threading.Thread(target=self.controller._data_rx_loop)
            self.controller.data_rx_thread.daemon = True
            self.controller.data_rx_thread.start()
        except Exception as e:
            print(f"連接錯誤: {e}")
        # 狀態顯示
        if ctrl_ok and data_ok:
            self.status_label.config(text="已連接", foreground="green")
            self._log_message(f"[連接成功] 控制端口: {self.controller.local_addr} (8880) 數據端口: {self.controller.local_addr[0]}:8881")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        elif not ctrl_ok:
            self.status_label.config(text="控制端口(8880)連接失敗", foreground="red")
            self._log_message(f"[連接失敗] 控制端口: {self.controller.local_addr} (8880)")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
        elif not data_ok:
            self.status_label.config(text="數據端口(8881)連接失敗", foreground="red")
            self._log_message(f"[連接失敗] 數據端口: {self.controller.local_addr[0]}:8881")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
    
    def _disconnect_device(self) -> None:
        self.controller.disconnect()
        self.status_label.config(text="未連接", foreground="red")
        self._log_message(f"[已斷開] 控制端口: {self.controller.local_addr} (8880) 數據端口: {self.controller.local_addr[0]}:8881")
        self._log_message("設備已斷開")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
    
    def _reset_system(self) -> None:
        pass  # 移除系統重置功能
    
    def _change_mode(self, event) -> None:
        pass  # 移除模式切換功能
    
    def _start_motors(self) -> None:
        pass  # 移除啟動馬達功能
    
    def _stop_motors(self) -> None:
        pass  # 移除停止馬達功能
    
    def _change_speed(self, value) -> None:
        pass  # 移除轉速調整功能
    
    def _start_scan(self) -> None:
        """開始掃描"""
        self.controller.start_data_transmission()
        self._log_message("[指令] 已發送開始掃描指令 (start_data_transmission)")
    
    def _stop_scan(self) -> None:
        """停止掃描"""
        self.controller.stop_data_transmission()
        self._log_message("掃描已停止")
    
    def _change_power(self, value) -> None:
        pass  # 移除雷射功率調整功能
    
    def _save_data(self) -> None:
        """保存數據"""
        filename = self.processor.save_buffer()
        if filename:
            self._log_message(f"數據已保存到: {filename}")
        else:
            messagebox.showwarning("警告", "沒有可保存的數據")
    
    def _export_report(self) -> None:
        """導出報告"""
        filename = self.monitor.export_status_report()
        if filename:
            self._log_message(f"報告已導出到: {filename}")
        else:
            messagebox.showwarning("警告", "沒有可導出的報告")
    
    def _show_network_settings(self) -> None:
        """顯示網路設置對話框"""
        # TODO: 實現網路設置對話框
        pass
    
    def _show_scan_settings(self) -> None:
        """顯示掃描設置對話框"""
        # TODO: 實現掃描設置對話框
        pass
    
    def _show_data_format_settings(self) -> None:
        """顯示數據格式設置對話框"""
        # TODO: 實現數據格式設置對話框
        pass
    
    def _show_help(self) -> None:
        """顯示幫助信息"""
        messagebox.showinfo(
            "使用說明",
            "LiDAR控制系統使用說明：\n\n"
            "1. 首先點擊'連接'按鈕連接設備\n"
            "2. 選擇系統模式（待機/掃描/校準）\n"
            "3. 使用控制面板調整參數\n"
            "4. 開始掃描後可以查看實時數據\n"
            "5. 可以隨時保存數據或導出報告"
        )
    
    def _show_about(self) -> None:
        """顯示關於信息"""
        messagebox.showinfo(
            "關於",
            "LiDAR控制系統\n"
            "版本：1.0.0\n"
            "開發日期：2024-03-17\n\n"
            "本系統用於控制LiDAR設備，\n"
            "支持實時數據採集和可視化。"
        )
    
    def on_new_frame(self, point_cloud):
        """處理新的點雲幀"""
        print(f"[DEBUG] on_new_frame 被呼叫, shape={point_cloud.shape if point_cloud is not None else 'None'}")
        self.processor.current_frame = point_cloud
        # 取得frame_id與點數
        frame_id = None
        if hasattr(self.controller, 'current_frame_id'):
            frame_id = self.controller.current_frame_id
        n_points = point_cloud.shape[0] if point_cloud is not None else 0
        self._log_message(f"[掃描進度] 完成幀 frame_id={frame_id}，點數={n_points}")
        # 更新可視化（移除 PyVista 更新）
        self._update_visualization()

    def _show_log_window(self):
        if self.log_window is not None and tk.Toplevel.winfo_exists(self.log_window):
            self.log_window.lift()
            return
        self.log_window = tk.Toplevel(self.root)
        self.log_window.title("系統日誌")
        self.log_window.geometry("600x400")
        self.log_text_widget = tk.Text(self.log_window, wrap=tk.WORD)
        self.log_text_widget.pack(fill=tk.BOTH, expand=True)
        for msg in self.log_buffer:
            self.log_text_widget.insert(tk.END, msg + "\n")
        self.log_text_widget.see(tk.END)
        scrollbar = ttk.Scrollbar(self.log_text_widget, command=self.log_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text_widget.config(yscrollcommand=scrollbar.set)
        def on_close():
            window = self.log_window  # 保存窗口引用
            self.log_window = None    # 清除類屬性
            self.log_text_widget = None
            window.destroy()          # 使用保存的引用銷毀窗口
        self.log_window.protocol("WM_DELETE_WINDOW", on_close)

    def _add_coordinate_arrows(self, ax):
        """在3D圖上添加座標軸箭頭"""
        # 取得當前軸的範圍
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        zlim = ax.get_zlim()
        # 計算箭頭長度（軸範圍的20%）
        arrow_length = 0.2
        max_range = max(xlim[1]-xlim[0], ylim[1]-ylim[0], zlim[1]-zlim[0])
        arrow_len = max_range * arrow_length
        # X軸箭頭（紅色）
        ax.quiver(0, 0, 0, arrow_len, 0, 0, color='red', arrow_length_ratio=0.1, linewidth=3, alpha=0.8)
        ax.text(arrow_len*1.1, 0, 0, 'X', color='red', fontsize=14, fontweight='bold')
        # Y軸箭頭（綠色）
        ax.quiver(0, 0, 0, 0, arrow_len, 0, color='green', arrow_length_ratio=0.1, linewidth=3, alpha=0.8)
        ax.text(0, arrow_len*1.1, 0, 'Y', color='green', fontsize=14, fontweight='bold')
        # Z軸箭頭（藍色）
        ax.quiver(0, 0, 0, 0, 0, arrow_len, color='blue', arrow_length_ratio=0.1, linewidth=3, alpha=0.8)
        ax.text(0, 0, arrow_len*1.1, 'Z', color='blue', fontsize=14, fontweight='bold')

    def _show_custom_range_dialog(self):
        """顯示自定義範圍設定對話框"""
        custom_window = tk.Toplevel(self.root)
        custom_window.title("自定義範圍設定")
        custom_window.geometry("300x200")
        custom_window.resizable(False, False)
        custom_window.transient(self.root)
        custom_window.grab_set()
        
        # 範圍輸入
        main_frame = ttk.LabelFrame(custom_window, text="輸入範圍 (米)")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # XY範圍
        xy_frame = ttk.Frame(main_frame)
        xy_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(xy_frame, text="XY平面範圍:").pack(side=tk.LEFT)
        xy_var = tk.DoubleVar(value=500)
        ttk.Entry(xy_frame, textvariable=xy_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(xy_frame, text="米").pack(side=tk.LEFT)
        
        # Z範圍
        z_frame = ttk.Frame(main_frame)
        z_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(z_frame, text="Z軸高度:").pack(side=tk.LEFT)
        z_var = tk.DoubleVar(value=100)
        ttk.Entry(z_frame, textvariable=z_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(z_frame, text="米").pack(side=tk.LEFT)
        
        # 說明
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(info_frame, text="XY範圍將設為 ±XY/2", font=('Arial', 8)).pack()
        ttk.Label(info_frame, text="Z範圍將設為 0 到 Z", font=('Arial', 8)).pack()
        
        # 按鈕
        button_frame = ttk.Frame(custom_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_custom():
            xy_range = xy_var.get()
            z_range = z_var.get()
            self._set_quick_range(xy_range, xy_range, z_range)
            custom_window.destroy()
        
        ttk.Button(button_frame, text="應用", command=apply_custom).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=custom_window.destroy).pack(side=tk.RIGHT) 