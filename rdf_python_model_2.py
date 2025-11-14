import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import Slider, TextBox, Button
import pandas as pd

class RDFPositionError:
    """
    Radio Direction Finding Position Error Calculator
    
    Calculates position fixing accuracy based on triangulation geometry,
    sensor positions, target position, and bearing measurement error.
    """
    
    def __init__(self, sensor1_pos, sensor2_pos, target_pos, bearing_error_deg):
        """
        Initialize the RDF model.
        
        Parameters:
        -----------
        sensor1_pos : tuple (x, y)
            Position of first sensor in meters
        sensor2_pos : tuple (x, y)
            Position of second sensor in meters
        target_pos : tuple (x, y)
            Position of target in meters
        bearing_error_deg : float
            Bearing measurement error in degrees
        """
        self.s1 = np.array(sensor1_pos)
        self.s2 = np.array(sensor2_pos)
        self.target = np.array(target_pos)
        self.bearing_error_deg = bearing_error_deg
        self.bearing_error_rad = np.radians(bearing_error_deg)
        
        self.calculate()
    
    def calculate(self):
        """Calculate all error metrics."""
        # Calculate ranges from sensors to target
        self.range1 = np.linalg.norm(self.target - self.s1)
        self.range2 = np.linalg.norm(self.target - self.s2)
        
        # Calculate bearings from sensors to target
        delta1 = self.target - self.s1
        delta2 = self.target - self.s2
        
        self.bearing1 = np.arctan2(delta1[0], delta1[1])
        self.bearing2 = np.arctan2(delta2[0], delta2[1])
        
        # Calculate intersection angle
        intersection = abs(self.bearing1 - self.bearing2)
        if intersection > np.pi:
            intersection = 2 * np.pi - intersection
        self.intersection_angle_deg = np.degrees(intersection)
        
        # Calculate baseline distance
        self.baseline = np.linalg.norm(self.s2 - self.s1)
        
        # Calculate lateral errors at each sensor
        self.lateral_error1 = self.range1 * np.tan(self.bearing_error_rad)
        self.lateral_error2 = self.range2 * np.tan(self.bearing_error_rad)
        
        # Calculate position error based on geometry
        sin_intersection = abs(np.sin(np.radians(self.intersection_angle_deg)))
        
        # GDOP (Geometric Dilution of Precision)
        self.gdop = 1 / sin_intersection if sin_intersection > 0 else float('inf')
        
        # Maximum position error
        if sin_intersection < 0.1:  # Poor geometry
            self.max_position_error = max(self.lateral_error1, self.lateral_error2) * 10
        else:
            self.max_position_error = np.sqrt(
                self.lateral_error1**2 + self.lateral_error2**2
            ) / sin_intersection
        
        # Error to range ratio
        self.error_range_ratio = self.max_position_error / max(self.range1, self.range2)
    
    def get_results(self):
        """Return results as a dictionary."""
        return {
            'Sensor 1 Position (m)': f"({self.s1[0]:.1f}, {self.s1[1]:.1f})",
            'Sensor 2 Position (m)': f"({self.s2[0]:.1f}, {self.s2[1]:.1f})",
            'Target Position (m)': f"({self.target[0]:.1f}, {self.target[1]:.1f})",
            'Bearing Error (deg)': f"{self.bearing_error_deg:.2f}",
            'Baseline Distance (m)': f"{self.baseline:.1f}",
            'Range to Sensor 1 (m)': f"{self.range1:.1f}",
            'Range to Sensor 2 (m)': f"{self.range2:.1f}",
            'Intersection Angle (deg)': f"{self.intersection_angle_deg:.1f}",
            'GDOP': f"{self.gdop:.2f}",
            'Lateral Error S1 (m)': f"{self.lateral_error1:.1f}",
            'Lateral Error S2 (m)': f"{self.lateral_error2:.1f}",
            'Max Position Error (m)': f"{self.max_position_error:.1f}",
            'Error/Range Ratio (%)': f"{self.error_range_ratio * 100:.2f}",
        }
    
    def print_results(self):
        """Print results in a formatted table."""
        results = self.get_results()
        print("\n" + "="*60)
        print("RDF POSITION ERROR ANALYSIS RESULTS")
        print("="*60)
        for key, value in results.items():
            print(f"{key:.<40} {value:>15}")
        print("="*60)
        
        # Warnings
        if self.intersection_angle_deg < 30:
            print("\n⚠️  WARNING: Poor geometry! Intersection angle < 30°")
            print("   Consider repositioning sensors for better accuracy.")
        if self.gdop > 5:
            print("\n⚠️  WARNING: High GDOP indicates geometry amplifies errors.")
        print()
    
    def export_to_excel(self, filename='rdf_analysis.xlsx'):
        """
        Export results to Excel file.
        
        Parameters:
        -----------
        filename : str
            Output Excel filename
        """
        # Create DataFrames for different sections
        config_data = {
            'Parameter': ['Sensor 1 X (m)', 'Sensor 1 Y (m)', 
                         'Sensor 2 X (m)', 'Sensor 2 Y (m)',
                         'Target X (m)', 'Target Y (m)',
                         'Bearing Error (deg)'],
            'Value': [self.s1[0], self.s1[1], 
                     self.s2[0], self.s2[1],
                     self.target[0], self.target[1],
                     self.bearing_error_deg]
        }
        
        results_data = {
            'Metric': ['Baseline Distance (m)', 'Range to Sensor 1 (m)', 
                      'Range to Sensor 2 (m)', 'Intersection Angle (deg)',
                      'GDOP', 'Lateral Error S1 (m)', 'Lateral Error S2 (m)',
                      'Max Position Error (m)', 'Error/Range Ratio (%)'],
            'Value': [self.baseline, self.range1, self.range2, 
                     self.intersection_angle_deg, self.gdop,
                     self.lateral_error1, self.lateral_error2,
                     self.max_position_error, self.error_range_ratio * 100]
        }
        
        df_config = pd.DataFrame(config_data)
        df_results = pd.DataFrame(results_data)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_config.to_excel(writer, sheet_name='Configuration', index=False)
            df_results.to_excel(writer, sheet_name='Results', index=False)
            
            # Format the sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        print(f"Results exported to {filename}")


