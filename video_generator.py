import bpy
import math
import os
from PIL import Image, ImageEnhance


blend_file_path = "./test.blend"
output_path = r".\render\frame_"
output_path_abs = os.path.abspath(output_path)
zoom_level = 20
rotation_radius = 30
resolution = (800, 480)
frames = 90


# Load the .blend file
bpy.ops.wm.open_mainfile(filepath=blend_file_path)

# Define the target object (assumes there's at least one object in the scene)
target_object = bpy.data.objects[0]

# Add a camera if there is no camera in the scene
if not bpy.data.cameras:
    bpy.ops.object.camera_add()
    camera = bpy.context.object
else:
    camera = bpy.data.objects[0]
    if camera.type != 'CAMERA':
        bpy.ops.object.camera_add()
        camera = bpy.context.object

# Set up camera settings
camera.location = (0, -10, 5)
camera.rotation_euler = (math.radians(90), 0, 0)
bpy.context.scene.camera = camera

# Set the camera lens (zoom level)
camera.data.lens = zoom_level

# Add an empty to act as the target for the camera to look at
bpy.ops.object.empty_add(location=target_object.location)
target_empty = bpy.context.object
target_empty.name = "CameraTarget"

# Add a Track To constraint to the camera
track_constraint = camera.constraints.new(type='TRACK_TO')
track_constraint.target = target_empty
track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
track_constraint.up_axis = 'UP_Y'

# Set up animation for camera rotation
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = frames
bpy.context.scene.render.fps = 24

# Create keyframes for camera rotation
for frame in range(1, frames + 1):
    angle = 2 * math.pi * (frame / frames)
    camera.location.x = rotation_radius * math.cos(angle)
    camera.location.y = rotation_radius * math.sin(angle)
    camera.location.z = 0
    camera.keyframe_insert(data_path="location", frame=frame)

# Set the background color to black
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)  # (R, G, B, Alpha)

# Set render settings for PNG sequence
bpy.context.scene.render.resolution_x = resolution[0]
bpy.context.scene.render.resolution_y = resolution[1]
bpy.context.scene.render.fps = 24
bpy.context.scene.render.filepath = output_path_abs
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # To include transparency if needed
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.render.film_transparent = True

def increase_brightness(image_path, brightness_factor):
    # 이미지 열기
    image = Image.open(image_path)
    
    # 밝기 조절
    enhancer = ImageEnhance.Brightness(image)
    brightened_image = enhancer.enhance(brightness_factor)
    
    # 밝기 조절된 이미지 저장 (원본 파일 덮어쓰기)
    brightened_image.save(image_path)
    
# Render the animation frame by frame
for frame in range(1, frames + 1):
    bpy.context.scene.frame_set(frame)
    abs_path = output_path_abs + f"{frame:04d}.png"
    bpy.context.scene.render.filepath = abs_path
    bpy.ops.render.render(write_still=True)
    increase_brightness(abs_path, 1.5)