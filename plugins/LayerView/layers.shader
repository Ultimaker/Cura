[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;
    uniform highp int u_layer_view_type;
    uniform highp int u_only_color_active_extruder;

    attribute highp int a_extruder;
    attribute highp int a_line_type;
    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    attribute lowp vec4 a_material_color;

    varying lowp vec4 v_color;
    varying float v_line_type;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        v_color = a_color;
        if ((u_only_color_active_extruder == 1) && (a_line_type != 8) && (a_line_type != 9)) {
            v_color = (a_extruder == u_active_extruder) ? v_color : vec4(0.4, 0.4, 0.4, v_color.a);
        }
        if ((u_only_color_active_extruder == 0) && (a_line_type != 8) && (a_line_type != 9)) {
            v_color = (a_extruder == u_active_extruder) ? v_color : vec4(u_shade_factor * v_color.rgb, v_color.a);
        }

        v_line_type = a_line_type;
    }

fragment =
    varying lowp vec4 v_color;
    varying float v_line_type;

    uniform int u_show_travel_moves;
    uniform int u_show_support;
    uniform int u_show_adhesion;
    uniform int u_show_skin;
    uniform int u_show_infill;

    void main()
    {
        if ((u_show_travel_moves == 0) && (v_line_type >= 7.5) && (v_line_type <= 9.5)) {  // actually, 8 and 9
            // discard movements
            discard;
        }
        // support: 4, 7, 10
        if ((u_show_support == 0) && (
            ((v_line_type >= 3.5) && (v_line_type <= 4.5)) ||
            ((v_line_type >= 6.5) && (v_line_type <= 7.5)) ||
            ((v_line_type >= 9.5) && (v_line_type <= 10.5))
            )) {
            discard;
        }
        // skin: 1, 2, 3
        if ((u_show_skin == 0) && (
            (v_line_type >= 0.5) && (v_line_type <= 3.5)
            )) {
            discard;
        }
        // adhesion:
        if ((u_show_adhesion == 0) && (v_line_type >= 4.5) && (v_line_type <= 5.5)) {
            // discard movements
            discard;
        }
        // infill:
        if ((u_show_infill == 0) && (v_line_type >= 5.5) && (v_line_type <= 6.5)) {
            // discard movements
            discard;
        }

        gl_FragColor = v_color;
    }

[defaults]
u_active_extruder = 0.0
u_shade_factor = 0.60
u_layer_view_type = 0
u_only_color_active_extruder = 1
u_extruder_opacity = [1.0, 1.0, 1.0, 1.0]

u_show_travel_moves = 0
u_show_support = 1
u_show_adhesion = 1
u_show_skin = 1
u_show_infill = 1

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
a_color = color
a_extruder = extruder
a_line_type = line_type
a_material_color = material_color
