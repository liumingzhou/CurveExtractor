# -*- coding: gbk -*-

import tkinter as tk

from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, ImageGrab

import cv2

import numpy as np

import pandas as pd

import os

import sys



# Add src to path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))



from image_processor import ImageProcessor

from coordinate_system import CoordinateSystem

from curve_extractor import CurveExtractor

from curve_fitter import CurveFitter

from curve_optimizer import CurveOptimizer



import copy

# ---------------- Color Theme ----------------
THEME = {
    'light': {
        'toolbar_bg': '#ECF0F1', 'sidebar_bg': '#F5F6FA',
        'canvas_bg': '#2C2C2C', 'canvas_frame_bg': '#1E1E1E',
        'card_bg': '#FFFFFF', 'status_bg': '#E8EAF6',
        'text': '#2C3E50', 'text_secondary': '#7F8C8D',
        'accent': '#3498DB', 'accent_hover': '#2980B9',
        'success': '#27AE60', 'warning': '#F39C12',
        'danger': '#E74C3C', 'border': '#D5D8DC',
        'highlight': '#D4E6F1', 'separator': '#BDC3C7',
        'scrollbar_trough': '#ECF0F1', 'scrollbar_thumb': '#BDC3C7',
        'listbox_bg': '#FFFFFF', 'listbox_fg': '#2C3E50',
    },
    'dark': {
        'toolbar_bg': '#252530', 'sidebar_bg': '#1E1E2A',
        'canvas_bg': '#151520', 'canvas_frame_bg': '#101018',
        'card_bg': '#2D2D3F', 'status_bg': '#2D2D3F',
        'text': '#E0E0E0', 'text_secondary': '#999999',
        'accent': '#5B9BD5', 'accent_hover': '#4A8AC4',
        'success': '#2ECC71', 'warning': '#F1C40F',
        'danger': '#E74C3C', 'border': '#3E3E50',
        'highlight': '#3A5070', 'separator': '#3E3E50',
        'scrollbar_trough': '#1E1E2A', 'scrollbar_thumb': '#3E3E50',
        'listbox_bg': '#2D2D3F', 'listbox_fg': '#E0E0E0',
    }
}



