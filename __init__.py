# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

import bpy
from bpy.app.handlers import persistent

class DynamicDistanceProperties(bpy.types.PropertyGroup):
    target_object: bpy.props.PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Object to measure distance to"
    )
    scale_modifier: bpy.props.FloatProperty(
        name="Scale Modifier",
        default=1.0,
        description="Scale factor for distance"
    )
    distance_value: bpy.props.FloatProperty(
        name="Distance Value",
        default=0.0,
        description="Current distance value"
    )
    enable_dynamic_text: bpy.props.BoolProperty(
        name="Enable Dynamic Text",
        default=True,
        description="Enable or disable dynamic text update"
    )

@persistent
def update_text_content(scene):
    for obj in scene.objects:
        if obj.type == 'FONT' and obj.data.dynamic_distance_props.enable_dynamic_text:
            target = obj.data.dynamic_distance_props.target_object
            if target:
                distance = (obj.location - target.location).length
                scaled_distance = distance * obj.data.dynamic_distance_props.scale_modifier
                obj.data.body = f"{scaled_distance:.2f}"

class OBJECT_PT_dynamic_distance(bpy.types.Panel):
    bl_label = "Dynamic Distance Text"
    bl_idname = "OBJECT_PT_dynamic_distance"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'FONT'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj.data.dynamic_distance_props, "enable_dynamic_text", text="Enable Dynamic Text")
        layout.prop(obj.data.dynamic_distance_props, "target_object")
        layout.prop(obj.data.dynamic_distance_props, "scale_modifier")
        layout.operator("object.bake_dynamic_distance", text="Bake Distance Animation")
        layout.operator("object.delete_bake_dynamic_distance", text="Delete Baked Animation")

class OBJECT_OT_bake_dynamic_distance(bpy.types.Operator):
    bl_idname = "object.bake_dynamic_distance"
    bl_label = "Bake Dynamic Distance"
    bl_description = "Bake the dynamic distance text into keyframes"

    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end

        if obj.type != 'FONT' or not obj.data.dynamic_distance_props.target_object:
            self.report({'WARNING'}, "Select a text object with a valid target object")
            return {'CANCELLED'}

        for frame in range(start_frame, end_frame + 1):
            scene.frame_set(frame)
            target = obj.data.dynamic_distance_props.target_object
            distance = (obj.location - target.location).length
            scaled_distance = distance * obj.data.dynamic_distance_props.scale_modifier
            obj.data.dynamic_distance_props.distance_value = scaled_distance
            obj.data.dynamic_distance_props.keyframe_insert(data_path="distance_value", frame=frame)

        self.report({'INFO'}, "Baking completed")
        return {'FINISHED'}

class OBJECT_OT_delete_bake_dynamic_distance(bpy.types.Operator):
    bl_idname = "object.delete_bake_dynamic_distance"
    bl_label = "Delete Baked Animation"
    bl_description = "Delete the baked keyframes of the dynamic distance"

    def execute(self, context):
        obj = context.object

        if obj.type != 'FONT':
            self.report({'WARNING'}, "Select a text object")
            return {'CANCELLED'}

        fcurves = obj.data.animation_data.action.fcurves if obj.data.animation_data else []
        for fcurve in fcurves:
            if fcurve.data_path == "dynamic_distance_props.distance_value":
                obj.data.animation_data.action.fcurves.remove(fcurve)

        self.report({'INFO'}, "Baked animation deleted")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DynamicDistanceProperties)
    bpy.types.TextCurve.dynamic_distance_props = bpy.props.PointerProperty(type=DynamicDistanceProperties)
    bpy.utils.register_class(OBJECT_PT_dynamic_distance)
    bpy.utils.register_class(OBJECT_OT_bake_dynamic_distance)
    bpy.utils.register_class(OBJECT_OT_delete_bake_dynamic_distance)
    bpy.app.handlers.frame_change_post.append(update_text_content)

def unregister():
    bpy.utils.unregister_class(DynamicDistanceProperties)
    del bpy.types.TextCurve.dynamic_distance_props
    bpy.utils.unregister_class(OBJECT_PT_dynamic_distance)
    bpy.utils.unregister_class(OBJECT_OT_bake_dynamic_distance)
    bpy.utils.unregister_class(OBJECT_OT_delete_bake_dynamic_distance)
    bpy.app.handlers.frame_change_post.remove(update_text_content)

if __name__ == "__main__":
    register()