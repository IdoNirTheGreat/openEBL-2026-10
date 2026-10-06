import gdsfactory as gf
from ubcpdk import PDK, cells

PDK.activate()


@gf.cell
def dwdm_splitter():
    """Vertical B-to-D bus: 50 um Ring A on the right, 10 um Ring C on the left.

    A, B (input), C, D couplers stay at y = 381, 254, 127, 0 um.
    Built-in PDK rings include both coupling buses and DevRec geometry.
    """
    c = gf.Component()
    pitch = 127.0
    short_length = 20.0
    long_length = 200.0
    bd_bend_radius = 30.0
    bus_x = long_length + bd_bend_radius
    bus_top_y = 2 * pitch - bd_bend_radius
    bus_bottom_y = bd_bend_radius

    stubs = {}
    for name, y, length in (
        ("A", 3 * pitch, short_length),
        ("B", 2 * pitch, long_length),
        ("C", pitch, short_length),
        ("D", 0.0, long_length),
    ):
        stub = c << cells.straight(length=length, cross_section="strip")
        stub.move((0, y))
        gc = c << cells.ebeam_gc_te1550()
        gc.connect("o1", stub.ports["o1"])
        stubs[name] = stub
        if name == "B":
            c.add_label(
                text="opt_in_TE_1550_device_IdoNirTheGreat_DWDM",
                position=gc.ports["o1"].center,
                layer=(10, 0),
            )

    # PDK o1/o2 = bottom-bus left/right; o3/o4 = top-bus left/right.
    # Rotate the complete cell to align its bottom bus with the U bus.
    # Original ring-center Y targets: A = 169 um, C = 55 um.
    # Extend bus ports beyond each ring before attaching external routes.
    ring_A = c << cells.ring_double(
        radius=50.0, gap=0.2, length_x=0.01, length_y=0.01,
        length_extension=53.0, cross_section="strip",
    )
    ring_A.rotate(270)
    ring_A.move((bus_x, bus_top_y - 50.0 - 5.0))

    ring_C = c << cells.ring_double(
        radius=10.0, gap=0.2, length_x=0.01, length_y=0.01,
        length_extension=13.0, cross_section="strip",
    )
    ring_C.rotate(90)
    ring_C.move((bus_x, bus_bottom_y + 2 * 10.0 + 5.0))

    # Main-bus flow goes down: input A.o1, through A.o2, input C.o2,
    # through C.o1. Upward drop ports A.o3 and C.o4 feed the outputs.
    for ring, add_port in ((ring_A, "o4"), (ring_C, "o3")):
        terminator = c << cells.ebeam_terminator_te1550()
        terminator.connect("o1", ring.ports[add_port])

    def route(p1, p2, radius=10.0, waypoints=None):
        return gf.routing.route_single(
            c, port1=p1, port2=p2, radius=radius, waypoints=waypoints,
            bend=cells.bend_euler, straight=cells.straight,
            cross_section="strip",
        )

    route(stubs["B"].ports["o2"], ring_A.ports["o1"],
          radius=bd_bend_radius, waypoints=[(bus_x, 2 * pitch)])
    route(ring_A.ports["o2"], ring_C.ports["o2"])
    route(ring_C.ports["o1"], stubs["D"].ports["o2"],
          radius=bd_bend_radius, waypoints=[(bus_x, 0.0)])
    route(ring_A.ports["o3"], stubs["A"].ports["o2"])
    route(ring_C.ports["o4"], stubs["C"].ports["o2"])
    return c
