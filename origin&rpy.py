import adsk.core, adsk.fusion, adsk.fusion, traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        
        # Check if a design is active
        if not design:
            ui.messageBox('No active design found')
            return
        
        # Get all component data with mass and inertia
        components_data = get_all_component_data(design)
        
        # Display results
        display_results(ui, components_data)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def get_component_origin_rpy(occurrence):
    """
    Get the origin position and RPY angles for a component occurrence
    Returns: (x, y, z, roll, pitch, yaw)
    """
    # Get the transformation matrix relative to root
    transform = occurrence.transform2
    
    # Extract translation (convert cm to meters)
    translation = transform.translation
    x = translation.x * 0.01
    y = translation.y * 0.01
    z = translation.z * 0.01
    
    # Extract RPY angles
    roll, pitch, yaw = matrix_to_rpy(transform)
    
    return x, y, z, roll, pitch, yaw

def matrix_to_rpy(transform):
    """
    Convert transformation matrix to roll, pitch, yaw angles
    """
    m = transform.asArray()
    
    # Extract the 3x3 rotation matrix
    r11, r12, r13 = m[0], m[1], m[2]
    r21, r22, r23 = m[4], m[5], m[6]
    r31, r32, r33 = m[8], m[9], m[10]
    
    # Calculate RPY angles
    # Roll (x-axis rotation)
    roll = math.atan2(r32, r33)
    
    # Pitch (y-axis rotation)
    pitch = math.atan2(-r31, math.sqrt(r32*r32 + r33*r33))
    
    # Yaw (z-axis rotation)
    yaw = math.atan2(r21, r11)
    
    return roll, pitch, yaw

