import customtkinter as ctk
from core.logger import logger  # 这行会触发 setup_logging()
from core.ui import ModManagerUI
from core.logic import ModLogic
from core.config_manager import ConfigManager
import tkinter.filedialog as fd
import os
import psutil
import keyboard
import threading
import time
import sys

# 强制将工作目录切换到 EXE 所在的文件夹
if getattr(sys, 'frozen', False):
    # 如果是打包后的 EXE
    exe_dir = os.path.dirname(sys.executable)
    os.chdir(exe_dir)
    # 这一步非常重要：确保所有相对路径（./）都指向 EXE 旁边
    print(f"Locked WorkDir to EXE: {exe_dir}")

GAME_PROCESS_NAME = "ZenlessZoneZero.exe"

class MainController:
    def __init__(self):
        # 1. 初始化各组件
        self.config_mgr = ConfigManager()
        self.logic = ModLogic()
        
        # 2. 状态记录变量
        self.current_char = None      # 当前选中的角色名
        self.current_mod = None       # 当前点击查看的Mod信息(dict)
        self.inspected_widget = None  # 当前带有绿色边框的Mod组件(ModGridItem)
        
        # 3. 启动UI
        self.ui = ModManagerUI(self)
        
        # 1. 初始化热键
        self.hotkey_handle = None  # 新增：用于存储热键句柄
         # 从配置读取并注册
        self.refresh_hotkey_from_config()
        # self.current_hotkey = self.config_mgr.config.get("hotkey", "f7")
        # self.register_hotkey(self.current_hotkey)
        
         # 2. 启动进程监控线程
        self.stop_threads = False
        self.monitor_thread = threading.Thread(target=self.process_monitor, daemon=True)
        self.monitor_thread.start()
        
        # 初始状态：隐藏右侧栏
        self.ui.show_right_panel("", {}, is_visible=False)
        
        # 加载左侧角色列表
        self.refresh_all_data()
        
        self.ui.mainloop()
        self.stop_threads = True # 窗口关闭时标记线程停止
        
    def refresh_all_data(self):
        """2. 刷新按钮逻辑：重置状态并重扫描"""
        self.current_char = None
        self.current_mod = None
        self.inspected_widget = None
        
        # 重新渲染
        storage = self.config_mgr.config.get("storage_path", "./Mod_Storage")
        chars = self.logic.get_characters(storage)
        self.ui.render_char_list(chars, None)
        self.ui.render_mod_grid([])
        self.ui.show_right_panel("", {}, is_visible=False)
        print("Storage rescanned.")

    def refresh_all(self):
        """刷新整个界面数据"""
        storage = self.config_mgr.config.get("storage_path", "./Mod_Storage")
        chars = self.logic.get_characters(storage)
        # 渲染左侧，并根据当前选中角色进行高亮
        self.ui.render_char_list(chars, self.current_char)
        
    # --- 交互：文件夹操作 ---
    def open_current_mod_folder(self):
        """3. 打开对应Mod文件夹"""
        if self.current_mod:
            self.logic.open_in_explorer(self.current_mod['path'])
    

    def select_character(self, char_name):
        """当点击左侧角色时触发"""
        self.current_char = char_name
        self.inspected_widget = None # 切换角色时清空正在查看的状态
        
        # 刷新左侧黄色高亮状态
        self.refresh_all()
        
        # 获取该角色下所有Mod，并判断哪些是当前正在生效(Link)的
        storage = self.config_mgr.config.get("storage_path", "./Mod_Storage")
        xxmi_path = self.config_mgr.config.get("xxmi_mods_path")
        char_path = os.path.join(storage, char_name)
        
        mods = self.logic.get_mods_in_char(char_path)
        for m in mods:
            m['is_active'] = self.logic.is_mod_linked(m['path'], xxmi_path, char_name)
            
        # 渲染中间网格
        self.ui.render_mod_grid(mods)
        # 隐藏右侧详情栏
        self.ui.show_right_panel("", {}, is_visible=False)

    def show_mod_detail(self, mod_info, widget):
        """当单击中间Mod网格时触发：显示绿色边框和右侧详情"""
        # 处理绿色边框切换
        if self.inspected_widget:
            self.inspected_widget.set_inspected(False)
        self.inspected_widget = widget
        self.inspected_widget.set_inspected(True)

        self.current_mod = mod_info
        # 加载称谓和描述
        data = self.config_mgr.get_mod_data(mod_info['path'], mod_info['name'])
        self.ui.show_right_panel(mod_info['cover_path'], data, is_visible=True)

    def save_current_mod_info(self, name, desc):
        """持久化保存当前Mod的自定义称谓和描述"""
        if self.current_mod:
            self.config_mgr.save_mod_data(self.current_mod['path'], name, desc)
            # 同步更新中间网格的显示文字
            if self.inspected_widget:
                self.inspected_widget.name_label.configure(text=name)
            self.refresh_all()  # 刷新整个界面，确保所有地方都更新到最新数据

    def apply_selected_mod(self):
        """【修复】对应UI中的 APPLY MOD 按钮"""
        if not self.current_char or not self.current_mod:
            return
            
        # 在应用前，如果处于编辑模式，先保存文字
        name = self.ui.title_entry.get()
        desc = self.ui.desc_textbox.get("1.0", "end-1c")
        self.save_current_mod_info(name, desc)
        
        self.execute_apply(self.current_mod)

    def quick_apply(self, mod_info):
        """双击Mod网格时触发"""
        self.current_mod = mod_info
        # 双击也会尝试保存一下描述框内容
        name = self.ui.title_entry.get()
        desc = self.ui.desc_textbox.get("1.0", "end-1c")
        self.save_current_mod_info(name, desc)
        
        self.execute_apply(mod_info)

    def execute_apply(self, mod_info):
        """执行真正的文件挂载逻辑"""
        xxmi_path = self.config_mgr.config.get("xxmi_mods_path")
        if not xxmi_path or not os.path.exists(xxmi_path):
            from tkinter import messagebox
            messagebox.showwarning("配置缺失", "请先在 Setting 中设置正确的 XXMI Mods 文件夹路径！")
            return
            
        # 1. 移除旧链接
        self.logic.remove_char_junctions(xxmi_path, self.current_char)
        # 2. 创建新链接
        self.logic.create_junction(mod_info['path'], xxmi_path, self.current_char)
        
        # 3. 【核心新增】发送 F10 热重载信号给游戏
        # 使用 after(100, ...) 稍微延迟一下，确保系统IO已完成
        self.ui.after(100, lambda: keyboard.send('f10'))
        
        # 4. 重新加载中间网格状态（以更新黄色高亮）
        self.select_character(self.current_char)

    def deselect_current_char(self):
        """取消选择：移除该角色下的所有Mod链接"""
        if not self.current_char: return
        xxmi_path = self.config_mgr.config.get("xxmi_mods_path")
        self.logic.remove_char_junctions(xxmi_path, self.current_char)
        self.select_character(self.current_char)

    # --- 设置窗口升级：支持热键录入 ---
    def open_settings(self):
        dialog = ctk.CTkToplevel(self.ui)
        dialog.title("Settings")
        dialog.geometry("550x400")
        # dialog.attributes("-topmost", True)
        # --- 【关键修复：层级与焦点控制】 ---
        
        # A. 设置为临时窗口，使其永远依附于主窗口上方
        dialog.transient(self.ui) 
        
        # B. 强制将窗口提升到最前方
        dialog.lift() 
        
        # C. 锁定焦点（模态对话框）
        # 这会使用户在关闭设置窗口前无法点击主窗口，防止设置窗口丢到后面找不着
        dialog.grab_set() 
        
        # D. 如果你希望它在全屏游戏上方也能看到，可以保留这一行
        dialog.attributes("-topmost", True) 

        # ----------------------------------

        # --- XXMI 路径部分 (保持不变) ---
        ctk.CTkLabel(dialog, text="XXMI Mods 文件夹路径:", font=("Arial", 12)).pack(pady=(20, 5))
        path_var = ctk.StringVar(value=self.config_mgr.config["xxmi_mods_path"])
        ctk.CTkEntry(dialog, textvariable=path_var, width=400).pack(pady=5)
        ctk.CTkButton(dialog, text="浏览文件夹...", command=lambda: path_var.set(fd.askdirectory() or path_var.get())).pack()

        # --- 热键设置部分 (重构) ---
        ctk.CTkLabel(dialog, text="呼出热键设置:", font=("Arial", 12, "bold")).pack(pady=(30, 10))
        
        hk_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        hk_frame.pack(pady=5)

        # 1. 修饰键下拉框
        mod_options = ["None", "Ctrl", "Shift", "Alt"]
        current_mod = self.config_mgr.config.get("hotkey_modifier", "None")
        mod_cmbox = ctk.CTkComboBox(hk_frame, values=mod_options, width=100)
        mod_cmbox.set(current_mod)
        mod_cmbox.pack(side="left", padx=5)

        ctk.CTkLabel(hk_frame, text="+", font=("Arial", 16, "bold")).pack(side="left", padx=5)

        # 2. 基础键录入按钮
        current_base = self.config_mgr.config.get("hotkey_base_key", "f7")
        base_key_var = ctk.StringVar(value=current_base)

        def start_record():
            btn_record.configure(text="按下任意键...", fg_color="#E74C3C")
            dialog.update()
            # 屏蔽所有输入直到录入一个键
            event = keyboard.read_event(suppress=True)
            if event.event_type == "down":
                key_name = event.name
                # 过滤掉单独按下的修饰键
                if key_name in ['ctrl', 'shift', 'alt', 'left windows', 'right windows']:
                    btn_record.configure(text=base_key_var.get(), fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                    return
                base_key_var.set(key_name)
                btn_record.configure(text=key_name, fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        btn_record = ctk.CTkButton(hk_frame, text=base_key_var.get(), width=120, command=start_record)
        btn_record.pack(side="left", padx=5)

        # --- 保存逻辑 ---
        def save():
            new_mod = mod_cmbox.get()
            new_base = base_key_var.get()
            
            self.config_mgr.save_config({
                "xxmi_mods_path": path_var.get(),
                "hotkey_modifier": new_mod,
                "hotkey_base_key": new_base
            })
            
            # 立即生效
            self.refresh_hotkey_from_config()
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save & Apply", fg_color="green", height=40, command=save).pack(pady=40)
    
    
    def refresh_hotkey_from_config(self):
        """从配置拼接并注册热键"""
        mod = self.config_mgr.config.get("hotkey_modifier", "None")
        base = self.config_mgr.config.get("hotkey_base_key", "f7")
        
        # 拼接逻辑
        if mod == "None":
            full_key = base
        else:
            full_key = f"{mod.lower()}+{base}"
        
        self.register_hotkey(full_key)
    
     # --- 核心：进程与热键逻辑 ---
    def process_monitor(self):
        """后台监控绝区零进程"""
        game_running = False
        
        print("Waiting for ZZZ process...")
        print("self.stop_threads", self.stop_threads)
        while not self.stop_threads:
            found = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == GAME_PROCESS_NAME.lower():
                    found = True
                    break
            
            if found and not game_running:
                print("ZZZ Started! Manager Ready.")
                game_running = True
            elif not found and game_running:
                print("ZZZ Exited. Closing Manager.")
                self.ui.after(0, self.ui.destroy) # 自动结束
                break
            
            time.sleep(3)

    def register_hotkey(self, full_key):
        """安全注册热键"""
        try:
            if self.hotkey_handle is not None:
                try: keyboard.remove_hotkey(self.hotkey_handle)
                except: pass
            
            # 注册并保存句柄
            self.hotkey_handle = keyboard.add_hotkey(
                full_key, 
                lambda: self.ui.after(0, self.toggle_window)
            )
            print(f"Hotkey '{full_key}' registered.")
        except Exception as e:
            print(f"Hotkey failed: {e}")
    
    def toggle_window(self):
        """切换窗口呼出/隐藏"""
        if self.ui.state() == "normal":
            self.ui.withdraw()
            logger.info("Manager hidden to background.")
        else:
             # 如果窗口是隐藏的，则呼出并置顶
            self.ui.deiconify()
            self.ui.attributes("-topmost", True)
            self.ui.focus_force()
            # 呼出时顺便刷新一下，确保数据最新
            self.refresh_all()
            logger.info("Manager restored from background.")

if __name__ == "__main__":
    MainController()