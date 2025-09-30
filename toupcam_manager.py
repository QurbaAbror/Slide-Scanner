#!/usr/bin/env python3
"""
Toupcam Streaming Module for NiceGUI
Converted from PyQt implementation to work with NiceGUI
"""

import asyncio
import threading
import base64
import time
import numpy as np
from typing import Optional, Callable
from nicegui import ui

try:
    import toupcam
    TOUPCAM_AVAILABLE = True
    print("Toupcam SDK loaded successfully")
except ImportError:
    try:
        import toupcam
        TOUPCAM_AVAILABLE = True
        print("Toupcam SDK loaded from system")
    except ImportError:
        print("Warning: Toupcam SDK not found. Main camera will not work.")
        TOUPCAM_AVAILABLE = False

class ToupcamStream:
    def __init__(self):
        """Initialize Toupcam stream"""
        self.hcam = None
        self.pData = None
        self.imgWidth = 0
        self.imgHeight = 0
        self.is_running = False
        self.cur = None
        self.res = 0

        # Threading control
        self.lock = threading.Lock()
        self.frame_callback: Optional[Callable] = None
        self.fps_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.current_frame = None

        # FPS tracking
        self.fps_timer_thread = None
        self.fps_stop_event = threading.Event()

        # Frame counting
        self.frame_count = 0
        
    def set_frame_callback(self, callback: Callable):
        """Set callback function to receive frames"""
        self.frame_callback = callback
    
    def set_fps_callback(self, callback: Callable):
        """Set callback function to receive FPS updates"""
        self.fps_callback = callback

    def set_error_callback(self, callback: Callable):
        """Set callback function to receive error messages"""
        self.error_callback = callback
    
    def initialize_camera(self) -> bool:
        """Initialize Toupcam camera - following main_cam.py pattern"""
        if not TOUPCAM_AVAILABLE:
            if self.error_callback:
                self.error_callback("Toupcam SDK not available")
            return False

        try:
            # Find cameras - exactly like main_cam.py
            arr = toupcam.Toupcam.EnumV2()
            if not arr:
                error_msg = "Tidak ada kamera Toupcam yang ditemukan."
                print(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False

            # Open first camera - exactly like main_cam.py
            self.cur = arr[0]
            self.hcam = toupcam.Toupcam.Open(self.cur.id)

            if not self.hcam:
                error_msg = f"Gagal membuka kamera: {self.cur.displayname}"
                print(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False

            # Get resolution - exactly like main_cam.py
            self.res = self.hcam.get_eSize()
            self.imgWidth = self.cur.model.res[self.res].width
            self.imgHeight = self.cur.model.res[self.res].height

            # Configure camera - exactly like main_cam.py
            self.hcam.put_Option(toupcam.TOUPCAM_OPTION_BYTEORDER, 0)

            # Real-time mode - exactly like main_cam.py
            try:
                self.hcam.put_RealTime(1)  # 1 = realtime (drop pending frames)
                print("[CAM] RealTime mode set to 1 (drop pending frames)")
            except Exception as e:
                print(f"[CAM] Failed to set RealTime mode: {e}")

            # Allocate buffer - exactly like main_cam.py
            buffer_size = toupcam.TDIBWIDTHBYTES(self.imgWidth * 24) * self.imgHeight
            self.pData = bytes(buffer_size)

            # Set vertical flip - exactly like main_cam.py
            self.hcam.put_VFlip(1)

            print(f"Toupcam initialized: {self.cur.displayname}")
            print(f"Resolution: {self.imgWidth}x{self.imgHeight}")

            return True

        except Exception as e:
            error_msg = f"Error initializing Toupcam: {e}"
            print(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def start_stream(self) -> bool:
        """Start Toupcam streaming - following main_cam.py pattern"""
        if not self.hcam:
            return False

        if self.is_running:
            print("Peringatan: Perintah start diterima, tetapi kamera sudah berjalan.")
            return True

        try:
            # Start pull mode with callback - exactly like main_cam.py
            self.hcam.StartPullModeWithCallback(self.event_callback, self)
            self.is_running = True

            # Start FPS timer
            self.start_fps_timer()

            print("Toupcam stream started")
            return True

        except toupcam.HRESULTException as e:
            self.stop_stream()
            error_msg = f"Gagal memulai pull mode: {e}"
            print(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error starting Toupcam stream: {e}"
            print(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def stop_stream(self):
        """Stop Toupcam streaming - following main_cam.py pattern"""
        if not self.is_running:
            return

        print("Stopping Toupcam stream...")

        # Signal threads to stop
        self.is_running = False
        self.fps_stop_event.set()

        # Wait for FPS timer thread to finish
        if self.fps_timer_thread and self.fps_timer_thread.is_alive():
            self.fps_timer_thread.join(timeout=2.0)

        # Close camera - exactly like main_cam.py
        if self.hcam:
            try:
                self.hcam.Close()
            except:
                pass
            self.hcam = None

        self.pData = None
        print("Toupcam stream stopped")
    
    def start_fps_timer(self):
        """Start FPS monitoring timer - following main_cam.py pattern"""
        def fps_update():
            while self.is_running and self.hcam and not self.fps_stop_event.is_set():
                try:
                    if self.hcam and self.is_running:
                        nFrame, nTime, nTotalFrame = self.hcam.get_FrameRate()
                        fps_val = (nFrame * 1000.0 / nTime) if nTime > 0 else 0.0
                        fps_text = f"Total Frames: {nTotalFrame}, FPS: {fps_val:.1f}"

                        if self.fps_callback:
                            self.fps_callback(fps_text)

                except Exception as e:
                    print(f"Error getting FPS: {e}")

                # Wait for 1 second or until stop event
                if self.fps_stop_event.wait(1.0):
                    break

        # Start FPS monitoring in separate thread
        self.fps_stop_event.clear()
        self.fps_timer_thread = threading.Thread(target=fps_update, daemon=True)
        self.fps_timer_thread.start()
    
    @staticmethod
    def event_callback(nEvent, self_obj):
        """Static callback for Toupcam events"""
        if self_obj and self_obj.is_running:
            self_obj.handle_event(nEvent)
    
    def handle_event(self, nEvent):
        """Handle Toupcam events - following main_cam.py pattern"""
        if not self.is_running:
            return

        if nEvent == toupcam.TOUPCAM_EVENT_IMAGE:
            self.handle_image_event()
        elif nEvent == toupcam.TOUPCAM_EVENT_STILLIMAGE:
            self.handle_still_image_event()
        elif nEvent == toupcam.TOUPCAM_EVENT_ERROR or nEvent == toupcam.TOUPCAM_EVENT_DISCONNECTED:
            error_msg = f"Kamera error atau terputus (event: {nEvent})."
            print(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            self.stop_stream()
    
    def handle_image_event(self):
        """Handle new image from Toupcam - SIMPLIFIED and FIXED"""
        try:
            # Pull image data - exactly like main_cam.py
            self.hcam.PullImageV4(self.pData, 0, 24, 0, None)

            # Convert to numpy array - exactly like main_cam.py
            image_np = np.frombuffer(self.pData, dtype=np.uint8).reshape((self.imgHeight, self.imgWidth, 3))

            # Simple validation
            if image_np is not None and image_np.size > 0:
                # Store current frame with thread safety
                with self.lock:
                    self.current_frame = image_np.copy()
                    self.frame_count += 1

                # Debug info every 200 frames
                if self.frame_count % 200 == 0:
                    print(f"Toupcam: {self.frame_count} frames processed")

        except toupcam.HRESULTException as e:
            print(f"Exception di handleImageEvent: {e}")
        except Exception as e:
            print(f"Error in Toupcam handleImageEvent: {e}")

    def handle_still_image_event(self):
        """Handle still image capture event"""
        try:
            print("Still image captured successfully")
            # TODO: Implement still image handling if needed
        except Exception as e:
            print(f"Error in handleStillImageEvent: {e}")
    
    def frame_to_base64(self, frame) -> str:
        """Convert numpy frame to base64 string for web display - FIXED"""
        try:
            import cv2

            # Validate frame
            if frame is None or frame.size == 0:
                print("Warning: Invalid frame for conversion")
                return ""

            # Ensure frame is in correct format
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                print(f"Warning: Unexpected frame shape: {frame.shape}")
                return ""

            # Convert RGB to BGR for OpenCV (Toupcam gives RGB, OpenCV expects BGR)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode as JPEG with higher quality for better display
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            success, buffer = cv2.imencode('.jpg', frame_bgr, encode_params)

            if not success:
                print("Warning: Failed to encode frame as JPEG")
                return ""

            # Convert to base64
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"

        except Exception as e:
            print(f"Error converting Toupcam frame to base64: {e}")
            return ""
    
    def get_current_frame_base64(self) -> str:
        """Get current frame as base64 string (thread-safe) - FIXED"""
        with self.lock:
            if self.current_frame is not None and self.current_frame.size > 0:
                # Create a copy to avoid race conditions
                frame_copy = self.current_frame.copy()

        # Convert outside the lock to minimize lock time
        if 'frame_copy' in locals():
            return self.frame_to_base64(frame_copy)
        return ""
    
    def snap_image(self, resolution_index: int = 0):
        """Capture still image"""
        if self.hcam and self.is_running:
            try:
                self.hcam.Snap(resolution_index)
                print(f"Toupcam: Snap command sent with resolution index {resolution_index}")
                return True
            except Exception as e:
                print(f"Error taking snap: {e}")
                return False
        return False
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if self.cur:
            return {
                'name': self.cur.displayname,
                'width': self.imgWidth,
                'height': self.imgHeight,
                'resolution': f"{self.imgWidth}x{self.imgHeight}",
                'available_resolutions': [f"{res.width}x{res.height}" for res in self.cur.model.res]
            }
        return {}
    
    def set_resolution(self, index: int):
        """Change camera resolution"""
        if not self.hcam or not self.is_running or not self.cur:
            return False
            
        try:
            # Stop temporarily
            self.hcam.Stop()
            
            # Change resolution
            self.res = index
            self.imgWidth = self.cur.model.res[index].width
            self.imgHeight = self.cur.model.res[index].height
            self.hcam.put_eSize(self.res)
            
            # Reallocate buffer
            buffer_size = toupcam.TDIBWIDTHBYTES(self.imgWidth * 24) * self.imgHeight
            self.pData = bytes(buffer_size)
            
            # Restart
            self.hcam.StartPullModeWithCallback(self.event_callback, self)
            print(f"Toupcam: Resolution changed to {self.imgWidth}x{self.imgHeight}")
            return True
            
        except Exception as e:
            print(f"Error changing resolution: {e}")
            return False
    
    def __del__(self):
        """Destructor - ensure camera is properly released"""
        self.stop_stream()
    

    def jpeg_frame_generator(self):
        """
        Generator yang menghasilkan frame dalam format MJPEG.
        Mengambil frame dari 'self.current_frame' yang diisi oleh callback.
        """
        print("INFO: Memulai MJPEG generator untuk Toupcam...")
        import cv2 # Impor cv2 di sini

        while self.is_running:
            frame_rgb = None
            with self.lock:
                if self.current_frame is not None:
                    frame_rgb = self.current_frame.copy()

            if frame_rgb is None:
                time.sleep(0.05)
                continue

            # Kamera Toupcam memberikan data RGB, OpenCV butuh BGR untuk encoding
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            
            # Encode frame ke JPEG
            ret, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()

            # Hasilkan byte stream dengan format MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        print("INFO: MJPEG generator untuk Toupcam berhenti.")
