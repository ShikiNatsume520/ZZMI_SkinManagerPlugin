import customtkinter as ctk
from PIL import Image
import os
import sys

def resource_path(relative_path):
    """ 获取资源的绝对路径，适配开发和 PyInstaller 环境 """
    if hasattr(sys, '_MEIPASS'):
        # 打包后的路径（临时文件夹或 _internal）
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境下的路径
    return os.path.abspath(os.path.join(os.getcwd(), relative_path))

class ModManagerUI(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("ZZMI Pro Mod Manager")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        
        self.set_window_icon()  # 设置窗口图标
        
        self.protocol("WM_DELETE_WINDOW", self.controller.toggle_window)
        
        self.withdraw() 
        self.is_editing = False
        
        # --- 重要：增加一个属性来持有图片引用，防止垃圾回收 ---
        self.detail_image_storage = None 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_top_bar()

        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=2)
        self.main_container.grid_columnconfigure(1, weight=5)
        self.main_container.grid_columnconfigure(2, weight=3)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.create_left_column()
        self.create_middle_column()
        self.create_right_column()
        
        self.bind_all("<Double-Button-1>", self.on_global_double_click)
        
    
    def set_window_icon(self):
        """ 设置窗口左上角及任务栏图标 """
        try:
            # 使用之前定义的 resource_path 寻找图标
            icon_p = resource_path("app.ico")
            
            if os.path.exists(icon_p):
                # Windows 平台特有方法，设置 .ico 图标
                self.iconbitmap(icon_p)
            else:
                print(f"Icon file not found at: {icon_p}")
        except Exception as e:
            # 捕获异常防止因为图标问题导致整个程序无法启动
            print(f"Failed to set window icon: {e}")

    def create_top_bar(self):
        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.settings_btn = ctk.CTkButton(self.top_bar, text="Setting", width=100, command=self.controller.open_settings)
        self.settings_btn.pack(side="left", padx=10, pady=5)
        
        self.refresh_btn = ctk.CTkButton(self.top_bar, text="Refresh_Storage", width=120, fg_color="#2b719e", command=self.controller.refresh_all_data)
        self.refresh_btn.pack(side="left", padx=10, pady=5)

    def create_left_column(self):
        self.left_frame = ctk.CTkScrollableFrame(self.main_container, label_text="Characters")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
    def create_middle_column(self):
        self.middle_container = ctk.CTkFrame(self.main_container)
        self.middle_container.grid(row=0, column=1, sticky="nsew", padx=5)
        self.middle_container.grid_rowconfigure(0, weight=1) 
        self.middle_container.grid_columnconfigure(0, weight=1)

        self.middle_grid = ctk.CTkScrollableFrame(self.middle_container, label_text="Available Mods")
        self.middle_grid.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.middle_grid._parent_canvas.grid_columnconfigure((0, 1, 2), weight=1)

        self.deselect_btn = ctk.CTkButton(
            self.middle_container, text="❌ Deselect All Mods", 
            fg_color="#444", hover_color="#333", height=40,
            command=self.controller.deselect_current_char
        )
        self.deselect_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

    def create_right_column(self):
        self.right_frame = ctk.CTkFrame(self.main_container)
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        self.details_inner_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")

        self.title_entry = ctk.CTkEntry(self.details_inner_frame, font=("Arial", 18, "bold"), 
                                        fg_color="transparent", border_width=0, justify="center")
        self.title_entry.pack(pady=10, fill="x")
        self.title_entry.configure(state="disabled") 
        self.title_entry.bind("<Double-Button-1>", lambda e: self.enable_edit(self.title_entry))

        self.detail_image_label = ctk.CTkLabel(self.details_inner_frame, text="")
        self.detail_image_label.pack(pady=5)

        self.desc_textbox = ctk.CTkTextbox(self.details_inner_frame, wrap="word", font=("Arial", 12))
        self.desc_textbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.desc_textbox.configure(state="disabled") 
        self.desc_textbox.bind("<Double-Button-1>", lambda e: self.enable_edit(self.desc_textbox))
        
        btn_container = ctk.CTkFrame(self.details_inner_frame, fg_color="transparent")
        btn_container.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.open_folder_btn = ctk.CTkButton(btn_container, text="FOLDER", width=60, height=50, fg_color="#555", command=self.controller.open_current_mod_folder)
        self.open_folder_btn.pack(side="left", padx=(0, 5))

        self.apply_btn = ctk.CTkButton(btn_container, text="APPLY MOD", height=50, font=("Arial", 14, "bold"), command=self.controller.apply_selected_mod)
        self.apply_btn.pack(side="right", fill="x", expand=True)

    def enable_edit(self, widget):
        widget.configure(state="normal")
        widget.focus_set()
        self.is_editing = True
        return "break"

    def on_global_double_click(self, event):
        if self.is_editing:
            try:
                if event.widget not in [self.title_entry._canvas, self.desc_textbox._textbox]:
                    self.save_and_lock_edits()
            except:
                self.save_and_lock_edits()
    
    def save_and_lock_edits(self):
        self.title_entry.configure(state="disabled")
        self.desc_textbox.configure(state="disabled")
        self.is_editing = False
        self.controller.save_current_mod_info(
            self.title_entry.get(),
            self.desc_textbox.get("1.0", "end-1c")
        )

    def render_char_list(self, characters, active_name=None):
        for widget in self.left_frame.winfo_children():
            widget.destroy()
        for char in characters:
            is_active = (char['name'] == active_name)
            btn = CharacterItem(
                self.left_frame, char['name'], char['icon_path'], is_active,
                command=lambda c=char['name']: self.controller.select_character(c)
            )
            btn.pack(fill="x", pady=2)

    def render_mod_grid(self, mods, active_mod_path=None):
        for widget in self.middle_grid.winfo_children():
            widget.destroy()
        for i, mod in enumerate(mods):
            is_active = mod.get('is_active', False)
            # --- 修复：on_click 接收两个参数，不在此处赋值 it=mod ---
            item = ModGridItem(
                self.middle_grid, mod, is_active,
                on_click=lambda m, it: self.controller.show_mod_detail(m, it),
                on_double_click=lambda m: self.controller.quick_apply(m)
            )
            item.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")

    def show_right_panel(self, cover_path, mod_data, is_visible=True):
        if is_visible:
            self.details_inner_frame.pack(fill="both", expand=True)
            try:
                img = Image.open(cover_path)
                # --- 修复：保持引用 ---
                self.detail_image_storage = ctk.CTkImage(img, size=(180, 360))
                self.detail_image_label.configure(image=self.detail_image_storage)
            except Exception as e:
                print(f"Error loading detail image: {e}")
            
            self.title_entry.configure(state="normal")
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, mod_data.get('display_name', 'Unknown'))
            self.title_entry.configure(state="disabled")
            
            self.desc_textbox.configure(state="normal")
            self.desc_textbox.delete("1.0", "end")
            self.desc_textbox.insert("1.0", mod_data.get('description', ''))
            self.desc_textbox.configure(state="disabled")
            self.update_idletasks() # 强制刷新UI布局
        else:
            self.details_inner_frame.pack_forget()

