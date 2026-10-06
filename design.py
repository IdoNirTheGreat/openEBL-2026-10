from pathlib import Path

import gdsfactory as gf
from ubcpdk import PDK, cells
import dwdm


USERNAME = "IdoNirTheGreat"

OUTPUT_DIR = Path("submissions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / f"EBeam_{USERNAME}.gds"

PDK.activate()


# ============================================================
# COURSE FLOORPLAN
# ============================================================

FLOORPLAN_WIDTH = 605.0
FLOORPLAN_HEIGHT = 410.0

# SiEPIC EBeam FloorPlan layer
FLOORPLAN_LAYER = (99, 0)


# ============================================================
# PLACEMENT
# ============================================================

RING_REFERENCE_X = 350.0
RING_REFERENCE_Y = 190.584

DWDM_X = -125.55
DWDM_Y = 0.0


# ============================================================
# PARAMETERS
# ============================================================

# Same gap as DWDM
RING_REFERENCE_GAP = 0.2
RING_REFERENCE_RADIUS = 10.0


# ============================================================
# RING REFERENCE
# ============================================================

ring_reference = cells.ring_double(
    radius=RING_REFERENCE_RADIUS,
    gap=RING_REFERENCE_GAP,
    length_x=0.01,
    length_y=0.01,
    length_extension=10.0,
    cross_section="strip",
)

ring_reference_test = cells.add_fiber_array(
    component=ring_reference,
    component_name=f"{USERNAME}_RING_REFERENCE",
    with_loopback=False,
)


# ============================================================
# DWDM
# ============================================================

dwdm_test = dwdm.dwdm_splitter()


# ============================================================
# TOP CELL
# ============================================================

top = gf.Component(f"EBeam_{USERNAME}")

ring_ref = top << ring_reference_test
dwdm_ref = top << dwdm_test


# ============================================================
# POSITIONING
# ============================================================

ring_ref.move(
    (
        RING_REFERENCE_X,
        RING_REFERENCE_Y,
    )
)

dwdm_ref.move(
    (
        DWDM_X,
        DWDM_Y,
    )
)


# ============================================================
# CHECK DEVICE SIZE BEFORE ADDING FLOORPLAN
# ============================================================

device_xmin = top.xmin
device_xmax = top.xmax
device_ymin = top.ymin
device_ymax = top.ymax

device_width = device_xmax - device_xmin
device_height = device_ymax - device_ymin

print("Device bounding box:")
for name, ref in (("DWDM", dwdm_ref), ("Ring reference", ring_ref)):
    print(
        f"{name} bbox: X {ref.xmin:.3f} -> {ref.xmax:.3f} um; "
        f"Y {ref.ymin:.3f} -> {ref.ymax:.3f} um"
    )
print(f"  X: {device_xmin:.3f} -> {device_xmax:.3f} um")
print(f"  Y: {device_ymin:.3f} -> {device_ymax:.3f} um")
print(
    f"  Size: {device_width:.3f} x "
    f"{device_height:.3f} um"
)


if device_width > FLOORPLAN_WIDTH:
    raise ValueError(
        f"Layout width {device_width:.3f} um exceeds "
        f"{FLOORPLAN_WIDTH:.3f} um."
    )

if device_height > FLOORPLAN_HEIGHT:
    raise ValueError(
        f"Layout height {device_height:.3f} um exceeds "
        f"{FLOORPLAN_HEIGHT:.3f} um."
    )


# ============================================================
# FLOORPLAN
#
# SiEPIC's EBeam DRC expects device-layer geometry to be
# enclosed by a FloorPlan polygon.
#
# Place the lower-left corner of the 605 x 410 um floorplan
# at the lower-left corner of the actual device geometry.
# ============================================================

floorplan = gf.components.rectangle(
    size=(
        FLOORPLAN_WIDTH,
        FLOORPLAN_HEIGHT,
    ),
    layer=FLOORPLAN_LAYER,
)

floorplan_ref = top << floorplan

floorplan_ref.move(
    (
        device_xmin,
        device_ymin,
    )
)


# ============================================================
# FINAL CHECK
# ============================================================

print()
print("Course floorplan:")
print(
    f"  {FLOORPLAN_WIDTH:.1f} x "
    f"{FLOORPLAN_HEIGHT:.1f} um"
)

print(
    f"  X: {device_xmin:.3f} -> "
    f"{device_xmin + FLOORPLAN_WIDTH:.3f} um"
)

print(
    f"  Y: {device_ymin:.3f} -> "
    f"{device_ymin + FLOORPLAN_HEIGHT:.3f} um"
)


# ============================================================
# EXPORT
# ============================================================

top.write_gds(OUTPUT_FILE)

print()
print(f"Saved to: {OUTPUT_FILE.resolve()}")

top.show()
