#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
距離顏色映射演示程序

此演示程序展示了新的固定距離區間顏色映射功能：
- 0-100米：紅色
- 100-200米：橙色
- 200-300米：黃色
- 300-400米：綠色
- 400米以上：藍色
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import sys
import os

# 添加src目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.color_mapper import DistanceColorMapper

class ColorMappingDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("距離顏色映射演示")
        self.root.geometry("1000x700")
        
        # 初始化顏色映射器
        self.color_mapper = DistanceColorMapper()
        
        # 生成演示數據
        self.generate_demo_data()
        
        # 設置界面
        self.setup_ui()
        
    def generate_demo_data(self):
        """生成演示用的點雲數據"""
        np.random.seed(42)  # 固定隨機種子以便重現
        
        # 生成不同距離範圍的點
        num_points = 1000
        
        # 生成隨機座標
        angles = np.random.uniform(0, 2*np.pi, num_points)
        elevations = np.random.uniform(-0.5, 0.5, num_points)
        
        # 生成不同距離範圍的點，確保每個顏色區間都有點
        distances = []
        
        # 每個距離區間生成一些點
        for i in range(5):  # 5個顏色區間
            range_start = i * 100
            range_end = (i + 1) * 100 if i < 4 else 500  # 最後一個區間到500米
            range_distances = np.random.uniform(range_start + 10, 
                                              min(range_end - 10, 480), 
                                              num_points // 5)
            distances.extend(range_distances)
        
        # 再生成一些隨機分佈的點
        extra_distances = np.random.uniform(0, 500, num_points - len(distances))
        distances.extend(extra_distances)
        
        distances = np.array(distances)
        
        # 轉換為3D座標
        self.x = distances * np.cos(elevations) * np.cos(angles)
        self.y = distances * np.cos(elevations) * np.sin(angles)
        self.z = distances * np.sin(elevations)
        self.distances = distances
        
    def setup_ui(self):
        """設置用戶界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側：圖表
        chart_frame = ttk.LabelFrame(main_frame, text="點雲可視化")
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 創建matplotlib圖表
        self.fig = Figure(figsize=(8, 6))
        self.ax1 = self.fig.add_subplot(121, projection='3d')
        self.ax2 = self.fig.add_subplot(122)
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 右側：控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)
        
        # 顏色映射說明
        info_frame = ttk.LabelFrame(control_frame, text="顏色映射規則")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 創建顏色對照表
        self.create_color_legend(info_frame)
        
        # 控制按鈕
        button_frame = ttk.LabelFrame(control_frame, text="操作")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="重新生成數據", 
                  command=self.regenerate_data).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="設定顏色映射", 
                  command=self.show_color_settings).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="重置為預設", 
                  command=self.reset_color_mapping).pack(fill=tk.X, pady=2)
        
        # 統計信息
        stats_frame = ttk.LabelFrame(control_frame, text="數據統計")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 9))
        self.stats_label.pack(padx=5, pady=5)
        
        # 初始繪製
        self.update_plot()
        
    def create_color_legend(self, parent):
        """創建顏色對照表"""
        legend_info = self.color_mapper.get_legend_info()
        
        for range_text, color in legend_info:
            range_frame = ttk.Frame(parent)
            range_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 顏色方塊
            color_canvas = tk.Canvas(range_frame, width=20, height=15, highlightthickness=0)
            color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            color_canvas.create_rectangle(0, 0, 20, 15, fill=color, outline='black')
            
            # 範圍標籤
            ttk.Label(range_frame, text=range_text, font=('Arial', 9)).pack(side=tk.LEFT)
    
    def update_plot(self):
        """更新圖表顯示"""
        # 清除舊圖
        self.ax1.clear()
        self.ax2.clear()
        
        # 設定標題和軸標籤
        self.ax1.set_title("3D點雲 (固定距離顏色映射)", fontsize=12)
        self.ax1.set_xlabel('X (m)')
        self.ax1.set_ylabel('Y (m)')
        self.ax1.set_zlabel('Z (m)')
        
        self.ax2.set_title("2D投影 (X-Y平面)", fontsize=12)
        self.ax2.set_xlabel('X (m)')
        self.ax2.set_ylabel('Y (m)')
        
        # 使用新的顏色映射繪製點雲
        self.color_mapper.plot_distance_colors(
            self.ax1, self.distances, self.x, self.y, self.z, point_size=10)
        self.color_mapper.plot_distance_colors(
            self.ax2, self.distances, self.x, self.y, None, point_size=10)
        
        # 設定相同的視角和範圍
        self.ax1.view_init(elev=20, azim=45)
        
        # 添加網格
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        
        # 更新統計信息
        self.update_statistics()
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_statistics(self):
        """更新統計信息"""
        # 計算各距離區間的點數
        stats_text = f"總點數: {len(self.distances)}\n\n"
        
        for range_info in self.color_mapper.color_ranges:
            if range_info['max'] == float('inf'):
                mask = self.distances >= range_info['min']
                range_text = f"{range_info['min']}m+"
            else:
                mask = (self.distances >= range_info['min']) & (self.distances < range_info['max'])
                range_text = f"{range_info['min']}-{range_info['max']}m"
            
            count = np.sum(mask)
            percentage = (count / len(self.distances)) * 100
            stats_text += f"{range_text}: {count}點 ({percentage:.1f}%)\n"
        
        self.stats_label.config(text=stats_text)
    
    def regenerate_data(self):
        """重新生成演示數據"""
        self.generate_demo_data()
        self.update_plot()
    
    def show_color_settings(self):
        """顯示顏色映射設定對話框"""
        self.color_mapper.show_color_mapping_dialog(self.root)
        self.update_plot()
        # 重新創建顏色圖例 (簡化版本，實際應用中可能需要更複雜的刷新邏輯)
    
    def reset_color_mapping(self):
        """重置顏色映射為預設值"""
        self.color_mapper = DistanceColorMapper()
        self.update_plot()
    
    def run(self):
        """運行演示程序"""
        self.root.mainloop()

def main():
    """主函數"""
    print("=== 距離顏色映射演示程序 ===")
    print("功能說明：")
    print("1. 展示固定距離區間對應特定顏色的映射方式")
    print("2. 0-100米：紅色")
    print("3. 100-200米：橙色") 
    print("4. 200-300米：黃色")
    print("5. 300-400米：綠色")
    print("6. 400米以上：藍色")
    print("7. 可以重新生成數據和調整顏色映射設定")
    print("\n啟動演示程序...")
    
    try:
        demo = ColorMappingDemo()
        demo.run()
    except Exception as e:
        print(f"啟動演示程序時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 