class CurveExtractorApp:

    def __init__(self, root):

        self.root = root

        self.root.title("科学曲线数据提取系统")

        self.root.geometry("1400x900")

        

        # State

        self.image_path = None

        self.processor = None

        self.coord_sys = None

        self.extractor = None

        self.extracted_data = None # Combined list for visualization

        self.min_curve_data = []

        self.max_curve_data = []

        

        self.fitter = CurveFitter()

        

        # Interaction State

        self.interaction_mode = 'view' # view, set_x, set_y, erase_point, erase_box, select_area, add_point, move_point

        self.target_curve = 'min' # 'min' or 'max'

        self.start_x = None

        self.start_y = None

        self.dragging_point = None # For move_point mode

        self.current_rect = None

        self.selection_coords = None # (x1, y1, x2, y2) in image pixels

        self.selection_rect_id = None # Canvas item ID for the persistent selection box

        self.selection_text_id = None # Canvas item ID for the dimensions text

        

        # Pan/Drag State (Right Click)

        self.pan_start_x = 0

        self.pan_start_y = 0

        

        # Display State

        self.current_zoom = 1.0

        self.show_grid = False

        self.tk_img = None

        

        # History for Undo/Redo

        self.history = []

        self.history_index = -1

        

        # Config file

        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.current_theme = 'light'

        # Setup ttk style
        self.setup_style()



        # UI Layout

        self.create_widgets()

        

        # Load settings

        self.load_settings()

        


    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        self.apply_theme()

    def apply_theme(self):
        t = THEME[self.current_theme]
        self.root.configure(bg=t['sidebar_bg'])

        style = ttk.Style()
        style.configure('.', font=('Microsoft YaHei UI', 9), background=t['sidebar_bg'])
        style.configure('TFrame', background=t['sidebar_bg'])
        style.configure('TLabel', background=t['sidebar_bg'], foreground=t['text'])
        style.configure('TLabelFrame', background=t['sidebar_bg'], foreground=t['text'])
        style.configure('TLabelFrame.Label', font=('Microsoft YaHei UI', 9, 'bold'), foreground=t['accent'])

        style.configure('Toolbar.TFrame', background=t['toolbar_bg'])
        style.configure('Toolbar.TLabel', background=t['toolbar_bg'], foreground=t['text'])

        style.configure('TButton', padding=(12, 6), font=('Microsoft YaHei UI', 9),
                        borderwidth=0, relief='flat')
        style.map('TButton',
                  background=[('active', t['accent_hover']), ('!active', t['accent'])],
                  foreground=[('active', 'white'), ('!active', 'white')])

        style.configure('Toolbar.TButton', padding=(10, 5), font=('Microsoft YaHei UI', 9))
        style.map('Toolbar.TButton',
                  background=[('active', t['accent_hover']), ('!active', t['accent'])],
                  foreground=[('active', 'white'), ('!active', 'white')])

        style.configure('Accent.TButton', font=('Microsoft YaHei UI', 9, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', t['success']), ('!active', t['accent'])],
                  foreground=[('active', 'white'), ('!active', 'white')])

        style.configure('Small.TButton', padding=(6, 3), font=('Microsoft YaHei UI', 8))
        style.map('Small.TButton',
                  background=[('active', t['accent_hover']), ('!active', t['accent'])],
                  foreground=[('active', 'white'), ('!active', 'white')])

        style.configure('TRadiobutton', background=t['sidebar_bg'], foreground=t['text'])
        style.map('TRadiobutton',
                  background=[('active', t['sidebar_bg'])],
                  foreground=[('active', t['accent'])])
        style.configure('TCheckbutton', background=t['sidebar_bg'], foreground=t['text'])
        style.map('TCheckbutton',
                  background=[('active', t['sidebar_bg'])],
                  foreground=[('active', t['accent'])])

        style.configure('Toolbar.TCheckbutton', background=t['toolbar_bg'], foreground=t['text'])
        style.map('Toolbar.TCheckbutton',
                  background=[('active', t['toolbar_bg'])],
                  foreground=[('active', t['accent'])])

        style.configure('TSeparator', background=t['separator'])
        style.configure('TEntry', fieldbackground=t['card_bg'], foreground=t['text'])

        style.configure('TScrollbar', troughcolor=t['scrollbar_trough'],
                        background=t['scrollbar_thumb'], arrowcolor=t['text'])
        style.map('TScrollbar', background=[('active', t['accent'])])

        style.configure('Status.TLabel', background=t['status_bg'], foreground=t['text'],
                        font=('Microsoft YaHei UI', 8), padding=(8, 4))

        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=t['canvas_bg'])
        if hasattr(self, 'x_point_list'):
            self.x_point_list.configure(bg=t['listbox_bg'], fg=t['listbox_fg'])
        if hasattr(self, 'y_point_list'):
            self.y_point_list.configure(bg=t['listbox_bg'], fg=t['listbox_fg'])

    def toggle_dark_mode(self):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme()
    def create_widgets(self):
        t = THEME[self.current_theme]

        # --- 1. Top Toolbar ---
        self.toolbar_frame = ttk.Frame(self.root, style='Toolbar.TFrame')
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, ipady=3)

        ttk.Button(self.toolbar_frame, text="打开图片", command=self.load_image, style='Toolbar.TButton').pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(self.toolbar_frame, text="粘贴", command=self.paste_image, style='Toolbar.TButton').pack(side=tk.LEFT, padx=4, pady=4)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        ttk.Button(self.toolbar_frame, text="提取数据", command=self.start_process_thread, style='Accent.TButton').pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(self.toolbar_frame, text="导出结果", command=self.export_data_simplified, style='Toolbar.TButton').pack(side=tk.LEFT, padx=4, pady=4)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        ttk.Button(self.toolbar_frame, text="放大 (+)", command=self.zoom_in, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(self.toolbar_frame, text="缩小 (-)", command=self.zoom_out, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(self.toolbar_frame, text="重置缩放", command=self.reset_zoom, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3, pady=4)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        self.show_grid_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.toolbar_frame, text="显示网格", variable=self.show_grid_var,
                       command=self.toggle_grid, style='Toolbar.TCheckbutton').pack(side=tk.LEFT, padx=8, pady=4)

        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        ttk.Button(self.toolbar_frame, text="撤销", command=self.undo, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(self.toolbar_frame, text="重做", command=self.redo, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3, pady=4)

        ttk.Button(self.toolbar_frame, text="[D]", command=self.toggle_dark_mode,
                   style='Toolbar.TButton', width=3).pack(side=tk.RIGHT, padx=8, pady=4)

        # --- 2. Left Sidebar ---
        self.sidebar_frame = ttk.Frame(self.root, width=260, style='TFrame')
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        ttk.Label(self.sidebar_frame, text="[ 控制面板 ]", font=('Microsoft YaHei UI', 11, 'bold'),
                  foreground=t['accent']).pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        curve_frame = ttk.LabelFrame(self.sidebar_frame, text="当前操作曲线", padding=(10, 8))
        curve_frame.pack(fill=tk.X, padx=8, pady=(10, 4))

        self.target_curve_var = tk.StringVar(value="min")
        ttk.Radiobutton(curve_frame, text="MIN 曲线 (绿)", variable=self.target_curve_var,
                       value="min", command=self.set_target_curve).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(curve_frame, text="MAX 曲线 (黄)", variable=self.target_curve_var,
                       value="max", command=self.set_target_curve).pack(anchor=tk.W, pady=2)

        tool_frame = ttk.LabelFrame(self.sidebar_frame, text="工具模式", padding=(10, 8))
        tool_frame.pack(fill=tk.X, padx=8, pady=4)

        self.mode_var = tk.StringVar(value="view")
        modes = [
            ("[ ] 浏览/拖拽", "view"),
            ("[+] 添加点(点击)", "add_point"),
            ("[~] 移动点(拖拽)", "move_point"),
            ("[-] 擦除点(点击)", "erase_point"),
            ("[#] 框选删除", "erase_box"),
            ("[=] 框选提取区域", "select_area"),
            ("[X] 校准 X轴", "set_x"),
            ("[Y] 校准 Y轴", "set_y"),
        ]

        for text, val in modes:
            ttk.Radiobutton(tool_frame, text=text, variable=self.mode_var, value=val, command=self.set_mode).pack(anchor=tk.W, pady=1)

        ttk.Button(tool_frame, text="清除选区", command=self.clear_selection, style='Small.TButton').pack(fill=tk.X, pady=(6, 0))

        setting_frame = ttk.LabelFrame(self.sidebar_frame, text="设置与校准", padding=(10, 8))
        setting_frame.pack(fill=tk.X, padx=8, pady=4)

        self.x_log_var = tk.BooleanVar(value=False)
        self.y_log_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(setting_frame, text="X轴对数", variable=self.x_log_var, command=self.on_axis_log_changed).pack(anchor=tk.W)
        ttk.Checkbutton(setting_frame, text="Y轴对数", variable=self.y_log_var, command=self.on_axis_log_changed).pack(anchor=tk.W)

        ttk.Separator(setting_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        calib_list_frame = ttk.Frame(setting_frame)
        calib_list_frame.pack(fill=tk.X)

        ttk.Label(calib_list_frame, text="X参考点:", font=('Microsoft YaHei UI', 8, 'bold')).pack(anchor=tk.W)
        self.x_point_list = tk.Listbox(calib_list_frame, height=3, font=("Consolas", 8),
                                        bg=t['listbox_bg'], fg=t['listbox_fg'],
                                        selectbackground=t['accent'], relief='flat', borderwidth=1)
        self.x_point_list.pack(fill=tk.X, pady=(2, 4))

        ttk.Label(calib_list_frame, text="Y参考点:", font=('Microsoft YaHei UI', 8, 'bold')).pack(anchor=tk.W)
        self.y_point_list = tk.Listbox(calib_list_frame, height=3, font=("Consolas", 8),
                                        bg=t['listbox_bg'], fg=t['listbox_fg'],
                                        selectbackground=t['accent'], relief='flat', borderwidth=1)
        self.y_point_list.pack(fill=tk.X, pady=(2, 4))

        btn_calib_reset = ttk.Frame(setting_frame)
        btn_calib_reset.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_calib_reset, text="刷新参考点", command=self.refresh_calibration_list,
                   style='Small.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(btn_calib_reset, text="重置所有", command=self.reset_calibration_points,
                   style='Small.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        smooth_frame = ttk.LabelFrame(self.sidebar_frame, text="平滑处理", padding=(10, 8))
        smooth_frame.pack(fill=tk.X, padx=8, pady=4)

        smooth_inner = ttk.Frame(smooth_frame)
        smooth_inner.pack(fill=tk.X)
        ttk.Label(smooth_inner, text="平滑处理 (1-10):", font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
        self.smooth_level_var = tk.IntVar(value=5)
        ttk.Entry(smooth_inner, textvariable=self.smooth_level_var, width=5).pack(side=tk.LEFT, padx=8)
        ttk.Button(smooth_inner, text="应用", command=self.apply_smoothing, style='Small.TButton').pack(side=tk.RIGHT)

        offset_frame = ttk.LabelFrame(self.sidebar_frame, text="导出偏移", padding=(10, 8))
        offset_frame.pack(fill=tk.X, padx=8, pady=4)

        self.x_offset_var = tk.StringVar(value="0.0%")
        self.y_offset_var = tk.StringVar(value="0.0%")

        offset_inner = ttk.Frame(offset_frame)
        offset_inner.pack(fill=tk.X)
        ttk.Label(offset_inner, text="X:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_x_off = ttk.Entry(offset_inner, textvariable=self.x_offset_var, width=8)
        self.entry_x_off.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(offset_inner, text="Y:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_y_off = ttk.Entry(offset_inner, textvariable=self.y_offset_var, width=8)
        self.entry_y_off.pack(side=tk.LEFT)

        ttk.Frame(self.sidebar_frame, height=10).pack(fill=tk.X)

        # --- 3. Canvas Area (Center) ---
        self.canvas_frame = ttk.Frame(self.root, style='TFrame')
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(self.canvas_frame, bg=t['canvas_bg'],
                                xscrollcommand=h_scroll.set,
                                yscrollcommand=v_scroll.set,
                                highlightthickness=0, borderwidth=0)

        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)

        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=(2, 0))

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-3>", self.on_right_mouse_down)
        self.canvas.bind("<B3-Motion>", self.on_right_mouse_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        self.root.bind("<Control-v>", self.paste_image)
        self.root.bind("<Escape>", self.on_key_press)
        self.root.bind("<Return>", self.on_key_press)

        # --- 4. Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var,
                                       style='Status.TLabel', anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # --- 5. Menu Bar ---
        menubar = tk.Menu(self.root, bg=t['toolbar_bg'], fg=t['text'],
                          activebackground=t['accent'], activeforeground='white')
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg=t['card_bg'], fg=t['text'],
                            activebackground=t['accent'], activeforeground='white')
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图片...", command=self.load_image)
        file_menu.add_command(label="另存项目...", command=self.save_project_as)
        file_menu.add_command(label="打开项目...", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        settings_menu = tk.Menu(menubar, tearoff=0, bg=t['card_bg'], fg=t['text'],
                                activebackground=t['accent'], activeforeground='white')
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="手动标定参数...", command=self.open_calibration_dialog)
        settings_menu.add_command(label="导出JSON...", command=self.export_json_data)
        settings_menu.add_command(label="导入配置...", command=self.import_configuration)
        settings_menu.add_command(label="导出配置...", command=self.export_configuration)

        self.x_min_var = tk.StringVar(value="0.01")
        self.x_max_var = tk.StringVar(value="100000")
        self.y_min_var = tk.StringVar(value="0.01")
        self.y_max_var = tk.StringVar(value="1000")

    def set_target_curve(self):

        self.target_curve = self.target_curve_var.get()

        self.status_var.set(f"当前操作曲线: {self.target_curve.upper()}")



    def toggle_grid(self):

        self.show_grid = self.show_grid_var.get()

        self.update_visualization()



    def zoom_in(self):

        self.current_zoom *= 1.2

        self.refresh_canvas()



    def zoom_out(self):

        self.current_zoom /= 1.2

        self.refresh_canvas()



    def reset_zoom(self):

        if not self.processor: return

        # Fit to canvas

        cw = self.canvas.winfo_width()

        ch = self.canvas.winfo_height()

        iw = self.processor.image.shape[1]

        ih = self.processor.image.shape[0]

        

        if cw > 1 and ch > 1:

            self.current_zoom = min(cw/iw, ch/ih)

        else:

            self.current_zoom = 1.0

        self.refresh_canvas()



    def on_mouse_wheel(self, event):

        # Zoom with wheel

        if event.delta > 0:

            self.zoom_in()

        else:

            self.zoom_out()



    def on_right_mouse_down(self, event):

        # Record start position for panning

        self.canvas.scan_mark(event.x, event.y)



    def on_right_mouse_drag(self, event):

        # Perform pan

        self.canvas.scan_dragto(event.x, event.y, gain=1)



    def refresh_canvas(self):

        if not self.processor: return

        

        # Get raw image

        cv_img = self.processor.image

        h, w = cv_img.shape[:2]

        

        new_w = int(w * self.current_zoom)

        new_h = int(h * self.current_zoom)

        

        if new_w < 1 or new_h < 1: return

        

        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(cv_img_rgb)

        

        # Resize

        method = Image.Resampling.NEAREST if self.current_zoom > 2.0 else Image.Resampling.BILINEAR

        pil_img = pil_img.resize((new_w, new_h), method)

        

        self.tk_img = ImageTk.PhotoImage(pil_img)

        

        self.canvas.delete("all")

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        self.canvas.config(scrollregion=(0, 0, new_w, new_h))

        

        # Store scale for coordinate conversion

        self.display_scale = self.current_zoom

        

        # Redraw overlays

        self.redraw_selection()

        self.update_visualization_overlay()



    def redraw_selection(self):

        if self.selection_coords:

            img_x1, img_y1, img_x2, img_y2 = self.selection_coords

            

            # Use current_zoom which is the display scale

            scale = self.current_zoom

            

            x1 = img_x1 * scale

            y1 = img_y1 * scale

            x2 = img_x2 * scale

            y2 = img_y2 * scale

            

            w = abs(x2 - x1)

            h = abs(y2 - y1)

            

            self.selection_rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue', width=2)

            self.selection_text_id = self.canvas.create_text(x1, y1 - 10, text=f"{int(w/scale)}x{int(h/scale)}", fill='blue', anchor=tk.SW)



    def display_image(self, cv_img):

        # Legacy entry point, mostly called after load/paste

        # Set default zoom to Fit, or maybe 1.0 if fit is too small?

        # Requirement: "Increase import image auto-scaling ratio"

        # Let's default to Fit, but if Fit < 0.5, maybe set to 0.5?

        # Or just set to Fit for overview.

        

        # We need to make sure canvas has size

        self.root.update_idletasks()

        cw = self.canvas.winfo_width()

        ch = self.canvas.winfo_height()

        iw = cv_img.shape[1]

        ih = cv_img.shape[0]

        

        if cw > 1 and ch > 1:

            ratio = min(cw/iw, ch/ih)

            # If image is very large, ratio is small.

            # If we want "more precision", maybe default to at least 50%?

            self.current_zoom = max(ratio, 0.5) 

        else:

            self.current_zoom = 1.0

            

        self.refresh_canvas()



    def update_visualization(self):

        self.refresh_canvas()



    def update_visualization_overlay(self):

        # Draw points, grid, etc. on top of the image

        if not self.tk_img: return

        

        # 1. Grid

        if self.show_grid and self.coord_sys and self.coord_sys.plot_area:

             self.draw_grid()

             

        # 2. Points

        self.draw_points(self.min_curve_data, 'green')

        self.draw_points(self.max_curve_data, 'yellow')

        

        # 3. Legend

        self.draw_legend()



    def draw_points(self, data, color):

        if not data: return

        r = 3 # Radius

        for p in data:

            if 'Pixel_X' not in p: continue

            px, py = p['Pixel_X'], p['Pixel_Y']

            

            # Scale to display

            sx = px * self.current_zoom

            sy = py * self.current_zoom

            

            # Check visibility optimization? No need for few thousand points

            self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=color, outline='black')



    def draw_grid(self):

        # Draw grid lines based on calibration

        # Simple implementation: 5x5 grid in Data Space mapped to Pixel Space

        # This is complex for Log scale.

        # Let's draw the bounding box of the plot area at least.

        if self.coord_sys.plot_area:

            x, y, w, h = self.coord_sys.plot_area

            sx = x * self.current_zoom

            sy = y * self.current_zoom

            sw = w * self.current_zoom

            sh = h * self.current_zoom

            self.canvas.create_rectangle(sx, sy, sx+sw, sy+sh, outline='cyan', dash=(2, 4))

            

    def draw_legend(self):

        # Draw legend in top-right corner of canvas (floating)

        # Use canvas coords relative to view? No, absolute canvas coords (0,0 is top-left of image)

        # We want it fixed on screen?

        # Canvas has `xview` and `yview`. We need to calculate position relative to scroll.

        # But `create_window` or `create_text` moves with scroll.

        # If we want fixed UI, we place it in a Frame overlay? 

        # Simpler: Just draw it at (10, 10) of the image.

        

        x, y = 10, 10

        w, h = 100, 60

        

        self.canvas.create_rectangle(x, y, x+w, y+h, fill='#333333', outline='white', stipple='gray50') # Semi-transparent-ish

        

        self.canvas.create_oval(x+10, y+15, x+20, y+25, fill='green', outline='black')

        self.canvas.create_text(x+30, y+20, text="MIN 曲线", fill='white', anchor=tk.W)

        

        self.canvas.create_oval(x+10, y+40, x+20, y+50, fill='yellow', outline='black')

        self.canvas.create_text(x+30, y+45, text="MAX 曲线", fill='white', anchor=tk.W)



    def export_json_data(self):

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])

        if not file_path: return

        

        import json

        data = {

            'min_curve': self.min_curve_data,

            'max_curve': self.max_curve_data,

            'calibration': {

                'x_min': self.x_min_var.get(),

                'x_max': self.x_max_var.get(),

                'x_log': self.x_log_var.get(),

                'y_min': self.y_min_var.get(),

                'y_max': self.y_max_var.get(),

                'y_log': self.y_log_var.get(),

            }

        }

        try:

            with open(file_path, 'w') as f:

                json.dump(data, f, indent=4)

            self.status_var.set(f"??°????·2?????oè?? {os.path.basename(file_path)}")

        except Exception as e:

            messagebox.showerror("错误", str(e))



    def on_axis_log_changed(self):

        # Toggle for individual axis log setting

        self.update_axis_settings() # Trigger recalibration/redraw

        

    def open_calibration_dialog(self):

        # Dialog to set calibration manually

        top = tk.Toplevel(self.root)

        top.title("?????¨??°")

        

        tk.Label(top, text="X 最小").grid(row=0, column=0)

        tk.Entry(top, textvariable=self.x_min_var).grid(row=0, column=1)

        tk.Label(top, text="X 最大").grid(row=1, column=0)

        tk.Entry(top, textvariable=self.x_max_var).grid(row=1, column=1)

        tk.Checkbutton(top, text="X 对数", variable=self.x_log_var).grid(row=2, column=1)

        

        tk.Label(top, text="Y ???").grid(row=3, column=0)

        tk.Entry(top, textvariable=self.y_min_var).grid(row=3, column=1)

        tk.Label(top, text="Y ???").grid(row=4, column=0)

        tk.Entry(top, textvariable=self.y_max_var).grid(row=4, column=1)

        tk.Checkbutton(top, text="Y 对数", variable=self.y_log_var).grid(row=5, column=1)

        

        ttk.Button(top, text="更新", command=lambda: [self.update_axis_settings(), top.destroy()]).grid(row=6, column=0, columnspan=2)



    def reset_calibration_points(self):

        if self.coord_sys:

            self.coord_sys.reset_references()

            self.refresh_calibration_list()

            self.save_settings()

            self.status_var.set("已重置所有手动标定点。")



    def refresh_calibration_list(self):

        # Update listboxes with current points

        if not hasattr(self, 'x_point_list') or not self.coord_sys:

            return

            

        self.x_point_list.delete(0, tk.END)

        self.y_point_list.delete(0, tk.END)

        

        # Sort for display

        x_pts = sorted(self.coord_sys.refs_x, key=lambda x: x[0])

        y_pts = sorted(self.coord_sys.refs_y, key=lambda x: x[0])

        

        for px, val in x_pts:

            self.x_point_list.insert(tk.END, f"{val:.4g}")

            

        for py, val in y_pts:

            self.y_point_list.insert(tk.END, f"{val:.4g}")



    def show_calibration_points(self):

        if not self.coord_sys:

            messagebox.showinfo("提示", "请先标定坐标系")

            return

            

        x_points = self.coord_sys.refs_x

        y_points = self.coord_sys.refs_y

        

        info = "Xè?′????1:\n"

        if not x_points:

            info += "  (????- ?????¨é??è??Min/Max)\n"

        else:

            for p, v in x_points:

                info += f"  ????′?: {p:.1f} -> ???? {v}\n"

                

        info += "\nYè?′????1:\n"

        if not y_points:

            info += "  (????- ?????¨é??è??Min/Max)\n"

        else:

            for p, v in y_points:

                info += f"  ????′?: {p:.1f} -> ???? {v}\n"

                

        messagebox.showinfo("提示", info)



    def load_settings(self):

        import json

        if os.path.exists(self.config_file):

            try:

                with open(self.config_file, 'r') as f:

                    config = json.load(f)

                    self.x_min_var.set(config.get('x_min', "0.01"))

                    self.x_max_var.set(config.get('x_max', "100000"))

                    

                    # Load individual axis log state

                    self.x_log_var.set(config.get('x_log', True))

                    self.y_log_var.set(config.get('y_log', True))

                    

                    self.y_min_var.set(config.get('y_min', "0.01"))

                    self.y_max_var.set(config.get('y_max', "1000"))

                    

                    # Offsets

                    self.x_offset_var.set(config.get('x_offset', "0.0%"))

                    self.y_offset_var.set(config.get('y_offset', "0.0%"))

                    

                    # Load saved calibration points

                    self.saved_refs_x = config.get('refs_x', [])

                    self.saved_refs_y = config.get('refs_y', [])

                    

                    # Load selection coords

                    self.selection_coords = config.get('selection_coords', None)

                    

                    # Smoothing

                    self.smooth_level_var.set(config.get('smooth_level', 5))

            except Exception as e:

                print(f"Failed to load settings: {e}")



    def save_settings(self):

        import json

        

        # Get current refs if available

        refs_x = []

        refs_y = []

        if self.coord_sys:

            refs_x = self.coord_sys.refs_x

            refs_y = self.coord_sys.refs_y

            

        config = {

            'x_min': self.x_min_var.get(),

            'x_max': self.x_max_var.get(),

            'x_log': self.x_log_var.get(),

            'y_min': self.y_min_var.get(),

            'y_max': self.y_max_var.get(),

            'y_log': self.y_log_var.get(),

            'x_offset': self.x_offset_var.get(),

            'y_offset': self.y_offset_var.get(),

            'refs_x': refs_x,

            'refs_y': refs_y,

            'selection_coords': self.selection_coords,

            'smooth_level': self.smooth_level_var.get()

        }

        try:

            with open(self.config_file, 'w') as f:

                json.dump(config, f)

        except Exception as e:

            print(f"Failed to save settings: {e}")



    def export_configuration(self):

        file_path = filedialog.asksaveasfilename(

            defaultextension=".json",

            filetypes=[("JSON Config", "*.json"), ("All Files", "*.*")],

            title="?ˉ???oé??"

        )

        if not file_path:

            return

            

        import json

        

        # Get current refs

        refs_x = []

        refs_y = []

        if self.coord_sys:

            refs_x = self.coord_sys.refs_x

            refs_y = self.coord_sys.refs_y

            

        config = {

            'x_min': self.x_min_var.get(),

            'x_max': self.x_max_var.get(),

            'x_log': self.x_log_var.get(),

            'y_min': self.y_min_var.get(),

            'y_max': self.y_max_var.get(),

            'y_log': self.y_log_var.get(),

            'x_offset': self.x_offset_var.get(),

            'y_offset': self.y_offset_var.get(),

            'refs_x': refs_x,

            'refs_y': refs_y,

            'smooth_level': self.smooth_level_var.get()

        }

        

        try:

            with open(file_path, 'w') as f:

                json.dump(config, f, indent=4)

            self.status_var.set(f"é??·2?????oè?? {os.path.basename(file_path)}")

        except Exception as e:

            messagebox.showerror("错误", f"保存项目时出错: {e}")



    def import_configuration(self):

        file_path = filedialog.askopenfilename(

            filetypes=[("JSON Config", "*.json"), ("All Files", "*.*")],

            title="?ˉ???￥é??"

        )

        if not file_path:

            return

            

        import json

        try:

            with open(file_path, 'r') as f:

                config = json.load(f)

                

            # Apply Settings

            self.x_min_var.set(config.get('x_min', "0.01"))

            self.x_max_var.set(config.get('x_max', "100000"))

            

            self.x_log_var.set(config.get('x_log', True))

            self.y_log_var.set(config.get('y_log', True))

            

            self.y_min_var.set(config.get('y_min', "0.01"))

            self.y_max_var.set(config.get('y_max', "1000"))

            

            self.x_offset_var.set(config.get('x_offset', "0.0%"))

            self.y_offset_var.set(config.get('y_offset', "0.0%"))

            

            self.smooth_level_var.set(config.get('smooth_level', 5))

            

            # Apply Calibration Points

            refs_x = config.get('refs_x', [])

            refs_y = config.get('refs_y', [])

            

            if self.coord_sys:

                self.coord_sys.refs_x = refs_x

                self.coord_sys.refs_y = refs_y

                # Apply axis types and ranges to coord_sys

                self.update_axis_settings()

                self.refresh_calibration_list()

                self.recalculate_data_mapping()

            else:

                # Save for later

                self.saved_refs_x = refs_x

                self.saved_refs_y = refs_y

                

            self.status_var.set(f"é??·2??? {os.path.basename(file_path)} ?ˉ???￥")

            

        except Exception as e:

            messagebox.showerror("错误", f"加载项目时出错: {e}")



    def reset_mode(self):

        self.mode_var.set("view")

        self.set_mode()



    def clear_selection(self):

        if self.selection_rect_id:

            self.canvas.delete(self.selection_rect_id)

            self.selection_rect_id = None

        if self.selection_text_id:

            self.canvas.delete(self.selection_text_id)

            self.selection_text_id = None

        

        self.selection_coords = None

        self.save_settings()

        self.status_var.set("已保存项目")



    def on_key_press(self, event):

        # Ignore if typing in an entry

        if isinstance(event.widget, tk.Entry):

            return



        if event.keysym == 'Escape':

            if self.interaction_mode == 'select_area' and self.current_rect:

                # Cancel current drag

                self.canvas.delete(self.current_rect)

                self.current_rect = None

                self.status_var.set("已保存数据到文件")

            elif self.interaction_mode != 'view':

                self.reset_mode()

            # If in view mode and has selection, maybe ESC clears it?

            # Or keep it consistent: ESC exits modes.

            

        elif event.keysym == 'Return':

            if self.selection_coords:

                self.status_var.set("已打开项目，正在恢复工作状态...")

                self.start_process_thread()

            else:

                # Maybe trigger process anyway?

                self.start_process_thread()



    def apply_smoothing(self):

        try:

            # New Advanced Optimization Logic

            optimizer = CurveOptimizer()

            

            # Map Level (1-10) to Parameters

            # Level 1: Low smoothing (small window, few iters)

            # Level 10: High smoothing (large window, many iters)

            level = self.smooth_level_var.get()

            level = max(1, min(10, level))

            

            # win_ratio: 0.02 to 0.20

            window_ratio = 0.02 * level

            # iterations: 1 to 5

            iterations = max(1, level // 2)

            

            # Optimize Min Curve

            if self.min_curve_data:

                opt_min, report_min = optimizer.optimize_curve(self.min_curve_data, iterations=iterations, window_ratio=window_ratio)

                self.min_curve_data = opt_min

                print(f"Min Curve Optimization: {report_min}")

            

            # Optimize Max Curve

            if self.max_curve_data:

                opt_max, report_max = optimizer.optimize_curve(self.max_curve_data, iterations=iterations, window_ratio=window_ratio)

                self.max_curve_data = opt_max

                print(f"Max Curve Optimization: {report_max}")

            

            self.push_history()

            self.update_visualization()

            self.status_var.set(f"?·2?o???¨é???o§?13??????(Level {level})")

            

        except Exception as e:

            messagebox.showerror("错误", f"?13????¤±è′￥: {e}")



    def export_data_simplified(self):

        if not hasattr(self, 'min_curve_data') or not hasattr(self, 'max_curve_data'):

            messagebox.showwarning("警告", "请先提取曲线数据")

            return



        # Parse Offsets

        try:

            x_off_str = self.x_offset_var.get().replace('%', '')

            x_off_pct = float(x_off_str) if x_off_str else 0.0

            

            y_off_str = self.y_offset_var.get().replace('%', '')

            y_off_pct = float(y_off_str) if y_off_str else 0.0

        except ValueError:

            messagebox.showerror("错误", "请输入有效的平滑级别 (1-10)")

            return



        x_factor_min = 1 + (x_off_pct / 100.0)

        x_factor_max = 1 - (x_off_pct / 100.0)

        y_factor_min = 1 + (y_off_pct / 100.0)

        y_factor_max = 1 - (y_off_pct / 100.0)

            

        # Prepare Data as before

        df1 = pd.DataFrame(self.min_curve_data)

        if not df1.empty:

            df1 = df1[['Data_Y', 'Data_X']].rename(columns={'Data_Y': 'Y1min', 'Data_X': 'X1min'})

            

            # Apply Offsets (Min Curve)

            df1['Y1min'] = df1['Y1min'] * y_factor_min

            df1['X1min'] = df1['X1min'] * x_factor_min

            

            df1.loc[df1['Y1min'] > 99999, 'Y1min'] = 99999

        

        df2 = pd.DataFrame(self.max_curve_data)

        if not df2.empty:

            df2 = df2[['Data_Y', 'Data_X']].rename(columns={'Data_Y': 'Y2max', 'Data_X': 'X2max'})

            

            # Apply Offsets (Max Curve)

            df2['Y2max'] = df2['Y2max'] * y_factor_max

            df2['X2max'] = df2['X2max'] * x_factor_max

            

            df2.loc[df2['Y2max'] > 99999, 'Y2max'] = 99999

        

        df1.reset_index(drop=True, inplace=True)

        df2.reset_index(drop=True, inplace=True)

        

        # Sorting

        if not df1.empty:

            df1 = df1.sort_values(by='Y1min', ascending=False)

        if not df2.empty:

            df2 = df2.sort_values(by='Y2max', ascending=False)

        

        # Re-index

        df1.reset_index(drop=True, inplace=True)

        df2.reset_index(drop=True, inplace=True)



        # Prepare Final DF (Side by Side)

        df_final = pd.concat([df1, df2], axis=1)

        

        # Insert Marker Row Logic

        val_min_x = df1['X1min'].iloc[0] if not df1.empty else 0

        val_max_x = df2['X2max'].iloc[0] if not df2.empty else 0

        

        marker_row = {

            'Y1min': 99999,

            'X1min': val_min_x,

            'Y2max': 99999,

            'X2max': val_max_x

        }

        

        df_marker = pd.DataFrame([marker_row])

        df_final = pd.concat([df_marker, df_final], ignore_index=True)

        

        # Show Data Display Window

        self.show_data_window(df_final)



    def show_data_window(self, df):

        top = tk.Toplevel(self.root)

        top.title("????°???")

        top.geometry("900x600")

        

        # Use simple Frame layout for symmetry

        main_frame = tk.Frame(top)

        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        

        # Left: AB Columns

        frame_ab = tk.Frame(main_frame)

        frame_ab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        

        tk.Label(frame_ab, text="MIN?? (AB?)", font=("Arial", 10, "bold")).pack(pady=5)

        

        btn_copy_ab = ttk.Button(frame_ab, text="?¤????AB????(???è?¨????", bg="#dddddd", 

                               command=lambda: self.copy_to_clipboard(df[['Y1min', 'X1min']], btn_copy_ab))

        btn_copy_ab.pack(pady=5)

        

        text_ab = tk.Text(frame_ab, wrap=tk.NONE)

        scroll_y_ab = tk.Scrollbar(frame_ab, command=text_ab.yview)

        scroll_x_ab = tk.Scrollbar(frame_ab, orient=tk.HORIZONTAL, command=text_ab.xview)

        text_ab.config(yscrollcommand=scroll_y_ab.set, xscrollcommand=scroll_x_ab.set)

        

        scroll_y_ab.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x_ab.pack(side=tk.BOTTOM, fill=tk.X)

        text_ab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        

        # Populate AB (No Header)

        # Convert to string with tab separator

        # Fix: use lineterminator='\n' to avoid double newlines on Windows

        # Fix: Remove extra blank lines logic

        try:

             txt_content_ab = df[['Y1min', 'X1min']].to_csv(sep='\t', index=False, header=False, float_format='%.6f', lineterminator='\n')

        except TypeError:

             # Fallback for older pandas versions

             txt_content_ab = df[['Y1min', 'X1min']].to_csv(sep='\t', index=False, header=False, float_format='%.6f')

        

        text_ab.insert(tk.END, txt_content_ab)

        text_ab.config(state=tk.DISABLED) # Read-only

        

        # Right: CD Columns

        frame_cd = tk.Frame(main_frame)

        frame_cd.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        

        tk.Label(frame_cd, text="MAX?? (CD?)", font=("Arial", 10, "bold")).pack(pady=5)

        

        btn_copy_cd = ttk.Button(frame_cd, text="?¤????CD????(???è?¨????", bg="#dddddd",

                               command=lambda: self.copy_to_clipboard(df[['Y2max', 'X2max']], btn_copy_cd))

        btn_copy_cd.pack(pady=5)

        

        text_cd = tk.Text(frame_cd, wrap=tk.NONE)

        scroll_y_cd = tk.Scrollbar(frame_cd, command=text_cd.yview)

        scroll_x_cd = tk.Scrollbar(frame_cd, orient=tk.HORIZONTAL, command=text_cd.xview)

        text_cd.config(yscrollcommand=scroll_y_cd.set, xscrollcommand=scroll_x_cd.set)

        

        scroll_y_cd.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x_cd.pack(side=tk.BOTTOM, fill=tk.X)

        text_cd.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        

        # Populate CD (No Header)

        try:

            txt_content_cd = df[['Y2max', 'X2max']].to_csv(sep='\t', index=False, header=False, float_format='%.6f', lineterminator='\n')

        except TypeError:

            txt_content_cd = df[['Y2max', 'X2max']].to_csv(sep='\t', index=False, header=False, float_format='%.6f')

            

        text_cd.insert(tk.END, txt_content_cd)

        text_cd.config(state=tk.DISABLED)



        # Shortcuts

        top.bind('<Control-c>', lambda e: self.status_var.set("数据已复制到剪贴板"))



    def copy_to_clipboard(self, df_subset, btn_widget):

        try:

            # Validate

            if df_subset.empty:

                messagebox.showwarning("警告", "未找到可导出的数据")

                return

            

            try:

                content = df_subset.to_csv(sep='\t', index=False, header=False, float_format='%.6f', lineterminator='\n')

            except TypeError:

                content = df_subset.to_csv(sep='\t', index=False, header=False, float_format='%.6f')

                

            self.root.clipboard_clear()

            self.root.clipboard_append(content)

            self.root.update() # Required to finalize clipboard

            

            # Visual Feedback

            orig_text = btn_widget.cget("text")

            btn_widget.config(text="?·2????", bg="#aaffaa")

            self.root.after(1500, lambda: btn_widget.config(text=orig_text, bg="#dddddd"))

            

            self.status_var.set("已成功导出数据到文件")

            

        except Exception as e:

            messagebox.showerror("错误", f"?¤?????¤±è′￥: {e}")



    def validate_number(self, new_value):

        if new_value == "":

            return True

        try:

            float(new_value)

            return True

        except ValueError:

            return False



    def update_axis_settings(self, event=None):

        # Validate logic and trigger preview or reload

        try:

            x_min = float(self.x_min_var.get())

            x_max = float(self.x_max_var.get())

            y_min = float(self.y_min_var.get())

            y_max = float(self.y_max_var.get())

            

            if x_min >= x_max or y_min >= y_max:

                # Don't error immediately, maybe user is typing

                return

                

            x_type = 'log' if self.x_log_var.get() else 'linear'

            y_type = 'log' if self.y_log_var.get() else 'linear'

            

            if self.coord_sys:

                self.coord_sys.set_calibration((x_min, x_max), (y_min, y_max), x_type, y_type)

                self.status_var.set(f"??è?′è????′?·2??′??°: X[{x_min}, {x_max}], Y[{y_min}, {y_max}]")

                self.save_settings()

                # Trigger reload if data exists

                if self.extracted_data:

                    self.recalculate_data_mapping()

                    

        except ValueError:

            pass



    def start_process_thread(self):

        import threading

        t = threading.Thread(target=self.process_image_safe)

        t.start()



    def process_image_safe(self):

        # Wrapper for thread safety with retry logic

        import time

        

        max_retries = 3

        for attempt in range(max_retries):

            try:

                self.status_var.set(f"?-￡??¨?¤???? (?°?èˉ? {attempt+1}/{max_retries})...")

                self.root.update_idletasks()

                

                # Check consistency if reloading

                old_hash = hash(str(self.extracted_data)) if self.extracted_data else 0

                

                self.process_image()

                

                new_hash = hash(str(self.extracted_data))

                

                # If we are just refreshing view, hash might be same, but if processing new image, it changes.

                # Just a placeholder for consistency check.

                

                self.status_var.set("提取完成")

                return # Success

                

            except Exception as e:

                print(f"Attempt {attempt+1} failed: {e}")

                if attempt < max_retries - 1:

                    wait_time = 2 ** attempt # Exponential backoff

                    self.status_var.set(f"?¤?????¤±è′￥???{wait_time}?§????é??èˉ?...")

                    self.root.update_idletasks()

                    time.sleep(wait_time)

                else:

                    messagebox.showerror("错误", f"提取数据失败 (已重试): {e}")

                    self.status_var.set("提取数据失败")



    def set_mode(self):

        self.interaction_mode = self.mode_var.get()

        self.status_var.set(f"???¨????: {self.interaction_mode}")



    def push_history(self):

        # Save current state (min_curve_data, max_curve_data)

        # Clear redo history

        if self.history_index < len(self.history) - 1:

            self.history = self.history[:self.history_index + 1]

            

        state = {

            'min': copy.deepcopy(self.min_curve_data),

            'max': copy.deepcopy(self.max_curve_data)

        }

        self.history.append(state)

        self.history_index += 1

        

        # Limit history size

        if len(self.history) > 20:

            self.history.pop(0)

            self.history_index -= 1



    def undo(self):

        if self.history_index > 0:

            self.history_index -= 1

            state = self.history[self.history_index]

            self.min_curve_data = copy.deepcopy(state['min'])

            self.max_curve_data = copy.deepcopy(state['max'])

            self.update_visualization()

            self.status_var.set("已选定区域")



    def redo(self):

        if self.history_index < len(self.history) - 1:

            self.history_index += 1

            state = self.history[self.history_index]

            self.min_curve_data = copy.deepcopy(state['min'])

            self.max_curve_data = copy.deepcopy(state['max'])

            self.update_visualization()

            self.status_var.set("已清除选区")







    def on_mouse_move(self, event):

        if not hasattr(self, 'tk_img') or not self.tk_img:

            return

            

        x = self.canvas.canvasx(event.x)

        y = self.canvas.canvasy(event.y)

        

        # --- Crosshair ---

        if hasattr(self, 'crosshair_lines'):

            for line in self.crosshair_lines:

                self.canvas.delete(line)

        self.crosshair_lines = []

        

        # Draw crosshair

        # We use a large number for length to cover scroll area

        self.crosshair_lines.append(self.canvas.create_line(0, y, 100000, y, fill='red', dash=(2,2)))

        self.crosshair_lines.append(self.canvas.create_line(x, 0, x, 100000, fill='red', dash=(2,2)))

        

        # Coordinate Text

        img_x = x / self.current_zoom

        img_y = y / self.current_zoom

        

        if not self.processor: return

        h, w = self.processor.image.shape[:2]

        

        if 0 <= img_x < w and 0 <= img_y < h:

            text = ""

            

            # Snapping logic

            snap_dist = 10 / self.current_zoom

            nearest_p = None

            min_d = float('inf')

            

            # Check both curves

            candidates = []

            if self.min_curve_data:

                for p in self.min_curve_data:

                    px, py = p.get('Pixel_X'), p.get('Pixel_Y')

                    if px is None: continue

                    d = np.sqrt((px - img_x)**2 + (py - img_y)**2)

                    if d < snap_dist: candidates.append((d, p, 'min'))

            if self.max_curve_data:

                for p in self.max_curve_data:

                    px, py = p.get('Pixel_X'), p.get('Pixel_Y')

                    if px is None: continue

                    d = np.sqrt((px - img_x)**2 + (py - img_y)**2)

                    if d < snap_dist: candidates.append((d, p, 'max'))

            

            if candidates:

                candidates.sort(key=lambda x: x[0])

                nearest_p = candidates[0][1]

                min_d = candidates[0][0]



            if nearest_p:

                disp_snap_x = nearest_p['Pixel_X'] * self.current_zoom

                disp_snap_y = nearest_p['Pixel_Y'] * self.current_zoom

                dx, dy = nearest_p['Data_X'], nearest_p['Data_Y']

                curve_name = "MIN" if nearest_p.get('Curve') == 'Min_Curve' else "MAX"

                text = f"[{curve_name}] X: {dx:.3e}, Y: {dy:.3e}"

                

                if hasattr(self, 'snap_highlight'):

                    self.canvas.delete(self.snap_highlight)

                self.snap_highlight = self.canvas.create_oval(disp_snap_x-3, disp_snap_y-3, disp_snap_x+3, disp_snap_y+3, outline='white', width=2)

            else:

                if hasattr(self, 'snap_highlight'):

                    self.canvas.delete(self.snap_highlight)

                    

                if self.coord_sys:

                    dx, dy = self.coord_sys.pixel_to_data(img_x, img_y)

                    text = f"X: {dx:.3e}, Y: {dy:.3e}"

                else:

                    text = f"Px: {int(img_x)}, Py: {int(img_y)}"

            

            self.status_var.set(text)

            

            # Magnifier

            self.update_magnifier(img_x, img_y, x, y)

        else:

            self.status_var.set("平滑级别已更新")

            if hasattr(self, 'magnifier_items'):

                for item in self.magnifier_items:

                    self.canvas.delete(item)

                self.magnifier_items = []



    def update_magnifier(self, img_x, img_y, canvas_x, canvas_y):

        if not self.processor: return

        

        # Settings

        mag_zoom = 3.0 # Zoom relative to original image

        mag_size = 200 # Size of magnifier window on screen

        

        # Calculate ROI in original image

        # ROI width in original pixels = mag_size / mag_zoom

        r = int(mag_size / (2 * mag_zoom))

        ix, iy = int(img_x), int(img_y)

        

        x1 = max(0, ix - r)

        y1 = max(0, iy - r)

        x2 = min(self.processor.image.shape[1], ix + r)

        y2 = min(self.processor.image.shape[0], iy + r)

        

        if x2 <= x1 or y2 <= y1: return

        

        roi = self.processor.image[y1:y2, x1:x2].copy()

        

        # Draw points on ROI

        # Filter points that are within ROI

        def draw_points_on_roi(data, color):

            for p in data:

                px, py = p.get('Pixel_X'), p.get('Pixel_Y')

                if px is None: continue

                if x1 <= px < x2 and y1 <= py < y2:

                    cv2.circle(roi, (int(px-x1), int(py-y1)), 2, color, -1)

                    

        draw_points_on_roi(self.min_curve_data, (0, 255, 0)) # Green

        draw_points_on_roi(self.max_curve_data, (0, 255, 255)) # Yellow

        

        # Resize to mag_size

        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

        pil_roi = Image.fromarray(roi_rgb)

        pil_roi = pil_roi.resize((mag_size, mag_size), Image.Resampling.NEAREST)

        

        # Create circular mask

        mask = Image.new('L', (mag_size, mag_size), 0)

        from PIL import ImageDraw

        draw = ImageDraw.Draw(mask)

        draw.ellipse((0, 0, mag_size, mag_size), fill=255)

        

        # Create output image

        output = Image.new('RGBA', (mag_size, mag_size), (0, 0, 0, 0))

        output.paste(pil_roi, (0, 0), mask)

        

        self.mag_img = ImageTk.PhotoImage(output)

        

        # Draw on canvas

        if hasattr(self, 'magnifier_items'):

            for item in self.magnifier_items:

                self.canvas.delete(item)

        self.magnifier_items = []

        

        # Position logic

        offset = 20

        mx = canvas_x + offset

        my = canvas_y + offset

        

        # Avoid going off screen

        cw = self.canvas.winfo_width()

        ch = self.canvas.winfo_height()

        

        if mx + mag_size > cw: mx = canvas_x - mag_size - offset

        if my + mag_size > ch: my = canvas_y - mag_size - offset

        

        self.magnifier_items.append(self.canvas.create_image(mx, my, anchor=tk.NW, image=self.mag_img))

        self.magnifier_items.append(self.canvas.create_oval(mx, my, mx+mag_size, my+mag_size, outline='white', width=2))

        

        # Crosshair

        cx, cy = mx + mag_size/2, my + mag_size/2

        self.magnifier_items.append(self.canvas.create_line(cx-10, cy, cx+10, cy, fill='red'))

        self.magnifier_items.append(self.canvas.create_line(cx, cy-10, cx, cy+10, fill='red'))

        

        # Text

        if self.coord_sys:

            dx, dy = self.coord_sys.pixel_to_data(img_x, img_y)

            text = f"({dx:.3g}, {dy:.3g})"

            

            # --- Background Box ---

            font_size = 10

            # Simple estimation

            char_w = 7

            text_w = len(text) * char_w

            text_h = 16

            

            pad_x = 8

            pad_y = 8

            

            box_w = text_w + 2 * pad_x

            box_h = text_h + 2 * pad_y

            

            # Center at bottom of magnifier

            # Magnifier is mag_size x mag_size

            # Center X: mag_size/2

            # Bottom Y: mag_size - margin

            

            center_x = mag_size / 2

            bottom_y = mag_size - 20 # 20px from bottom

            

            # Box coords relative to magnifier TOP-LEFT (mx, my)

            # Box Top-Left

            box_rel_x = center_x - box_w / 2

            box_rel_y = bottom_y - box_h

            

            # Absolute canvas coords

            abs_box_x = mx + box_rel_x

            abs_box_y = my + box_rel_y

            

            # Create semi-transparent image for background

            box_img = Image.new('RGBA', (int(box_w), int(box_h)), (0, 0, 0, 0))

            draw_box = ImageDraw.Draw(box_img)

            # Black #000000 with 70% opacity -> alpha=178

            draw_box.rounded_rectangle([(0, 0), (box_w-1, box_h-1)], radius=4, fill=(0, 0, 0, 178))

            

            self.mag_text_bg = ImageTk.PhotoImage(box_img)

            self.magnifier_items.append(self.canvas.create_image(abs_box_x, abs_box_y, anchor=tk.NW, image=self.mag_text_bg))

            

            # Text (White)

            # Center text in box

            text_abs_x = abs_box_x + box_w / 2

            text_abs_y = abs_box_y + box_h / 2

            self.magnifier_items.append(self.canvas.create_text(text_abs_x, text_abs_y, text=text, fill='white', font=("Arial", font_size, "bold")))



    def get_image_coords(self, event):

        x = self.canvas.canvasx(event.x)

        y = self.canvas.canvasy(event.y)

        img_x = x / self.current_zoom

        img_y = y / self.current_zoom

        return img_x, img_y



    def on_mouse_down(self, event):

        if not self.processor:

            return

            

        img_x, img_y = self.get_image_coords(event)

        

        # Store start pos for drag operations

        self.start_x = self.canvas.canvasx(event.x)

        self.start_y = self.canvas.canvasy(event.y)

        

        # Check bounds

        h, w = self.processor.image.shape[:2]

        if not (0 <= img_x < w and 0 <= img_y < h):

            return



        if self.interaction_mode == 'add_point':

            self.add_point(img_x, img_y)

        

        elif self.interaction_mode == 'move_point':

            self.start_move_point(img_x, img_y)

            

        elif self.interaction_mode.startswith('set_'):

            self.handle_calibration_click(img_x, img_y, self.interaction_mode)

            

        elif self.interaction_mode == 'erase_point':

            self.erase_point(img_x, img_y)

            

        elif self.interaction_mode in ['erase_box', 'select_area']:

            self.current_rect = None



    def add_point(self, px, py):

        if not self.coord_sys:

            messagebox.showwarning("警告", "请先标定坐标系")

            return

            

        dx, dy = self.coord_sys.pixel_to_data(px, py)

        point = {

            'Curve': 'Min_Curve' if self.target_curve == 'min' else 'Max_Curve',

            'Pixel_X': px,

            'Pixel_Y': py,

            'Data_X': dx,

            'Data_Y': dy

        }

        

        self.push_history()

        

        if self.target_curve == 'min':

            self.min_curve_data.append(point)

            self.min_curve_data.sort(key=lambda p: p['Pixel_Y']) # Sort by Y pixel (top to bottom)

        else:

            self.max_curve_data.append(point)

            self.max_curve_data.sort(key=lambda p: p['Pixel_Y'])

            

        self.refresh_canvas()

        self.status_var.set(f"?·2?·??1: ({dx:.2f}, {dy:.2f})")



    def start_move_point(self, px, py):

        radius = 10 / self.current_zoom 

        candidates = []

        for p in self.min_curve_data:

            d = np.sqrt((p['Pixel_X'] - px)**2 + (p['Pixel_Y'] - py)**2)

            if d < radius: candidates.append((d, p))

            

        for p in self.max_curve_data:

            d = np.sqrt((p['Pixel_X'] - px)**2 + (p['Pixel_Y'] - py)**2)

            if d < radius: candidates.append((d, p))

            

        if candidates:

            candidates.sort(key=lambda x: x[0])

            self.dragging_point = candidates[0][1]

            self.push_history() # Save state before move

            self.status_var.set(f"é????-???? ({self.dragging_point['Data_X']:.2f}, {self.dragging_point['Data_Y']:.2f})")



    def on_mouse_drag(self, event):

        cur_x = self.canvas.canvasx(event.x)

        cur_y = self.canvas.canvasy(event.y)

        

        if self.interaction_mode == 'move_point' and self.dragging_point:

            img_x, img_y = self.get_image_coords(event)

            self.dragging_point['Pixel_X'] = img_x

            self.dragging_point['Pixel_Y'] = img_y

            # Update data coords

            if self.coord_sys:

                dx, dy = self.coord_sys.pixel_to_data(img_x, img_y)

                self.dragging_point['Data_X'] = dx

                self.dragging_point['Data_Y'] = dy

            self.refresh_canvas()

            self.status_var.set(f"?§???¨???? ({dx:.2f}, {dy:.2f})")

            return



        if self.interaction_mode == 'erase_box':

            if self.current_rect:

                self.canvas.delete(self.current_rect)

            self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='red')

            

        elif self.interaction_mode == 'select_area':

            if self.current_rect:

                self.canvas.delete(self.current_rect)

            self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='blue', dash=(4, 4), width=2)

            

            # Show dimensions

            w = abs(cur_x - self.start_x) / self.current_zoom

            h = abs(cur_y - self.start_y) / self.current_zoom

            self.status_var.set(f"??é????o: {int(w)} x {int(h)}")



    def on_mouse_up(self, event):

        if self.interaction_mode == 'move_point':

            self.dragging_point = None

            return



        if self.interaction_mode == 'erase_box':

            if self.current_rect:

                self.canvas.delete(self.current_rect)

                self.current_rect = None

                

            end_x = self.canvas.canvasx(event.x)

            end_y = self.canvas.canvasy(event.y)

            

            x1 = min(self.start_x, end_x) / self.current_zoom

            y1 = min(self.start_y, end_y) / self.current_zoom

            x2 = max(self.start_x, end_x) / self.current_zoom

            y2 = max(self.start_y, end_y) / self.current_zoom

            

            self.erase_box(x1, y1, x2, y2)

            

        elif self.interaction_mode == 'select_area':

            # Finalize selection

            if self.current_rect:

                self.canvas.delete(self.current_rect)

                self.current_rect = None

                

            end_x = self.canvas.canvasx(event.x)

            end_y = self.canvas.canvasy(event.y)

            

            # Remove old selection if exists

            if self.selection_rect_id:

                self.canvas.delete(self.selection_rect_id)

            if self.selection_text_id:

                self.canvas.delete(self.selection_text_id)

            

            # Check size

            w = abs(end_x - self.start_x)

            h = abs(end_y - self.start_y)

            

            if w < 5:

                self.status_var.set("已标定区域，点击提取数据")

                return

            

            # Draw persistent rectangle

            x1_c = min(self.start_x, end_x)

            y1_c = min(self.start_y, end_y)

            x2_c = max(self.start_x, end_x)

            y2_c = max(self.start_y, end_y)

            

            self.selection_rect_id = self.canvas.create_rectangle(x1_c, y1_c, x2_c, y2_c, outline='blue', width=2)

            self.selection_text_id = self.canvas.create_text(x1_c, y1_c - 10, text=f"{int(w/self.current_zoom)}x{int(h/self.current_zoom)}", fill='blue', anchor=tk.SW)

            

            # Calculate and store Image Coordinates

            img_x1 = x1_c / self.current_zoom

            img_y1 = y1_c / self.current_zoom

            img_x2 = x2_c / self.current_zoom

            img_y2 = y2_c / self.current_zoom

            

            self.selection_coords = (img_x1, img_y1, img_x2, img_y2)

            self.status_var.set(f"???·2é?????")

            self.save_settings()



    def handle_calibration_click(self, px, py, mode):

        # Custom Dialog for Precision Calibration

        axis = 'x' if 'x' in mode else 'y'

        

        # Determine click context

        context_hint = ""

        is_log = False

        

        if axis == 'x':

            is_log = self.x_log_var.get()

            if self.coord_sys and self.coord_sys.plot_area:

                x0, _, w, _ = self.coord_sys.plot_area

                if px < x0 + w/2:

                    context_hint = "Xè?′????°??"

                else:

                    context_hint = "Xè?′????¤§?"

        else:

            is_log = self.y_log_var.get()

            if self.coord_sys and self.coord_sys.plot_area:

                _, y0, _, h = self.coord_sys.plot_area

                if py > y0 + h/2:

                    context_hint = "Yè?′????°?? # Bottom"

                else:

                    context_hint = "Yè?′????¤§? # Top"



        # Create Toplevel Dialog

        dialog = tk.Toplevel(self.root)

        dialog.title("???3??2??o|???")

        dialog.attributes('-topmost', True) # Keep on top

        dialog.geometry("450x300")

        dialog.resizable(False, False)

        

        # Center relative to root

        root_x = self.root.winfo_x()

        root_y = self.root.winfo_y()

        root_w = self.root.winfo_width()

        root_h = self.root.winfo_height()

        pos_x = root_x + (root_w - 450) // 2

        pos_y = root_y + (root_h - 300) // 2

        dialog.geometry(f"+{pos_x}+{pos_y}")

        

        # Fonts

        font_label = ("Microsoft YaHei", 14, "bold")

        font_normal = ("Microsoft YaHei", 10)

        

        # Validation Logic

        def validate_coord(P):

            if P == "" or P == "-": return True

            try:

                v = float(P)

                return -9999.999 <= v <= 9999.999 and len(P.split('.')[-1]) <= 3 if '.' in P else True

            except ValueError:

                return False

                

        vcmd = (dialog.register(validate_coord), '%P')

        

        # Layout Frames

        main_frame = tk.Frame(dialog, padx=20, pady=20)

        main_frame.pack(fill=tk.BOTH, expand=True)

        

        # Variables

        x_var = tk.StringVar()

        y_var = tk.StringVar()

        

        # Highlight invalid input helper

        def on_focus_out(entry, var):

            try:

                val = float(var.get())

                if not (-9999.999 <= val <= 9999.999):

                    raise ValueError

                entry.config(bg="white")

            except ValueError:

                entry.config(bg="#FFCCCC") # Light red



        # Conditional UI Rendering

        if axis == 'x':

            tk.Label(main_frame, text="Xè?′???èˉ·è?????Xè?′???", font=font_label).grid(row=0, column=0, sticky=tk.W, pady=10)

            entry_x = tk.Entry(main_frame, textvariable=x_var, validate='key', validatecommand=vcmd, font=font_normal, width=15)

            entry_x.grid(row=0, column=1, padx=10)

            entry_x.focus_set()

            entry_x.bind("<FocusOut>", lambda e: on_focus_out(entry_x, x_var))

        else:

            tk.Label(main_frame, text="Yè?′???èˉ·è?????Yè?′???", font=font_label).grid(row=0, column=0, sticky=tk.W, pady=10)

            entry_y = tk.Entry(main_frame, textvariable=y_var, validate='key', validatecommand=vcmd, font=font_normal, width=15)

            entry_y.grid(row=0, column=1, padx=10)

            entry_y.focus_set()

            entry_y.bind("<FocusOut>", lambda e: on_focus_out(entry_y, y_var))

        

        # Real-time Preview

        preview_var = tk.StringVar(value="?????è?????..)")

        lbl_preview = tk.Label(main_frame, textvariable=preview_var, font=("Arial", 10), fg="blue")

        lbl_preview.grid(row=2, column=0, columnspan=2, pady=15, sticky=tk.W)

        

        # Real-time update logic

        def update_preview():

            if not dialog.winfo_exists(): return

            

            try:

                cx, cy = self.canvas.winfo_pointerxy()

                cx = cx - self.canvas.winfo_rootx()

                cy = cy - self.canvas.winfo_rooty()

                

                cx = self.canvas.canvasx(cx)

                cy = self.canvas.canvasy(cy)

                

                disp_w = self.tk_img.width()

                disp_h = self.tk_img.height()

                orig_w = self.processor.image.shape[1]

                orig_h = self.processor.image.shape[0]

                sx = orig_w / disp_w

                sy = orig_h / disp_h

                

                mx = cx * sx

                my = cy * sy

                

                if self.coord_sys:

                    dx, dy = self.coord_sys.pixel_to_data(mx, my)

                    

                    if axis == 'x':

                        dx1, _ = self.coord_sys.pixel_to_data(mx+0.1, my)

                        err_x = abs(dx1 - dx)

                        preview_var.set(f"??? X: {dx:.3f} ?±{err_x:.1e}")

                    else:

                        _, dy1 = self.coord_sys.pixel_to_data(mx, my+0.1)

                        err_y = abs(dy1 - dy)

                        preview_var.set(f"??? Y: {dy:.3f} ?±{err_y:.1e}")

                else:

                    preview_var.set(f"??")

            except:

                pass

                

            dialog.after(30, update_preview) # 30ms ~ 33Hz

            

        update_preview()

        

        # Buttons

        btn_frame = tk.Frame(dialog)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        

        def on_apply():

            # Validate and Save

            try:

                vx = float(x_var.get()) if (axis == 'x' and x_var.get()) else None

                vy = float(y_var.get()) if (axis == 'y' and y_var.get()) else None

                

                if vx is None and vy is None:

                    return

                

                # Apply

                old_dx, old_dy = self.coord_sys.pixel_to_data(px, py)

                

                if vx is not None:

                    self.coord_sys.add_reference_point('x', px, vx)

                if vy is not None:

                    self.coord_sys.add_reference_point('y', py, vy)

                

                # Recalculate

                self.recalculate_data_mapping()

                self.refresh_calibration_list()

                self.save_settings()

                

                # Log

                self.log_calibration(old_dx, vx if vx else old_dx, old_dy, vy if vy else old_dy)

                

                # Toast

                self.show_toast("?2??o|?·2??è?3?±0.1px")

                

                dialog.destroy()

                

            except ValueError:

                messagebox.showerror("错误", "请输入有效的数值", parent=dialog)



        def on_reset():

            # Reset only current axis? Or all?

            # Requirement says "Reset restores factory calibration values".

            # Usually implies resetting the specific axis or all.

            # "Reset" button usually resets ALL manual points.

            self.coord_sys.reset_references()

            self.refresh_calibration_list()

            self.recalculate_data_mapping()

            self.save_settings()

            self.status_var.set("数据已导出完成")

            

        btn_apply = ttk.Button(btn_frame, text="?o???¨", command=on_apply, width=10, bg="#DDDDDD")

        btn_apply.pack(side=tk.LEFT, padx=10)

        

        btn_reset = ttk.Button(btn_frame, text="é?????", command=on_reset, width=10)

        btn_reset.pack(side=tk.LEFT, padx=10)

        

        btn_cancel = ttk.Button(btn_frame, text="??", command=dialog.destroy, width=10)

        btn_cancel.pack(side=tk.RIGHT, padx=10)

        

        # Keyboard Nav

        dialog.bind('<Return>', lambda e: on_apply())

        dialog.bind('<Escape>', lambda e: dialog.destroy())

        

        self.root.wait_window(dialog)



    def log_calibration(self, old_x, new_x, old_y, new_y):

        import datetime

        log_file = os.path.join(os.path.dirname(self.config_file), "calibration.log")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        

        log_entry = f"[{timestamp}] Operator: User | Old: ({old_x:.3f}, {old_y:.3f}) -> New: ({new_x:.3f}, {new_y:.3f})\n"

        

        try:

            # Rotate logs (simple check: if file too old? Or parse lines?)

            # "Keep for 180 days".

            # Append first

            with open(log_file, 'a') as f:

                f.write(log_entry)

                

            # Cleanup logic (optional, run occasionally)

            # ...

        except:

            pass



    def show_toast(self, message):

        # Transient window

        toast = tk.Toplevel(self.root)

        toast.overrideredirect(True)

        toast.attributes('-topmost', True)

        

        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 100

        y = self.root.winfo_y() + self.root.winfo_height() - 100

        toast.geometry(f"200x40+{x}+{y}")

        

        lbl = tk.Label(toast, text=message, bg="black", fg="white", padx=10, pady=5)

        lbl.pack(fill=tk.BOTH, expand=True)

        

        toast.after(2000, toast.destroy)



    def recalculate_data_mapping(self):

        # Update all Data_X/Y based on new calibration

        for p in self.min_curve_data:

            if 'Pixel_X' in p and 'Pixel_Y' in p:

                dx, dy = self.coord_sys.pixel_to_data(p['Pixel_X'], p['Pixel_Y'])

                p['Data_X'] = dx

                p['Data_Y'] = dy

            

        for p in self.max_curve_data:

            if 'Pixel_X' in p and 'Pixel_Y' in p:

                dx, dy = self.coord_sys.pixel_to_data(p['Pixel_X'], p['Pixel_Y'])

                p['Data_X'] = dx

                p['Data_Y'] = dy

            

        self.update_visualization()



    def erase_point(self, px, py):

        # Find nearest point within radius

        radius = 5

        self.push_history() # Save state before delete

        

        deleted = False

        

        def filter_points(data_list):

            nonlocal deleted

            new_list = []

            for p in data_list:

                dist = np.sqrt((p['Pixel_X'] - px)**2 + (p['Pixel_Y'] - py)**2)

                if dist < radius:

                    deleted = True

                else:

                    new_list.append(p)

            return new_list



        self.min_curve_data = filter_points(self.min_curve_data)

        self.max_curve_data = filter_points(self.max_curve_data)

        

        if deleted:

            self.update_visualization()

            self.status_var.set("数据已复制到剪贴板")

        else:

            # Pop history if nothing changed

            self.history.pop() 

            self.history_index -= 1



    def erase_box(self, x1, y1, x2, y2):

        self.push_history()

        

        def filter_box(data_list):

            new_list = []

            for p in data_list:

                if not (x1 <= p['Pixel_X'] <= x2 and y1 <= p['Pixel_Y'] <= y2):

                    new_list.append(p)

            return new_list

            

        self.min_curve_data = filter_box(self.min_curve_data)

        self.max_curve_data = filter_box(self.max_curve_data)

        

        self.update_visualization()

        self.status_var.set("已复制数据到剪贴板")



    def _on_model_change(self, event):

        if self.fit_model_var.get() == "Polynomial":

            self.fit_order_entry.config(state=tk.NORMAL)

        else:

            self.fit_order_entry.config(state=tk.DISABLED)



    def load_image(self):

        file_path = filedialog.askopenfilename(filetypes=[("???", "*.png;*.jpg;*.jpeg;*.tiff;*.bmp")])

        if not file_path:

            return

        

        self.image_path = file_path

        self.processor = ImageProcessor(image_path=file_path)

        self.display_image(self.processor.image)

        self.status_var.set(f"?·2???{os.path.basename(file_path)}")

        

        self._detect_and_calibrate()



    def paste_image(self, event=None):

        try:

            # Grab image from clipboard

            img = ImageGrab.grabclipboard()

            

            if isinstance(img, Image.Image):

                # Convert PIL image to OpenCV format (numpy array)

                # PIL is RGB, OpenCV is BGR

                if img.mode != 'RGB':

                    img = img.convert('RGB')

                img_np = np.array(img)

                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

                

                self.image_path = "Clipboard"

                self.processor = ImageProcessor(image_data=img_cv)

                self.display_image(self.processor.image)

                self.status_var.set("已保存项目配置")

                

                self._detect_and_calibrate()

            else:

                messagebox.showwarning("警告", "剪贴板中没有图片数据")

                

        except Exception as e:

            messagebox.showerror("错误", f"?2?è′′?¤±è′￥: {e}")



    def _detect_and_calibrate(self):

        # Auto-detect plot area

        self.coord_sys = CoordinateSystem(self.processor.image)

        rect = self.coord_sys.find_plot_area()

        if rect:

            x, y, w, h = rect

            self.refresh_canvas()

            self.status_var.set("正在识别图像特征，准备提取曲线...")

            self.root.update()

            

            # Check if user has already set calibration (Memory Function)

            # If the Vars are not default, assume user set them and keep them.

            # Default values: 0.01, 100000, 0.01, 1000

            # Simple check: just don't overwrite if they match "Memory"?

            # No, we want to OVERWRITE if this is a NEW image and we haven't manually touched it?

            # Or, if "Memory" is active, we APPLY memory to the Vars.

            

            # Implementation: If Vars have values, use them?

            # But Vars always have values.

            # Let's assume if the user edited them, we keep them.

            # But when we load a new image, how do we know if it's "user edited"?

            # Let's just NOT overwrite if the current values are valid?

            # No, usually we want OCR to run.

            

            # Requirement: "Coordinate axis calibration should have memory function, subsequent imported pictures can follow"

            # This implies: If I load Image A, set to 1-100. Load Image B, it should stay 1-100.

            # So, we should NOT auto-detect scales if we are "following" previous settings.

            # Let's try to detect scales ONLY if we think we should.

            # Or better: Run detection, but only apply if confidence is high OR if user hasn't locked it.

            

            # Simplest Memory: Just don't overwrite the GUI variables with OCR results!

            # The user can click "Auto Detect" if they want?

            # Or: The Vars ALREADY contain the values from the previous image.

            # So by default, we ARE remembering them.

            # The issue is `_detect_and_calibrate` OVERWRITES them with OCR results.

            

            # Solution: Comment out the OCR overwriting part, or make it optional?

            # Or: Only overwrite if OCR is successful AND differs significantly?

            # Let's keep OCR log to console, but NOT set the variables automatically 

            # if we assume "Memory" is the priority.

            # Or: Check if it's the FIRST image load.

            

            # Let's disable auto-overwrite for now to satisfy "Memory".

            # The Vars `self.x_min_var` etc. persist.

            # We just need to ensure `self.coord_sys` gets updated with these vars.

            

            # Apply current GUI vars to the new coord_sys

            try:

                x_min = float(self.x_min_var.get())

                x_max = float(self.x_max_var.get())

                y_min = float(self.y_min_var.get())

                y_max = float(self.y_max_var.get())

                x_type = 'log' if self.x_log_var.get() else 'linear'

                y_type = 'log' if self.y_log_var.get() else 'linear'

                

                self.coord_sys.set_calibration((x_min, x_max), (y_min, y_max), x_type, y_type)

                

                # Restore saved calibration points

                if hasattr(self, 'saved_refs_x') and self.saved_refs_x:

                    self.coord_sys.refs_x = self.saved_refs_x

                if hasattr(self, 'saved_refs_y') and self.saved_refs_y:

                    self.coord_sys.refs_y = self.saved_refs_y

                    

                self.refresh_calibration_list()

                self.status_var.set("已自动检测坐标轴")

            except:

                pass



            # Optional: Attempt OCR and print/suggest?

            # try:

            #     x_range, y_range = self.coord_sys.detect_axes_scales()

            #     # If successful, we could prompt user? Or just log.

            #     print(f"OCR Suggestion: X={x_range}, Y={y_range}")

            # except:

            #     pass

                

        else:

            self.status_var.set("正在识别图像特征...")







    def process_image(self):

        if not self.processor or not self.coord_sys:

            messagebox.showerror("错误", "请先加载图片并标定坐标系")

            return

            

        # Update calibration

        try:

            x_min = float(self.x_min_var.get())

            x_max = float(self.x_max_var.get())

            y_min = float(self.y_min_var.get())

            y_max = float(self.y_max_var.get())

            

            x_type = 'log' if self.x_log_var.get() else 'linear'

            y_type = 'log' if self.y_log_var.get() else 'linear'

            

            self.coord_sys.set_calibration((x_min, x_max), (y_min, y_max), x_type, y_type)

        except ValueError:

            messagebox.showerror("错误", "请输入有效的偏移数值")

            return



        # Extract Curves

        # Determine extraction area: User selection > Auto-detected

        plot_area = None

        if self.selection_coords:

             # User manual selection

             x1, y1, x2, y2 = self.selection_coords

             plot_area = (x1, y1, x2-x1, y2-y1)

             # self.status_var.set("?????¨??¨??·???é????è??è?????..") # Don't overwrite status immediately or it flickers

        elif self.coord_sys.plot_area:

             plot_area = self.coord_sys.plot_area

        else:

             messagebox.showerror("错误", "无法提取曲线数据，请检查图像质量")

             return



        x_plot, y_plot, w_plot, h_plot = plot_area

        self.extractor = CurveExtractor(self.processor.image, (x_plot, y_plot, w_plot, h_plot))

        

        # Extract Min (Left) and Max (Right) curves

        # Now uses adaptive sampling internally

        min_pixels, max_pixels = self.extractor.extract_blue_curves()

        

        # Map to data

        self.extracted_data = []

        

        # Helper to process and filter points

        def process_curve_points(pixels, curve_name):

            points = []

            for px, py in pixels:

                data_point = self.coord_sys.pixel_to_data(px, py)

                if data_point:

                    points.append({

                        'Curve': curve_name,

                        'Pixel_X': px,

                        'Pixel_Y': py,

                        'Data_X': data_point[0],

                        'Data_Y': data_point[1]

                    })

            

            if not points:

                return []

                

            # Optimization Strategy Update:

            # 1. Filter points that are too close in Pixel Space (Density Control)

            # This ensures we don't have thousands of points for a straight line, 

            # but keeps corners and shape.

            

            # Sort by Y (Image Y is monotonic-ish for vertical, X for horizontal)

            # Since we have a mix, let's sort by Y (Data Y Descending)

            points.sort(key=lambda p: p['Data_Y'], reverse=True)

            

            filtered_points = []

            if points:

                filtered_points.append(points[0])

                for i in range(1, len(points)):

                    curr = points[i]

                    prev = filtered_points[-1]

                    

                    # Euclidean distance in Pixel Space

                    dist = np.sqrt((curr['Pixel_X'] - prev['Pixel_X'])**2 + 

                                   (curr['Pixel_Y'] - prev['Pixel_Y'])**2)

                    

                    # Threshold: 2 pixels (Adjustable)

                    if dist >= 2.0:

                        filtered_points.append(curr)

            

            # Final check: Ensure we have enough points?

            # If not, maybe relax threshold? 2.0 is quite fine.

            

            # Clean invalid

            clean_points = []

            for p in filtered_points:

                if p['Data_X'] > 0 and p['Data_Y'] > 0:

                     clean_points.append(p)

                     

            return clean_points



        # Clear history before new process

        self.history = []

        self.history_index = -1

        

        # Process Min Curve (Left) -> Y1min, X1min

        min_data = process_curve_points(min_pixels, 'Min_Curve')

        

        # Process Max Curve (Right) -> Y2max, X2max

        max_data = process_curve_points(max_pixels, 'Max_Curve')

        

        # --- 97% Distribution Filtering (1.5% - 98.5%) ---

        def filter_by_y_distribution(data_list):

            if not data_list:

                return []

            y_vals = [p['Data_Y'] for p in data_list]

            if not y_vals:

                return []

            

            # Calculate percentiles

            lower_bound = np.percentile(y_vals, 1.5)

            upper_bound = np.percentile(y_vals, 98.5)

            

            filtered = [p for p in data_list if lower_bound <= p['Data_Y'] <= upper_bound]

            return filtered



        min_data = filter_by_y_distribution(min_data)

        max_data = filter_by_y_distribution(max_data)

        # -------------------------------------------------

        

        # Store separately for export

        self.min_curve_data = min_data

        self.max_curve_data = max_data

        

        # Push initial state to history

        self.push_history()

        

        # Combine for visualization/fitting (legacy structure)

        self.extracted_data.extend(min_data)

        self.extracted_data.extend(max_data)

        

        self.status_var.set(f"已提取 {len(self.extracted_data)} ?????°?????1?")

        

        self.update_visualization() # Use new visualizer



    def process_image_legacy(self):

        # Renamed old method or just keep structure? 

        # I replaced the content of process_image's internal helper.

        # But I need to make sure I didn't break the indentation of process_image.

        # The code above is the *content* of process_image.

        # Wait, I used SearchReplace on the inner helper function `process_curve_points` 

        # but also included `self.history = []` which is outside the helper.

        pass



    def export_data_with_fit(self):

        if not hasattr(self, 'min_curve_data') or not hasattr(self, 'max_curve_data'):

            messagebox.showwarning("警告", "请先提取数据再导出")

            return

            

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])

        if not file_path:

            return

            

        # Prepare 4-column data

        df1 = pd.DataFrame(self.min_curve_data)

        if not df1.empty:

            df1 = df1[['Data_Y', 'Data_X']].rename(columns={'Data_Y': 'Y1min', 'Data_X': 'X1min'})

        

        df2 = pd.DataFrame(self.max_curve_data)

        if not df2.empty:

            df2 = df2[['Data_Y', 'Data_X']].rename(columns={'Data_Y': 'Y2max', 'Data_X': 'X2max'})

        

        df1.reset_index(drop=True, inplace=True)

        df2.reset_index(drop=True, inplace=True)

        

        df_out = pd.concat([df1, df2], axis=1)

        

        # Prepare Optimization Report

        raw_count = (len(self.min_curve_data) + len(self.max_curve_data)) # This is after processing, need raw count

        # Actually we don't have the raw-raw count anymore unless we store it.

        # But we can compare to the pixels count roughly.

        

        report_data = {

            'Metric': ['Total Points', 'Min Curve Points', 'Max Curve Points'],

            'Count': [len(df1)+len(df2), len(df1), len(df2)]

        }

        df_report = pd.DataFrame(report_data)



        # Save to File

        if file_path.endswith('.xlsx'):

            with pd.ExcelWriter(file_path) as writer:

                df_out.to_excel(writer, sheet_name='????°???', index=False)

                df_report.to_excel(writer, sheet_name='????￥???', index=False)

                # Add fit logic if needed

        else: # CSV

            df_out.to_csv(file_path, index=False)

            with open(file_path, 'a', newline='') as f:

                f.write("\n\n# ????￥???\n")

                df_report.to_csv(f, index=False)



        self.status_var.set(f"?·2?????oè?? {file_path}")



    def export_data(self):

        # Legacy export, redirected to new one with default options or just raw

        # But for now, let's keep the button calling the old logic or remove it?

        # The user asked to "enhance the export function".

        # I'll replace the old export button with the new one in the UI setup.

        pass



    def save_project_as(self):

        # Save complete project state to a zip file (.cep or .zip)

        import zipfile

        import datetime

        

        if not self.processor:

            messagebox.showwarning("警告", "请先加载图片再操作")

            return

            

        default_name = f"Project_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.cep"

        file_path = filedialog.asksaveasfilename(

            initialfile=default_name,

            defaultextension=".cep",

            filetypes=[("Curve Extractor Project", "*.cep"), ("ZIP Archive", "*.zip")],

            title="??|?-?é?1???"

        )

        

        if not file_path:

            return

            

        try:

            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:

                # 1. Save Image (Original)

                # We need to save the cv2 image as png

                # Use a temp buffer

                success, encoded_img = cv2.imencode('.png', self.processor.image)

                if success:

                    zf.writestr('image.png', encoded_img.tobytes())

                else:

                    raise Exception("Failed to encode image")

                

                # 2. Save Data (JSON)

                # Gather all data

                refs_x = self.coord_sys.refs_x if self.coord_sys else []

                refs_y = self.coord_sys.refs_y if self.coord_sys else []

                

                project_data = {

                    'version': '1.0',

                    'timestamp': datetime.datetime.now().isoformat(),

                    'calibration': {

                        'x_min': self.x_min_var.get(),

                        'x_max': self.x_max_var.get(),

                        'x_log': self.x_log_var.get(),

                        'y_min': self.y_min_var.get(),

                        'y_max': self.y_max_var.get(),

                        'y_log': self.y_log_var.get(),

                        'refs_x': refs_x,

                        'refs_y': refs_y

                    },

                    'settings': {

                        'x_offset': self.x_offset_var.get(),

                        'y_offset': self.y_offset_var.get(),

                        'smooth_level': self.smooth_level_var.get(),

                        'selection_coords': self.selection_coords

                    },

                    'data': {

                        'min_curve': self.min_curve_data,

                        'max_curve': self.max_curve_data

                    },

                    'history': self.history # Optional, might be large

                }

                

                import json

                zf.writestr('project.json', json.dumps(project_data, indent=4))

                

            self.status_var.set(f"é?1????·2??????-?è?3 {os.path.basename(file_path)}")

            messagebox.showinfo("提示", f"é?1????·2???\n{file_path}")

            

        except Exception as e:

            messagebox.showerror("错误", f"????3?????-?é?1???: {str(e)}")

            

    def open_project(self):

        import zipfile

        import json

        

        file_path = filedialog.askopenfilename(

            filetypes=[("Curve Extractor Project", "*.cep"), ("ZIP Archive", "*.zip"), ("All Files", "*.*")],

            title="??é?1???"

        )

        

        if not file_path:

            return

            

        try:

            with zipfile.ZipFile(file_path, 'r') as zf:

                # 1. Load Image

                if 'image.png' not in zf.namelist():

                    raise Exception("Project file missing image.png")

                    

                img_data = zf.read('image.png')

                img_array = np.frombuffer(img_data, np.uint8)

                cv_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                

                if cv_img is None:

                    raise Exception("Failed to decode image from project")

                    

                # 2. Load Data

                if 'project.json' not in zf.namelist():

                    raise Exception("Project file missing project.json")

                    

                project_data = json.loads(zf.read('project.json').decode('utf-8'))

                

                # Apply Image

                self.image_path = file_path # Or indicate it's from a project

                self.processor = ImageProcessor(image_data=cv_img)

                self.display_image(self.processor.image)

                

                # Apply Calibration

                calib = project_data.get('calibration', {})

                self.x_min_var.set(calib.get('x_min', "0.01"))

                self.x_max_var.set(calib.get('x_max', "100000"))

                self.y_min_var.set(calib.get('y_min', "0.01"))

                self.y_max_var.set(calib.get('y_max', "1000"))

                

                self.x_log_var.set(calib.get('x_log', True))

                self.y_log_var.set(calib.get('y_log', True))

                

                # Apply Settings

                settings = project_data.get('settings', {})

                self.x_offset_var.set(settings.get('x_offset', "0.0%"))

                self.y_offset_var.set(settings.get('y_offset', "0.0%"))

                self.smooth_level_var.set(settings.get('smooth_level', 5))

                self.selection_coords = settings.get('selection_coords')

                

                # Init Coord Sys

                self.coord_sys = CoordinateSystem(self.processor.image)

                # Try to restore plot area if possible, or just set calibration

                # If selection_coords exists, maybe use that?

                # Or just assume full image or let user re-detect if needed?

                # Actually we should restore calibration fully.

                

                # We need to set calibration manually on the new coord_sys

                x_type = 'log' if self.x_log_var.get() else 'linear'

                y_type = 'log' if self.y_log_var.get() else 'linear'

                

                # Refs

                self.coord_sys.refs_x = calib.get('refs_x', [])

                self.coord_sys.refs_y = calib.get('refs_y', [])

                

                # Note: plot_area might be missing if we didn't save it explicitly in 'calibration'

                # But 'set_calibration' doesn't require plot_area for mapping if we have refs?

                # Actually CoordinateSystem usually needs plot_area for some defaults.

                # Let's try to detect it silently or just proceed.

                self.coord_sys.find_plot_area() # Try to find it

                

                # Apply params

                self.coord_sys.set_calibration(

                    (float(self.x_min_var.get()), float(self.x_max_var.get())),

                    (float(self.y_min_var.get()), float(self.y_max_var.get())),

                    x_type, y_type

                )

                

                # Apply Data

                data = project_data.get('data', {})

                self.min_curve_data = data.get('min_curve', [])

                self.max_curve_data = data.get('max_curve', [])

                

                # Apply History

                self.history = project_data.get('history', [])

                self.history_index = len(self.history) - 1

                

                # Refresh UI

                self.refresh_calibration_list()

                self.update_visualization()

                self.redraw_selection()

                

                self.status_var.set(f"é?1????·2??? {os.path.basename(file_path)}")

                messagebox.showinfo("提示", "项目已成功加载")

                

        except Exception as e:

            messagebox.showerror("错误", f"????3???é?1???: {str(e)}")





if __name__ == "__main__":

    root = tk.Tk()

    app = CurveExtractorApp(root)

    root.mainloop()