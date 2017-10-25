import os
import sys
import time

import bpy
import bge
import mathutils
import math

sys.path.append(os.path.join(os.path.dirname(bpy.data.filepath), 'lib'))
import Leap

class LeapListener(Leap.Listener):
    last_frame_id = None

    def on_connect(self, ctrl):
        print('Leap connected')

    def on_disconnect(self, ctrl):
        print('Leap disconnected')

    def on_frame(self, ctrl):
        scene = bge.logic.getCurrentScene()

        print(ctrl.frame())
        frame = ctrl.frame()

        if(frame and frame.id != self.last_frame_id):
            print(frame.hands[0].palm_position)
            # hand = scene.objects['Hand']
            # if(frame and frame.hands > 0):
                # hand.worldPosition = frame.hands[0].palm_position

        self.last_frame_id = frame.id

SCALE = 1/10

FINGERS_TYPES = (
    Leap.Finger.TYPE_THUMB,
    Leap.Finger.TYPE_INDEX,
    Leap.Finger.TYPE_MIDDLE,
    Leap.Finger.TYPE_RING,
    Leap.Finger.TYPE_PINKY,
)

BONES_TYPES = (
    Leap.Bone.TYPE_METACARPAL,
    Leap.Bone.TYPE_PROXIMAL,
    Leap.Bone.TYPE_INTERMEDIATE,
    Leap.Bone.TYPE_DISTAL,
)

scene = bge.logic.getCurrentScene()
controller = bge.logic.getCurrentController()
owner = controller.owner

if(not 'leap_ctrl' in scene):
    print('new leap controller')
    # scene['leap'] = LeapControl(scene)
    # listener = LeapListener()
    # scene['leap'] = Leap.Controller(listener)
    scene['leap_ctrl'] = Leap.Controller()

ctrl = scene['leap_ctrl']

if(not 'leap_mem' in scene):
    scene['leap_mem'] = {}

memory = scene['leap_mem']

def get_memory(key, default):
    if key not in memory:
        memory[key] = default.copy()

    return memory[key]

def update_hand(hand):
    if not hand.is_valid:
        return

    hand_side = 'L' if hand.is_left else 'R'

    if hand_side == 'L':
         return

    # palm object
    palm_3D_name = '_'.join((hand_side, 'Hand'))
    if not palm_3D_name in scene.objects:
        return

    palm_3D = scene.objects[palm_3D_name]

    # palm position
    palm_3D.worldPosition = mathutils.Vector([
        hand.palm_position.x,
        -hand.palm_position.z,
        hand.palm_position.y,
    ]) * SCALE

    # palm orientation
    palm_3D.worldOrientation = mathutils.Matrix((
        (hand.basis.x_basis.x, -hand.basis.z_basis.x, hand.basis.y_basis.x),
        (-hand.basis.x_basis.z, hand.basis.z_basis.z, -hand.basis.y_basis.z),
        (hand.basis.x_basis.y, -hand.basis.z_basis.y, hand.basis.y_basis.y)
    ))

    # palm scaling
    palm_initial_scale = get_memory('_'.join((hand_side, 'Palm', 'worldScale')), palm_3D.worldScale)

    palm_3D.worldScale = mathutils.Vector((
        hand.palm_width * SCALE / palm_initial_scale.x,
        palm_initial_scale.z,
        palm_initial_scale.y,
    ))

    # wrist position
    wrist_3D_name = '_'.join((hand_side, 'Wrist'))
    if not wrist_3D_name in scene.objects:
        return

    wrist_3D = scene.objects[wrist_3D_name]

    wrist_3D.worldPosition = mathutils.Vector([
        hand.wrist_position.x,
        -hand.wrist_position.z,
        hand.wrist_position.y,
    ]) * SCALE



    # # armature object
    # palm_armature_name = '_'.join((hand_side, 'Hand', 'Armature'))
    # if not palm_armature_name in scene.objects:
    #     return
    #
    # palm_armature = scene.objects[palm_armature_name]
    #
    # # armature position
    # palm_armature.worldPosition = palm_3D.worldPosition
    #
    # # armature rotation
    # palm_armature.worldOrientation = palm_3D.worldOrientation

    for finger in hand.fingers:

        for bone_type in BONES_TYPES:

            bone = finger.bone(bone_type)
            if not bone.is_valid:
                continue

            bone_3D_name = '_'.join((hand_side, 'Bone', str(finger.type), str(bone.type)))
            if not bone_3D_name in scene.objects:
                continue

            bone_3D = scene.objects[bone_3D_name]


            # bone orientation
            # bone_orientation = mathutils.Matrix((
            #     (bone.basis.x_basis.x, -bone.basis.x_basis.z, bone.basis.x_basis.y),
            #     (-bone.basis.z_basis.x, bone.basis.z_basis.z, -bone.basis.z_basis.y),
            #     (bone.basis.y_basis.x, -bone.basis.y_basis.z, bone.basis.y_basis.y)
            # ))

            # bone_orientation.invert()

            bone_3D.localOrientation = mathutils.Matrix((
                (bone.basis.x_basis.x, -bone.basis.z_basis.x, bone.basis.y_basis.x),
                (-bone.basis.x_basis.z, bone.basis.z_basis.z, -bone.basis.y_basis.z),
                (bone.basis.x_basis.y, -bone.basis.z_basis.y, bone.basis.y_basis.y)
            ))

            # bone position
            bone_3D.worldPosition = mathutils.Vector([
                bone.prev_joint.x,
                -bone.prev_joint.z,
                bone.prev_joint.y,
            ]) * SCALE

            # scale bone
            initial_scale = get_memory('_'.join((hand_side, str(finger.type), str(bone.type), 'worldScale')), bone_3D.worldScale)

            bone_3D.worldScale = mathutils.Vector((
                initial_scale.x,
                bone.length * SCALE / initial_scale.z,
                initial_scale.y,
            ))

            # set bone tip
            bone_3D_tip_name = '_'.join((hand_side, 'Bone', str(finger.type), str(bone.type), 'Tip'))
            if bone_3D_tip_name in scene.objects:
                bone_3D_tip = scene.objects[bone_3D_tip_name]

                tip_position = bone.next_joint
                bone_3D_tip.worldPosition = mathutils.Vector([
                    tip_position.x,
                    -tip_position.z,
                    tip_position.y,
                ]) * SCALE

def leap():
    frame = ctrl.frame()
    last_frame_id = scene['leap_last_frame_id'] if 'leap_last_frame_id' in scene else None

    if(frame and frame.id != last_frame_id):
        for hand in frame.hands:
            update_hand(hand)

    scene['leap_last_frame_id'] = frame.id

leap()
