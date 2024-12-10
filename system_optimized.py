# system_optimized.py

import math
import numpy as np
from numba import njit, prange
from collections import namedtuple

# 定义一个简单的粒子结构
Particle = namedtuple('Particle', ['x', 'y', 'radius'])

@njit(parallel=True)
def move_particles_numba(particles_x, particles_y, move_step, width, height):
    num_particles = particles_x.shape[0]
    new_x = np.empty(num_particles, dtype=np.float64)
    new_y = np.empty(num_particles, dtype=np.float64)
    for i in prange(num_particles):
        angle = np.random.uniform(0, 2 * math.pi)
        dist = np.random.uniform(0, move_step)
        new_x[i] = (particles_x[i] + dist * math.cos(angle)) % width
        new_y[i] = (particles_y[i] + dist * math.sin(angle)) % height
    return new_x, new_y

@njit(parallel=True)
def assign_particles_to_grid(particles_x, particles_y, grid_size, grid_count_x, grid_count_y):
    num_particles = particles_x.shape[0]
    grid_particle_indices = -1 * np.ones((grid_count_x, grid_count_y, num_particles), dtype=np.int32)
    grid_lengths = np.zeros((grid_count_x, grid_count_y), dtype=np.int32)
    
    for i in prange(num_particles):
        grid_x = int(particles_x[i] // grid_size) % grid_count_x
        grid_y = int(particles_y[i] // grid_size) % grid_count_y
        idx = grid_lengths[grid_x, grid_y]
        if idx < num_particles:
            grid_particle_indices[grid_x, grid_y, idx] = i
            grid_lengths[grid_x, grid_y] += 1
    return grid_particle_indices, grid_lengths

@njit(parallel=True)
def check_overlaps_numba(new_x, new_y, radii, grid_size, width, height, 
                        grid_count_x, grid_count_y, grid_particle_indices, grid_lengths):
    overlaps = 0  # 计数是否存在任何重叠
    
    for idx in prange(grid_count_x * grid_count_y):
        grid_x = idx // grid_count_y
        grid_y = idx % grid_count_y
        particles_in_cell = grid_particle_indices[grid_x, grid_y, :grid_lengths[grid_x, grid_y]]
        num_particles_in_cell = grid_lengths[grid_x, grid_y]
        grid_overlap = False  # 当前网格是否存在重叠
        
        # 检查同一网格内的粒子是否重叠
        for i in range(num_particles_in_cell):
            idx1 = particles_in_cell[i]
            for j in range(i + 1, num_particles_in_cell):
                idx2 = particles_in_cell[j]
                dx = abs(new_x[idx1] - new_x[idx2])
                dy = abs(new_y[idx1] - new_y[idx2])
                dx = min(dx, width - dx)
                dy = min(dy, height - dy)
                distance_sq = dx * dx + dy * dy
                radii_sum = radii[idx1] + radii[idx2]
                if distance_sq < radii_sum * radii_sum:
                    grid_overlap = True
                    break
            if grid_overlap:
                break
        
        # 如果当前网格内没有重叠，检查相邻网格中的粒子
        if not grid_overlap:
            for dx_cell in (-1, 0, 1):
                for dy_cell in (-1, 0, 1):
                    neighbor_x = (grid_x + dx_cell) % grid_count_x
                    neighbor_y = (grid_y + dy_cell) % grid_count_y
                    if neighbor_x == grid_x and neighbor_y == grid_y:
                        continue
                    particles_in_neighbor = grid_particle_indices[neighbor_x, neighbor_y, :grid_lengths[neighbor_x, neighbor_y]]
                    for idx2 in particles_in_neighbor:
                        if idx2 <= particles_in_cell[0]:
                            continue
                        dx = abs(new_x[particles_in_cell[0]] - new_x[idx2])
                        dy = abs(new_y[particles_in_cell[0]] - new_y[idx2])
                        dx = min(dx, width - dx)
                        dy = min(dy, height - dy)
                        distance_sq = dx * dx + dy * dy
                        radii_sum = radii[particles_in_cell[0]] + radii[idx2]
                        if distance_sq < radii_sum * radii_sum:
                            grid_overlap = True
                            break
                    if grid_overlap:
                        break
        if grid_overlap:
            overlaps += 1  # 记录存在重叠
    
    # 返回是否存在任何重叠
    return overlaps > 0

@njit(parallel=True)
def test_random_insertions_numba(particles_x, particles_y, radii, width, height, num_tests, radius):
    success = 0
    for test in prange(num_tests):
        x = np.random.uniform(0, width)
        y = np.random.uniform(0, height)
        overlap = False
        for i in range(particles_x.shape[0]):
            dx = abs(x - particles_x[i])
            dy = abs(y - particles_y[i])
            dx = min(dx, width - dx)
            dy = min(dy, height - dy)
            distance_sq = dx * dx + dy * dy
            if distance_sq < (radius + radii[i]) ** 2:
                overlap = True
                break
        if not overlap:
            success += 1
    return success

class SystemOptimized:
    def __init__(self, particles, width=100.0, height=100.0, move_step=1.0, grid_size=5.0):
        self.num_particles = len(particles)
        self.width = width
        self.height = height
        self.move_step = move_step
        self.grid_size = grid_size
        self.grid_count_x = int(math.ceil(self.width / self.grid_size))
        self.grid_count_y = int(math.ceil(self.height / self.grid_size))
        
        # 使用NumPy数组存储粒子位置和半径
        self.particles_x = np.empty(self.num_particles, dtype=np.float64)
        self.particles_y = np.empty(self.num_particles, dtype=np.float64)
        self.radii = np.empty(self.num_particles, dtype=np.float64)
        for i, p in enumerate(particles):
            self.particles_x[i] = p.x
            self.particles_y[i] = p.y
            self.radii[i] = p.radius
        
        # 接收率统计
        self.total_tries = 0
        self.success_count = 0
    
    def attempt_all_particles_move(self):
        """
        尝试让所有粒子同时随机移动一次，并检查是否有重叠。
        """
        # 移动粒子
        new_x, new_y = move_particles_numba(self.particles_x, self.particles_y, self.move_step, self.width, self.height)
        
        # 分配粒子到格子
        grid_particle_indices, grid_lengths = assign_particles_to_grid(new_x, new_y, self.grid_size, self.grid_count_x, self.grid_count_y)
        
        # 检查重叠
        overlap = check_overlaps_numba(new_x, new_y, self.radii, self.grid_size, self.width, self.height, 
                                      self.grid_count_x, self.grid_count_y, grid_particle_indices, grid_lengths)
        
        # 更新统计
        self.total_tries += 1
        
        if not overlap:
            # 接受移动
            self.particles_x = new_x
            self.particles_y = new_y
            self.success_count += 1
        else:
            # 拒绝移动，保持原位
            pass
    
    def run_until_success(self, target_success_steps, reset=False):
        """
        运行模拟，直到达到指定的成功步数。
        
        参数：
        - target_success_steps: 需要达到的成功步数
        - reset: 是否在运行前清空历史统计数据（默认为False）
        
        返回：
        - final_particles: 最终的粒子列表
        - acceptance_ratio: 接收率 = 成功次数 / 总尝试次数
        """
        if reset:
            self.reset_stats()
        
        while self.success_count < target_success_steps:
            self.attempt_all_particles_move()
            # 可选：打印进度
            if self.total_tries % 100 == 0:
                print(f"Progress: {self.success_count}/{target_success_steps} successful moves.")
        
        # 构建最终粒子列表
        final_particles = [Particle(x, y, r) for x, y, r in zip(self.particles_x, self.particles_y, self.radii)]
        return final_particles, self.get_acceptance_ratio()
    
    def run_steps(self, num_steps, reset=False):
        """
        运行指定数量的成功步数。
        
        参数：
        - num_steps: 需要达到的成功步数
        - reset: 是否在运行前清空历史统计数据
        
        返回：
        - acceptance_ratio: 接收率 = 成功次数 / 总尝试次数
        """
        if reset:
            self.reset_stats()
        
        while self.success_count < num_steps:
            self.attempt_all_particles_move()
            # 可选：打印进度
            #if self.total_tries % 100 == 0:
            #    print(f"Progress: {self.success_count}/{num_steps} successful moves.")
    
    def reset_stats(self):
        """清空当前统计数据。"""
        self.total_tries = 0
        self.success_count = 0
    
    def get_acceptance_ratio(self):
        """返回接收率 = 成功次数 / 总尝试次数。"""
        if self.total_tries == 0:
            return 0.0
        return self.success_count / self.total_tries
    
    def test_random_insertions(self, num_tests, radius):
        """
        进行多次随机粒子插入测试，计算成功插入的次数。
        
        参数：
        - num_tests: 测试次数
        - radius: 插入粒子的半径
        
        返回：
        - success: 成功插入的次数
        """
        success = test_random_insertions_numba(self.particles_x, self.particles_y, self.radii, 
                                              self.width, self.height, num_tests, radius)
        #print(f"Random Insertion Tests Completed: {success}/{num_tests} successful insertions.")
        return success