class InteractiveRDFPlotter:
    """Interactive matplotlib GUI for RDF position error analysis."""
    
    def __init__(self):
        # Initial values
        self.s1_x = -5000
        self.s1_y = 0
        self.s2_x = 5000
        self.s2_y = 0
        self.target_x = 0
        self.target_y = 8000
        self.bearing_error = 2.0
        
        # Create figure and axes
        self.fig = plt.figure(figsize=(16, 10))
        
        # Main plot area
        self.ax = plt.subplot2grid((4, 3), (0, 0), colspan=2, rowspan=4)
        
        # Results text area
        self.ax_results = plt.subplot2grid((4, 3), (0, 2), rowspan=2)
        self.ax_results.axis('off')
        
        # Sliders and controls area
        self.ax_controls = plt.subplot2grid((4, 3), (2, 2), rowspan=2)
        self.ax_controls.axis('off')
        
        # Create sliders
        slider_height = 0.02
        slider_left = 0.70
        slider_width = 0.25
        
        ax_s1x = plt.axes([slider_left, 0.45, slider_width, slider_height])
        ax_s1y = plt.axes([slider_left, 0.42, slider_width, slider_height])
        ax_s2x = plt.axes([slider_left, 0.38, slider_width, slider_height])
        ax_s2y = plt.axes([slider_left, 0.35, slider_width, slider_height])
        ax_tx = plt.axes([slider_left, 0.30, slider_width, slider_height])
        ax_ty = plt.axes([slider_left, 0.27, slider_width, slider_height])
        ax_err = plt.axes([slider_left, 0.22, slider_width, slider_height])
        
        self.slider_s1x = Slider(ax_s1x, 'S1 X (km)', -20, 20, valinit=self.s1_x/1000, valstep=0.1)
        self.slider_s1y = Slider(ax_s1y, 'S1 Y (km)', -20, 20, valinit=self.s1_y/1000, valstep=0.1)
        self.slider_s2x = Slider(ax_s2x, 'S2 X (km)', -20, 20, valinit=self.s2_x/1000, valstep=0.1)
        self.slider_s2y = Slider(ax_s2y, 'S2 Y (km)', -20, 20, valinit=self.s2_y/1000, valstep=0.1)
        self.slider_tx = Slider(ax_tx, 'Target X (km)', -20, 20, valinit=self.target_x/1000, valstep=0.1)
        self.slider_ty = Slider(ax_ty, 'Target Y (km)', 0, 30, valinit=self.target_y/1000, valstep=0.1)
        self.slider_err = Slider(ax_err, 'Bearing Error (°)', 0.1, 10, valinit=self.bearing_error, valstep=0.1)
        
        # Export button
        ax_button = plt.axes([slider_left, 0.15, 0.12, 0.04])
        self.btn_export = Button(ax_button, 'Export to Excel')
        self.btn_export.on_clicked(self.export_callback)
        
        # Print button
        ax_button2 = plt.axes([slider_left + 0.13, 0.15, 0.12, 0.04])
        self.btn_print = Button(ax_button2, 'Print Results')
        self.btn_print.on_clicked(self.print_callback)
        
        # Connect sliders to update function
        self.slider_s1x.on_changed(self.update)
        self.slider_s1y.on_changed(self.update)
        self.slider_s2x.on_changed(self.update)
        self.slider_s2y.on_changed(self.update)
        self.slider_tx.on_changed(self.update)
        self.slider_ty.on_changed(self.update)
        self.slider_err.on_changed(self.update)
        
        # Initial plot
        self.update(None)
        
        plt.show()
    
    def update(self, val):
        """Update plot when sliders change."""
        # Get current values from sliders (convert km to m)
        self.s1_x = self.slider_s1x.val * 1000
        self.s1_y = self.slider_s1y.val * 1000
        self.s2_x = self.slider_s2x.val * 1000
        self.s2_y = self.slider_s2y.val * 1000
        self.target_x = self.slider_tx.val * 1000
        self.target_y = self.slider_ty.val * 1000
        self.bearing_error = self.slider_err.val
        
        # Create model
        self.model = RDFPositionError(
            sensor1_pos=(self.s1_x, self.s1_y),
            sensor2_pos=(self.s2_x, self.s2_y),
            target_pos=(self.target_x, self.target_y),
            bearing_error_deg=self.bearing_error
        )
        
        # Clear and redraw main plot
        self.ax.clear()
        self.plot_geometry()
        
        # Update results text
        self.ax_results.clear()
        self.ax_results.axis('off')
        self.display_results()
        
        self.fig.canvas.draw_idle()
    
    def plot_geometry(self):
        """Plot the sensor-target geometry."""
        s1 = self.model.s1
        s2 = self.model.s2
        target = self.model.target
        
        # Plot sensors
        self.ax.plot(s1[0], s1[1], 'bs', markersize=14, label='Sensor 1', zorder=5)
        self.ax.plot(s2[0], s2[1], 'rs', markersize=14, label='Sensor 2', zorder=5)
        
        # Plot target
        self.ax.plot(target[0], target[1], 'go', markersize=14, label='Target', zorder=5)
        
        # Plot baseline
        self.ax.plot([s1[0], s2[0]], [s1[1], s2[1]], 
                'k--', linewidth=2, alpha=0.5, label='Baseline')
        
        # Plot bearing lines
        line_length = max(self.model.range1, self.model.range2) * 1.3
        
        # Sensor 1 bearing lines
        for angle_offset, style, alpha, lw in [(0, '-', 1.0, 2.5), 
                                                (self.model.bearing_error_rad, '--', 0.5, 1.5), 
                                                (-self.model.bearing_error_rad, '--', 0.5, 1.5)]:
            bearing = self.model.bearing1 + angle_offset
            end_point = s1 + line_length * np.array([np.sin(bearing), np.cos(bearing)])
            self.ax.plot([s1[0], end_point[0]], [s1[1], end_point[1]], 
                   'b' + style, linewidth=lw, alpha=alpha)
        
        # Sensor 2 bearing lines
        for angle_offset, style, alpha, lw in [(0, '-', 1.0, 2.5), 
                                                (self.model.bearing_error_rad, '--', 0.5, 1.5), 
                                                (-self.model.bearing_error_rad, '--', 0.5, 1.5)]:
            bearing = self.model.bearing2 + angle_offset
            end_point = s2 + line_length * np.array([np.sin(bearing), np.cos(bearing)])
            self.ax.plot([s2[0], end_point[0]], [s2[1], end_point[1]], 
                   'r' + style, linewidth=lw, alpha=alpha)
        
        # Plot error circle
        error_circle = Circle(target, self.model.max_position_error, 
                             color='orange', fill=True, alpha=0.25, 
                             edgecolor='orange', linewidth=2.5, linestyle='--',
                             label=f'Position Error', zorder=3)
        self.ax.add_patch(error_circle)
        
        # Add text annotations
        offset = max(self.model.range1, self.model.range2) * 0.03
        self.ax.text(s1[0], s1[1] - offset, 'S1', 
               ha='center', va='top', fontsize=13, fontweight='bold', 
               color='white', bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.8))
        self.ax.text(s2[0], s2[1] - offset, 'S2', 
               ha='center', va='top', fontsize=13, fontweight='bold', 
               color='white', bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.8))
        self.ax.text(target[0], target[1] + offset, 'Target', 
               ha='center', va='bottom', fontsize=13, fontweight='bold', 
               color='white', bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.8))
        
        # Set axis properties
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
        self.ax.set_xlabel('X Position (m)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Y Position (m)', fontsize=12, fontweight='bold')
        
        # Title
        title = 'RDF Position Error Analysis - Interactive'
        self.ax.set_title(title, fontsize=15, fontweight='bold', pad=15)
        
        # Auto-scale with margins
        all_x = [s1[0], s2[0], target[0]]
        all_y = [s1[1], s2[1], target[1]]
        margin = self.model.max_position_error * 1.5
        self.ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        self.ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    
    def display_results(self):
        """Display results in text area."""
        results_text = "═══ RESULTS ═══\n\n"
        results_text += f"Max Position Error:\n  {self.model.max_position_error:.0f} m\n\n"
        results_text += f"Baseline: {self.model.baseline:.0f} m\n"
        results_text += f"Range S1: {self.model.range1:.0f} m\n"
        results_text += f"Range S2: {self.model.range2:.0f} m\n\n"
        results_text += f"Intersection Angle:\n  {self.model.intersection_angle_deg:.1f}°\n"
        results_text += f"GDOP: {self.model.gdop:.2f}\n"
        results_text += f"Error/Range: {self.model.error_range_ratio*100:.2f}%\n\n"
        
        # Warnings
        if self.model.intersection_angle_deg < 30:
            results_text += "⚠️ POOR GEOMETRY\n  Angle < 30°\n"
        elif self.model.gdop > 5:
            results_text += "⚠️ HIGH GDOP\n"
        else:
            results_text += "✓ Good Geometry\n"
        
        self.ax_results.text(0.05, 0.95, results_text, 
                            transform=self.ax_results.transAxes,
                            fontsize=11, verticalalignment='top',
                            family='monospace',
                            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def export_callback(self, event):
        """Export current configuration to Excel."""
        self.model.export_to_excel('rdf_interactive_results.xlsx')
        print("✓ Results exported to 'rdf_interactive_results.xlsx'")
    
    def print_callback(self, event):
        """Print results to console."""
        self.model.print_results()


def parametric_study(bearing_errors, ranges, baseline=10000, 
                     excel_filename='rdf_parametric_study.xlsx'):
    """
    Perform a parametric study varying bearing error and range.
    
    Parameters:
    -----------
    bearing_errors : list
        List of bearing errors to test (degrees)
    ranges : list
        List of target ranges to test (meters)
    baseline : float
        Distance between sensors (meters)
    excel_filename : str
        Output Excel filename
    """
    results = []
    
    for bearing_error in bearing_errors:
        for target_range in ranges:
            # Position sensors symmetrically
            s1 = (-baseline/2, 0)
            s2 = (baseline/2, 0)
            # Position target at specified range, perpendicular to baseline
            target = (0, target_range)
            
            model = RDFPositionError(s1, s2, target, bearing_error)
            
            results.append({
                'Bearing Error (deg)': bearing_error,
                'Target Range (m)': target_range,
                'Baseline (m)': baseline,
                'Intersection Angle (deg)': model.intersection_angle_deg,
                'GDOP': model.gdop,
                'Max Position Error (m)': model.max_position_error,
                'Error/Range (%)': model.error_range_ratio * 100
            })
    
    df = pd.DataFrame(results)
    df.to_excel(excel_filename, index=False)
    print(f"\nParametric study exported to {excel_filename}")
    
    return df


# Main entry point
if __name__ == "__main__":
    print("="*60)
    print("RDF POSITION ERROR CALCULATOR")
    print("="*60)
    print("\nChoose mode:")
    print("1. Interactive GUI (adjust parameters with sliders)")
    print("2. Single calculation (command line)")
    print("3. Parametric study (multiple scenarios)")
    
    choice = input("\nEnter choice (1/2/3) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        print("\nLaunching interactive GUI...")
        print("Use sliders to adjust parameters in real-time!")
        print("Click 'Export to Excel' to save current results")
        print("Click 'Print Results' to display in console")
        InteractiveRDFPlotter()
    
    elif choice == "2":
        print("\n" + "="*60)
        print("SINGLE CALCULATION MODE")
        print("="*60)
        
        # Get user inputs
        s1_x = float(input("Sensor 1 X position (m) [default: -5000]: ") or -5000)
        s1_y = float(input("Sensor 1 Y position (m) [default: 0]: ") or 0)
        s2_x = float(input("Sensor 2 X position (m) [default: 5000]: ") or 5000)
        s2_y = float(input("Sensor 2 Y position (m) [default: 0]: ") or 0)
        t_x = float(input("Target X position (m) [default: 0]: ") or 0)
        t_y = float(input("Target Y position (m) [default: 8000]: ") or 8000)
        bearing_err = float(input("Bearing error (degrees) [default: 2.0]: ") or 2.0)
        
        model = RDFPositionError(
            sensor1_pos=(s1_x, s1_y),
            sensor2_pos=(s2_x, s2_y),
            target_pos=(t_x, t_y),
            bearing_error_deg=bearing_err
        )
        
        model.print_results()
        
        if input("\nExport to Excel? (y/n) [default: y]: ").lower() != 'n':
            model.export_to_excel('rdf_single_analysis.xlsx')
        
        if input("Show plot? (y/n) [default: y]: ").lower() != 'n':
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Plot geometry (simplified version)
            s1, s2, target = model.s1, model.s2, model.target
            ax.plot(s1[0], s1[1], 'bs', markersize=12, label='Sensor 1')
            ax.plot(s2[0], s2[1], 'rs', markersize=12, label='Sensor 2')
            ax.plot(target[0], target[1], 'go', markersize=12, label='Target')
            ax.plot([s1[0], s2[0]], [s1[1], s2[1]], 'k--', linewidth=2, alpha=0.5)
            
            # Error circle
            error_circle = Circle(target, model.max_position_error, 
                                 color='orange', fill=True, alpha=0.2, 
                                 edgecolor='orange', linewidth=2, linestyle='--')
            ax.add_patch(error_circle)
            
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_xlabel('X Position (m)')
            ax.set_ylabel('Y Position (m)')
            ax.set_title(f'RDF Position Error: {model.max_position_error:.0f} m')
            plt.show()
    
    elif choice == "3":
        print("\n" + "="*60)
        print("PARAMETRIC STUDY MODE")
        print("="*60)
        
        baseline = float(input("Baseline distance (m) [default: 10000]: ") or 10000)
        
        print("\nBearing errors to test (comma-separated, degrees)")
        bearing_input = input("[default: 0.5,1,2,3,5]: ") or "0.5,1,2,3,5"
        bearing_errors = [float(x.strip()) for x in bearing_input.split(',')]
        
        print("\nTarget ranges to test (comma-separated, meters)")
        range_input = input("[default: 5000,10000,15000,20000,30000]: ") or "5000,10000,15000,20000,30000"
        ranges = [float(x.strip()) for x in range_input.split(',')]
        
        df_study = parametric_study(
            bearing_errors=bearing_errors,
            ranges=ranges,
            baseline=baseline,
            excel_filename='rdf_parametric_study.xlsx'
        )
        
        print("\nParametric study results (first 10 rows):")
        print(df_study.head(10).to_string(index=False))
        print(f"\nTotal scenarios tested: {len(df_study)}")
    
    else:
        print("Invalid choice. Exiting.")
