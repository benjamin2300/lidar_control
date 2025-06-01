import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from src.controller.lidar_controller import LidarController
from src.data.data_processor import LidarDataProcessor
from src.monitor.system_monitor import LidarMonitor
from src.gui.main_window import MainWindow

def main():
    # 創建主視窗
    root = ThemedTk(theme="arc")  # 使用現代主題
    root.title("LiDAR 控制系統")
    root.geometry("1200x800")  # 設置初始視窗大小
    
    # 初始化各個模組
    processor = LidarDataProcessor()
    controller = LidarController(processor)
    monitor = LidarMonitor()
    
    # 創建主應用程序視窗
    app = MainWindow(root, controller, processor, monitor)
    
    # 運行應用程序
    root.mainloop()

if __name__ == "__main__":
    main() 