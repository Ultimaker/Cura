[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;
    uniform highp int u_layer_view_type;

    attribute highp float a_extruder;
    attribute highp float a_line_type;
    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    attribute lowp vec4 a_material_color;
    attribute highp float a_vertex_index;

    varying lowp vec4 v_color;
    varying float v_line_type;
    varying highp float v_vertex_index;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        // shade the color depending on the extruder index
        v_color = a_color;
        // 8 and 9 are travel moves
        if ((a_line_type != 8.0) && (a_line_type != 9.0)) {
            v_color = (a_extruder == u_active_extruder) ? v_color : vec4(u_shade_factor * v_color.rgb, v_color.a);
        }

        v_line_type = a_line_type;
        v_vertex_index = a_vertex_index;
    }

fragment =
    #ifdef GL_ES
        #ifdef GL_FRAGMENT_PRECISION_HIGH
            precision highp float;
        #else
            precision mediump float;
        #endif // GL_FRAGMENT_PRECISION_HIGH
    #endif // GL_ES
    varying lowp vec4 v_color;
    varying float v_line_type;
    varying highp float v_vertex_index;

    uniform int u_show_travel_moves;
    uniform int u_show_helpers;
    uniform int u_show_skin;
    uniform int u_show_infill;

    uniform highp vec2 u_drawRange;

    void main()
    {
        if (u_drawRange.x >= 0.0 && u_drawRange.y >= 0.0 && (v_vertex_index < u_drawRange.x || v_vertex_index > u_drawRange.y))
        {
            discard;
        }
        if ((u_show_travel_moves == 0) && (v_line_type >= 7.5) && (v_line_type <= 9.5)) {  // actually, 8 and 9
            // discard movements
            discard;
        }
        // support: 4, 5, 7, 10, 11 (prime tower)
        if ((u_show_helpers == 0) && (
            ((v_line_type >= 3.5) && (v_line_type <= 4.5)) ||
            ((v_line_type >= 4.5) && (v_line_type <= 5.5)) ||
            ((v_line_type >= 6.5) && (v_line_type <= 7.5)) ||
            ((v_line_type >= 9.5) && (v_line_type <= 10.5)) ||
            ((v_line_type >= 10.5) && (v_line_type <= 11.5))
            )) {
            discard;
        }
        // skin: 1, 2, 3
        if ((u_show_skin == 0) && (
            (v_line_type >= 0.5) && (v_line_type <= 3.5)
            )) {
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
u_extruder_opacity = [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]

u_show_travel_moves = 0
u_show_helpers = 1
u_show_skin = 1
u_show_infill = 1

u_drawRange = [-1.0, -1.0]

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_drawRange = draw_range

[attributes]
a_vertex = vertex
a_color = color
a_extruder = extruder
a_line_type = line_type
a_material_color = material_color
a_vertex_index = vertex_index
