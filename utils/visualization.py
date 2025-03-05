import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import datetime
from typing import Dict, List
import config

def create_personal_progress_graph(user_id: str, username: str, health_data: Dict, 
                                  show_weight=False, show_body_fat=False, 
                                  show_muscle_mass=False, show_bmr=False):
    """Create personal progress graphs for the user"""
    # Convert data to pandas DataFrame
    df = pd.DataFrame.from_dict(health_data[user_id], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Count how many plots we need
    plots_needed = sum([show_weight, show_body_fat, show_muscle_mass, show_bmr])
    
    # Create subplot grid
    plt.style.use(config.GRAPH_STYLE)
    fig, axs = plt.subplots(plots_needed, 1, figsize=(10, 6*plots_needed))
    
    # If only one plot, axs needs to be in a list
    if plots_needed == 1:
        axs = [axs]

    current_plot = 0

    # Create individual plots
    if show_weight:
        axs[current_plot].plot(df.index, df['weight'], config.COLOR_WEIGHT, label='Weight (lbs)')
        axs[current_plot].set_title('Weight Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if show_body_fat:
        axs[current_plot].plot(df.index, df['body_fat'], config.COLOR_BODY_FAT, label='Body Fat %')
        axs[current_plot].set_title('Body Fat Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if show_muscle_mass:
        axs[current_plot].plot(df.index, df['muscle_mass'], config.COLOR_MUSCLE_MASS, label='Muscle Mass (lbs)')
        axs[current_plot].set_title('Muscle Mass Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if show_bmr:
        axs[current_plot].plot(df.index, df['bmr'], config.COLOR_BMR, label='BMR (cal)')
        axs[current_plot].set_title('BMR Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()

    fig.suptitle(f'Health Progress for {username}', fontsize=16)
    plt.tight_layout()
    
    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Clean up matplotlib
    plt.close()
    
    return buf

def create_competition_graph(comp_name: str, progress_data: Dict, user_names: Dict):
    """Create competition progress visualization"""
    plt.style.use(config.GRAPH_STYLE)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=config.GRAPH_FIGSIZE)
    
    # Fix for the date ordering bug:
    # 1. Collect all unique dates across all participants
    all_dates = set()
    for user_id in progress_data:
        all_dates.update(progress_data[user_id]['dates'])
    
    # 2. Sort all dates chronologically
    all_dates = sorted(list(all_dates))
    
    # Plot total points progression with properly ordered dates
    for user_id in progress_data:
        # Create a complete timeline with all dates
        complete_dates = all_dates.copy()
        complete_points = []
        
        # For each date in the complete timeline, find the corresponding point value
        # or use None for dates where this user has no data
        last_valid_point = 0  # Use last valid point for missing data
        
        for date in complete_dates:
            if date in progress_data[user_id]['dates']:
                idx = progress_data[user_id]['dates'].index(date)
                point = progress_data[user_id]['points'][idx]
                last_valid_point = point
                complete_points.append(point)
            else:
                # If user doesn't have data for this date, use last valid point
                # This ensures the line doesn't drop to zero for missing dates
                complete_points.append(last_valid_point)
        
        # Plot the complete timeline
        ax1.plot(complete_dates, complete_points, marker='o', label=user_names[user_id])
    
    ax1.set_title('Total Points Progress')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Total Points')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Plot points breakdown (stacked bar chart)
    for user_id in progress_data:
        if not progress_data[user_id]['dates']:  # Skip if no data
            continue
            
        # Use last available date for each user
        idx = -1  # Last date's index
        
        # Stacked bars for each component
        ax2.bar(user_names[user_id],
                progress_data[user_id]['body_fat_points'][idx],
                label='Body Fat Points', 
                color=config.COLOR_BF_POINTS)
                
        ax2.bar(user_names[user_id], 
                progress_data[user_id]['muscle_mass_points'][idx],
                bottom=progress_data[user_id]['body_fat_points'][idx],
                label='Muscle Mass Points', 
                color=config.COLOR_MM_POINTS)
                
        ax2.bar(user_names[user_id], 
                progress_data[user_id]['bmr_points'][idx],
                bottom=progress_data[user_id]['body_fat_points'][idx] + 
                        progress_data[user_id]['muscle_mass_points'][idx],
                label='BMR Points', 
                color=config.COLOR_BMR_POINTS)
    
    ax2.set_title('Current Points Breakdown')
    ax2.set_ylabel('Points')
    ax2.grid(True, alpha=0.3)
    
    # Create proper legend (avoiding duplicates)
    handles, labels = ax2.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax2.legend(by_label.values(), by_label.keys())
    
    plt.tight_layout()
    
    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf