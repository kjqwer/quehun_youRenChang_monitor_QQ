import win32gui
import win32ui
import win32con
import ctypes
import cv2
import numpy as np
import json
import os
from PIL import Image
import gc
import win32api
import comtypes
import comtypes.client
import time

# 导入DWM API
try:
    from ctypes.wintypes import RECT, DWORD, HWND, HRESULT, BOOL
    from comtypes.automation import POINTER

    # DWM缩略图API定义
    DWMAPI = ctypes.WinDLL('dwmapi')
    THUMBNAILID = ctypes.c_ulonglong

    class DWM_THUMBNAIL_PROPERTIES(ctypes.Structure):
        _fields_ = [
            ('dwFlags', DWORD),
            ('rcDestination', RECT),
            ('rcSource', RECT),
            ('opacity', ctypes.c_byte),
            ('fVisible', BOOL),
            ('fSourceClientAreaOnly', BOOL),
        ]

    # 定义DWM API函数
    DWMAPI.DwmRegisterThumbnail.restype = HRESULT
    DWMAPI.DwmRegisterThumbnail.argtypes = [HWND, HWND, POINTER(THUMBNAILID)]
    
    DWMAPI.DwmUpdateThumbnailProperties.restype = HRESULT
    DWMAPI.DwmUpdateThumbnailProperties.argtypes = [THUMBNAILID, POINTER(DWM_THUMBNAIL_PROPERTIES)]
    
    DWMAPI.DwmUnregisterThumbnail.restype = HRESULT
    DWMAPI.DwmUnregisterThumbnail.argtypes = [THUMBNAILID]
    
    # 定义DWM常量
    DWM_TNP_VISIBLE = 0x8
    DWM_TNP_RECTDESTINATION = 0x1
    DWM_TNP_RECTSOURCE = 0x2
    
    HAS_DWM_SUPPORT = True
except:
    HAS_DWM_SUPPORT = False
    print("DWM支持加载失败，将使用备用捕获方法")

