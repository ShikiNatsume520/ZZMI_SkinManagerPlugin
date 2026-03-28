import os
import subprocess
import keyboard

class ModLogic:
    @staticmethod
    def get_characters(storage_path):
        """获取所有角色文件夹信息"""
        chars = []
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        
        for name in os.listdir(storage_path):
            full_path = os.path.join(storage_path, name)
            if os.path.isdir(full_path):
                icon_path = os.path.join(full_path, "character.png")
                chars.append({
                    "name": name,
                    "path": full_path,
                    "icon_path": icon_path if os.path.exists(icon_path) else "assets/default_char.png"
                })
        return sorted(chars, key=lambda x: x['name'])

    @staticmethod
    def get_mods_in_char(char_path):
        """获取角色下的所有Mod文件夹"""
        mods = []
        for name in os.listdir(char_path):
            full_path = os.path.join(char_path, name)
            if os.path.isdir(full_path):
                cover_path = os.path.join(full_path, "cover.png")
                mods.append({
                    "name": name,
                    "path": full_path,
                    "cover_path": cover_path if os.path.exists(cover_path) else "assets/default_cover.png"
                })
        return mods

    @staticmethod
    def remove_char_junctions(xxmi_mods_path, char_name):
        """清除XXMI对应角色目录下的所有链接"""
        target_dir = os.path.join(xxmi_mods_path, char_name)
        if not os.path.exists(target_dir):
            return
        
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            # 仅删除交汇点目录
            if os.path.isdir(item_path):
                try:
                    # Windows下删除Junction目录
                    subprocess.run(f'rmdir "{item_path}"', shell=True)
                except: pass

    @staticmethod
    def create_junction(src_path, xxmi_mods_path, char_name):
        """创建目录交汇点"""
        mod_name = os.path.basename(src_path)
        dest_dir = os.path.join(xxmi_mods_path, char_name)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, mod_name)

        # 执行mklink /J
        cmd = f'mklink /J "{dest_path}" "{src_path}"'
        subprocess.run(cmd, shell=True, capture_output=True)
        
        # 发送F10热重载
        keyboard.send('f10')

    @staticmethod
    def is_mod_linked(src_path, xxmi_mods_path, char_name):
        """判断Mod是否已挂载"""
        mod_name = os.path.basename(src_path)
        dest_path = os.path.join(xxmi_mods_path, char_name, mod_name)
        return os.path.exists(dest_path)
    
    @staticmethod
    def open_in_explorer(path):
        """调用资源管理器打开指定路径"""
        if os.path.exists(path):
            os.startfile(path) # Windows 特有快捷方法