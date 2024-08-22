import bpy  # requires python 3.11.*

# Load the .blend file
bpy.ops.wm.open_mainfile(filepath="./test.blend")

# Set up rendering settings
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = r"D:\zDev\vsc\project\hologram\render.png"

# Render the scene
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.ops.render.render(write_still=True)