# --- 列表项组件 ---

class CharacterItem(ctk.CTkFrame):
    def __init__(self, master, name, icon_path, is_active, command):
        bg_color = "#FFCC00" if is_active else "transparent"
        text_color = "black" if is_active else "white"
        super().__init__(master, fg_color=bg_color, cursor="hand2", corner_radius=6)
        
        # 确保路径存在，否则用资源路径下的默认图
        final_icon = icon_path if os.path.exists(icon_path) else resource_path("assets/default_char.png")
        img = Image.open(final_icon)
        self.photo = ctk.CTkImage(img, size=(45, 45))
        
        self.img_label = ctk.CTkLabel(self, image=self.photo, text="")
        self.img_label.pack(side="left", padx=10, pady=5)
        
        self.name_label = ctk.CTkLabel(self, text=name, text_color=text_color, font=("Arial", 14, "bold"))
        self.name_label.pack(side="left", padx=5)
        
        for w in [self, self.img_label, self.name_label]:
            w.bind("<Button-1>", lambda e: command())

class ModGridItem(ctk.CTkFrame):
    def __init__(self, master, mod_info, is_active, on_click, on_double_click):
        border_color = "#FFCC00" if is_active else "#333"
        bg_color = "#FFCC00" if is_active else "transparent"
        text_color = "black" if is_active else "white"
        
        super().__init__(master, corner_radius=10, border_width=2, border_color=border_color, fg_color=bg_color)
        
        # 封面路径
        raw_cover = os.path.join(mod_info['path'], "cover.png")
        final_cover = raw_cover if os.path.exists(raw_cover) else resource_path("assets/default_cover.png")
        
        img = Image.open(final_cover)
        self.photo = ctk.CTkImage(img, size=(100, 200)) 
        
        self.img_label = ctk.CTkLabel(self, image=self.photo, text="")
        self.img_label.pack(pady=(12, 5), padx=10)
        
        self.name_label = ctk.CTkLabel(self, text=mod_info['name'], text_color=text_color, font=("Arial", 11, "bold"), wraplength=100)
        self.name_label.pack(pady=(0, 10))
        
        # --- 这里的绑定是正确的：传递 (mod_info, self) ---
        self.bind("<Button-1>", lambda e: on_click(mod_info, self))
        self.bind("<Double-Button-1>", lambda e: on_double_click(mod_info))

        for w in [self.img_label, self.name_label]:
            w.bind("<Button-1>", lambda e: on_click(mod_info, self))
            w.bind("<Double-Button-1>", lambda e: on_double_click(mod_info))
            
    def set_inspected(self, is_inspected):
        if is_inspected:
            self.configure(border_color="#2ECC71")
        else:
            active_color = "#FFCC00" if self.cget("fg_color") == "#FFCC00" else "#333"
            self.configure(border_color=active_color)