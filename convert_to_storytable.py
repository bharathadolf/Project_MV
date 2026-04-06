import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, "pipeline_data.json")
storytable_file_path = os.path.join(script_dir, "pipeline_data.storytable")

with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define the columns that will be used for shots.
# This makes it easy to add more columns later.
columns = ["Scene_ID", "Shot_ID", "Duration", "Camera", "Visual_Beat", "Animation_Notes", "Assets", "Lighting", "Sound"]

with open(storytable_file_path, 'w', encoding='utf-8') as f:
    # Optional metadata header
    f.write(f"@PROJECT|{data.get('project', 'Project')}\n\n")
    
    for scene in data.get('scenes', []):
        scene_id = scene.get('scene_id', '')
        name = scene.get('scene_name', '')
        duration = scene.get('scene_duration', '')
        color = scene.get('color_palette', '')
        
        # Write scene definition
        f.write(f"@SCENE|{scene_id}|{name}|{duration}|{color}\n")
        
        # Write column definitions so GUI knows how to parse subsequent shots
        f.write(f"@COLUMNS|{'|'.join(columns)}\n")
        
        # Write each shot
        for shot in scene.get('shots', []):
            row_data = [
                str(scene_id),
                str(shot.get('shot_id', '')),
                str(shot.get('duration_seconds', '')),
                str(shot.get('camera', '')),
                str(shot.get('visual_beat', '')),
                str(shot.get('animation_notes', '')),
                ", ".join(shot.get('assets', [])), # Convert list back to string
                str(shot.get('lighting', '')),
                str(shot.get('sound', ''))
            ]
            f.write(f"@SHOT|{'|'.join(row_data)}\n")
        
        # Add spacing between scenes
        f.write("\n")

print("Successfully generated:", storytable_file_path)