class WindowCapture:
    """窗口捕获类，负责窗口截图和区域选择"""
    
    def __init__(self):
        """初始化窗口捕获"""
        self.selected_window = None
        self.crop_area = None
        self.crop_area_file = 'last_crop_area.txt'
        self.use_background_capture = True  # 默认使用背景捕获模式
        
        # 检查捕获功能
        self.check_capture_capabilities()
    
    def check_capture_capabilities(self):
        """检查捕获功能的支持情况"""
        capabilities = {
            "基础窗口API": True,  # 总是支持
            "PrintWindow": self.check_printwindow_support(),
            "DWM缩略图": HAS_DWM_SUPPORT
        }
        
        print("窗口捕获功能支持检查:")
        for feature, supported in capabilities.items():
            status = "支持" if supported else "不支持"
            print(f"  - {feature}: {status}")
        
        # 至少要有一种背景捕获方法可用
        if not capabilities["PrintWindow"] and not capabilities["DWM缩略图"]:
            print("警告: 所有背景捕获方法均不可用，将只能使用前台模式捕获窗口")
            self.use_background_capture = False
    
    def check_printwindow_support(self):
        """检查PrintWindow API是否支持高级选项"""
        try:
            # 创建一个测试窗口
            test_hwnd = win32gui.GetDesktopWindow()
            dc = win32gui.GetWindowDC(test_hwnd)
            mfcDC = win32ui.CreateDCFromHandle(dc)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, 1, 1)
            saveDC.SelectObject(saveBitMap)
            
            # 尝试使用PrintWindow
            result = ctypes.windll.user32.PrintWindow(test_hwnd, saveDC.GetSafeHdc(), 2)
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(test_hwnd, dc)
            
            return result != 0
        except:
            return False
    
    def get_window_list(self):
        """获取所有可见窗口列表"""
        windows = []
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((title, hwnd))
        win32gui.EnumWindows(enum_windows_callback, None)
        return windows
    
    def find_window_by_title(self, title):
        """根据标题查找窗口"""
        windows = self.get_window_list()
        for window_title, hwnd in windows:
            if title in window_title:
                return hwnd
        return None
    
    def capture_window(self, hwnd):
        """截图窗口内容"""
        if self.use_background_capture:
            return self.capture_window_background(hwnd)
        else:
            return self.capture_window_foreground(hwnd)
    
    def capture_window_foreground(self, hwnd):
        """使用前台模式截图窗口内容（需要窗口置顶）"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            # 确保资源释放
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            return im
        except Exception as e:
            print(f"前台截图过程出错: {str(e)}")
            # 确保资源释放
            try:
                if 'saveBitMap' in locals():
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                if 'saveDC' in locals():
                    saveDC.DeleteDC()
                if 'mfcDC' in locals():
                    mfcDC.DeleteDC()
                if 'hwndDC' in locals():
                    win32gui.ReleaseDC(hwnd, hwndDC)
            except:
                pass
            return None
            
    def capture_window_background(self, hwnd):
        """使用背景模式截图窗口内容（不需要窗口置顶，即使被遮挡也能获取内容）"""
        try:
            # 首先检查窗口是否存在
            if not win32gui.IsWindow(hwnd):
                print("窗口不存在或已关闭")
                return None
                
            # 尝试使用PrintWindow API
            im = self.capture_using_printwindow(hwnd)
            if im is not None:
                return im
                
            # 如果PrintWindow失败，尝试DWM缩略图捕获
            print("PrintWindow失败，尝试DWM缩略图捕获...")
            im = self.capture_using_dwm(hwnd)
            if im is not None:
                return im
                
            # 如果两种方法都失败，尝试最后的方案
            print("所有背景捕获方式都失败，尝试前台模式...")
            return self.capture_window_foreground(hwnd)
            
        except Exception as e:
            print(f"背景截图过程出错: {str(e)}")
            print("尝试使用前台模式截图...")
            return self.capture_window_foreground(hwnd)
    
    def capture_using_printwindow(self, hwnd):
        """使用PrintWindow API捕获窗口内容"""
        try:
            # 获取窗口位置和大小
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # 获取窗口DC
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 使用PrintWindow捕获窗口内容，使用PW_RENDERFULLCONTENT标志(2)能捕获整个窗口内容
            # 即使窗口被覆盖或最小化
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            
            if result == 0:
                # PrintWindow失败
                self.clean_dc_resources(saveBitMap, saveDC, mfcDC, hwndDC, hwnd)
                return None
            
            # 获取位图信息
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 创建PIL图片对象
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # 清理资源
            self.clean_dc_resources(saveBitMap, saveDC, mfcDC, hwndDC, hwnd)
            
            return im
        except Exception as e:
            print(f"PrintWindow捕获失败: {str(e)}")
            return None
    
    def clean_dc_resources(self, bitmap, dc, mfcDC, hwndDC, hwnd):
        """清理DC资源，避免内存泄漏"""
        try:
            if bitmap:
                win32gui.DeleteObject(bitmap.GetHandle())
            if dc:
                dc.DeleteDC()
            if mfcDC:
                mfcDC.DeleteDC()
            if hwndDC and hwnd:
                win32gui.ReleaseDC(hwnd, hwndDC)
        except Exception as e:
            print(f"清理DC资源时出错: {str(e)}")
    
    def capture_using_dwm(self, hwnd):
        """使用DWM缩略图API捕获窗口内容"""
        if not HAS_DWM_SUPPORT:
            return None
        
        try:
            # 创建目标DC
            desk_hwnd = win32gui.GetDesktopWindow()
            desk_dc = win32gui.GetWindowDC(desk_hwnd)
            dest_dc = win32ui.CreateDCFromHandle(desk_dc)
            mem_dc = dest_dc.CreateCompatibleDC()
            
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width, height = right - left, bottom - top
            
            # 创建位图
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(dest_dc, width, height)
            mem_dc.SelectObject(bitmap)
            
            # 注册缩略图
            thumbnail_id = ctypes.c_ulonglong(0)
            ret = DWMAPI.DwmRegisterThumbnail(
                desk_hwnd, hwnd, ctypes.byref(thumbnail_id)
            )
            
            if ret != 0:
                print(f"DWM注册缩略图失败: {ret}")
                return None
            
            # 设置缩略图属性
            props = DWM_THUMBNAIL_PROPERTIES()
            props.dwFlags = DWM_TNP_VISIBLE | DWM_TNP_RECTDESTINATION | DWM_TNP_RECTSOURCE
            props.fVisible = True
            
            # 设置源区域为整个窗口
            props.rcSource.left = 0
            props.rcSource.top = 0
            props.rcSource.right = width
            props.rcSource.bottom = height
            
            # 设置目标位置
            props.rcDestination.left = 0
            props.rcDestination.top = 0
            props.rcDestination.right = width
            props.rcDestination.bottom = height
            
            # 更新缩略图属性
            ret = DWMAPI.DwmUpdateThumbnailProperties(thumbnail_id, ctypes.byref(props))
            if ret != 0:
                print(f"DWM更新缩略图属性失败: {ret}")
                DWMAPI.DwmUnregisterThumbnail(thumbnail_id)
                return None
            
            # 等待缩略图渲染完成
            time.sleep(0.1)
            
            # 复制到位图
            mem_dc.BitBlt((0, 0), (width, height), dest_dc, (0, 0), win32con.SRCCOPY)
            
            # 取消注册缩略图
            DWMAPI.DwmUnregisterThumbnail(thumbnail_id)
            
            # 获取位图数据
            bitmap_info = bitmap.GetInfo()
            bitmap_bits = bitmap.GetBitmapBits(True)
            
            # 创建PIL图像
            image = Image.frombuffer(
                'RGB',
                (bitmap_info['bmWidth'], bitmap_info['bmHeight']),
                bitmap_bits, 'raw', 'BGRX', 0, 1
            )
            
            # 清理资源
            win32gui.DeleteObject(bitmap.GetHandle())
            mem_dc.DeleteDC()
            dest_dc.DeleteDC()
            win32gui.ReleaseDC(desk_hwnd, desk_dc)
            
            return image
            
        except Exception as e:
            print(f"使用DWM捕获窗口失败: {str(e)}")
            return None
    
    def toggle_capture_mode(self):
        """切换截图模式"""
        self.use_background_capture = not self.use_background_capture
        mode = "背景模式（无需窗口置顶）" if self.use_background_capture else "前台模式（需要窗口置顶）"
        print(f"已切换截图模式: {mode}")
        return self.use_background_capture
    
    def select_monitor_area(self):
        """选择监控区域"""
        if not self.selected_window:
            print("请先选择监控窗口")
            return False
            
        # 获取窗口截图
        image = self.capture_window(self.selected_window)
        if image is None:
            print("无法捕获窗口内容")
            return False
            
        img_np = np.array(image)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        # 创建窗口并选择ROI
        cv2.namedWindow('Select Region', cv2.WINDOW_NORMAL)
        print("请用鼠标选择监控区域，选择完成后按Enter键确认")
        roi = cv2.selectROI('Select Region', img_cv, False)
        cv2.destroyAllWindows()
        
        # 释放图像资源
        del img_np
        del img_cv
        del image
        gc.collect()  # 强制回收
        
        # 转换ROI格式
        x, y, w, h = roi
        if w > 0 and h > 0:  # 确保选择了有效区域
            self.crop_area = (x, y, x + w, y + h)
            print(f"已选择监控区域: {self.crop_area}")
            
            # 保存裁剪区域到文件
            try:
                with open(self.crop_area_file, 'w') as f:
                    json.dump(list(self.crop_area), f)
                print("已保存监控区域设置")
                return True
            except Exception as e:
                print(f"保存监控区域失败: {str(e)}")
                return False
        else:
            print("未选择有效的监控区域，请重试")
            return False
    
    def load_crop_area(self):
        """加载上次保存的裁剪区域"""
        try:
            if os.path.exists(self.crop_area_file):
                with open(self.crop_area_file, 'r') as f:
                    self.crop_area = tuple(json.load(f))
                print(f"已加载上次的监控区域: {self.crop_area}")
                return True
            return False
        except Exception as e:
            print(f"加载监控区域失败: {str(e)}")
            return False
    
    def get_cropped_image(self):
        """捕获窗口并裁剪指定区域"""
        if not self.selected_window or not self.crop_area:
            print("未设置监控窗口或区域")
            return None
            
        # 多次尝试捕获窗口
        max_retries = 3
        for i in range(max_retries):
            image = self.capture_window(self.selected_window)
            if image is not None:
                break
            print(f"捕获失败，重试 ({i+1}/{max_retries})...")
            time.sleep(0.5)
        
        if image is None:
            print("多次尝试捕获窗口失败")
            return None
            
        try:
            cropped_image = image.crop(self.crop_area)
            # 释放原始图像资源
            del image
            return cropped_image
        except Exception as e:
            print(f"裁剪图像失败: {str(e)}")
            return None
    
    def toggle_window_topmost(self, hwnd):
        """切换窗口的置顶状态
        
        Args:
            hwnd: 要操作的窗口句柄
            
        Returns:
            bool: 操作后窗口是否置顶
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            print("窗口无效，无法更改置顶状态")
            return False
            
        # 获取窗口当前样式
        current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        is_topmost = (current_style & win32con.WS_EX_TOPMOST) != 0
        
        # 切换置顶状态
        if is_topmost:
            # 取消置顶
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_NOTOPMOST, 
                0, 0, 0, 0, 
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            print(f"已取消窗口置顶")
            return False
        else:
            # 设置置顶
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 
                0, 0, 0, 0, 
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            print(f"已设置窗口置顶")
            return True
    
    def is_window_topmost(self, hwnd):
        """检查窗口是否置顶
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 窗口是否置顶
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
            
        # 获取窗口当前样式
        current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        is_topmost = (current_style & win32con.WS_EX_TOPMOST) != 0
        return is_topmost 