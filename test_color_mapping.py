#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Distance Color Mapping Test Script
Simple test for the new fixed distance interval color mapping feature
"""

import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.data.color_mapper import DistanceColorMapper
    print("✓ Successfully imported DistanceColorMapper")
except ImportError as e:
    print(f"✗ Failed to import DistanceColorMapper: {e}")
    sys.exit(1)

def test_color_mapping():
    """Test the color mapping functionality"""
    print("\n=== Distance Color Mapping Test ===")
    
    # Initialize color mapper
    mapper = DistanceColorMapper()
    print("✓ Color mapper initialized")
    
    # Generate test data
    np.random.seed(42)
    num_points = 500
    
    # Create distances in different ranges to test all colors
    distances = []
    
    # Each range gets some points
    ranges = [(0, 100), (100, 200), (200, 300), (300, 400), (400, 500)]
    for min_dist, max_dist in ranges:
        range_distances = np.random.uniform(min_dist + 5, max_dist - 5, num_points // 5)
        distances.extend(range_distances)
    
    distances = np.array(distances)
    
    # Generate 3D coordinates
    angles = np.random.uniform(0, 2*np.pi, len(distances))
    elevations = np.random.uniform(-0.3, 0.3, len(distances))
    
    x = distances * np.cos(elevations) * np.cos(angles)
    y = distances * np.cos(elevations) * np.sin(angles)
    z = distances * np.sin(elevations)
    
    print(f"✓ Generated {len(distances)} test points")
    
    # Test color mapping
    color_indices = mapper.map_distances_to_colors(distances)
    print(f"✓ Mapped distances to color indices")
    
    # Create figure
    fig = plt.figure(figsize=(12, 5))
    
    # 3D plot
    ax1 = fig.add_subplot(121, projection='3d')
    scatter1 = mapper.plot_distance_colors(ax1, distances, x, y, z, point_size=10)
    ax1.set_title('3D Point Cloud (Fixed Distance Colors)')
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')
    
    # 2D plot
    ax2 = fig.add_subplot(122)
    scatter2 = mapper.plot_distance_colors(ax2, distances, x, y, None, point_size=10)
    ax2.set_title('2D Projection (X-Y Plane)')
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.grid(True, alpha=0.3)
    
    # Create legend manually (text-based)
    legend_info = mapper.get_legend_info()
    legend_text = "Color Mapping:\n"
    for range_text, color in legend_info:
        legend_text += f"{range_text}: {color}\n"
    
    # Add text box with legend
    ax2.text(1.02, 0.98, legend_text, transform=ax2.transAxes, 
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    # Print statistics
    print("\n=== Color Distribution Statistics ===")
    total_points = len(distances)
    
    for i, range_info in enumerate(mapper.color_ranges):
        if range_info['max'] == float('inf'):
            mask = distances >= range_info['min']
            range_text = f"{range_info['min']}m+"
        else:
            mask = (distances >= range_info['min']) & (distances < range_info['max'])
            range_text = f"{range_info['min']}-{range_info['max']}m"
        
        count = np.sum(mask)
        percentage = (count / total_points) * 100
        color = range_info['color']
        print(f"{range_text:>10} ({color:>6}): {count:>3} points ({percentage:>5.1f}%)")
    
    print(f"\nTotal points: {total_points}")
    print("✓ All tests completed successfully!")
    
    # Show the plot
    plt.show()

def test_individual_functions():
    """Test individual functions of the color mapper"""
    print("\n=== Individual Function Tests ===")
    
    mapper = DistanceColorMapper()
    
    # Test single distance mapping
    test_distances = [50, 150, 250, 350, 450]
    for dist in test_distances:
        color = mapper.get_color_for_distance(dist)
        print(f"Distance {dist}m -> Color: {color}")
    
    # Test distance array mapping
    test_array = np.array([25, 75, 125, 175, 225, 275, 325, 375, 425, 475])
    color_indices = mapper.map_distances_to_colors(test_array)
    print(f"\nDistance array: {test_array}")
    print(f"Color indices:  {color_indices}")
    
    # Test legend info
    legend_info = mapper.get_legend_info()
    print(f"\nLegend info:")
    for range_text, color in legend_info:
        print(f"  {range_text}: {color}")

if __name__ == "__main__":
    try:
        test_individual_functions()
        test_color_mapping()
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 