"""
matplotlib 3D圖固定比例尺示例程式
展示如何控制3D圖的軸範圍，避免自動縮放
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time

class FixedScale3DDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3D圖固定比例尺示例")
        self.root.geometry("1000x700")
        
        # 比例尺設定
        self.fixed_scale = True
        self.x_range = [-10, 10]
        self.y_range = [-10, 10] 
        self.z_range = [-5, 15]
        
        # 模擬數據生成參數
        self.data_range = 5  # 數據點的範圍
        self.point_count = 100
        
        self.setup_ui()
        self.generate_data()
        self.update_plot()
        
    def setup_ui(self):
        """設置用戶界面"""
        # 控制面板
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 固定比例尺切換
        self.scale_var = tk.BooleanVar(value=self.fixed_scale)
        ttk.Checkbutton(control_frame, text="固定比例尺", 
                       variable=self.scale_var, 
                       command=self.toggle_scale).pack(side=tk.LEFT, padx=5)
        
        # 數據範圍控制
        ttk.Label(control_frame, text="數據範圍:").pack(side=tk.LEFT, padx=5)
        self.range_var = tk.DoubleVar(value=self.data_range)
        range_scale = ttk.Scale(control_frame, from_=1, to=20, 
                               variable=self.range_var,
                               orient=tk.HORIZONTAL, length=200,
                               command=self.update_data_range)
        range_scale.pack(side=tk.LEFT, padx=5)
        
        self.range_label = ttk.Label(control_frame, text=f"{self.data_range:.1f}m")
        self.range_label.pack(side=tk.LEFT, padx=5)
        
        # 重新生成數據按鈕
        ttk.Button(control_frame, text="重新生成數據", 
                  command=self.regenerate_data).pack(side=tk.LEFT, padx=10)
        
        # 設置按鈕
        ttk.Button(control_frame, text="比例尺設置", 
                  command=self.show_scale_settings).pack(side=tk.LEFT, padx=5)
        
        # 創建matplotlib圖表
        self.fig = Figure(figsize=(12, 8))
        
        # 創建兩個子圖進行對比
        self.ax1 = self.fig.add_subplot(121, projection='3d')
        self.ax2 = self.fig.add_subplot(122, projection='3d')
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(self.root, text="")
        self.status_label.pack(pady=5)
        
    def generate_data(self):
        """生成隨機3D點雲數據"""
        # 生成在不同範圍內的隨機點
        x = np.random.uniform(-self.data_range, self.data_range, self.point_count)
        y = np.random.uniform(-self.data_range, self.data_range, self.point_count)
        z = np.random.uniform(0, self.data_range*2, self.point_count)
        
        # 添加一些顏色信息（基於距離）
        colors = np.sqrt(x**2 + y**2 + z**2)
        
        self.data = np.column_stack([x, y, z, colors])
        
    def update_plot(self):
        """更新圖表顯示"""
        # 清除舊圖
        self.ax1.clear()
        self.ax2.clear()
        
        x, y, z, colors = self.data[:, 0], self.data[:, 1], self.data[:, 2], self.data[:, 3]
        
        # 左側：固定比例尺
        self.ax1.scatter(x, y, z, c=colors, cmap='viridis', alpha=0.6)
        self.ax1.set_title("固定比例尺", fontsize=14, weight='bold')
        self.ax1.set_xlabel('X (m)')
        self.ax1.set_ylabel('Y (m)')
        self.ax1.set_zlabel('Z (m)')
        
        if self.fixed_scale:
            # 應用固定比例尺
            self.ax1.set_xlim(self.x_range)
            self.ax1.set_ylim(self.y_range)
            self.ax1.set_zlim(self.z_range)
            self.ax1.set_autoscale_on(False)
        
        # 右側：自動比例尺（對比用）
        self.ax2.scatter(x, y, z, c=colors, cmap='viridis', alpha=0.6)
        self.ax2.set_title("自動比例尺（對比）", fontsize=14, weight='bold')
        self.ax2.set_xlabel('X (m)')
        self.ax2.set_ylabel('Y (m)')
        self.ax2.set_zlabel('Z (m)')
        # 右側始終使用自動比例尺
        self.ax2.set_autoscale_on(True)
        
        # 添加網格
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        
        # 設置相同的視角
        self.ax1.view_init(elev=20, azim=45)
        self.ax2.view_init(elev=20, azim=45)
        
        self.fig.tight_layout()
        self.canvas.draw()
        
        # 更新狀態信息
        data_bounds = f"數據範圍: X[{x.min():.1f}, {x.max():.1f}], Y[{y.min():.1f}, {y.max():.1f}], Z[{z.min():.1f}, {z.max():.1f}]"
        scale_info = f"固定比例尺: {'開啟' if self.fixed_scale else '關閉'}"
        self.status_label.config(text=f"{scale_info} | {data_bounds}")
        
    def toggle_scale(self):
        """切換固定比例尺功能"""
        self.fixed_scale = self.scale_var.get()
        self.update_plot()
        
    def update_data_range(self, value):
        """更新數據範圍"""
        self.data_range = float(value)
        self.range_label.config(text=f"{self.data_range:.1f}m")
        self.generate_data()
        self.update_plot()
        
    def regenerate_data(self):
        """重新生成數據"""
        self.generate_data()
        self.update_plot()
        
    def show_scale_settings(self):
        """顯示比例尺設置對話框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("比例尺設置")
        settings_window.geometry("350x250")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 軸範圍設定
        range_frame = ttk.LabelFrame(settings_window, text="軸範圍設定 (米)")
        range_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # X軸
        x_frame = ttk.Frame(range_frame)
        x_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(x_frame, text="X軸:").pack(side=tk.LEFT)
        x_min_var = tk.DoubleVar(value=self.x_range[0])
        x_max_var = tk.DoubleVar(value=self.x_range[1])
        ttk.Entry(x_frame, textvariable=x_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(x_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(x_frame, textvariable=x_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # Y軸
        y_frame = ttk.Frame(range_frame)
        y_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(y_frame, text="Y軸:").pack(side=tk.LEFT)
        y_min_var = tk.DoubleVar(value=self.y_range[0])
        y_max_var = tk.DoubleVar(value=self.y_range[1])
        ttk.Entry(y_frame, textvariable=y_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(y_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(y_frame, textvariable=y_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # Z軸
        z_frame = ttk.Frame(range_frame)
        z_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(z_frame, text="Z軸:").pack(side=tk.LEFT)
        z_min_var = tk.DoubleVar(value=self.z_range[0])
        z_max_var = tk.DoubleVar(value=self.z_range[1])
        ttk.Entry(z_frame, textvariable=z_min_var, width=8).pack(side=tk.LEFT, padx=(10,2))
        ttk.Label(z_frame, text="到").pack(side=tk.LEFT, padx=2)
        ttk.Entry(z_frame, textvariable=z_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # 預設按鈕
        preset_frame = ttk.Frame(range_frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=10)
        
        def set_preset(preset_type):
            if preset_type == "small":
                x_min_var.set(-5); x_max_var.set(5)
                y_min_var.set(-5); y_max_var.set(5)
                z_min_var.set(0); z_max_var.set(10)
            elif preset_type == "medium":
                x_min_var.set(-25); x_max_var.set(25)
                y_min_var.set(-25); y_max_var.set(25)
                z_min_var.set(-5); z_max_var.set(20)
            elif preset_type == "large":
                x_min_var.set(-100); x_max_var.set(100)
                y_min_var.set(-100); y_max_var.set(100)
                z_min_var.set(0); z_max_var.set(50)
            elif preset_type == "huge":
                x_min_var.set(-250); x_max_var.set(250)
                y_min_var.set(-250); y_max_var.set(250)
                z_min_var.set(0); z_max_var.set(100)
            elif preset_type == "massive":
                x_min_var.set(-500); x_max_var.set(500)
                y_min_var.set(-500); y_max_var.set(500)
                z_min_var.set(0); z_max_var.set(200)
        
        # 第一排預設按鈕
        preset_frame1 = ttk.Frame(preset_frame)
        preset_frame1.pack(fill=tk.X, pady=2)
        ttk.Button(preset_frame1, text="10m", command=lambda: set_preset("small")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame1, text="50m", command=lambda: set_preset("medium")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame1, text="200m", command=lambda: set_preset("large")).pack(side=tk.LEFT, padx=2)
        
        # 第二排預設按鈕
        preset_frame2 = ttk.Frame(preset_frame)
        preset_frame2.pack(fill=tk.X, pady=2)
        ttk.Button(preset_frame2, text="500m", command=lambda: set_preset("huge")).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame2, text="1km", command=lambda: set_preset("massive")).pack(side=tk.LEFT, padx=2)
        
        # 按鈕
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply():
            self.x_range = [x_min_var.get(), x_max_var.get()]
            self.y_range = [y_min_var.get(), y_max_var.get()]
            self.z_range = [z_min_var.get(), z_max_var.get()]
            self.update_plot()
            settings_window.destroy()
            
        ttk.Button(button_frame, text="應用", command=apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=settings_window.destroy).pack(side=tk.RIGHT)
        
    def run(self):
        """運行應用程序"""
        self.root.mainloop()

def main():
    """主函數 - 展示如何在matplotlib中控制3D圖的比例尺"""
    print("=== matplotlib 3D圖固定比例尺示例 ===")
    print("功能說明：")
    print("1. 左側圖表：使用固定比例尺，軸範圍不會隨數據變化")
    print("2. 右側圖表：使用自動比例尺，軸範圍會根據數據自動調整")
    print("3. 可以調整數據範圍來觀察兩種模式的差異")
    print("4. 提供比例尺設置對話框來自定義軸範圍")
    print("\n關鍵技術點：")
    print("- 使用 ax.set_xlim(), ax.set_ylim(), ax.set_zlim() 固定軸範圍")
    print("- 使用 ax.set_autoscale_on(False) 關閉自動縮放")
    print("- 對比顯示固定vs自動比例尺的效果")
    print("\n啟動應用程序...")
    
    app = FixedScale3DDemo()
    app.run()

if __name__ == "__main__":
    main() 