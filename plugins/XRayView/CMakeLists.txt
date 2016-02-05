add_custom_target( XRayView SOURCES
    __init__.py
    xray.shader
    xray_composite.shader
    XRayPass.py
    XRayView.py
)

subdirs( avr_isp )
