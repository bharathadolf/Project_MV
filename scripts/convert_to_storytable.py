import json
import os
import re

def convert_json_to_storytable(json_file_path, storytable_file_path):
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
    return storytable_file_path

def convert_md_to_storytable(md_file_path, storytable_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    project_name = "Visual Narrative Breakdown"
    scenes = []
    current_scene = None
    
    # Regex patterns
    scene_pattern = re.compile(r'^##\s*\*\*Scene\s+(\d+)\s+[–-]\s+(.*?)\*\*')
    duration_pattern = re.compile(r'^\*\*Duration:\*\*\s*(.*)')
    color_pattern = re.compile(r'^\*\*Color:\*\*\s*(.*)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        scene_match = scene_pattern.match(line)
        if scene_match:
            if current_scene:
                scenes.append(current_scene)
            current_scene = {
                'scene_id': scene_match.group(1),
                'scene_name': scene_match.group(2).strip(),
                'scene_duration': '',
                'color_palette': '',
                'shots': []
            }
            continue
            
        if current_scene:
            dur_match = duration_pattern.match(line)
            if dur_match:
                current_scene['scene_duration'] = dur_match.group(1).strip()
                continue
                
            col_match = color_pattern.match(line)
            if col_match:
                current_scene['color_palette'] = col_match.group(1).strip()
                continue
                
            if line.startswith('|') and 'Shot ID' not in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 8:
                    shot = {
                        'shot_id': parts[0],
                        'duration_seconds': parts[1].replace('s', ''),
                        'camera': parts[2],
                        'visual_beat': parts[3],
                        'animation_notes': parts[4],
                        'assets': [a.strip() for a in parts[5].split(',')],
                        'lighting': parts[6],
                        'sound': parts[7]
                    }
                    current_scene['shots'].append(shot)
    
    if current_scene:
        scenes.append(current_scene)
        
    columns = ["Scene_ID", "Shot_ID", "Duration", "Camera", "Visual_Beat", "Animation_Notes", "Assets", "Lighting", "Sound"]

    with open(storytable_file_path, 'w', encoding='utf-8') as f:
        f.write(f"@PROJECT|{project_name}\n\n")
        
        for scene in scenes:
            scene_id = scene.get('scene_id', '')
            name = scene.get('scene_name', '')
            duration = scene.get('scene_duration', '')
            color = scene.get('color_palette', '')
            
            f.write(f"@SCENE|{scene_id}|{name}|{duration}|{color}\n")
            f.write(f"@COLUMNS|{'|'.join(columns)}\n")
            
            for shot in scene.get('shots', []):
                row_data = [
                    str(scene_id),
                    str(shot.get('shot_id', '')),
                    str(shot.get('duration_seconds', '')),
                    str(shot.get('camera', '')),
                    str(shot.get('visual_beat', '')),
                    str(shot.get('animation_notes', '')),
                    ", ".join(shot.get('assets', [])),
                    str(shot.get('lighting', '')),
                    str(shot.get('sound', ''))
                ]
                f.write(f"@SHOT|{'|'.join(row_data)}\n")
            
            f.write("\n")

    print("Successfully generated from MD:", storytable_file_path)
    return storytable_file_path

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_file_path = os.path.join(project_dir, "data", "pipeline_data.json")
    storytable_file_path = os.path.join(project_dir, "data", "pipeline_data.storytable")
    
    if os.path.exists(json_file_path):
        convert_json_to_storytable(json_file_path, storytable_file_path)
    else:
        print(f"Error: Could not find {json_file_path}")
