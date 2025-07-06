#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Demo - Dynamic Distance Color Mapping
Complete demonstration of the new dynamic scale color mapping feature
"""

import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.color_mapper import DistanceColorMapper

def demonstrate_dynamic_mapping():
    """Demonstrate how the dynamic color mapping works with different scenarios"""
    print("=== Dynamic Distance Color Mapping Demo ===")
    print("This demonstrates the new color mapping system:")
    print("- Colors automatically adjust based on the maximum distance in the data")
    print("- Red -> Orange -> Yellow -> Green -> Blue (fixed color order)")
    print("- Distance ranges change dynamically based on scale")
    print()
    
    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Dynamic Distance Color Mapping - Different Scenarios', fontsize=16)
    
    # Test scenarios
    scenarios = [
        {"max_dist": 500, "title": "Scene 1: Max Distance 500m", "description": "Normal outdoor LiDAR scan"},
        {"max_dist": 1000, "title": "Scene 2: Max Distance 1000m", "description": "Long-range LiDAR scan"},
        {"max_dist": 200, "title": "Scene 3: Max Distance 200m", "description": "Indoor or close-range scan"}
    ]
    
    for i, scenario in enumerate(scenarios):
        max_distance = scenario["max_dist"]
        title = scenario["title"]
        description = scenario["description"]
        
        print(f"--- {title} ---")
        print(f"Description: {description}")
        
        # Initialize mapper
        mapper = DistanceColorMapper()
        
        # Generate realistic point cloud data
        np.random.seed(42 + i)  # Different seed for each scenario
        num_points = 400
        
        # Generate distances with realistic distribution (more points closer, fewer far away)
        distances = generate_realistic_distances(max_distance, num_points)
        
        # Generate 3D coordinates
        angles = np.random.uniform(0, 2*np.pi, num_points)
        elevations = np.random.uniform(-0.3, 0.3, num_points)
        
        x = distances * np.cos(elevations) * np.cos(angles)
        y = distances * np.cos(elevations) * np.sin(angles)
        z = distances * np.sin(elevations)
        
        # Apply dynamic color mapping
        color_indices = mapper.map_distances_to_colors(distances)
        
        # 3D plot
        ax_3d = axes[0, i]
        ax_3d.remove()
        ax_3d = fig.add_subplot(2, 3, i+1, projection='3d')
        
        scatter = mapper.plot_distance_colors(ax_3d, distances, x, y, z, point_size=15)
        ax_3d.set_title(f'{title}\n3D Point Cloud')
        ax_3d.set_xlabel('X (m)')
        ax_3d.set_ylabel('Y (m)')
        ax_3d.set_zlabel('Z (m)')
        ax_3d.view_init(elev=20, azim=45)
        
        # 2D plot with legend
        ax_2d = axes[1, i]
        mapper.plot_distance_colors(ax_2d, distances, x, y, None, point_size=15)
        ax_2d.set_title(f'2D View (X-Y Plane)')
        ax_2d.set_xlabel('X (m)')
        ax_2d.set_ylabel('Y (m)')
        ax_2d.grid(True, alpha=0.3)
        
        # Add color legend as text
        legend_info = mapper.get_legend_info()
        legend_text = "Color Mapping:\n"
        for range_text, color in legend_info:
            legend_text += f"{range_text}: {color}\n"
        
        ax_2d.text(1.02, 0.98, legend_text, transform=ax_2d.transAxes, 
                  fontsize=8, verticalalignment='top',
                  bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # Print color ranges and statistics
        ranges = mapper._calculate_dynamic_ranges(max_distance)
        print(f"Color ranges:")
        total_points = len(distances)
        
        for j, (min_dist, max_dist) in enumerate(ranges):
            if max_dist == float('inf'):
                mask = distances >= min_dist
                range_text = f"{min_dist:.0f}m+"
            else:
                mask = (distances >= min_dist) & (distances < max_dist)
                range_text = f"{min_dist:.0f}-{max_dist:.0f}m"
            
            count = np.sum(mask)
            percentage = (count / total_points) * 100
            color = mapper.colors[j]
            print(f"  {range_text:>12} -> {color:>6}: {count:>3} points ({percentage:>5.1f}%)")
        
        print()
    
    plt.tight_layout()
    plt.show()

def generate_realistic_distances(max_distance, num_points):
    """Generate realistic distance distribution (more points closer, fewer far away)"""
    # Use exponential distribution for more realistic point cloud
    # Most points are closer, fewer points are far away
    distances = np.random.exponential(scale=max_distance/4, size=num_points)
    
    # Clip to max distance and add some uniform distribution
    distances = np.clip(distances, 0, max_distance)
    
    # Add some uniform points for better coverage
    uniform_points = int(num_points * 0.2)  # 20% uniform distribution
    uniform_distances = np.random.uniform(0, max_distance, uniform_points)
    
    # Combine and shuffle
    all_distances = np.concatenate([distances[:-uniform_points], uniform_distances])
    np.random.shuffle(all_distances)
    
    return all_distances

def show_feature_comparison():
    """Show comparison between old percentage-based and new dynamic scale mapping"""
    print("=== Feature Comparison ===")
    print()
    print("OLD SYSTEM (Percentage-based):")
    print("- If max distance is 200m: 200m shows as yellow (100%)")
    print("- If max distance is 500m: 500m shows as yellow (100%)")
    print("- Same distance (e.g., 100m) shows different colors in different scans")
    print("- Inconsistent color meaning")
    print()
    
    print("NEW SYSTEM (Dynamic Scale):")
    print("- Fixed color sequence: Red -> Orange -> Yellow -> Green -> Blue")
    print("- Distance ranges adjust automatically based on data")
    print("- Example with 500m max:")
    print("  • 0-100m: Red")
    print("  • 100-200m: Orange") 
    print("  • 200-300m: Yellow")
    print("  • 300-400m: Green")
    print("  • 400-500m: Blue")
    print()
    print("- Example with 1000m max:")
    print("  • 0-200m: Red")
    print("  • 200-400m: Orange")
    print("  • 400-600m: Yellow") 
    print("  • 600-800m: Green")
    print("  • 800-1000m: Blue")
    print()
    print("BENEFITS:")
    print("✓ Color ranges automatically adapt to data scale")
    print("✓ Fixed color sequence is easy to remember")
    print("✓ Better visual discrimination of distance ranges")
    print("✓ Consistent interpretation across different scans")

def main():
    print("=== LiDAR Distance Color Mapping System ===")
    print("New Dynamic Scale Feature Demonstration")
    print("=" * 50)
    
    try:
        show_feature_comparison()
        print("\nStarting visual demonstration...")
        demonstrate_dynamic_mapping()
        
        print("\n=== Summary ===")
        print("✓ Dynamic color mapping successfully demonstrated")
        print("✓ Color ranges automatically adjust based on maximum distance")
        print("✓ Fixed color sequence: Red -> Orange -> Yellow -> Green -> Blue")
        print("✓ Better visual interpretation of distance data")
        print("\nThe new system is now integrated into the main LiDAR control application.")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 