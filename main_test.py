from system_optimized import Particle, SystemOptimized
#from visualization import visualizer
import math
import random
import sys
import threading

def initialize_particles(num_particles, width, height, radius, ordered=False):
    """
    初始化粒子列表，支持随机分布和有序网格排列。
    
    参数：
    - num_particles: 粒子数量
    - width: 模拟空间宽度
    - height: 模拟空间高度
    - radius: 粒子半径
    - ordered: 是否生成有序排列的粒子（默认为False，随机排列）
    
    返回：
    - particles: 初始化后的粒子列表
    """
    particles = []
    if not ordered:
        # 随机排列
        attempts = 0
        max_attempts = num_particles * 100  # 防止无限循环
        while len(particles) < num_particles and attempts < max_attempts:
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            new_particle = Particle(x, y, radius)
            overlap = False
            for p in particles:
                dx = abs(p.x - new_particle.x)
                dy = abs(p.y - new_particle.y)
                dx = min(dx, width - dx)
                dy = min(dy, height - dy)
                distance_sq = dx * dx + dy * dy
                if distance_sq < (p.radius + new_particle.radius) ** 2:
                    overlap = True
                    break
            if not overlap:
                particles.append(new_particle)
            attempts += 1
        if len(particles) < num_particles:
            print(f"警告：仅成功初始化了 {len(particles)} 个粒子，未达到目标 {num_particles} 个。")
        else:
            print(f"成功初始化了 {num_particles} 个随机排列的粒子。")
    else:
        # 有序网格排列
        # 计算网格的行数和列数，尽量接近正方形
        cols = math.floor((width-2*radius)/2*radius+1)
        rows = math.floor((height-2*radius)/2*radius+1)    
        spacing_x = width / cols
        spacing_y = height / rows
        if spacing_x < 2 * radius or spacing_y < 2 * radius:
            print("警告：粒子半径过大，无法在有序网格中排列所有粒子。尝试减少粒子数量或减小半径。")
        for i in range(rows):
            for j in range(cols):
                if len(particles) >= num_particles:
                    break
                x = radius + j * 2*radius
                y = radius + i * 2*radius
                if x<=width-radius and y<=height-radius:
                    particles.append(Particle(x, y, radius))
                else:
                    pass
        print(f"成功初始化了 {len(particles)} 个有序排列的粒子（网格状）。")
    
    return particles

def main():
    #设置粒子密度packing_density
    packing_density=0.5

    # 初始化一些粒子
    num_particles = 1000  # 根据需要调整粒子数量
    particle_radius = 1  # 粒子半径，可根据需要调整
    ordered = True  # 设置为True以生成有序排列的粒子，False为随机排列

    # 设置模拟空间大小
    width = height = math.sqrt(num_particles*math.pi*particle_radius**2/packing_density)

    # 初始化粒子，选择有序或随机排列
    print("初始化粒子...")
    particles = initialize_particles(num_particles, width, height, particle_radius, ordered=ordered)

    # 创建优化后的系统实例
    system = SystemOptimized(particles, width=width, height=height, move_step=0.01, grid_size=5.0)

    #for _ in range(100):
    #    system.attempt_all_particles_move()
    try_inssert=20

    final_paticles,acceptance_ratio=system.run_until_success(try_inssert)

    print(f"\n进行了{try_inssert}次插入，插入的接收率为{acceptance_ratio}")



if __name__ == "__main__":
    main()