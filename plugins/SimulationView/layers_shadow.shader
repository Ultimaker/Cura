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

    varying lowp vec4 v_color;
    varying float v_line_type;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        // shade the color depending on the extruder index
        v_color = vec4(0.4, 0.4, 0.4, 0.9);    // default color for not current layer;
        // 8 and 9 are travel moves
        // if ((a_line_type != 8.0) && (a_line_type != 9.0)) {
        //     v_color = (a_extruder == u_active_extruder) ? v_color : vec4(u_shade_factor * v_color.rgb, v_color.a);
        // }

        v_line_type = a_line_type;
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

    uniform int u_show_travel_moves;
    uniform int u_show_helpers;
    uniform int u_show_skin;
    uniform int u_show_infill;

    void main()
    {
        if ((u_show_travel_moves == 0) && (v_line_type >= 7.5) && (v_line_type <= 9.5))
        {  // actually, 8 and 9
            // discard movements
            discard;
        }
        // support: 4, 5, 7, 10, 11
        if ((u_show_helpers == 0) && (
            ((v_line_type >= 3.5) && (v_line_type <= 4.5)) ||
            ((v_line_type >= 6.5) && (v_line_type <= 7.5)) ||
            ((v_line_type >= 9.5) && (v_line_type <= 10.5)) ||
            ((v_line_type >= 4.5) && (v_line_type <= 5.5)) ||
            ((v_line_type >= 10.5) && (v_line_type <= 11.5))
            ))
        {
            discard;
        }

        // skin: 1, 2, 3
        if ((u_show_skin == 0) && (
            (v_line_type >= 0.5) && (v_line_type <= 3.5)
            )) {
            discard;
        }
        // infill:
        if ((u_show_infill == 0) && (v_line_type >= 5.5) && (v_line_type <= 6.5))
        {
            // discard movements
            discard;
        }

        gl_FragColor = v_color;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;
    uniform highp int u_layer_view_type;

    in highp float a_extruder;
    in highp float a_line_type;
    in highp vec4 a_vertex;
    in lowp vec4 a_color;
    in lowp vec4 a_material_color;

    out lowp vec4 v_color;
    out float v_line_type;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        v_color = vec4(0.4, 0.4, 0.4, 0.9);    // default color for not current layer
        // if ((a_line_type != 8) && (a_line_type != 9)) {
        //     v_color = (a_extruder == u_active_extruder) ? v_color : vec4(u_shade_factor * v_color.rgb, v_color.a);
        // }

        v_line_type = a_line_type;
    }

fragment41core =
    #version 410
    in lowp vec4 v_color;
    in float v_line_type;
    out vec4 frag_color;

    uniform int u_show_travel_moves;
    uniform int u_show_helpers;
    uniform int u_show_skin;
    uniform int u_show_infill;

    void main()
    {
        if ((u_show_travel_moves == 0) && (v_line_type >= 7.5) && (v_line_type <= 9.5)) {  // actually, 8 and 9
            // discard movements
            discard;
        }
        // helpers: 4, 5, 7, 10, 11
        if ((u_show_helpers == 0) && (
            ((v_line_type >= 3.5) && (v_line_type <= 4.5)) ||
            ((v_line_type >= 6.5) && (v_line_type <= 7.5)) ||
            ((v_line_type >= 9.5) && (v_line_type <= 10.5)) ||
            ((v_line_type >= 4.5) && (v_line_type <= 5.5)) ||
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

        frag_color = v_color;
    }

[defaults]
u_active_extruder = 0.0
u_shade_factor = 0.60
u_layer_view_type = 0
u_extruder_opacity = [1.0, 1.0, 1.0, 1.0]

u_show_travel_moves = 0
u_show_helpers = 1
u_show_skin = 1
u_show_infill = 1

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix

[attributes]
a_vertex = vertex
a_color = color
a_extruder = extruder
a_line_type = line_type
a_material_color = material_color
