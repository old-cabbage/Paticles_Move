# main.py

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
        cols = math.ceil(math.sqrt(num_particles * width / height))
        rows = math.ceil(num_particles / cols)
        spacing_x = width / cols
        spacing_y = height / rows
        if spacing_x < 2 * radius or spacing_y < 2 * radius:
            print("警告：粒子半径过大，无法在有序网格中排列所有粒子。尝试减少粒子数量或减小半径。")
        for i in range(rows):
            for j in range(cols):
                if len(particles) >= num_particles:
                    break
                x = (j + 0.5) * spacing_x
                y = (i + 0.5) * spacing_y
                particles.append(Particle(x, y, radius))
        print(f"成功初始化了 {len(particles)} 个有序排列的粒子（网格状）。")
    
    return particles

def main():
    #设置粒子密度packing_density
    packing_density=0.4

    # 初始化一些粒子
    num_particles = 5000  # 根据需要调整粒子数量
    particle_radius = 1  # 粒子半径，可根据需要调整
    ordered = False  # 设置为True以生成有序排列的粒子，False为随机排列

    # 设置模拟空间大小
    width = height = math.sqrt(num_particles*math.pi*particle_radius**2/packing_density)

    # 初始化粒子，选择有序或随机排列
    print("初始化粒子...")
    particles = initialize_particles(num_particles, width, height, particle_radius, ordered=ordered)

    # 创建优化后的系统实例
    system = SystemOptimized(particles, width=width, height=height, move_step=0.001, grid_size=5.0)

    # 创建可视化器
    #steps_per_update = 5  # 每次可视化更新进行的模拟步数
    #visualizer = Visualizer(system, steps_per_update=steps_per_update)

    # 启动可视化器的线程
    #visual_thread = threading.Thread(target=visualizer.start)
    #visual_thread.daemon = True  # 设置为守护线程，主线程退出时自动关闭
    #visual_thread.start()

    # 初始化统计变量
    total_success = 0
    total_attempts = 0
    iterations = 1000
    moves_per_cycle = 5
    insertions_per_cycle = 1000
    insert_radius = particle_radius

    print("\n开始进行循环模拟和插入测试...")
    for cycle in range(1, iterations + 1):
        system.run_steps(moves_per_cycle)
        # 进行5次随机移动
        #for _ in range(moves_per_cycle):
        #    system.attempt_all_particles_move()
        
        # 进行1000次随机插入尝试，记录成功次数
        successes = system.test_random_insertions(insertions_per_cycle, insert_radius)
        total_success += successes
        total_attempts += insertions_per_cycle
        
        # 可选：打印每个循环的结果
        if cycle>5 and cycle % (iterations//10)==0:
            print(f"循环 {cycle}/{iterations}: 成功插入 {successes}/{insertions_per_cycle} 次。")
    
    # 计算最终的成功插入概率
    final_probability = total_success / total_attempts if total_attempts > 0 else 0.0
    print(f"\n最终插入成功概率: {final_probability * 100:.2f}% ({total_success}/{total_attempts})")

    # 等待可视化窗口关闭
    #print("\n模拟完成。可视化窗口仍在运行，按关闭按钮退出程序。")
    #visual_thread.join()

if __name__ == "__main__":
    main()
