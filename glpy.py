import time
import threading
import numpy as np
import moderngl
import pyglet
from pyglet import clock

class UltraHighFPSRenderer:
    def __init__(self, width=640, height=480, target_fps=15000):
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.frame_count = 0
        self.running = False
        
        # 初始化窗口和OpenGL上下文
        self.window = pyglet.window.Window(width, height, vsync=False)
        self.ctx = moderngl.create_context()
        
        # 极简渲染管线
        self.program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 fragColor;
                void main() {
                    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
                }
            """,
        )
        
        # 预分配所有资源
        vertices = np.array([-0.5, -0.5, 0.5, -0.5, 0.0, 0.5], dtype='f4')
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, 'in_vert')
    
    def render_frame(self):
        # 清除缓冲区
        self.ctx.clear(0.0, 0.0, 0.0)
        
        # 极简绘制调用
        self.vao.render(moderngl.TRIANGLES)
        
        # 交换缓冲区 (无垂直同步)
        self.window.flip()
        self.frame_count += 1
    
    def run(self):
        self.running = True
        last_time = time.perf_counter()
        
        # 禁用pyglet的默认事件循环
        clock.set_fps_limit(None)
        
        while self.running:
            current_time = time.perf_counter()
            delta = current_time - last_time
            
            # 精确帧时间控制
            if delta < self.frame_time:
                sleep_time = self.frame_time - delta
                time.sleep(sleep_time)
            
            # 处理事件 (最小化)
            pyglet.clock.tick()
            self.window.switch_to()
            self.window.dispatch_events()
            
            # 渲染帧
            self.render_frame()
            
            last_time = current_time
    
    def start(self):
        render_thread = threading.Thread(target=self.run)
        render_thread.daemon = True
        render_thread.start()
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    renderer = UltraHighFPSRenderer(target_fps=15000)
    renderer.start()
    
    try:
        while True:
            time.sleep(1)
            fps = renderer.frame_count
            renderer.frame_count = 0
            print(f"Current FPS: {fps}")
    except KeyboardInterrupt:
        renderer.stop()