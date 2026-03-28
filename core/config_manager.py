import json
import os

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        # 默认配置：如果文件不存在则使用这些
        self.default_config = {
            "xxmi_mods_path": "../ZZMI/Mods",      # XXMI的Mods文件夹路径
            "storage_path": "./Mod_Storage", # 用户存放Mod的仓库路径
            "hotkey_modifier": "None", # 可选: None, Ctrl, Shift, Alt
            "hotkey_base_key": "f7",
            "theme": "dark"
        }
        self.config = self.load_config()

    # ================= 全局配置 (config.json) 相关 =================

    def load_config(self):
        """加载全局配置文件"""
        if not os.path.exists(self.config_path):
            # 如果不存在，则创建一个默认的
            self._write_json(self.config_path, self.default_config)
            return self.default_config
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保默认键都存在（防止旧版本配置缺少新字段）
                for key, value in self.default_config.items():
                    if key not in data:
                        data[key] = value
                return data
        except Exception as e:
            print(f"读取配置失败: {e}")
            return self.default_config

    def save_config(self, new_config_items):
        """保存全局配置，new_config_items 为字典"""
        self.config.update(new_config_items)
        self._write_json(self.config_path, self.config)

    # ================= Mod元数据 (desc.json) 相关 =================

    def get_mod_data(self, mod_path, folder_name):
        """
        获取特定Mod的详细数据。
        如果文件夹内没有 desc.json，则生成默认数据（称谓默认为文件夹名）。
        """
        desc_file = os.path.join(mod_path, "desc.json")
        
        # 默认返回的数据结构
        mod_data = {
            "display_name": folder_name,
            "description": "双击此处编辑关于该Mod的描述信息内容..."
        }

        if os.path.exists(desc_file):
            try:
                with open(desc_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    # 将读取到的数据合并到默认数据中
                    mod_data.update(saved_data)
            except Exception as e:
                print(f"读取Mod描述失败 {mod_path}: {e}")
        
        return mod_data

    def save_mod_data(self, mod_path, display_name, description):
        """持久化保存某个Mod的自定义称谓和描述"""
        desc_file = os.path.join(mod_path, "desc.json")
        data_to_save = {
            "display_name": display_name,
            "description": description
        }
        try:
            self._write_json(desc_file, data_to_save)
            print(f"成功保存数据到: {desc_file}")
        except Exception as e:
            print(f"保存Mod描述失败: {e}")

    # ================= 内部通用方法 =================

    def _write_json(self, file_path, data):
        """通用的写入JSON方法，确保缩进和中文显示"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # ensure_ascii=False 保证中文正常存储，indent=4 方便人类阅读
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"文件写入异常 {file_path}: {e}")