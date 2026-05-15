class Offsets:
    # Static Roots
    # Found via PlayerController.OnNetworkSpawn -> stsfld 0x0400027f
    LOCAL_INSTANCE = 0x0400027f 

    # PlayerController Offsets
    WALK_SPEED = 0x283
    SPRINT_SPEED = 0x284
    JUMP_FORCE = 0x285
    IS_DEAD = 0x2D9
    HAND_MANAGER = 0x250

    # HandManager Offsets
    GRAB_PACK = 0x20

    # GrabPack Offsets
    # Field index 7 -> 0x107
    MAX_DISTANCE = 0x107

    # HuggyAI Offsets
    # Static instance found via [Class + 0xD0] + 0x0
    # Field indices: chase=6, vision=8
    HUGGY_CHASE_SPEED = 0x176
    HUGGY_VISION_RANGE = 0x178

    # Transform -> Position
    TRANSFORM = 0x50
    POS_X = 0x90
    POS_Y = 0x94
    POS_Z = 0x98
