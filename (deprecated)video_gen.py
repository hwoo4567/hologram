import bpy
import math

# Path to your .blend file
blend_file_path = "./test.blend"
# Output path for the rendered video
output_path = r"D:\zDev\vsc\project\hologram\render.mp4"

# Adjust the zoom level (focal length)
zoom_level = 20  # Change this value to adjust zoom level
# camera rotation radius
rotation_radius = 30

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
frames = 250
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

# Set render settings for video
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.fps = 24
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.render.film_transparent = True

# Render the animation
bpy.ops.render.render(animation=True)
