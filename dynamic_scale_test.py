#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Scale Color Mapping Test
Test the new dynamic scale color mapping functionality
"""

import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.color_mapper import DistanceColorMapper

def test_dynamic_scale():
    """Test dynamic scale color mapping with different max distances"""
    print("=== Dynamic Scale Color Mapping Test ===")
    
    # Test different scenarios
    scenarios = [
        {"max_dist": 500, "name": "Max 500m"},
        {"max_dist": 1000, "name": "Max 1000m"}, 
        {"max_dist": 200, "name": "Max 200m"}
    ]
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Dynamic Scale Color Mapping Test', fontsize=16)
    
    for i, scenario in enumerate(scenarios):
        max_distance = scenario["max_dist"]
        name = scenario["name"]
        
        print(f"\n--- Testing {name} ---")
        
        # Initialize mapper
        mapper = DistanceColorMapper()
        
        # Generate test data with specific max distance
        np.random.seed(42)
        num_points = 300
        
        # Generate distances from 0 to max_distance
        distances = np.random.uniform(0, max_distance, num_points)
        
        # Generate coordinates
        angles = np.random.uniform(0, 2*np.pi, num_points)
        elevations = np.random.uniform(-0.2, 0.2, num_points)
        
        x = distances * np.cos(elevations) * np.cos(angles)
        y = distances * np.cos(elevations) * np.sin(angles)
        z = distances * np.sin(elevations)
        
        # Map colors using dynamic scale
        color_indices = mapper.map_distances_to_colors(distances)
        
        # Plot 3D view
        ax_3d = axes[0, i]
        ax_3d.remove()
        ax_3d = fig.add_subplot(2, 3, i+1, projection='3d')
        
        scatter = mapper.plot_distance_colors(ax_3d, distances, x, y, z, point_size=20)
        ax_3d.set_title(f'{name}\n3D View')
        ax_3d.set_xlabel('X (m)')
        ax_3d.set_ylabel('Y (m)')
        ax_3d.set_zlabel('Z (m)')
        
        # Plot 2D view
        ax_2d = axes[1, i]
        mapper.plot_distance_colors(ax_2d, distances, x, y, None, point_size=20)
        ax_2d.set_title(f'{name}\n2D View (X-Y)')
        ax_2d.set_xlabel('X (m)')
        ax_2d.set_ylabel('Y (m)')
        ax_2d.grid(True, alpha=0.3)
        
        # Print color mapping info
        legend_info = mapper.get_legend_info()
        print(f"Color ranges for {name}:")
        for range_text, color in legend_info:
            print(f"  {range_text}: {color}")
        
        # Print statistics
        ranges = mapper._calculate_dynamic_ranges(max_distance)
        print(f"Statistics for {name}:")
        for j, (min_dist, max_dist) in enumerate(ranges):
            if max_dist == float('inf'):
                mask = distances >= min_dist
                range_text = f"{min_dist:.0f}m+"
            else:
                mask = (distances >= min_dist) & (distances < max_dist)
                range_text = f"{min_dist:.0f}-{max_dist:.0f}m"
            
            count = np.sum(mask)
            percentage = (count / len(distances)) * 100
            color = mapper.colors[j]
            print(f"  {range_text} ({color}): {count} points ({percentage:.1f}%)")
    
    plt.tight_layout()
    plt.show()

def test_manual_scale_setting():
    """Test manual scale setting functionality"""
    print("\n=== Manual Scale Setting Test ===")
    
    mapper = DistanceColorMapper()
    
    # Test distances
    test_distances = [50, 150, 250, 350, 450]
    
    # Test with different max distance settings
    max_distances = [500, 1000, 200]
    
    for max_dist in max_distances:
        print(f"\nWith max distance set to {max_dist}m:")
        mapper.set_max_distance(max_dist)
        
        for dist in test_distances:
            if dist <= max_dist:
                color = mapper.get_color_for_distance(dist, max_dist)
                print(f"  Distance {dist}m -> Color: {color}")
        
        # Show ranges
        ranges = mapper._calculate_dynamic_ranges(max_dist)
        print(f"  Color ranges:")
        for i, (min_dist, max_dist_range) in enumerate(ranges):
            if max_dist_range == float('inf'):
                range_text = f"{min_dist:.0f}m+"
            else:
                range_text = f"{min_dist:.0f}-{max_dist_range:.0f}m"
            print(f"    {range_text}: {mapper.colors[i]}")

if __name__ == "__main__":
    try:
        test_manual_scale_setting()
        test_dynamic_scale()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc() 