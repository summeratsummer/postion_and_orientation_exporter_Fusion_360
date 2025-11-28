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
        
        # Get all component origins
        components_data = get_all_component_origins(design)
        
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

def get_all_component_origins(design):
    """
    Get origin and RPY for all components in the assembly
    """
    components_data = []
    root = design.rootComponent
    
    # Get all occurrences in the assembly
    all_occurrences = root.allOccurrences
    
    for occ in all_occurrences:
        try:
            x, y, z, roll, pitch, yaw = get_component_origin_rpy(occ)
            
            component_info = {
                'name': occ.name,
                'component': occ.component.name,
                'x': x, 'y': y, 'z': z,
                'roll': roll, 'pitch': pitch, 'yaw': yaw
            }
            components_data.append(component_info)
            
        except Exception as e:
            print(f"Error processing {occ.name}: {e}")
    
    return components_data

def display_results(ui, components_data):
    """
    #Display the results in a message box and text output
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
        
        # URDF format
        xyz = f"{comp['x']:.6f} {comp['y']:.6f} {comp['z']:.6f}"
        rpy = f"{comp['roll']:.6f} {comp['pitch']:.6f} {comp['yaw']:.6f}"
        results += f"URDF: <origin xyz=\"{xyz}\" rpy=\"{rpy}\"/>\n\n"
    
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
    print("\n" + "="*80)
    print("COMPONENT ORIGINS FOR URDF")
    print("="*80)
    for comp in components_data:
        xyz = f"{comp['x']:.6f} {comp['y']:.6f} {comp['z']:.6f}"
        rpy = f"{comp['roll']:.6f} {comp['pitch']:.6f} {comp['yaw']:.6f}"
        print(f"<!-- {comp['name']} -->")
        print(f'<origin xyz="{xyz}" rpy="{rpy}"/>')
        print()