def get_mass_properties(occurrence):
    """
    Get mass properties for a component
    """
    try:
        # Get physical properties from the occurrence's component
        phys_props = occurrence.component.getPhysicalProperties(
            adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        
        mass = phys_props.mass  # kg
        volume = phys_props.volume * 1e-6  # cm³ to m³
        
        # Center of mass (convert cm to m)
        com = phys_props.centerOfMass
        center_of_mass = (com.x * 0.01, com.y * 0.01, com.z * 0.01)
        
        # Get inertia tensor (convert from kg·cm² to kg·m²)
        inertia = phys_props.getXYZMomentsOfInertia()
        inertia_xx = inertia[0] * 1e-4
        inertia_yy = inertia[1] * 1e-4
        inertia_zz = inertia[2] * 1e-4
        
        # Products of inertia (convert from kg·cm² to kg·m²)
        prod_inertia = phys_props.getXYZProductsOfInertia()
        inertia_xy = prod_inertia[0] * 1e-4
        inertia_xz = prod_inertia[1] * 1e-4
        inertia_yz = prod_inertia[2] * 1e-4
        
        return {
            'mass': mass,
            'center_of_mass': center_of_mass,
            'inertia_xx': inertia_xx,
            'inertia_xy': inertia_xy,
            'inertia_xz': inertia_xz,
            'inertia_yy': inertia_yy,
            'inertia_yz': inertia_yz,
            'inertia_zz': inertia_zz,
            'volume': volume
        }
        
    except Exception as e:
        print(f"Error getting mass properties for {occurrence.name}: {e}")
        # Return default values
        return {
            'mass': 0.1,
            'center_of_mass': (0, 0, 0),
            'inertia_xx': 0.001,
            'inertia_xy': 0.0,
            'inertia_xz': 0.0,
            'inertia_yy': 0.001,
            'inertia_yz': 0.0,
            'inertia_zz': 0.001,
            'volume': 0.001
        }

def get_all_component_data(design):
    """
    Get origin, RPY, mass, and inertia for all components in the assembly
    """
    components_data = []
    root = design.rootComponent
    
    # Get all occurrences in the assembly
    all_occurrences = root.allOccurrences
    
    for occ in all_occurrences:
        try:
            x, y, z, roll, pitch, yaw = get_component_origin_rpy(occ)
            
            # Get mass properties
            mass_props = get_mass_properties(occ)
            
            component_info = {
                'name': occ.name,
                'component': occ.component.name,
                'x': x, 'y': y, 'z': z,
                'roll': roll, 'pitch': pitch, 'yaw': yaw,
                'mass': mass_props['mass'],
                'center_of_mass': mass_props['center_of_mass'],
                'inertia_xx': mass_props['inertia_xx'],
                'inertia_xy': mass_props['inertia_xy'],
                'inertia_xz': mass_props['inertia_xz'],
                'inertia_yy': mass_props['inertia_yy'],
                'inertia_yz': mass_props['inertia_yz'],
                'inertia_zz': mass_props['inertia_zz'],
                'volume': mass_props['volume']
            }
            components_data.append(component_info)
            
        except Exception as e:
            print(f"Error processing {occ.name}: {e}")
    
    return components_data

# Version 2 counts the component click ok and the things pops-up
def display_results(ui, components_data):
    """
    Display the results in a message box and text output
    """
    if not components_data:
        ui.messageBox('No components found')
        return
    
    # Create results text
    results = f"FOUND {len(components_data)} COMPONENTS:\n\n"
    results += "Format: Component (Position in meters, RPY in radians)\n"
    results += "=" * 80 + "\n\n"
    
    for comp in components_data:
        results += f"Component: {comp['name']}\n"
        results += f"Base: {comp['component']}\n"
        results += f"Position: ({comp['x']:.6f}, {comp['y']:.6f}, {comp['z']:.6f}) m\n"
        results += f"RPY: ({comp['roll']:.6f}, {comp['pitch']:.6f}, {comp['yaw']:.6f}) rad\n"
        results += f"Mass: {comp['mass']:.6f} kg\n"
        results += f"Center of Mass: ({comp['center_of_mass'][0]:.6f}, {comp['center_of_mass'][1]:.6f}, {comp['center_of_mass'][2]:.6f}) m\n"
        results += f"Inertia: Ixx={comp['inertia_xx']:.6f}, Iyy={comp['inertia_yy']:.6f}, Izz={comp['inertia_zz']:.6f} kg·m²\n"
        
        # URDF format
        xyz = f"{comp['x']:.6f} {comp['y']:.6f} {comp['z']:.6f}"
        rpy = f"{comp['roll']:.6f} {comp['pitch']:.6f} {comp['yaw']:.6f}"
        results += f"URDF Origin: <origin xyz=\"{xyz}\" rpy=\"{rpy}\"/>\n\n"
    
    # Show ALL components in popup using multiple messages if needed
    if len(results) <= 2000:
        ui.messageBox(results)
    else:
        # Split into multiple messages to show all components
        lines = results.split('\n')
        current_message = ""
        message_count = 1
        
        for line in lines:
            if len(current_message + line + '\n') < 1900:
                current_message += line + '\n'
            else:
                ui.messageBox(f"PART {message_count}:\n\n{current_message}")
                message_count += 1
                current_message = line + '\n'
        
        # Show the last part
        if current_message:
            ui.messageBox(f"PART {message_count}:\n\n{current_message}")
    
    # Also print to Text Commands window
    print("\n" + "="*100)
    print("COMPLETE URDF DATA FOR ALL COMPONENTS")
    print("="*100)
    for comp in components_data:
        xyz = f"{comp['x']:.6f} {comp['y']:.6f} {comp['z']:.6f}"
        rpy = f"{comp['roll']:.6f} {comp['pitch']:.6f} {comp['yaw']:.6f}"
        com_xyz = f"{comp['center_of_mass'][0]:.6f} {comp['center_of_mass'][1]:.6f} {comp['center_of_mass'][2]:.6f}"
        
        print(f"<!-- ===== {comp['name']} ===== -->")
        print(f'<link name="{comp["name"]}">')
        
        # Inertial properties
        print('  <inertial>')
        print(f'    <origin xyz="{com_xyz}" rpy="0 0 0"/>')
        print(f'    <mass value="{comp["mass"]:.6f}"/>')
        print(f'    <inertia ixx="{comp["inertia_xx"]:.6f}" ixy="{comp["inertia_xy"]:.6f}" ixz="{comp["inertia_xz"]:.6f}" iyy="{comp["inertia_yy"]:.6f}" iyz="{comp["inertia_yz"]:.6f}" izz="{comp["inertia_zz"]:.6f}"/>')
        print('  </inertial>')
        
        # Visual properties
        print('  <visual>')
        print(f'    <origin xyz="{xyz}" rpy="{rpy}"/>')
        print('    <geometry>')
        print(f'      <mesh filename="package://robot_meshes/{comp["name"]}.stl"/>')
        print('    </geometry>')
        print('  </visual>')
        
        # Collision properties
        print('  <collision>')
        print(f'    <origin xyz="{xyz}" rpy="{rpy}"/>')
        print('    <geometry>')
        print(f'      <mesh filename="package://robot_meshes/{comp["name"]}.stl"/>')
        print('    </geometry>')
        print('  </collision>')
        
        print('</link>')
        print()